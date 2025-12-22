#!/usr/bin/env python3
"""
Gmail sender using OAuth2 authentication.

Usage:
    python send_gmail.py --to EMAIL --to-name NAME --subject SUBJ --template TMPL --vars JSON

Requirements:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import argparse
import base64
import json
import re
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OAuth scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
TOKEN_FILE = PROJECT_ROOT / 'token.json'
TEMPLATES_DIR = Path(__file__).parent / 'templates'

# Default logo URL
DEFAULT_LOGO_URL = "https://i.imgur.com/EeWMfvf.png"


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found.", file=sys.stderr)
                print("Download OAuth credentials from Google Cloud Console.", file=sys.stderr)
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


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

    # Authenticate and send
    service = get_gmail_service()
    message = create_message(args.to, args.to_name, subject, html_body)
    result = send_email(service, message)

    print(f"Email sent successfully!")
    print(f"Message ID: {result['id']}")
    print(f"Thread ID: {result['threadId']}")


if __name__ == '__main__':
    main()
