#!/usr/bin/env python3
"""
Gmail sender with multiple authentication methods.

Usage:
    python send_gmail.py --to EMAIL --to-name NAME --subject SUBJ --template TMPL --vars JSON

Authentication Priority (first match wins):
    1. SMTP with App Password (simplest, never expires)
       - Env: GMAIL_SENDER_EMAIL + GMAIL_APP_PASSWORD

    2. Service Account (never expires - for Google Workspace admins)
       - File: service-account.json OR Env: GOOGLE_SERVICE_ACCOUNT
       - Requires: GMAIL_SENDER_EMAIL

    3. OAuth2 Token (may expire after ~6 months)
       - File: token.json OR Env: GOOGLE_TOKEN
"""

import argparse
import base64
import json
import os
import re
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Lazy imports for Google libraries (only needed for OAuth/Service Account)
def _import_google_libs():
    global Request, Credentials, service_account, InstalledAppFlow, build, HttpError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SERVICE_ACCOUNT_FILE = PROJECT_ROOT / 'service-account.json'
CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
TOKEN_FILE = PROJECT_ROOT / 'token.json'
TEMPLATES_DIR = Path(__file__).parent / 'templates'

# Default logo URL
DEFAULT_LOGO_URL = "https://i.imgur.com/EeWMfvf.png"

# OAuth scope for sending emails (only used for OAuth/Service Account methods)
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def send_email_smtp(sender_email: str, app_password: str, to: str, to_name: str, subject: str, html_body: str) -> dict:
    """Send email via SMTP with App Password. Simplest method, never expires."""
    message = MIMEMultipart('alternative')
    message['From'] = sender_email
    message['To'] = f'{to_name} <{to}>'
    message['Subject'] = subject

    # Plain text fallback
    plain_text = html_to_plain_text(html_body)
    message.attach(MIMEText(plain_text, 'plain'))
    message.attach(MIMEText(html_body, 'html'))

    # Connect to Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.send_message(message)

    return {'id': 'smtp', 'threadId': 'smtp'}


def get_gmail_service_with_service_account(sender_email: str):
    """Authenticate using Service Account with domain-wide delegation.

    This method never expires and is recommended for Google Workspace.
    """
    _import_google_libs()
    sa_creds = None

    # Try environment variable first
    sa_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
    if sa_json:
        try:
            sa_info = json.loads(sa_json)
            sa_creds = service_account.Credentials.from_service_account_info(
                sa_info, scopes=SCOPES
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Invalid GOOGLE_SERVICE_ACCOUNT env var: {e}", file=sys.stderr)
            sa_creds = None

    # Fall back to file
    if not sa_creds and SERVICE_ACCOUNT_FILE.exists():
        sa_creds = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE), scopes=SCOPES
        )

    if sa_creds:
        # Delegate to the sender's email (impersonate the user)
        delegated_creds = sa_creds.with_subject(sender_email)
        return build('gmail', 'v1', credentials=delegated_creds)

    return None


def get_gmail_service_with_oauth():
    """Authenticate using OAuth2 (legacy method - tokens may expire)."""
    _import_google_libs()
    creds = None

    # Try environment variable first (for cloud deployment)
    google_token = os.environ.get('GOOGLE_TOKEN')
    if google_token:
        try:
            token_data = json.loads(google_token)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Invalid GOOGLE_TOKEN env var: {e}", file=sys.stderr)
            creds = None

    # Fall back to file-based token
    if not creds and TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            if not google_token:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            else:
                print("Note: Token was refreshed. Update GOOGLE_TOKEN env var with new token.", file=sys.stderr)
        else:
            # Need to do initial OAuth flow - requires credentials.json
            google_creds = os.environ.get('GOOGLE_CREDENTIALS')

            if google_creds:
                try:
                    creds_data = json.loads(google_creds)
                    flow = InstalledAppFlow.from_client_config(creds_data, SCOPES)
                    creds = flow.run_local_server(port=0)
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"ERROR: Invalid GOOGLE_CREDENTIALS env var: {e}", file=sys.stderr)
                    return None
            elif CREDENTIALS_FILE.exists():
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)
            else:
                return None

            # Save token for future use (file-based only)
            if not google_token and creds:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())

    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)

    return None


def get_gmail_service(sender_email: str = None):
    """Get Gmail service using best available authentication method.

    Priority:
    1. Service Account (never expires) - requires sender_email for delegation
    2. OAuth2 (may expire)
    """
    # Get sender email from arg, env, or None
    sender = sender_email or os.environ.get('GMAIL_SENDER_EMAIL')

    # Try Service Account first (recommended - never expires)
    if sender:
        service = get_gmail_service_with_service_account(sender)
        if service:
            print(f"Authenticated via Service Account (delegating to {sender})", file=sys.stderr)
            return service

    # Fall back to OAuth2
    service = get_gmail_service_with_oauth()
    if service:
        print("Authenticated via OAuth2", file=sys.stderr)
        return service

    # No valid auth method found
    print("ERROR: No valid credentials found.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Option 1 - Service Account (recommended, never expires):", file=sys.stderr)
    print("  - Place service-account.json in project root", file=sys.stderr)
    print("  - Set GMAIL_SENDER_EMAIL env var to your email", file=sys.stderr)
    print("  - Or use --sender flag", file=sys.stderr)
    print("", file=sys.stderr)
    print("Option 2 - OAuth2 (tokens may expire):", file=sys.stderr)
    print("  - Place credentials.json in project root", file=sys.stderr)
    print("  - Run once locally to generate token.json", file=sys.stderr)
    sys.exit(1)


def load_template(template_name: str) -> str:
    """Load HTML template from templates directory."""
    template_path = TEMPLATES_DIR / f'{template_name}_email.html'
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(encoding='utf-8')


def render_template(template: str, variables: dict) -> str:
    """Replace {variable} placeholders with values."""
    result = template
    for key, value in variables.items():
        result = result.replace(f'{{{key}}}', str(value))
    return result


def html_to_plain_text(html: str) -> str:
    """Convert HTML to plain text for email fallback."""
    # Replace common HTML elements
    text = html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = text.replace('</p>', '\n\n').replace('</div>', '\n')
    text = text.replace('</li>', '\n').replace('<li>', '  - ')
    text = text.replace('</h1>', '\n\n').replace('</h2>', '\n\n')
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def create_message(to: str, to_name: str, subject: str, html_body: str) -> dict:
    """Create email message in Gmail API format."""
    message = MIMEMultipart('alternative')
    message['to'] = f'{to_name} <{to}>'
    message['subject'] = subject

    # Plain text fallback
    plain_text = html_to_plain_text(html_body)

    message.attach(MIMEText(plain_text, 'plain'))
    message.attach(MIMEText(html_body, 'html'))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw}


def send_email(service, message: dict) -> dict:
    """Send email via Gmail API."""
    _import_google_libs()
    try:
        result = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        return result
    except HttpError as error:
        print(f"Gmail API error: {error}", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description='Send email via Gmail API')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--to-name', required=True, help='Recipient name')
    parser.add_argument('--subject', required=True, help='Email subject')
    parser.add_argument('--template', required=True, help='Template name (without _email.html)')
    parser.add_argument('--vars', required=True, help='JSON object with template variables')
    parser.add_argument('--sender', help='Sender email (required for Service Account auth, or set GMAIL_SENDER_EMAIL env var)')
    parser.add_argument('--smtp-password', help='SMTP App Password (or set GMAIL_APP_PASSWORD env var)')

    args = parser.parse_args()

    # Parse template variables
    try:
        variables = json.loads(args.vars)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in --vars: {e}", file=sys.stderr)
        sys.exit(1)

    # Add default logo_url if not provided
    if 'logo_url' not in variables:
        variables['logo_url'] = DEFAULT_LOGO_URL

    # Load and render template
    try:
        template = load_template(args.template)
        html_body = render_template(template, variables)
        subject = render_template(args.subject, variables)
    except FileNotFoundError as e:
        print(f"Template error: {e}", file=sys.stderr)
        sys.exit(1)

    # Check for SMTP credentials first (simplest, recommended)
    sender_email = args.sender or os.environ.get('GMAIL_SENDER_EMAIL')
    app_password = args.smtp_password or os.environ.get('GMAIL_APP_PASSWORD')

    if sender_email and app_password:
        # Use SMTP - simplest method, never expires
        print(f"Sending via SMTP as {sender_email}...", file=sys.stderr)
        try:
            result = send_email_smtp(sender_email, app_password, args.to, args.to_name, subject, html_body)
            print(f"Email sent successfully via SMTP!")
            return
        except Exception as e:
            print(f"SMTP failed: {e}", file=sys.stderr)
            print("Falling back to API methods...", file=sys.stderr)

    # Fall back to API methods (OAuth/Service Account)
    service = get_gmail_service(sender_email=args.sender)
    message = create_message(args.to, args.to_name, subject, html_body)
    result = send_email(service, message)

    print(f"Email sent successfully!")
    print(f"Message ID: {result['id']}")
    print(f"Thread ID: {result['threadId']}")


if __name__ == '__main__':
    main()
