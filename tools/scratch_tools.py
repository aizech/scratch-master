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


@tool
def get_block_help(category: str | None = None) -> str:
    """Get Scratch block opcode reference for the agent.

    Use this when unsure of the correct block opcode to use in a project.
    Categories: motion, looks, sound, events, control, sensing, operators, variables, pen, music

    Args:
        category: Block category to get opcodes for. If None, returns all categories.

    Returns:
        JSON with opcodes and descriptions for the requested category.
    """
    # Block reference organized by category
    BLOCKS = {
        "motion": {
            "motion_movesteps": "Move N steps",
            "motion_turnright": "Turn right N degrees",
            "motion_turnleft": "Turn left N degrees",
            "motion_gotoxy": "Go to x: N y: N",
            "motion_changexby": "Change x by N",
            "motion_setx": "Set x to N",
            "motion_changeyby": "Change y by N",
            "motion_sety": "Set y to N",
            "motion_ifonedgebounce": "If on edge, bounce",
            "motion_pointindirection": "Point in direction N",
            "motion_pointtowards": "Point towards (sprite)",
            "motion_glidesecstoxy": "Glide N secs to x: N y: N",
            "motion_setrotationstyle": "Set rotation style (left-right/all around/don't rotate)",
        },
        "looks": {
            "looks_sayforsecs": "Say 'text' for N secs",
            "looks_say": "Say 'text'",
            "looks_thinkforsecs": "Think 'text' for N secs",
            "looks_think": "Think 'text'",
            "looks_show": "Show",
            "looks_hide": "Hide",
            "looks_switchcostumeto": "Switch costume to (name)",
            "looks_nextcostume": "Next costume",
            "loves_switchbackdropto": "Switch backdrop to (name)",
            "looks_changesizeby": "Change size by N",
            "looks_setsizeto": "Set size to N%",
            "looks_cleargraphiceffects": "Clear graphic effects",
            "looks_gotofrontback": "Go to front/back",
        },
        "sound": {
            "sound_play": "Start sound (name)",
            "sound_playuntildone": "Play sound (name) until done",
            "sound_stopallsounds": "Stop all sounds",
            "sound_changevolumeby": "Change volume by N",
            "sound_setvolumeto": "Set volume to N%",
        },
        "events": {
            "event_whenflagclicked": "When green flag clicked (hat block)",
            "event_whenkeypressed": "When key (space/arrow) pressed (hat block)",
            "event_whenthisspriteclicked": "When this sprite clicked (hat block)",
            "event_whenbroadcastreceived": "When I receive (message) (hat block)",
            "event_broadcast": "Broadcast (message)",
            "event_broadcastandwait": "Broadcast (message) and wait",
        },
        "control": {
            "control_wait": "Wait N seconds",
            "control_repeat": "Repeat N times",
            "control_forever": "Forever loop",
            "control_if": "If condition then",
            "control_if_else": "If condition then else",
            "control_wait_until": "Wait until condition",
            "control_repeat_until": "Repeat until condition",
            "control_stop": "Stop (all/this script/other scripts)",
        },
        "sensing": {
            "sensing_keypressed": "Key (space/arrow) pressed? (reporter)",
            "sensing_mousedown": "Mouse down? (reporter)",
            "sensing_mousex": "Mouse x (reporter)",
            "sensing_mousey": "Mouse y (reporter)",
            "sensing_touchingobject": "Touching (mouse pointer/sprite)? (reporter)",
            "sensing_distanceto": "Distance to (mouse pointer/sprite) (reporter)",
            "sensing_timer": "Timer (reporter)",
            "sensing_resettimer": "Reset timer",
            "sensing_askandwait": "Ask 'question' and wait",
            "sensing_answer": "Answer (reporter)",
        },
        "operators": {
            "operator_add": "N + N (reporter)",
            "operator_subtract": "N - N (reporter)",
            "operator_multiply": "N * N (reporter)",
            "operator_divide": "N / N (reporter)",
            "operator_random": "Random N to N (reporter)",
            "operator_gt": "N > N (reporter, boolean)",
            "operator_lt": "N < N (reporter, boolean)",
            "operator_equals": "N = N (reporter, boolean)",
            "operator_and": "condition AND condition (reporter)",
            "operator_or": "condition OR condition (reporter)",
            "operator_not": "NOT condition (reporter)",
            "operator_join": "Join 'hello' 'world' (reporter)",
        },
        "variables": {
            "data_setvariableto": "Set (variable) to N",
            "data_changevariableby": "Change (variable) by N",
            "data_showvariable": "Show variable (variable)",
            "data_hidevariable": "Hide variable (variable)",
        },
        "pen": {
            "pen_clear": "Erase all",
            "pen_stamp": "Stamp",
            "pen_penDown": "Pen down",
            "pen_penUp": "Pen up",
            "pen_setPenSizeTo": "Set pen size to N",
            "pen_changePenSizeBy": "Change pen size by N",
        },
    }

    if category is None:
        # Return summary of all categories
        return json.dumps(
            {cat: list(blocks.keys())[:5] + ["..."] for cat, blocks in BLOCKS.items()},
            indent=2,
        )

    category = category.lower()
    if category not in BLOCKS:
        return f"Unknown category '{category}'. Valid: {', '.join(BLOCKS.keys())}"

    return json.dumps(BLOCKS[category], indent=2)


@tool
def validate_spec_tool(json_content: str) -> str:
    """Validate a Scratch project specification before generation.

    Use this to check for errors, unknown opcodes, invalid formats,
    and get auto-corrections before saving the spec.

    Args:
        json_content: Full JSON spec string to validate.

    Returns:
        Validation report with errors, warnings, and auto-corrections.
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "scratch-coder" / "scripts"))
    from spec_validator import validate_spec, format_validation_report

    try:
        spec = json.loads(json_content)
    except json.JSONDecodeError as e:
        return f"JSON parse error: {e}"

    result = validate_spec(spec)
    return format_validation_report(result)
