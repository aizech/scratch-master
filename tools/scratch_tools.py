#!/usr/bin/env python3
"""
Scratch project management tools for the Agno agent.

Provides tools to list, load, inspect, and save Scratch projects
(.sb3 files and _spec.json specification files).
"""

import json
import zipfile
from pathlib import Path

from agno.tools import tool

_BASE_DIR = Path(__file__).parent.parent.resolve()
_OUTPUT_DIR = _BASE_DIR / "output"


def _ensure_output_dir() -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _OUTPUT_DIR


@tool
def list_projects() -> str:
    """List all Scratch projects in the output directory.

    Returns a JSON string with two lists:
    - 'sb3_files': compiled .sb3 files ready to open in Scratch
    - 'spec_files': JSON specification files that can be edited and rebuilt
    """
    output_dir = _ensure_output_dir()
    sb3_files = sorted(p.name for p in output_dir.glob("*.sb3"))
    spec_files = sorted(p.name for p in output_dir.glob("*_spec.json"))
    return json.dumps({"sb3_files": sb3_files, "spec_files": spec_files}, indent=2)


@tool
def load_spec(filename: str) -> str:
    """Load an existing Scratch project specification (JSON) from the output directory.

    Args:
        filename: Name of the spec file (e.g. 'pong_game_spec.json').
                  Must be inside the output/ directory.

    Returns:
        The full JSON content of the spec file as a string, or an error message.
    """
    output_dir = _ensure_output_dir()
    spec_path = output_dir / filename
    if not spec_path.exists():
        return f"Error: spec file not found: {filename}"
    if not spec_path.suffix == ".json":
        return f"Error: expected a .json file, got: {filename}"
    return spec_path.read_text(encoding="utf-8")


@tool
def save_spec(filename: str, json_content: str) -> str:
    """Save a Scratch project specification JSON to the output directory.

    Use this to write a new or modified spec before generating the .sb3 file.

    Args:
        filename: Target filename (e.g. 'my_game_spec.json').
                  Will be saved in output/.
        json_content: Full JSON string to write.

    Returns:
        Confirmation message or error string.
    """
    output_dir = _ensure_output_dir()
    if not filename.endswith(".json"):
        filename = filename + ".json"
    spec_path = output_dir / filename
    try:
        parsed = json.loads(json_content)
        spec_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
        return f"Saved spec to output/{filename}"
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON: {e}"


@tool
def inspect_sb3(filename: str) -> str:
    """Inspect a compiled Scratch .sb3 file and return a human-readable summary.

    Shows sprite names, variable names, extension list, and block counts
    without requiring the user to open Scratch.

    Args:
        filename: Name of the .sb3 file in output/ (e.g. 'pong_game.sb3').

    Returns:
        JSON summary with sprites, variables, extensions, and block counts.
    """
    output_dir = _ensure_output_dir()
    sb3_path = output_dir / filename
    if not sb3_path.exists():
        sb3_path = Path(filename)
    if not sb3_path.exists():
        return f"Error: .sb3 file not found: {filename}"

    try:
        with zipfile.ZipFile(sb3_path, "r") as zf:
            project = json.loads(zf.read("project.json"))
    except Exception as e:
        return f"Error reading .sb3: {e}"

    summary: dict = {
        "name": project.get("meta", {}).get("agent", "unknown"),
        "extensions": project.get("extensions", []),
        "sprites": [],
        "stage_variables": [],
    }

    for target in project.get("targets", []):
        if target.get("isStage"):
            summary["stage_variables"] = [
                v[0] for v in target.get("variables", {}).values()
            ]
        else:
            sprite_info = {
                "name": target["name"],
                "visible": target.get("visible", True),
                "position": {"x": target.get("x", 0), "y": target.get("y", 0)},
                "costumes": [c["name"] for c in target.get("costumes", [])],
                "block_count": len(target.get("blocks", {})),
                "variables": [v[0] for v in target.get("variables", {}).values()],
            }
            summary["sprites"].append(sprite_info)

    return json.dumps(summary, indent=2)


@tool
def load_sb3_project(filename: str) -> str:
    """Load the full project.json from inside a .sb3 file.

    Use this when you need to read and edit the raw Scratch block data
    of an existing project that has no _spec.json available.

    Args:
        filename: Name of the .sb3 file in output/ (e.g. 'pong_game.sb3').

    Returns:
        Full project.json content as a JSON string, or an error message.
    """
    output_dir = _ensure_output_dir()
    sb3_path = output_dir / filename
    if not sb3_path.exists():
        sb3_path = Path(filename)
    if not sb3_path.exists():
        return f"Error: .sb3 file not found: {filename}"

    try:
        with zipfile.ZipFile(sb3_path, "r") as zf:
            return zf.read("project.json").decode("utf-8")
    except Exception as e:
        return f"Error reading .sb3: {e}"
