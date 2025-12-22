# Onboard New User

Send a personalized onboarding email to a new user, introducing the company and inviting them to a kickoff call.

## Trigger

User says: "onboard [name] at [email@domain.com]"

Examples:
- "onboard Sarah at sarah@acme.com"
- "onboard John Smith at john.smith@example.org"
- "Onboard Maria Garcia at maria@startup.io"

## Inputs

| Input | Required | Source | Description |
|-------|----------|--------|-------------|
| recipient_name | Yes | Parsed from trigger | Full name of the person being onboarded |
| recipient_email | Yes | Parsed from trigger | Email address to send to |
| company_name | Yes | Default | Name of the company doing the onboarding |
| company_description | Yes | Default | 1-2 sentence description of what the company does |
| sender_name | Yes | Default | Name of the person sending (for signature) |
| sender_title | No | Default | Title/role of sender (optional) |

## Defaults

Use these values automatically—do not ask unless the user specifies otherwise:

| Field | Value |
|-------|-------|
| company_name | BTB AI |
| company_description | We build AI-powered automation solutions for businesses |
| sender_name | Ben |
| sender_title | Founder |

## Tools/Scripts

**Primary script:** `execution/send_gmail.py`

**Required credentials:**
- `credentials.json` - OAuth client credentials from Google Cloud Console
- `token.json` - Auto-generated refresh token (created on first run)

## Execution Flow

1. **Parse the trigger** - Extract recipient name and email from user's request
2. **Use defaults** - Apply default company/sender info (do not ask)
3. **Validate email** - Basic format validation
4. **Compose email** - Use template with provided information
5. **Send via Gmail API** - Run execution script
6. **Confirm success** - Report back to user

## Script Usage

```bash
python execution/send_gmail.py \
  --to "recipient@example.com" \
  --to-name "Recipient Name" \
  --subject "Welcome to {company_name} - Let's Schedule Your Kickoff!" \
  --template "onboarding" \
  --vars '{"recipient_name": "...", "company_name": "...", "company_description": "...", "sender_name": "...", "sender_title": "...", "cal_link": "https://cal.com/btb-ai/kickoff-call"}'
```

## Outputs

- Email sent confirmation with message ID
- Recipient name and email echoed back

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Invalid email format | Reject and ask for correction |
| Gmail API auth expired | Prompt to re-run OAuth flow |
| Rate limit hit | Wait and retry, inform user of delay |
| Missing company info | Ask before proceeding |
| Email send fails | Show error, suggest checking credentials |
| Missing sender_title | Use empty string (optional field) |

## Email Content

**Subject:** `Welcome to {company_name} - Let's Schedule Your Kickoff!`

**Body includes:**
1. Personalized greeting with recipient name
2. Company introduction (from provided description)
3. What to expect in the kickoff call
4. Cal.com scheduling link button
5. Warm sign-off with sender name/title

## Constants

- **Cal.com link:** `https://cal.com/btb-ai/kickoff-call`
- **Email template:** `execution/templates/onboarding_email.html`

## Notes

- Company info is provided fresh each time (not stored)
- First run will open browser for OAuth consent
- Token auto-refreshes; manual re-auth only needed if refresh fails
