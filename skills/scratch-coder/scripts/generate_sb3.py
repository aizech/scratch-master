#!/usr/bin/env python3
"""
Generate SB3 - Create Scratch 3.0 .sb3 files from project specifications.

Usage:
    python generate_sb3.py <spec.json> [--output <output.sb3>]

Or use as a module:
    from generate_sb3 import create_project, save_sb3
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from block_builder import BlockBuilder, generate_id, input_value, input_block

# ---------------------------------------------------------------------------
# Embedded SVG assets — bundled directly so no CDN download is required.
# These are the exact bytes from assets.scratch.mit.edu for each hash.
# ---------------------------------------------------------------------------
_EMBEDDED_ASSETS: dict[str, bytes] = {}

def _load_embedded_assets() -> None:
    """Populate _EMBEDDED_ASSETS from the local cache or neighbouring asset files."""
    # Look in the local user asset cache first (populated on first successful run)
    cache_dir = Path.home() / ".scratch-coder-assets"
    # Also look next to this script in an 'assets/' folder
    script_assets = Path(__file__).parent / "assets"

    for search_dir in (cache_dir, script_assets):
        if search_dir.exists():
            for f in search_dir.glob("*.svg"):
                _EMBEDDED_ASSETS[f.name] = f.read_bytes()
            for f in search_dir.glob("*.wav"):
                _EMBEDDED_ASSETS[f.name] = f.read_bytes()

_load_embedded_assets()


DEFAULT_CAT_COSTUME = {
    "assetId": "bcf454acf82e4504149f7ffe07081dbc",
    "name": "costume1",
    "md5ext": "bcf454acf82e4504149f7ffe07081dbc.svg",
    "dataFormat": "svg",
    "bitmapResolution": 1,
    "rotationCenterX": 48,
    "rotationCenterY": 50,
}

DEFAULT_CAT_COSTUME_2 = {
    "assetId": "0fb9be3e8397c983338cb71dc84d0b25",
    "name": "costume2",
    "md5ext": "0fb9be3e8397c983338cb71dc84d0b25.svg",
    "dataFormat": "svg",
    "bitmapResolution": 1,
    "rotationCenterX": 46,
    "rotationCenterY": 53,
}

DEFAULT_POP_SOUND = {
    "assetId": "83a9787d4cb6f3b7632b4ddfebf74367",
    "name": "pop",
    "dataFormat": "wav",
    "format": "",
    "rate": 48000,
    "sampleCount": 1123,
    "md5ext": "83a9787d4cb6f3b7632b4ddfebf74367.wav",
}

DEFAULT_STAGE_COSTUME = {
    "assetId": "cd21514d0531fdffb22204e0ec5ed84a",
    "name": "backdrop1",
    "md5ext": "cd21514d0531fdffb22204e0ec5ed84a.svg",
    "dataFormat": "svg",
    "rotationCenterX": 240,
    "rotationCenterY": 180,
}

BUILT_IN_COSTUMES = {
    "cat": [
        {"assetId": "bcf454acf82e4504149f7ffe07081dbc", "name": "costume1",
         "md5ext": "bcf454acf82e4504149f7ffe07081dbc.svg", "dataFormat": "svg",
         "bitmapResolution": 1, "rotationCenterX": 48, "rotationCenterY": 50},
        {"assetId": "0fb9be3e8397c983338cb71dc84d0b25", "name": "costume2",
         "md5ext": "0fb9be3e8397c983338cb71dc84d0b25.svg", "dataFormat": "svg",
         "bitmapResolution": 1, "rotationCenterX": 46, "rotationCenterY": 53},
    ],
    # 'empty' uses the blank stage SVG — guaranteed to be available and truly invisible
    "empty": [
        {"assetId": "cd21514d0531fdffb22204e0ec5ed84a", "name": "costume1",
         "md5ext": "cd21514d0531fdffb22204e0ec5ed84a.svg", "dataFormat": "svg",
         "rotationCenterX": 0, "rotationCenterY": 0},
    ],
    # banana/tennis/basketball reuse cat costumes — the original CDN hashes 503 too often.
    # Using cat SVGs ensures the asset is always available in the embedded cache.
    "banana": [
        {"assetId": "0fb9be3e8397c983338cb71dc84d0b25", "name": "banana",
         "md5ext": "0fb9be3e8397c983338cb71dc84d0b25.svg", "dataFormat": "svg",
         "bitmapResolution": 1, "rotationCenterX": 15, "rotationCenterY": 15},
    ],
    "tennis": [
        {"assetId": "bcf454acf82e4504149f7ffe07081dbc", "name": "tennis ball",
         "md5ext": "bcf454acf82e4504149f7ffe07081dbc.svg", "dataFormat": "svg",
         "bitmapResolution": 1, "rotationCenterX": 22, "rotationCenterY": 22},
    ],
    "basketball": [
        {"assetId": "0fb9be3e8397c983338cb71dc84d0b25", "name": "basketball",
         "md5ext": "0fb9be3e8397c983338cb71dc84d0b25.svg", "dataFormat": "svg",
         "bitmapResolution": 1, "rotationCenterX": 25, "rotationCenterY": 25},
    ],
}


def resolve_backdrop(backdrop_spec: str | dict) -> dict:
    """Resolve a backdrop specification to proper costume format."""
    blank = DEFAULT_STAGE_COSTUME.copy()

    if isinstance(backdrop_spec, str):
        entry = BUILT_IN_COSTUMES.get(backdrop_spec)
        if entry:
            c = entry[0].copy()
            c["name"] = backdrop_spec
            return c
        blank["name"] = backdrop_spec
        return blank
    elif isinstance(backdrop_spec, dict):
        if "assetId" in backdrop_spec and "md5ext" in backdrop_spec:
            return backdrop_spec
        if "color" in backdrop_spec:
            return backdrop_spec
        # {"name": "...", "costume": "..."} form from agent
        costume_key = backdrop_spec.get("costume", "")
        display_name = backdrop_spec.get("name", costume_key or "backdrop1")
        entry = BUILT_IN_COSTUMES.get(costume_key)
        if entry:
            c = entry[0].copy()
            c["name"] = display_name
            return c
        # Unknown backdrop name — use blank stage SVG with the given display name
        blank["name"] = display_name
        return blank
    return blank


_HAT_OPCODES = {
    "event_whenflagclicked",
    "event_whenkeypressed",
    "event_whenthisspriteclicked",
    "event_whenstageclicked",
    "event_whenbackdropswitchesto",
    "event_whengreaterthan",
    "event_whenbroadcastreceived",
    "control_start_as_clone",
    "procedures_definition",
}


def _extract_inline_block(val: dict, blocks: dict, parent_id: str) -> str:
    """Recursively extract an inline block dict to a top-level entry and return its ID."""
    bid = generate_id()
    inputs = {}
    for k, v in val.get("inputs", {}).items():
        inputs[k] = _resolve_input_value(v, blocks, bid)
    fields = dict(val.get("fields", {}))
    # sensing_keypressed: KEY_OPTION must be a field not an input
    if val.get("opcode") == "sensing_keypressed" and "KEY_OPTION" in inputs:
        raw = inputs.pop("KEY_OPTION")
        if isinstance(raw, list):
            if len(raw) >= 2 and isinstance(raw[0], int):
                v2 = raw[1] if isinstance(raw[1], list) else [raw[1], None]
            else:
                v2 = raw if len(raw) == 2 else [raw[0], None]
            fields["KEY_OPTION"] = v2 if isinstance(v2, list) and len(v2) == 2 else [v2, None]
        else:
            fields["KEY_OPTION"] = [raw, None]
    # Normalise field values: Scratch expects [value, null] not just a scalar
    normalised_fields = {}
    for fname, fval in fields.items():
        normalised_fields[fname] = fval if isinstance(fval, list) else [fval, None]
    blocks[bid] = {
        "opcode": val.get("opcode", ""),
        "next": None,
        "parent": parent_id,
        "inputs": inputs,
        "fields": normalised_fields,
        "shadow": val.get("shadow", False),
        "topLevel": False,
    }
    return bid


def _resolve_input_value(raw, blocks: dict, parent_id: str):
    """Convert a raw input value to a valid Scratch input tuple, extracting inline blocks."""
    if not isinstance(raw, list):
        return raw
    if len(raw) < 2:
        return raw
    kind = raw[0]
    inner = raw[1]

    # Agent shadow pattern: [3, {"shadow": true, "value": {"opcode": "sensing_mousey"}}]
    # Convert to proper [3, reporter_block_id, default_shadow]
    if isinstance(inner, dict) and inner.get("shadow") is True and "value" in inner:
        val = inner["value"]
        if isinstance(val, dict) and "opcode" in val:
            reporter_id = _extract_inline_block(val, blocks, parent_id)
            # default numeric shadow for the second slot
            return [3, reporter_id, [4, 0]]

    # Inline block object — extract it
    if isinstance(inner, dict) and "opcode" in inner:
        new_id = _extract_inline_block(inner, blocks, parent_id)
        return [kind, new_id]

    # Shadow/obscured: [3, block_or_val, shadow] where slot 2 may also be an inline block
    if kind == 3 and len(raw) > 2:
        shadow = raw[2]
        if isinstance(shadow, dict) and "opcode" in shadow:
            shadow_id = _extract_inline_block(shadow, blocks, parent_id)
            return [3, inner, shadow_id]

    return raw


def convert_blocks_from_agent_format(blocks_spec: dict) -> dict:
    """Convert agent block specs to valid Scratch 3.0 block format.

    Handles two agent output styles:

    Style A — list format (auto-wraps with green-flag hat if needed):
        {"script1": [{"opcode": "motion_movesteps", "inputs": {"STEPS": [4, 10]}}]}

    Style B — dict format (string-keyed, passed through with normalisation):
        {"HAT_ID": {"opcode": "event_whenflagclicked", "next": "BLOCK2", ...},
         "BLOCK2": {"opcode": "motion_movesteps", ...}}
    """
    # -----------------------------------------------------------------------
    # Phase 1: detect format and build initial blocks dict
    # -----------------------------------------------------------------------
    all_values = list(blocks_spec.values())
    is_list_format = any(isinstance(v, list) for v in all_values)

    blocks: dict = {}

    if is_list_format:
        # --- Style A: list-of-block-defs per script ---
        script_y = 0
        for script_name, block_list in blocks_spec.items():
            if not isinstance(block_list, list) or not block_list:
                if isinstance(block_list, dict):
                    # mixed: single block dict under a name
                    blocks[script_name] = _make_block_entry(block_list)
                continue

            ids = [generate_id() for _ in block_list]
            first_opcode = block_list[0].get("opcode", "") if isinstance(block_list[0], dict) else ""
            needs_hat = first_opcode not in _HAT_OPCODES

            if needs_hat:
                hat_id = generate_id()
                blocks[hat_id] = {
                    "opcode": "event_whenflagclicked",
                    "next": ids[0],
                    "parent": None,
                    "inputs": {},
                    "fields": {},
                    "shadow": False,
                    "topLevel": True,
                    "x": 20,
                    "y": script_y,
                }
                script_y += 250
                parent_of_first = hat_id
            else:
                parent_of_first = None

            for i, block_def in enumerate(block_list):
                if not isinstance(block_def, dict):
                    continue
                bid = ids[i]
                # Use explicit 'next' string ref if it names a block outside this list
                explicit_next = block_def.get("next")
                if isinstance(explicit_next, str) and explicit_next not in ids:
                    next_id = explicit_next  # cross-reference to a dict-keyed block
                else:
                    next_id = ids[i + 1] if i + 1 < len(ids) else None
                parent_id = parent_of_first if i == 0 else ids[i - 1]

                inputs = {}
                for k, v in block_def.get("inputs", {}).items():
                    inputs[k] = _resolve_input_value(v, blocks, bid)

                fields = {}
                for fname, fval in block_def.get("fields", {}).items():
                    fields[fname] = fval if isinstance(fval, list) else [fval, None]

                is_hat = block_def.get("opcode", "") in _HAT_OPCODES
                blocks[bid] = {
                    "opcode": block_def.get("opcode", ""),
                    "next": next_id,
                    "parent": parent_id,
                    "inputs": inputs,
                    "fields": fields,
                    "shadow": block_def.get("shadow", False),
                    "topLevel": is_hat and i == 0 and not needs_hat,
                }
                if is_hat and i == 0 and not needs_hat:
                    blocks[bid]["x"] = 20
                    blocks[bid]["y"] = script_y
                    script_y += 250

    else:
        # --- Style B: dict-keyed blocks (string IDs), possibly mixed with list entries ---
        # First pass: copy all blocks. List values are treated as sub-scripts.
        script_y = 0
        for bid, block_def in blocks_spec.items():
            if isinstance(block_def, list):
                # inline list sub-script — convert and merge
                sub = convert_blocks_from_agent_format({bid: block_def})
                blocks.update(sub)
            elif isinstance(block_def, dict):
                blocks[bid] = _make_block_entry(block_def)

        # Second pass: fix topLevel, add x/y to hat blocks
        for bid, block in blocks.items():
            opcode = block.get("opcode", "")
            parent = block.get("parent")
            # A block is top-level if it's a hat AND has no parent (or parent not in blocks)
            if opcode in _HAT_OPCODES and (not parent or parent not in blocks):
                block["topLevel"] = True
                block["parent"] = None
                if "x" not in block:
                    block["x"] = 20
                if "y" not in block:
                    block["y"] = script_y
                script_y += 250
            else:
                block["topLevel"] = False

    # -----------------------------------------------------------------------
    # Phase 2: resolve remaining string-ID references in inputs
    # (handles [2, "some_block_name"] where some_block_name is a key in blocks)
    # -----------------------------------------------------------------------
    for bid, block in list(blocks.items()):
        new_inputs = {}
        for k, v in block.get("inputs", {}).items():
            new_inputs[k] = _resolve_input_value(v, blocks, bid)
        block["inputs"] = new_inputs

        # Normalise fields
        new_fields = {}
        for fname, fval in block.get("fields", {}).items():
            new_fields[fname] = fval if isinstance(fval, list) else [fval, None]
        block["fields"] = new_fields

    # -----------------------------------------------------------------------
    # Phase 3: normalise primitive input literals
    # [1, "10"] → [1, [4, "10"]]   (number stored as bare string)
    # [4, 5]    → [1, [4, "5"]]    (old shorthand: primitive type used as shadow type)
    # -----------------------------------------------------------------------
    _normalize_primitive_inputs(blocks)

    # -----------------------------------------------------------------------
    # Phase 4: infer missing parent references from next/SUBSTACK/CONDITION
    # -----------------------------------------------------------------------
    _infer_parents(blocks)

    return blocks


def _normalize_primitive_inputs(blocks: dict) -> None:
    """Normalise all input literals to Scratch 3.0 canonical format in-place.

    Scratch input format: [shadow_type, value_or_primitive]
      shadow_type 1 = no shadow, 2 = block ref, 3 = obscured shadow
      inner value for literals: [primitive_type, value_string]
        4  = positive number, 5 = positive int, 6 = int, 7 = angle,
        8  = color, 9 = str, 10 = str (TEXT), 12 = variable, 13 = list

    Bad patterns we must fix:
      [1, "10"]      → agent stored bare string/number as inner value
      [4, 10]        → old shorthand (primitive type used as outer shadow type)
    """
    def _fix(v, block_ids: set):
        if not isinstance(v, list) or len(v) < 2:
            return v
        kind = v[0]
        inner = v[1]

        # [2, id] or [3, id, shadow] — block references, leave as-is
        if kind in (2, 3):
            return v

        # [1, [type, val]] — already canonical with a primitive array
        if kind == 1 and isinstance(inner, list):
            return v

        # [1, block_id_str] — block reference with same-shadow, leave as-is
        if kind == 1 and isinstance(inner, str) and inner in block_ids:
            return v

        # [1, bare_value] — string/number that isn't a block ID → wrap as literal
        if kind == 1 and isinstance(inner, (str, int, float)):
            s = str(inner)
            try:
                float(s)
                ptype = 4  # number
            except ValueError:
                ptype = 10  # string
            return [1, [ptype, s]]

        # [4-13, value] — old shorthand (primitive type in outer shadow slot)
        if isinstance(kind, int) and kind >= 4:
            return [1, [kind, str(inner)]]

        return v

    block_ids = set(blocks.keys())
    for block in blocks.values():
        new_inputs = {}
        for k, v in block.get("inputs", {}).items():
            fixed = _fix(v, block_ids)
            # For [3, block_id, shadow], also fix the shadow slot
            if (isinstance(fixed, list) and len(fixed) == 3
                    and fixed[0] == 3 and isinstance(fixed[2], list)):
                shadow = fixed[2]
                if (len(shadow) == 2 and isinstance(shadow[0], int)
                        and shadow[0] >= 4 and not isinstance(shadow[1], list)):
                    fixed = [3, fixed[1], [shadow[0], str(shadow[1])]]
            new_inputs[k] = fixed
        block["inputs"] = new_inputs


def _infer_parents(blocks: dict) -> None:
    """Infer missing parent references in-place from next/SUBSTACK/CONDITION links."""
    for bid, block in blocks.items():
        # next-chain: the block pointed to by 'next' has this block as its parent
        nxt = block.get("next")
        if nxt and nxt in blocks and blocks[nxt].get("parent") is None:
            blocks[nxt]["parent"] = bid

        # input substacks / conditions
        for input_val in block.get("inputs", {}).values():
            if not isinstance(input_val, list):
                continue
            # [2, target_id] or [3, target_id, ...]
            if len(input_val) >= 2 and input_val[0] in (2, 3):
                target = input_val[1]
                if isinstance(target, str) and target in blocks:
                    if blocks[target].get("parent") is None:
                        blocks[target]["parent"] = bid


def _make_block_entry(block_def: dict) -> dict:
    """Normalise a single block definition dict into a proper Scratch block entry."""
    inputs = dict(block_def.get("inputs", {}))
    fields = dict(block_def.get("fields", {}))

    # sensing_keypressed: KEY_OPTION must be a field, not an input
    # Agent sometimes puts it in inputs as ["space", null] or [1, ["space", null]]
    if block_def.get("opcode") == "sensing_keypressed" and "KEY_OPTION" in inputs:
        raw = inputs.pop("KEY_OPTION")
        if isinstance(raw, list):
            # ["space", null] or [1, ["space", null]] or ["space"]
            val = raw
            if len(raw) >= 2 and isinstance(raw[0], int):
                val = raw[1] if isinstance(raw[1], list) else [raw[1], None]
            if not isinstance(val, list):
                val = [val, None]
            if len(val) == 1:
                val = [val[0], None]
            fields["KEY_OPTION"] = val
        else:
            fields["KEY_OPTION"] = [raw, None]

    return {
        "opcode": block_def.get("opcode", ""),
        "next": block_def.get("next", None),
        "parent": block_def.get("parent", None),
        "inputs": inputs,
        "fields": fields,
        "shadow": block_def.get("shadow", False),
        "topLevel": block_def.get("topLevel", False),
    }


def create_stage(spec: dict) -> dict:
    """Create the Stage target."""
    stage = {
        "isStage": True,
        "name": "Stage",
        "variables": {},
        "lists": {},
        "broadcasts": {},
        "blocks": {},
        "comments": {},
        "currentCostume": 0,
        "costumes": [DEFAULT_STAGE_COSTUME.copy()],
        "sounds": [],
        "volume": 100,
        "layerOrder": 0,
        "tempo": 60,
        "videoTransparency": 50,
        "videoState": "on",
        "textToSpeechLanguage": None,
    }

    if "variables" in spec:
        for var_id, var_data in spec["variables"].items():
            if isinstance(var_data, list) and len(var_data) == 2 and isinstance(var_data[0], str):
                stage["variables"][var_id] = var_data  # already [name, value]
            else:
                stage["variables"][var_id] = [var_id, var_data]

    if "broadcasts" in spec:
        stage["broadcasts"] = spec["broadcasts"]

    if "backdrops" in spec:
        if isinstance(spec["backdrops"], list) and spec["backdrops"]:
            costumes = []
            for b in spec["backdrops"]:
                resolved = resolve_backdrop(b)
                if isinstance(resolved, list):
                    costumes.extend(resolved)
                else:
                    costumes.append(resolved)
            stage["costumes"] = costumes
        elif isinstance(spec["backdrops"], str):
            resolved = resolve_backdrop(spec["backdrops"])
            stage["costumes"] = resolved if isinstance(resolved, list) else [resolved]
        elif isinstance(spec["backdrops"], dict):
            resolved = resolve_backdrop(spec["backdrops"])
            stage["costumes"] = resolved if isinstance(resolved, list) else [resolved]

    if "blocks" in spec:
        stage["blocks"] = convert_blocks_from_agent_format(spec["blocks"])

    return stage


def create_sprite(
    name: str,
    costume: str = "cat",
    x: int = 0,
    y: int = 0,
    visible: bool = True,
    direction: int = 90,
    rotation_style: str = "all around",
    blocks: dict | None = None,
    variables: dict | None = None,
    lists: dict | None = None,
    broadcasts: dict | None = None,
) -> dict:
    """Create a sprite target."""
    costumes = BUILT_IN_COSTUMES.get(costume, BUILT_IN_COSTUMES["cat"])

    sprite_blocks = {}
    if blocks and isinstance(blocks, dict):
        sprite_blocks = convert_blocks_from_agent_format(blocks)

    sprite = {
        "isStage": False,
        "name": name,
        "variables": variables or {},
        "lists": lists or {},
        "broadcasts": broadcasts or {},
        "blocks": sprite_blocks or {},
        "comments": {},
        "currentCostume": 0,
        "costumes": costumes.copy(),
        "sounds": [],
        "volume": 100,
        "layerOrder": 1,
        "visible": visible,
        "x": x,
        "y": y,
        "size": 100,
        "direction": direction,
        "draggable": False,
        "rotationStyle": rotation_style,
    }

    return sprite


def build_blocks_from_spec(blocks_spec: list) -> dict:
    """Build blocks from a specification list.
    
    Format: [{"opcode": "...", "inputs": {...}, "fields": {...}}, ...]
    """
    blocks = {}
    prev_id = None

    for i, spec in enumerate(blocks_spec):
        block_id = generate_id()
        block = {
            "opcode": spec["opcode"],
            "next": None,
            "parent": prev_id,
            "inputs": spec.get("inputs", {}),
            "fields": spec.get("fields", {}),
            "shadow": spec.get("shadow", False),
            "topLevel": False,
        }

        if i > 0 and prev_id:
            blocks[prev_id]["next"] = block_id

        blocks[block_id] = block
        prev_id = block_id

    return blocks


def create_project(spec: dict) -> dict:
    """Create a complete project JSON from a specification."""
    project = {
        "targets": [],
        "monitors": [],
        "extensions": [],
        "meta": {
            "semver": "3.0.0",
            "vm": "0.2.0",
            "agent": "scratch-coder/1.0.0",
        },
    }

    stage = create_stage(spec.get("stage", {}))
    project["targets"].append(stage)

    for sprite_spec in spec.get("sprites", []):
        sprite = create_sprite(
            name=sprite_spec.get("name", "Sprite"),
            costume=sprite_spec.get("costume", "cat"),
            x=sprite_spec.get("x", 0),
            y=sprite_spec.get("y", 0),
            visible=sprite_spec.get("visible", True),
            direction=sprite_spec.get("direction", 90),
            rotation_style=sprite_spec.get("rotationStyle", "all around"),
            blocks=sprite_spec.get("blocks", {}),
            variables=sprite_spec.get("variables", {}),
            lists=sprite_spec.get("lists", {}),
        )

        for i, t in enumerate(project["targets"]):
            if t.get("isStage"):
                t["layerOrder"] = i
        sprite["layerOrder"] = len(project["targets"])

        project["targets"].append(sprite)

    if "extensions" in spec:
        project["extensions"] = spec["extensions"]

    return project


def get_required_assets(project: dict) -> set[str]:
    """Get all asset IDs required by the project."""
    assets = set()
    for target in project.get("targets", []):
        for costume in target.get("costumes", []):
            if "assetId" in costume and "md5ext" in costume:
                assets.add(costume["md5ext"])
        for sound in target.get("sounds", []):
            if "assetId" in sound and "md5ext" in sound:
                assets.add(sound["md5ext"])
    return assets


def download_asset(md5ext: str, cache_dir: Path) -> bytes | None:
    """Return asset bytes: embedded cache → local file cache → Scratch CDN."""
    # 1. Already loaded into the in-process embedded cache
    if md5ext in _EMBEDDED_ASSETS:
        return _EMBEDDED_ASSETS[md5ext]

    # 2. Local user cache file
    cache_file = cache_dir / md5ext
    if cache_file.exists():
        data = cache_file.read_bytes()
        _EMBEDDED_ASSETS[md5ext] = data  # promote to in-process cache
        return data

    # 3. Scratch CDN (may be unavailable)
    url = f"https://assets.scratch.mit.edu/{md5ext}"
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Scratch-Coder/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_bytes(data)
            _EMBEDDED_ASSETS[md5ext] = data
            return data
    except Exception:
        return None


def save_sb3(project: dict, output_path: str | Path) -> Path:
    """Save a project as an .sb3 file with all required assets."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cache_dir = Path.home() / ".scratch-coder-assets"
    
    assets_to_download = get_required_assets(project)
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(project, indent=2))
        
        for md5ext in assets_to_download:
            data = download_asset(md5ext, cache_dir)
            if data:
                zf.writestr(md5ext, data)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate Scratch 3.0 .sb3 files")
    parser.add_argument("spec", help="Path to project specification JSON")
    parser.add_argument(
        "-o", "--output", help="Output path for .sb3 file (default: output/<name>.sb3)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing file"
    )

    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: Spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    spec = json.loads(spec_path.read_text())

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        name = spec.get("name", spec_path.stem)
        output_path = output_dir / f"{name}.sb3"

    if output_path.exists() and not args.overwrite:
        print(f"Error: Output file exists: {output_path}", file=sys.stderr)
        print("Use --overwrite to replace.", file=sys.stderr)
        sys.exit(1)

    project = create_project(spec)
    result_path = save_sb3(project, output_path)

    print(f"Created: {result_path}")
    print(f"Targets: {len(project['targets'])} (1 stage + {len(project['targets']) - 1} sprites)")


if __name__ == "__main__":
    main()
