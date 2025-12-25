"""
Workflow Launcher API Server

FastAPI backend that:
- Lists available workflows from directives/
- Returns workflow details with inputs and defaults
- Executes workflows via their execution scripts
- Serves the frontend
- Client Hub: Task management with Supabase backend
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add execution directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from directive_parser import parse_directive, scan_directives

# Import Client Hub router (conditional to avoid errors if Supabase not configured)
try:
    from client_hub.router import router as client_hub_router
    from client_hub.webhooks import router as webhooks_router
    CLIENT_HUB_AVAILABLE = True
except ImportError as e:
    CLIENT_HUB_AVAILABLE = False
    print(f"Client Hub not available: {e}")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DIRECTIVES_DIR = PROJECT_ROOT / "directives"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# FastAPI app
app = FastAPI(
    title="Workflow Launcher API",
    description="Execute workflows defined in directives/",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Client Hub routers if available
if CLIENT_HUB_AVAILABLE:
    app.include_router(client_hub_router)
    app.include_router(webhooks_router)


class WorkflowRunRequest(BaseModel):
    inputs: dict[str, Any]


@app.get("/api/workflows")
def list_workflows():
    """List all available workflows."""
    workflows = scan_directives(DIRECTIVES_DIR)
    # Return summary for list view
    return {
        "workflows": [
            {
                "id": w["id"],
                "title": w["title"],
                "description": w["description"],
                "input_count": len(w["inputs"]),
            }
            for w in workflows
        ]
    }


@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    """Get full workflow details including inputs and defaults."""
    md_file = DIRECTIVES_DIR / f"{workflow_id}.md"
    if not md_file.exists():
        raise HTTPException(status_code=404, detail="Workflow not found")
    return parse_directive(md_file)


@app.post("/api/workflows/{workflow_id}/run")
def run_workflow(workflow_id: str, request: WorkflowRunRequest):
    """Execute a workflow with provided inputs."""
    md_file = DIRECTIVES_DIR / f"{workflow_id}.md"
    if not md_file.exists():
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = parse_directive(md_file)

    # Merge defaults with provided inputs (user inputs override defaults)
    final_inputs = {**workflow["defaults"], **request.inputs}

    # Execute based on workflow type
    try:
        result = execute_workflow(workflow, final_inputs)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def execute_workflow(workflow: dict, inputs: dict) -> dict:
    """
    Execute the workflow script with inputs.

    Each workflow type has its own execution logic.
    """
    workflow_id = workflow["id"]

    if workflow_id == "onboard_new_user":
        return execute_onboard_new_user(inputs)

    # Generic fallback - attempt to run script directly if defined
    if workflow.get("script_path"):
        return execute_generic_script(workflow, inputs)

    raise ValueError(f"Unknown workflow type: {workflow_id}")


def execute_onboard_new_user(inputs: dict) -> dict:
    """Execute the onboarding email workflow via n8n webhook."""
    import urllib.request
    import urllib.error

    # n8n webhook URL
    webhook_url = "https://breeder80.app.n8n.cloud/webhook/btb-onboard"

    # Build payload for n8n
    payload = {
        "to": inputs.get("recipient_email", ""),
        "to_name": inputs.get("recipient_name", ""),
        "subject": f"Welcome to {inputs.get('company_name', 'BTB AI')} - Let's Schedule Your Kickoff!",
        "recipient_name": inputs.get("recipient_name", ""),
        "company_name": inputs.get("company_name", "BTB AI"),
        "company_description": inputs.get("company_description", "We build AI-powered automation solutions for businesses"),
        "sender_name": inputs.get("sender_name", "Ben"),
        "sender_title": inputs.get("sender_title", "Founder"),
        "cal_link": "https://cal.com/btb-ai/kickoff-call"
    }

    # Send to n8n webhook
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            return {
                "output": f"Email triggered via n8n: {result}",
                "recipient": inputs.get("recipient_email", ""),
                "recipient_name": inputs.get("recipient_name", "")
            }
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"n8n webhook error {e.code}: {e.read().decode('utf-8')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"n8n webhook connection error: {e.reason}")


def execute_generic_script(workflow: dict, inputs: dict) -> dict:
    """
    Generic script execution for future workflows.

    This is a placeholder for workflows that don't have custom execution logic.
    """
    raise NotImplementedError(f"Generic execution not yet implemented for: {workflow['id']}")


# Serve frontend
@app.get("/")
def serve_frontend():
    """Serve the frontend HTML."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


# Mount static assets if the folder exists
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

# Mount client-hub static files if the folder exists
if (FRONTEND_DIR / "client-hub").exists():
    app.mount("/client-hub", StaticFiles(directory=FRONTEND_DIR / "client-hub"), name="client-hub")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
