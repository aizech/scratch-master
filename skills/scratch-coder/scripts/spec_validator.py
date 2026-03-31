"""
Spec Validation - Validate and auto-correct project specifications before generation.

Usage:
    from spec_validator import validate_spec, ValidationResult
    
    result = validate_spec(spec_dict)
    if result.has_errors:
        print(result.errors)
    spec_dict = result.corrected_spec  # Use auto-corrected version
"""

from typing import Any
import re


class ValidationResult:
    """Result of spec validation with errors, warnings, and corrected spec."""
    
    def __init__(self, original_spec: dict):
        self.original_spec = dict(original_spec)
        self.corrected_spec = dict(original_spec)
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.auto_corrections: list[str] = []
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0
    
    def __repr__(self) -> str:
        return f"ValidationResult(errors={len(self.errors)}, warnings={len(self.warnings)})"


# Known opcodes from Scratch 3.0
KNOWN_OPCODES = {
    # Motion
    "motion_movesteps", "motion_turnright", "motion_turnleft", "motion_goto",
    "motion_gotoxy", "motion_glideto", "motion_glidesecstoxy", "motion_pointindirection",
    "motion_pointtowards", "motion_changexby", "motion_setx", "motion_changeyby",
    "motion_sety", "motion_ifonedgebounce", "motion_setrotationstyle",
    "motion_xposition", "motion_yposition", "motion_direction",
    # Looks
    "looks_sayforsecs", "looks_say", "looks_thinkforsecs", "looks_think",
    "looks_show", "looks_hide", "looks_switchcostumeto", "looks_nextcostume",
    "looks_switchbackdropto", "looks_nextbackdrop", "looks_changesizeby",
    "looks_setsizeto", "looks_changeeffectby", "looks_seteffectto",
    "looks_cleargraphiceffects", "looks_gotofrontback", "looks_goforwardbackwardlayers",
    "looks_costumenumbername", "looks_backdropnumbername", "looks_size",
    # Sound
    "sound_play", "sound_playuntildone", "sound_stopallsounds",
    "sound_changeeffectby", "sound_seteffectto", "sound_cleareffects",
    "sound_changevolumeby", "sound_setvolumeto", "sound_volume",
    # Events
    "event_whenflagclicked", "event_whenkeypressed", "event_whenthisspriteclicked",
    "event_whenstageclicked", "event_whenbroadcastreceived", "event_whenbackdropswitchesto",
    "event_whengreaterthan", "event_whenhatcloneinit", "event_broadcast",
    "event_broadcastandwait",
    # Control
    "control_wait", "control_repeat", "control_forever", "control_if",
    "control_if_else", "control_wait_until", "control_repeat_until",
    "control_stop", "control_start_as_clone", "control_create_clone_of",
    "control_delete_this_clone", "control_get_counter", "control_incr_counter",
    "control_clear_counter", "control_all_at_once",
    # Sensing
    "sensing_touchingobject", "sensing_touchingcolor", "sensing_coloristouchingcolor",
    "sensing_distanceto", "sensing_askandwait", "sensing_answer",
    "sensing_keypressed", "sensing_mousedown", "sensing_mousex", "sensing_mousey",
    "sensing_setdragmode", "sensing_timer", "sensing_resettimer",
    "sensing_of", "sensing_current", "sensing_dayssince2000",
    "sensing_username", "sensing_userid",
    # Operators
    "operator_add", "operator_subtract", "operator_multiply", "operator_divide",
    "operator_random", "operator_gt", "operator_lt", "operator_equals",
    "operator_and", "operator_or", "operator_not", "operator_join",
    "operator_letter_of", "operator_length", "operator_contains",
    "operator_mod", "operator_round", "operator_mathop",
    # Variables
    "data_setvariableto", "data_changevariableby", "data_showvariable",
    "data_hidevariable", "data_addtolist", "data_deleteoflist", "data_deletealloflist",
    "data_insertatlist", "data_replaceitemoflist", "data_itemoflist",
    "data_itemnumoflist", "data_lengthoflist", "data_listcontainsitem",
    "data_showlist", "data_hidelist",
    # Procedures (custom blocks)
    "procedures_definition", "procedures_call", "procedures_prototype",
    "procedures_declaration",
    # Pen extension
    "pen_clear", "pen_stamp", "pen_penDown", "pen_penUp", "pen_setPenColorToColor",
    "pen_changePenColorParamBy", "pen_setPenColorParamTo", "pen_changePenSizeBy",
    "pen_setPenSizeTo",
    # Music extension
    "music_playDrumForBeats", "music_restForBeats", "music_playNoteForBeats",
    "music_setInstrument", "music_setTempo", "music_changeTempo", "music_getTempo",
    # Video sensing
    "videoSensing_whenMotionGreaterThan", "videoSensing_videoOn",
    "videoSensing_videoToggle", "videoSensing_setVideoTransparency",
    # Text to speech
    "text2speech_speakAndWait", "text2speech_setVoice", "text2speech_setLanguage",
    # Translate
    "translate_getTranslate", "translate_getViewerLanguage",
    # Makey Makey
    "makeymakey_whenMakeyKeyPressed", "makeymakey_whenCodePressed",
}

# Valid costume keys
VALID_COSTUMES = {"cat", "empty", "banana", "tennis", "basketball"}

# Valid rotation styles
VALID_ROTATION_STYLES = {"all around", "left-right", "don't rotate"}

# Hat opcodes (top-level event handlers)
HAT_OPCODES = {
    "event_whenflagclicked", "event_whenkeypressed", "event_whenthisspriteclicked",
    "event_whenstageclicked", "event_whenbroadcastreceived", "event_whenbackdropswitchesto",
    "event_whengreaterthan", "control_start_as_clone", "procedures_definition",
}


def validate_spec(spec: dict) -> ValidationResult:
    """
    Validate and auto-correct a project specification.
    
    Returns ValidationResult with errors, warnings, and corrected spec.
    """
    result = ValidationResult(spec)
    
    # Validate top-level structure
    _validate_top_level(result)
    
    # Validate stage
    _validate_stage(result)
    
    # Validate sprites
    _validate_sprites(result)
    
    # Validate extensions
    _validate_extensions(result)
    
    return result


def _validate_top_level(result: ValidationResult):
    """Validate top-level spec structure."""
    spec = result.corrected_spec
    
    # Check for required 'name' field
    if "name" not in spec:
        result.warnings.append("Spec missing 'name' field - using 'Untitled Project'")
        spec["name"] = "Untitled Project"
    elif not isinstance(spec["name"], str) or not spec["name"].strip():
        result.warnings.append("Spec 'name' is empty - using 'Untitled Project'")
        spec["name"] = "Untitled Project"
    
    # Check for sprites array
    if "sprites" not in spec:
        result.warnings.append("Spec missing 'sprites' array - adding default sprite")
        spec["sprites"] = [{"name": "Sprite1", "costume": "cat"}]
    elif not isinstance(spec["sprites"], list):
        result.errors.append("'sprites' must be an array")
        spec["sprites"] = [{"name": "Sprite1", "costume": "cat"}]
    
    # Ensure stage exists (even if empty)
    if "stage" not in spec:
        spec["stage"] = {}


def _validate_stage(result: ValidationResult):
    """Validate stage configuration."""
    stage = result.corrected_spec.get("stage", {})
    
    if not isinstance(stage, dict):
        result.errors.append("'stage' must be an object")
        result.corrected_spec["stage"] = stage = {}
    
    # Validate variables format
    if "variables" in stage:
        _validate_variables(stage["variables"], "stage", result)
    
    # Validate broadcasts
    if "broadcasts" in stage and not isinstance(stage["broadcasts"], dict):
        result.warnings.append("Stage 'broadcasts' should be an object")
        stage["broadcasts"] = {}
    
    # Validate backdrops
    if "backdrops" in stage:
        _validate_backdrops(stage["backdrops"], result)
    
    # Validate stage blocks
    if "blocks" in stage:
        _validate_blocks(stage["blocks"], "stage", result)


def _validate_sprites(result: ValidationResult):
    """Validate all sprites in the spec."""
    sprites = result.corrected_spec.get("sprites", [])
    
    if not sprites:
        result.warnings.append("No sprites defined - adding default cat sprite")
        sprites.append({"name": "Sprite1", "costume": "cat"})
    
    # Track sprite names for duplicates
    names_seen = set()
    
    for i, sprite in enumerate(sprites):
        if not isinstance(sprite, dict):
            result.errors.append(f"Sprite[{i}] is not an object")
            continue
        
        # Validate name
        name = sprite.get("name", f"Sprite{i+1}")
        if not name or not isinstance(name, str):
            name = f"Sprite{i+1}"
            sprite["name"] = name
            result.auto_corrections.append(f"Sprite[{i}] missing name - assigned '{name}'")
        
        if name in names_seen:
            new_name = f"{name}_{i}"
            result.warnings.append(f"Duplicate sprite name '{name}' renamed to '{new_name}'")
            sprite["name"] = new_name
            name = new_name
        names_seen.add(name)
        
        # Validate costume
        costume = sprite.get("costume", "cat")
        if costume not in VALID_COSTUMES:
            result.warnings.append(f"Sprite '{name}' has unknown costume '{costume}' - using 'cat'")
            sprite["costume"] = "cat"
        
        # Validate position
        for coord in ["x", "y"]:
            if coord in sprite and not isinstance(sprite[coord], (int, float)):
                result.warnings.append(f"Sprite '{name}' {coord} is not a number - using 0")
                sprite[coord] = 0
        
        # Validate rotation style
        rotation = sprite.get("rotationStyle", "all around")
        if rotation not in VALID_ROTATION_STYLES:
            result.warnings.append(f"Sprite '{name}' has invalid rotationStyle '{rotation}' - using 'all around'")
            sprite["rotationStyle"] = "all around"
        
        # Validate direction
        if "direction" in sprite:
            if not isinstance(sprite["direction"], (int, float)):
                result.warnings.append(f"Sprite '{name}' direction is not a number - using 90")
                sprite["direction"] = 90
            else:
                # Normalize to valid range
                sprite["direction"] = float(sprite["direction"]) % 360
        
        # Validate size
        if "size" in sprite:
            if not isinstance(sprite["size"], (int, float)):
                result.warnings.append(f"Sprite '{name}' size is not a number - using 100")
                sprite["size"] = 100
            else:
                # Clamp to reasonable range
                sprite["size"] = max(0, min(500, float(sprite["size"])))
        
        # Validate variables
        if "variables" in sprite:
            _validate_variables(sprite["variables"], name, result)
        
        # Validate blocks
        if "blocks" in sprite:
            _validate_blocks(sprite["blocks"], name, result)


def _validate_variables(variables: dict, context: str, result: ValidationResult):
    """Validate variable definitions."""
    if not isinstance(variables, dict):
        result.warnings.append(f"{context} 'variables' should be an object")
        return
    
    for var_id, var_data in variables.items():
        # Check if already in correct format [name, value]
        if isinstance(var_data, list) and len(var_data) == 2:
            if not isinstance(var_data[0], str):
                result.auto_corrections.append(f"Variable '{var_id}' name is not a string - converting")
                var_data[0] = str(var_data[0])
        elif isinstance(var_data, (int, float, str, bool)):
            # Convert scalar to [name, value] format
            result.auto_corrections.append(f"Variable '{var_id}' converted to [name, value] format")
            variables[var_id] = [var_id, var_data]
        else:
            result.warnings.append(f"Variable '{var_id}' has unexpected format")


def _validate_backdrops(backdrops: Any, result: ValidationResult):
    """Validate backdrop specifications."""
    if isinstance(backdrops, list):
        for i, bd in enumerate(backdrops):
            if isinstance(bd, str) and bd not in VALID_COSTUMES:
                result.warnings.append(f"Backdrop[{i}] '{bd}' is not a known costume name")
    elif isinstance(backdrops, str):
        if backdrops not in VALID_COSTUMES:
            result.warnings.append(f"Backdrop '{backdrops}' is not a known costume name")
    elif isinstance(backdrops, dict):
        # Dict format backdrop
        if "assetId" not in backdrops and "costume" not in backdrops and "color" not in backdrops:
            result.warnings.append("Backdrop dict should have 'assetId', 'costume', or 'color'")


def _validate_blocks(blocks: Any, context: str, result: ValidationResult):
    """Validate block definitions."""
    if not isinstance(blocks, dict):
        result.warnings.append(f"{context} 'blocks' should be an object")
        return
    
    # Check for at least one hat block
    has_hat = False
    
    for block_id, block in blocks.items():
        if not isinstance(block, dict):
            result.errors.append(f"Block '{block_id}' in {context} is not an object")
            continue
        
        # Check for required opcode
        opcode = block.get("opcode", "")
        if not opcode:
            result.errors.append(f"Block '{block_id}' in {context} missing 'opcode'")
            continue
        
        # Validate opcode is known
        if opcode not in KNOWN_OPCODES:
            result.warnings.append(f"Block '{block_id}' has unknown opcode '{opcode}'")
        
        # Check if hat block
        if opcode in HAT_OPCODES:
            has_hat = True
            # Hat blocks should be topLevel
            if not block.get("topLevel", False):
                result.auto_corrections.append(f"Hat block '{block_id}' marked as topLevel")
                block["topLevel"] = True
        
        # Validate inputs format
        if "inputs" in block:
            _validate_inputs(block["inputs"], f"{context}/{block_id}", result)
        
        # Validate fields format
        if "fields" in block:
            _validate_fields(block["fields"], f"{context}/{block_id}", result)
    
    # Warn if no hat blocks
    if blocks and not has_hat:
        result.warnings.append(f"{context} has no hat blocks (event handlers) - scripts won't run automatically")


def _validate_inputs(inputs: dict, context: str, result: ValidationResult):
    """Validate block input formats."""
    if not isinstance(inputs, dict):
        result.warnings.append(f"{context} 'inputs' should be an object")
        return
    
    for input_name, input_val in inputs.items():
        # Valid input formats:
        # [1, [4, "value"]] - number literal
        # [1, [10, "value"]] - string literal
        # [2, block_id] - block reference
        # [3, block_id, [4, "default"]] - obscured shadow
        
        if not isinstance(input_val, list):
            result.warnings.append(f"{context} input '{input_name}' is not an array - may cause issues")
            continue
        
        if len(input_val) < 2:
            result.warnings.append(f"{context} input '{input_name}' has invalid format")
            continue
        
        kind = input_val[0]
        
        if kind not in [1, 2, 3]:
            # Old shorthand format [4, value] - should be normalized
            if isinstance(kind, int) and kind >= 4:
                result.auto_corrections.append(f"{context} input '{input_name}' uses old shorthand - will normalize")


def _validate_fields(fields: dict, context: str, result: ValidationResult):
    """Validate block field formats."""
    if not isinstance(fields, dict):
        result.warnings.append(f"{context} 'fields' should be an object")
        return
    
    for field_name, field_val in fields.items():
        # Fields should be [value, id] format
        if isinstance(field_val, list):
            if len(field_val) != 2:
                result.warnings.append(f"{context} field '{field_name}' has unexpected array length")
        elif field_val is not None:
            # Scalar - will be normalized
            result.auto_corrections.append(f"{context} field '{field_name}' will be normalized to [value, null]")


def _validate_extensions(result: ValidationResult):
    """Validate extension references."""
    spec = result.corrected_spec
    
    if "extensions" not in spec:
        return
    
    extensions = spec["extensions"]
    
    if not isinstance(extensions, list):
        result.warnings.append("'extensions' should be an array")
        spec["extensions"] = []
        return
    
    valid_extensions = {
        "pen", "music", "videoSensing", "text2speech", "translate",
        "makeymakey", "microbit", "ev3", "boost", "wedo2", "gdxfor",
    }
    
    for ext in extensions:
        if ext not in valid_extensions:
            result.warnings.append(f"Extension '{ext}' may not be supported in standard Scratch")


def format_validation_report(result: ValidationResult) -> str:
    """Format validation results for display."""
    lines = []
    lines.append(f"Validation Report for: {result.corrected_spec.get('name', 'Untitled')}")
    lines.append("=" * 50)
    
    if result.has_errors:
        lines.append(f"\n❌ ERRORS ({len(result.errors)}):")
        for err in result.errors:
            lines.append(f"  • {err}")
    
    if result.has_warnings:
        lines.append(f"\n⚠️ WARNINGS ({len(result.warnings)}):")
        for warn in result.warnings:
            lines.append(f"  • {warn}")
    
    if result.auto_corrections:
        lines.append(f"\n🔧 AUTO-CORRECTIONS ({len(result.auto_corrections)}):")
        for corr in result.auto_corrections:
            lines.append(f"  • {corr}")
    
    if not result.has_errors and not result.has_warnings and not result.auto_corrections:
        lines.append("\n✅ Spec is valid - no issues found!")
    
    return "\n".join(lines)


# Export
__all__ = [
    "validate_spec",
    "ValidationResult",
    "format_validation_report",
    "KNOWN_OPCODES",
    "VALID_COSTUMES",
    "VALID_ROTATION_STYLES",
    "HAT_OPCODES",
]
