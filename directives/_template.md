# Workflow Title

One-sentence description of what this workflow does.

## Trigger

User says: "trigger phrase with [variable1] and [variable2]"

Examples:
- "example trigger one"
- "example trigger two"

## Inputs

| Input | Required | Source | Description |
|-------|----------|--------|-------------|
| variable1 | Yes | Parsed from trigger | Description of first variable |
| variable2 | Yes | Parsed from trigger | Description of second variable |
| setting1 | Yes | Default | A setting with a default value |
| setting2 | No | Default | Optional setting |

## Defaults

Use these values automatically—do not ask unless the user specifies otherwise:

| Field | Value |
|-------|-------|
| setting1 | Default value |
| setting2 | Optional default |

## Tools/Scripts

**Primary script:** `execution/your_script.py`

**Required credentials:**
- List any credentials or API keys needed

## Execution Flow

1. **Parse the trigger** - Extract variables from user's request
2. **Use defaults** - Apply default settings (do not ask)
3. **Validate inputs** - Basic validation
4. **Execute script** - Run the execution script
5. **Confirm success** - Report back to user

## Script Usage

```bash
python execution/your_script.py \
  --arg1 "value1" \
  --arg2 "value2" \
  --vars '{"key1": "...", "key2": "..."}'
```

## Outputs

- Success confirmation with relevant details
- Any data returned from the workflow

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Invalid input | Reject and ask for correction |
| API error | Show error, suggest checking credentials |
| Rate limit | Wait and retry, inform user of delay |

## Notes

- Add any additional notes or learnings here
- Update this section as you discover edge cases
