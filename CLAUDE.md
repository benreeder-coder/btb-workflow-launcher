
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

### Common Commands
```bash
# Start local dev server
python -m uvicorn execution.api_server:app --reload --port 8000

# Deploy to Railway (auto-deploys on push)
git push origin main

# Manual Railway deploy
railway up
```

### Key URLs
- **Local:** http://localhost:8000
- **Production:** https://web-production-42e73.up.railway.app/
- **Repo:** https://github.com/benreeder-coder/btb-workflow-launcher

---

# Agent Instructions

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- Basically just SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level employee

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings
- You're the glue between intent and execution. E.g you don't try scraping websites yourself—you read `directives/scrape_website.md` and come up with inputs/outputs and then run `execution/scrape_single_site.py`

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Environment variables, api tokens, etc are stored in `.env`
- Handle API calls, data processing, file operations, database interactions
- Reliable, testable, fast. Use scripts instead of manual work.

**Why this works:** if you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. The solution is push complexity into deterministic code. That way you just focus on decision-making.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check w user first)
- Update the directive with what you learned (API limits, timing, edge cases)
- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite script to accommodate → test → update directive.

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

## Self-annealing loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test tool, make sure it works
4. Update directive to include new flow
5. System is now stronger

## File Organization

**Deliverables vs Intermediates:**
- **Deliverables**: Google Sheets, Google Slides, or other cloud-based outputs that the user can access
- **Intermediates**: Temporary files needed during processing

**Directory structure:**
- `.tmp/` - All intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.
- `execution/` - Python scripts (the deterministic tools)
- `directives/` - SOPs in Markdown (the instruction set)
- `frontend/` - Web UI for workflow launcher dashboard
- `.env` - Environment variables and API keys
- `credentials.json`, `token.json` - Google OAuth credentials (required files, in `.gitignore`)

**Key principle:** Local files are only for processing. Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Everything in `.tmp/` can be deleted and regenerated.

## Building New Workflows

When creating a new workflow, follow this exact process to ensure it works in both CLI and the web UI.

### Step 1: Create the Directive

Create a new markdown file in `directives/` with this exact structure:

```markdown
# Workflow Title

One-sentence description of what this workflow does.

## Trigger

User says: "trigger phrase with [variable1] and [variable2]"

Examples:
- "example trigger phrase"

## Inputs

| Input | Required | Source | Description |
|-------|----------|--------|-------------|
| input_name | Yes | Parsed from trigger | What this input is for |
| another_input | Yes | Default | Another input with a default value |
| optional_input | No | Default | Optional input |

## Defaults

| Field | Value |
|-------|-------|
| another_input | Default value here |
| optional_input | Optional default |

## Tools/Scripts

**Primary script:** `execution/your_script.py`

## Execution Flow

1. **Step one** - Description
2. **Step two** - Description
3. **Step three** - Description

## Script Usage

```bash
python execution/your_script.py \
  --arg1 "value1" \
  --arg2 "value2" \
  --vars '{"key": "value"}'
```

## Outputs

- What the workflow returns on success

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Error case | How to handle it |
```

### Step 2: Create the Execution Script

Create a Python script in `execution/` that:
1. Uses argparse for CLI arguments
2. Returns clear success/error messages
3. Handles errors gracefully

Example pattern:
```python
#!/usr/bin/env python3
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description='Your script description')
    parser.add_argument('--input1', required=True, help='First input')
    parser.add_argument('--vars', required=True, help='JSON object with variables')
    args = parser.parse_args()

    variables = json.loads(args.vars)

    # Do the work
    result = do_something(args.input1, variables)

    print(f"Success! Result: {result}")

if __name__ == '__main__':
    main()
```

### Step 3: Register in API Server

Add the workflow execution logic to `execution/api_server.py`:

1. Add a handler function:
```python
def execute_your_workflow(inputs: dict) -> dict:
    vars_dict = {
        "key1": inputs.get("input_name", ""),
        "key2": inputs.get("another_input", "default"),
    }

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "execution" / "your_script.py"),
        "--input1", inputs.get("input_name", ""),
        "--vars", json.dumps(vars_dict)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")

    return {"output": result.stdout}
```

2. Register it in `execute_workflow()`:
```python
def execute_workflow(workflow: dict, inputs: dict) -> dict:
    workflow_id = workflow["id"]

    if workflow_id == "onboard_new_user":
        return execute_onboard_new_user(inputs)

    if workflow_id == "your_workflow_name":  # Add this
        return execute_your_workflow(inputs)

    # ... rest of function
```

### Step 4: Test Locally

```bash
# Start the server
python -m uvicorn execution.api_server:app --reload --port 8000

# Open browser to http://localhost:8000
# Your new workflow should appear in the grid
```

### Step 5: Commit and Deploy

```bash
git add directives/your_workflow.md execution/your_script.py execution/api_server.py
git commit -m "Add your_workflow workflow"
git push

# If deployed to Railway, it auto-deploys on push
```

## Frontend Dashboard

The workflow launcher dashboard (`frontend/index.html`) automatically:
- Scans `directives/` for available workflows
- Parses markdown to extract inputs and defaults
- Generates dynamic forms with pre-filled defaults
- Executes workflows via the API

**To run locally:**
```bash
python -m uvicorn execution.api_server:app --reload --port 8000
# Open http://localhost:8000
```

**Key files:**
- `execution/api_server.py` - FastAPI backend serving workflows + frontend
- `execution/directive_parser.py` - Parses directive markdown into JSON
- `frontend/index.html` - Single-page app with dark purple theme

## Deployment (Railway)

The app is configured for Railway deployment:

**To deploy:**
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize project: `railway init`
4. Deploy: `railway up`

**Files:**
- `Procfile` - Tells Railway how to start the app
- `railway.json` - Railway configuration
- `requirements.txt` - Python dependencies

**Environment variables needed in Railway:**
- Copy contents of `credentials.json` to `GOOGLE_CREDENTIALS` env var
- Set any other secrets from `.env`

**Note:** For Gmail workflows to work in production, you'll need to:
1. Use a service account OR
2. Store OAuth tokens securely (more complex)

## GitHub Repository

**Repo:** https://github.com/benreeder-coder/btb-workflow-launcher

## Cloud Webhooks (Modal)

The system supports event-driven execution via Modal webhooks. Each webhook maps to exactly one directive with scoped tool access.

**When user says "add a webhook that...":**
1. Read `directives/add_webhook.md` for complete instructions
2. Create the directive file in `directives/`
3. Add entry to `execution/webhooks.json`
4. Deploy: `modal deploy execution/modal_webhook.py`
5. Test the endpoint

**Key files:**
- `execution/webhooks.json` - Webhook slug → directive mapping
- `execution/modal_webhook.py` - Modal app (do not modify unless necessary)
- `directives/add_webhook.md` - Complete setup guide

**Endpoints:**
- `https://nick-90891--claude-orchestrator-list-webhooks.modal.run` - List webhooks
- `https://nick-90891--claude-orchestrator-directive.modal.run?slug={slug}` - Execute directive
- `https://nick-90891--claude-orchestrator-test-email.modal.run` - Test email

**Available tools for webhooks:** `send_email`, `read_sheet`, `update_sheet`

**All webhook activity streams to Slack in real-time.**

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

Also, use Opus-4.5 for everything while building. It came out a few days ago and is an order of magnitude better than Sonnet and other models. If you can't find it, look it up first.