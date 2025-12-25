# Project Context Resume

Last updated: December 23, 2024

## Project Overview

**BTB Workflow Launcher** - A web-based workflow automation dashboard that triggers business workflows via a clean UI. Built with FastAPI backend and vanilla JS frontend, deployed on Railway.

**Live URL:** https://web-production-42e73.up.railway.app/
**Repo:** https://github.com/benreeder-coder/btb-workflow-launcher

## Current Architecture

```
User clicks "Run Workflow" in UI
        ↓
Frontend (index.html) → POST /api/workflows/{id}/run
        ↓
api_server.py → Routes to workflow handler
        ↓
Workflow handler → Calls external service (n8n webhook)
        ↓
n8n handles email/automation
        ↓
Returns result to UI
```

## Working Workflows

### 1. Onboard New User
- **Trigger:** User fills form with recipient email, name, company info
- **Action:** Sends data to n8n webhook, n8n sends styled HTML email
- **Webhook:** `https://breeder80.app.n8n.cloud/webhook/btb-onboard`
- **Handler:** `execute_onboard_new_user()` in `api_server.py:120`

**Payload sent to n8n:**
```json
{
  "to": "recipient@email.com",
  "to_name": "Recipient Name",
  "subject": "Welcome to BTB AI - Let's Schedule Your Kickoff!",
  "recipient_name": "Recipient Name",
  "company_name": "BTB AI",
  "company_description": "...",
  "sender_name": "Ben",
  "sender_title": "Founder",
  "cal_link": "https://cal.com/btb-ai/kickoff-call"
}
```

## Key Files

| File | Purpose |
|------|---------|
| `execution/api_server.py` | FastAPI backend, workflow routing, webhook calls |
| `execution/directive_parser.py` | Parses markdown directives into JSON for UI |
| `frontend/index.html` | Single-page dashboard UI |
| `directives/*.md` | Workflow definitions (parsed for UI forms) |
| `execution/templates/*.html` | Email templates (reference only - n8n has the live templates) |

## How to Create a New Workflow

### Step 1: Create the Directive
Create `directives/your_workflow.md`:

```markdown
# Your Workflow Title

One-sentence description.

## Trigger

User says: "do something with [input1] and [input2]"

## Inputs

| Input | Required | Source | Description |
|-------|----------|--------|-------------|
| input1 | Yes | Parsed from trigger | What this is |
| input2 | No | Default | Optional input |

## Defaults

| Field | Value |
|-------|-------|
| input2 | default value |

## Tools/Scripts

**Primary:** n8n webhook

## Outputs

- What happens on success
```

### Step 2: Create n8n Workflow
1. Create new workflow in n8n
2. Add **Webhook** node as trigger
3. Add your logic nodes (Send Email, HTTP Request, etc.)
4. For emails: paste HTML template with `{{ $json.variable }}` placeholders
5. Activate workflow and copy webhook URL

### Step 3: Add Handler in api_server.py

```python
def execute_your_workflow(inputs: dict) -> dict:
    """Execute your workflow via n8n."""
    import urllib.request

    webhook_url = "https://breeder80.app.n8n.cloud/webhook/your-webhook"

    payload = {
        "field1": inputs.get("input1", ""),
        "field2": inputs.get("input2", "default"),
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            return {"output": f"Success: {result}"}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Webhook error: {e.read().decode('utf-8')}")
```

### Step 4: Register in execute_workflow()

In `api_server.py`, find `execute_workflow()` and add:

```python
if workflow_id == "your_workflow":
    return execute_your_workflow(inputs)
```

### Step 5: Test & Deploy

```bash
# Test locally
python -m uvicorn execution.api_server:app --reload --port 8000

# Deploy (auto-deploys on push)
git add execution/api_server.py directives/your_workflow.md
git commit -m "Add your_workflow"
git push origin main
```

## Email Sending - CRITICAL LESSON

**DO NOT use Gmail SMTP, OAuth, or Resend directly from Railway.**

After hours of debugging:
- Gmail SMTP ports are blocked on Railway
- OAuth tokens expire constantly and refresh is unreliable
- Environment variables don't always pass to subprocesses correctly

**Solution: Use n8n for ALL emails**
1. Create n8n workflow with Webhook trigger
2. Add Gmail or SMTP node in n8n (n8n handles auth properly)
3. Call the webhook from api_server.py with JSON payload
4. n8n sends the email - it just works

## Environment & Deployment

### Local Development
```bash
cd "C:\Users\breed\OneDrive\Desktop\Claude Code UPD\Agentic Workflows"
python -m uvicorn execution.api_server:app --reload --port 8000
# Open http://localhost:8000
```

### Railway Deployment
- Auto-deploys on push to `main` branch
- No environment variables needed (n8n handles email auth)
- Check deploy status in Railway dashboard

### n8n Instance
- URL: https://breeder80.app.n8n.cloud
- Used for: Email sending, scheduled tasks, complex automations
- Webhooks are the integration point between Railway app and n8n

## File Organization

```
Agentic Workflows/
├── execution/
│   ├── api_server.py       # Main backend - EDIT THIS for new workflows
│   ├── directive_parser.py # Parses directive markdown
│   ├── send_gmail.py       # LEGACY - don't use, kept for reference
│   └── templates/          # HTML templates (reference, n8n has live copies)
├── directives/
│   ├── onboard_new_user.md # Working workflow
│   └── TEMPLATE.example.md # Template for new workflows
├── frontend/
│   └── index.html          # Dashboard UI
├── CLAUDE.md               # AI agent instructions
├── CONTEXT_RESUME.md       # This file
├── requirements.txt        # Python dependencies
├── Procfile                # Railway: uvicorn start command
└── railway.json            # Railway build config
```

## Git Workflow

```bash
# Standard flow
git add execution/api_server.py directives/new_workflow.md
git commit -m "Add new workflow"
git push origin main

# Railway auto-deploys in ~1-2 minutes
```

**Warning:** Never commit files with secrets (tokens, API keys, passwords). GitHub will block the push with secret scanning.

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Email not sending from Railway | Use n8n webhook instead of direct email |
| Workflow not appearing in UI | Check directive markdown format, needs proper headers |
| Railway deploy fails | Check logs in Railway dashboard |
| Webhook timeout/hanging | Add `timeout=30` to urllib request |
| "Script failed" error | Check the error message, usually auth or network |
| Button spins forever | Add timeout, check Railway logs |

## Key URLs

| Resource | URL |
|----------|-----|
| Live Dashboard | https://web-production-42e73.up.railway.app/ |
| GitHub Repo | https://github.com/benreeder-coder/btb-workflow-launcher |
| n8n Instance | https://breeder80.app.n8n.cloud |
| Onboard Webhook | https://breeder80.app.n8n.cloud/webhook/btb-onboard |
| RAG Chatbot Webhook | https://breeder80.app.n8n.cloud/webhook/btb-ai-rag-chatbot-agent |
| Cal.com Booking | https://cal.com/btb-ai/kickoff-call |

## Next Steps / Ideas

- [ ] Daily call digest workflow (8 PM trigger via n8n schedule)
- [ ] Weekly call digest workflow (Sunday 8 PM)
- [ ] Integrate RAG chatbot for call summaries
- [ ] Add "Latest Digest" card to dashboard
- [ ] More workflow templates

## Quick Reference

**Start local server:**
```bash
python -m uvicorn execution.api_server:app --reload --port 8000
```

**Deploy:**
```bash
git push origin main
```

**Test webhook manually:**
```bash
curl -X POST https://breeder80.app.n8n.cloud/webhook/btb-onboard \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","to_name":"Test","recipient_name":"Test","company_name":"BTB AI","sender_name":"Ben","cal_link":"https://cal.com/btb-ai/kickoff-call"}'
```

## Recent History

- Switched from Gmail SMTP/OAuth to n8n webhooks for email (Dec 23)
- Added SMTP, Resend support (didn't work on Railway, removed)
- Original Gmail OAuth worked locally but failed in production
- n8n integration is now the stable, working solution
