# n8n Fireflies Integration

This directory contains the LLM prompt and schema for processing Fireflies transcripts in n8n.

## Files

- `fireflies_prompt.txt` - System prompt for Claude/GPT to extract structured data
- `output_schema.json` - JSON Schema for structured output validation

## n8n Workflow Setup

### 1. Fireflies Webhook Trigger
Configure Fireflies to send transcripts to your n8n webhook.

### 2. Extract Domains (Code Node)
```javascript
// Get unique domains from participants
const participants = $input.first().json.participants || [];
const domains = [...new Set(
  participants
    .filter(email => email.includes('@'))
    .map(email => email.split('@')[1].toLowerCase())
    .filter(domain => !domain.includes('gmail') && !domain.includes('outlook'))
)];
return { domains };
```

### 3. Check Client (HTTP Request)
```
GET {{API_BASE_URL}}/api/hub/clients/lookup?domain={{domain}}
Headers:
  Authorization: Bearer {{API_KEY}}
```

### 4. Branch: Client Found?
- **Yes**: Continue to LLM node
- **No**: Send Slack alert and stop

### 5. LLM Node (Claude/GPT)
- System Prompt: Contents of `fireflies_prompt.txt`
- Replace template variables:
  - `{{call_date}}` - From Fireflies payload
  - `{{client_name}}` - From lookup response
  - `{{client_id}}` - From lookup response
  - `{{tomorrow_date}}` - Calculate in Code node
  - `{{friday_date}}` - Calculate in Code node
  - `{{next_monday_date}}` - Calculate in Code node
  - `{{end_of_month_date}}` - Calculate in Code node

### 6. Parse JSON (Code Node)
```javascript
const output = JSON.parse($input.first().json.text);
return {
  call: output.call,
  my_tasks: output.my_tasks,
  client_tasks: output.client_tasks
};
```

### 7. Upsert Call (HTTP Request)
```
POST {{API_BASE_URL}}/api/webhooks/calls/upsert
Headers:
  X-Webhook-Secret: {{WEBHOOK_SECRET}}
Body:
{
  "calls": [{
    "fireflies_id": "{{call.fireflies_id}}",
    "client": { "name": "{{client_name}}", "domain": "{{domain}}" },
    "title": "{{call.title}}",
    ...
  }]
}
```

### 8. Upsert Tasks (HTTP Request)
```
POST {{API_BASE_URL}}/api/webhooks/tasks/upsert
Headers:
  X-Webhook-Secret: {{WEBHOOK_SECRET}}
Body:
{
  "source": { "workflow_id": "fireflies", "run_id": "{{$execution.id}}" },
  "tasks": [... my_tasks array ...]
}
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/hub/clients/lookup` | GET | Check if client exists by domain |
| `/api/hub/clients/{id}/domains` | POST | Add domain to client |
| `/api/webhooks/calls/upsert` | POST | Upsert call records |
| `/api/webhooks/tasks/upsert` | POST | Upsert task records |

## Environment Variables

Set these in n8n:
- `API_BASE_URL` - Your API base URL (e.g., https://your-app.railway.app)
- `WEBHOOK_SECRET` - Secret for webhook authentication
- `SLACK_WEBHOOK_URL` - For unknown client alerts
