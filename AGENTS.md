# AGENTS.md

This file contains guidelines for agentic coding agents operating in this repository.

---

## Project Overview

This is a **skill-creator** system for creating, testing, and improving Claude Code skills. Skills are defined in `SKILL.md` files with YAML frontmatter and markdown body content.

### Directory Structure

```
skills/skill-creator/
├── SKILL.md              # Main skill definition and workflow
├── agents/
│   ├── grader.md         # Agent for evaluating assertions
│   ├── analyzer.md       # Agent for analyzing benchmark results
│   └── comparator.md     # Agent for blind A/B comparisons
├── scripts/
│   ├── run_loop.py       # Main eval + improvement loop
│   ├── run_eval.py       # Run trigger evaluations
│   ├── improve_description.py  # Optimize skill descriptions
│   ├── generate_report.py # Generate HTML reports
│   ├── aggregate_benchmark.py  # Aggregate benchmark results
│   ├── package_skill.py  # Package skills as .skill files
│   ├── quick_validate.py # Validate skill structure
│   └── utils.py          # Shared utilities
├── references/
│   └── schemas.md        # JSON schemas for evals, grading, etc.
└── eval-viewer/
    └── generate_review.py  # Interactive eval viewer
```

---

## Build/Test Commands

### Running Scripts

All scripts are run as Python modules from the `skills/skill-creator/` directory:

```bash
# Run the full eval + improvement loop
python -m scripts.run_loop --eval-set <path> --skill-path <path> --model <model>

# Run trigger evaluation only
python -m scripts.run_eval --eval-set <path> --skill-path <path>

# Generate HTML report
python -m scripts.generate_report <input.json> -o output.html

# Aggregate benchmark results
python -m scripts.aggregate_benchmark <benchmark_dir>

# Package a skill
python -m scripts.package_skill <skill-folder> [output-dir]

# Validate a skill
python -m scripts.quick_validate <skill-directory>
```

### Skill Validation

```bash
# Validate skill structure
python scripts/quick_validate.py <skill-directory>
```

### Running a Single Test

For testing individual scripts or debugging:

```bash
# Test a specific function
python -c "from scripts.utils import parse_skill_md; print(parse_skill_md('skills/my-skill'))"

# Run script with verbose output
python -m scripts.run_eval --eval-set evals.json --skill-path my-skill --verbose
```

### Subprocess Commands Used

Some scripts use `claude -p` as a subprocess:
```bash
# Used by run_eval.py and improve_description.py
claude -p <prompt> --output-format stream-json
```

---

## Code Style Guidelines

### Python Style

- **Python Version**: Python 3.10+
- **Line Length**: 88 characters (Black default)
- **Style Tool**: Black formatter

### Imports

Standard library first, then third-party, then local:

```python
# Standard library
import argparse
import json
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Third-party (if used)
import yaml

# Local imports (use relative paths within package)
from scripts.utils import parse_skill_md
```

### Type Annotations

Use type annotations for function signatures:

```python
def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    ...

def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    ...
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `eval_set`, `skill_path` |
| Functions | snake_case | `parse_skill_md`, `run_eval` |
| Classes | PascalCase | `MyClass` (rarely used) |
| Constants | SCREAMING_SNAKE_CASE | `EXCLUDE_DIRS` |
| Module constants | UPPER_CASE | `MAX_RETRIES` |

### Error Handling

- Use specific exception types
- Include context in error messages
- Use `sys.exit(1)` for CLI errors

```python
if not skill_path.exists():
    print(f"Error: Skill folder not found: {skill_path}", file=sys.stderr)
    sys.exit(1)

try:
    data = json.loads(Path(args.input).read_text())
except json.JSONDecodeError as e:
    print(f"Warning: Invalid JSON: {e}", file=sys.stderr)
    continue
```

### Docstrings

Use docstrings for module-level documentation and complex functions:

```python
#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query and return whether the skill was triggered.

    Creates a command file in .claude/commands/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    """
```

### File Structure for Scripts

1. Shebang line (for executable scripts)
2. Module docstring
3. Imports
4. Constants
5. Helper functions
6. Main functions
7. `if __name__ == "__main__":` block

```python
#!/usr/bin/env python3
"""Module description."""

import argparse
import json
from pathlib import Path

CONSTANT = "value"

def helper():
    ...

def main_function():
    ...

def main():
    parser = argparse.ArgumentParser(...)
    ...

if __name__ == "__main__":
    main()
```

---

## SKILL.md Format

Skills are defined with YAML frontmatter:

```markdown
---
name: skill-name           # kebab-case, lowercase, max 64 chars
description: >              # max 1024 chars, no angle brackets
  Use this skill for X. Trigger when user mentions Y.
compatibility: (optional)    # max 500 chars
---

# Skill Title

Skill content...
```

### Skill Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons)
```

---

## JSON Schemas

Key data formats are defined in `references/schemas.md`:

- **evals.json** - Skill evaluation test cases
- **grading.json** - Assertion grading results
- **benchmark.json** - Aggregated benchmark statistics
- **timing.json** - Execution timing data
- **comparison.json** - Blind comparison results

---

## Workflow Patterns

### Creating a New Skill

1. Interview user to capture intent and edge cases
2. Write SKILL.md draft with frontmatter and instructions
3. Create test cases in `evals/evals.json`
4. Run eval loop: `python -m scripts.run_loop ...`
5. Review results with user
6. Iterate based on feedback

### Evaluating Skills

1. Spawn parallel subagents with/without skill
2. Grade outputs against assertions
3. Aggregate into benchmark.json
4. Generate HTML report
5. Review with user

### Packaging Skills

```bash
python -m scripts.package_skill <skill-folder> [output-dir]
```

Validation runs automatically before packaging.

---

## Development Notes

- Scripts use `argparse` for CLI argument parsing
- Output JSON via `json.dumps()` with `indent=2`
- Errors go to stderr, data to stdout
- Use `pathlib.Path` for file operations
- Temporary files use `tempfile` module
- HTML reports generated via string concatenation (no template engine)
