"""
Workflow Launcher API Server

FastAPI backend that:
- Lists available workflows from directives/
- Returns workflow details with inputs and defaults
- Executes workflows via their execution scripts
- Serves the frontend
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add execution directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from directive_parser import parse_directive, scan_directives

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
    """Execute the onboarding email workflow."""
    # Build template variables
    vars_dict = {
        "recipient_name": inputs.get("recipient_name", ""),
        "company_name": inputs.get("company_name", "BTB AI"),
        "company_description": inputs.get("company_description", "We build AI-powered automation solutions for businesses"),
        "sender_name": inputs.get("sender_name", "Ben"),
        "sender_title": inputs.get("sender_title", "Founder"),
        "cal_link": "https://cal.com/btb-ai/kickoff-call"
    }

    # SMTP credentials - hardcoded for reliability
    smtp_sender = os.environ.get("GMAIL_SENDER_EMAIL") or "benreeder@builderbenai.com"
    smtp_password = os.environ.get("GMAIL_APP_PASSWORD") or "qxjkwxvkleloefny"

    # Build command
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "execution" / "send_gmail.py"),
        "--to", inputs.get("recipient_email", ""),
        "--to-name", inputs.get("recipient_name", ""),
        "--subject", f"Welcome to {vars_dict['company_name']} - Let's Schedule Your Kickoff!",
        "--template", "onboarding",
        "--vars", json.dumps(vars_dict)
    ]

    # Add SMTP credentials if available
    if smtp_sender:
        cmd.extend(["--sender", smtp_sender])
    if smtp_password:
        cmd.extend(["--smtp-password", smtp_password])

    # Execute with timeout (30 seconds max)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env=os.environ.copy(),
            timeout=30
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Script timed out after 30 seconds - SMTP connection may be blocked")

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")

    return {
        "output": result.stdout,
        "recipient": inputs.get("recipient_email", ""),
        "recipient_name": inputs.get("recipient_name", "")
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
