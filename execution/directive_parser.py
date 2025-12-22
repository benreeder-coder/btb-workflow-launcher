"""
Directive Parser - Extracts workflow metadata from markdown files.

Parses directive files in directives/ folder and returns structured JSON
for the API to serve to the frontend.
"""

import re
from pathlib import Path
from typing import Optional


def parse_markdown_table(content: str) -> list[dict]:
    """
    Parse a markdown table into a list of dictionaries.

    Args:
        content: The table content (lines starting with |)

    Returns:
        List of dicts with column headers as keys
    """
    lines = [line.strip() for line in content.strip().split('\n') if line.strip().startswith('|')]

    if len(lines) < 3:  # Need header, separator, and at least one data row
        return []

    # Parse header row
    headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]

    # Skip separator row (index 1), parse data rows
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if len(cells) == len(headers):
            row = {headers[i].lower().replace(' ', '_'): cells[i] for i in range(len(headers))}
            rows.append(row)

    return rows


def extract_section(content: str, section_name: str) -> Optional[str]:
    """
    Extract content under a specific markdown section header.

    Args:
        content: Full markdown content
        section_name: Name of the section (without ##)

    Returns:
        Content between this section and the next, or None if not found
    """
    pattern = rf'^##\s+{re.escape(section_name)}\s*$'
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

    if not match:
        return None

    start = match.end()

    # Find next section (## or #)
    next_section = re.search(r'^##?\s+', content[start:], re.MULTILINE)

    if next_section:
        end = start + next_section.start()
    else:
        end = len(content)

    return content[start:end].strip()


def parse_directive(filepath: Path) -> dict:
    """
    Parse a single directive markdown file.

    Args:
        filepath: Path to the .md file

    Returns:
        Dictionary with workflow metadata:
        {
            "id": "onboard_new_user",
            "title": "Onboard New User",
            "description": "...",
            "inputs": [...],
            "defaults": {...},
            "script_path": "execution/send_gmail.py"
        }
    """
    content = filepath.read_text(encoding='utf-8')

    # Extract ID from filename
    workflow_id = filepath.stem

    # Extract title from first H1
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else workflow_id.replace('_', ' ').title()

    # Extract description (line right after title)
    # Format is: # Title\n\nDescription paragraph\n\n## Next Section
    lines = content.split('\n')
    description = ""
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('## '):
            # Found title, look for description in next non-empty lines
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('#'):
                    description = next_line
                    break
            break

    # Parse inputs table
    inputs_section = extract_section(content, 'Inputs')
    inputs = []
    if inputs_section:
        raw_inputs = parse_markdown_table(inputs_section)
        for inp in raw_inputs:
            inputs.append({
                "name": inp.get('input', ''),
                "required": inp.get('required', '').lower() == 'yes',
                "source": inp.get('source', ''),
                "description": inp.get('description', '')
            })

    # Parse defaults table
    defaults_section = extract_section(content, 'Defaults')
    defaults = {}
    if defaults_section:
        raw_defaults = parse_markdown_table(defaults_section)
        for d in raw_defaults:
            field = d.get('field', '')
            value = d.get('value', '')
            if field:
                defaults[field] = value

    # Extract script path from Script Usage section
    script_section = extract_section(content, 'Script Usage')
    script_path = None
    if script_section:
        script_match = re.search(r'execution/\w+\.py', script_section)
        if script_match:
            script_path = script_match.group(0)

    # Also check Tools/Scripts section
    if not script_path:
        tools_section = extract_section(content, 'Tools/Scripts')
        if tools_section:
            script_match = re.search(r'execution/\w+\.py', tools_section)
            if script_match:
                script_path = script_match.group(0)

    return {
        "id": workflow_id,
        "title": title,
        "description": description,
        "inputs": inputs,
        "defaults": defaults,
        "script_path": script_path
    }


def scan_directives(directives_dir: Path) -> list[dict]:
    """
    Scan directives folder and parse all markdown files.

    Args:
        directives_dir: Path to directives/ folder

    Returns:
        List of parsed workflow dictionaries
    """
    workflows = []

    for md_file in sorted(directives_dir.glob('*.md')):
        try:
            workflow = parse_directive(md_file)
            workflows.append(workflow)
        except Exception as e:
            print(f"Warning: Failed to parse {md_file}: {e}")
            continue

    return workflows


if __name__ == "__main__":
    # Quick test
    import json

    project_root = Path(__file__).parent.parent
    directives_dir = project_root / "directives"

    workflows = scan_directives(directives_dir)
    print(json.dumps(workflows, indent=2))
