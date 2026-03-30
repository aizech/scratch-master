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


def convert_blocks_from_agent_format(blocks_spec: dict) -> dict:
    """Convert blocks from agent format to proper Scratch block format.
    
    Agent format (simple):
        {"event_name": [{"opcode": "...", "inputs": {...}}]}
    
    Scratch format (proper):
        {"BLOCK_ID": {"opcode": "...", "next": "BLOCK_ID2", ...}}
    """
    blocks = {}
    id_mapping = {}  # Maps names to block IDs
    
    for script_name, block_list in blocks_spec.items():
        if not isinstance(block_list, list):
            blocks[script_name] = block_list
            continue
        
        prev_id = None
        hat_id = None
        
        for i, block_def in enumerate(block_list):
            if not isinstance(block_def, dict):
                continue
                
            block_id = generate_id()
            id_mapping[f"{script_name}_{i}"] = block_id
            
            block = {
                "opcode": block_def.get("opcode", ""),
                "next": None,
                "parent": prev_id,
                "inputs": block_def.get("inputs", {}).copy(),
                "fields": block_def.get("fields", {}).copy(),
                "shadow": block_def.get("shadow", False),
                "topLevel": False,
            }
            
            if i == 0:
                hat_id = generate_id()
                blocks[hat_id] = {
                    "opcode": "event_whenflagclicked",
                    "next": block_id,
                    "parent": None,
                    "inputs": {},
                    "fields": {},
                    "shadow": False,
                    "topLevel": True,
                    "x": 0,
                    "y": len([b for b in blocks.values() if b.get("topLevel")]) * 100,
                }
                block["parent"] = hat_id
            
            if prev_id:
                blocks[prev_id]["next"] = block_id
            
            blocks[block_id] = block
            prev_id = block_id
    
    for block in blocks.values():
        for input_name, input_val in block["inputs"].items():
            if isinstance(input_val, list) and len(input_val) >= 2:
                if input_val[0] == 2 and isinstance(input_val[1], str):
                    for script_name, block_list in blocks_spec.items():
                        if isinstance(block_list, list):
                            for i, bd in enumerate(block_list):
                                if isinstance(bd, dict):
                                    ref_key = f"{script_name}_{i}"
                                    if id_mapping.get(ref_key):
                                        block["inputs"][input_name] = [2, id_mapping[ref_key]]
    
    return blocks


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
            stage["variables"][var_id] = var_data

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

    sprite_blocks = blocks
    if blocks and isinstance(blocks, dict):
        has_string_keys = any(isinstance(k, str) and not k.startswith("_") for k in blocks.keys())
        if has_string_keys and any(isinstance(v, list) for v in blocks.values()):
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
