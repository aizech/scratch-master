"""
Block Templates - Pre-built, validated patterns for common Scratch game mechanics.

Usage:
    from templates import PlatformerMovement, PongPaddle, BouncingBall, ScoreCounter
    
    # Generate complete block subgraphs
    blocks = PlatformerMovement(left_key="left arrow", right_key="right arrow").build()
"""

from typing import Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from block_builder import BlockBuilder, generate_id, input_block, input_value


class InputBuilder:
    """Build canonical Scratch input formats."""
    
    @staticmethod
    def number(n: int | float) -> list:
        """Create a number input: [1, [4, "value"]]"""
        return [1, [4, str(n)]]
    
    @staticmethod
    def integer(n: int) -> list:
        """Create an integer input: [1, [5, "value"]]"""
        return [1, [5, str(int(n))]]
    
    @staticmethod
    def string(s: str) -> list:
        """Create a string input: [1, [10, "value"]]"""
        return [1, [10, s]]
    
    @staticmethod
    def block_ref(block_id: str) -> list:
        """Reference another block: [2, block_id]"""
        return [2, block_id]
    
    @staticmethod
    def obscured_shadow(block_id: str, default_value: Any) -> list:
        """Obscured shadow input: [3, block_id, [type, value]]"""
        if isinstance(default_value, (int, float)):
            shadow = [4, str(default_value)]
        else:
            shadow = [10, str(default_value)]
        return [3, block_id, shadow]


class BlockTemplate:
    """Base class for all block templates."""
    
    def __init__(self):
        self.builder = BlockBuilder()
        self.blocks: dict[str, Any] = {}
    
    def build(self) -> dict[str, Any]:
        """Return the complete blocks dictionary."""
        return dict(self.blocks)


class PlatformerMovement(BlockTemplate):
    """
    Platformer player movement with arrow keys and jumping.
    
    Generates: green flag hat → forever loop with:
      - Left/right movement with key detection
      - Jump when space pressed (simple version)
    """
    
    def __init__(
        self,
        left_key: str = "left arrow",
        right_key: str = "right arrow",
        jump_key: str = "space",
        move_speed: int = 5,
        jump_height: int = 10,
    ):
        super().__init__()
        self.left_key = left_key
        self.right_key = right_key
        self.jump_key = jump_key
        self.move_speed = move_speed
        self.jump_height = jump_height
        self._build()
    
    def _build(self):
        # Green flag hat
        hat_id = generate_id()
        self.blocks[hat_id] = {
            "opcode": "event_whenflagclicked",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 20,
            "y": 20,
        }
        
        # Forever block
        forever_id = generate_id()
        self.blocks[forever_id] = {
            "opcode": "control_forever",
            "next": None,
            "parent": hat_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = forever_id
        
        # Left key check (if key pressed → change x by -speed)
        left_if_id, left_substack_id = self._add_key_movement(
            parent=forever_id,
            key=self.left_key,
            dx=-self.move_speed,
            x=50,
            y=20,
        )
        self.blocks[forever_id]["inputs"]["SUBSTACK"] = [2, left_if_id]
        
        # Right key check (chain after left)
        right_if_id, right_substack_id = self._add_key_movement(
            parent=left_if_id,
            key=self.right_key,
            dx=self.move_speed,
            x=50,
            y=100,
        )
        self.blocks[left_if_id]["next"] = right_if_id
        
        # Jump key check
        jump_if_id, jump_substack_id = self._add_key_jump(
            parent=right_if_id,
            key=self.jump_key,
        )
        self.blocks[right_if_id]["next"] = jump_if_id
    
    def _add_key_movement(self, parent: str, key: str, dx: int, x: int, y: int):
        """Add if-key-pressed → change x by dx."""
        # Key pressed sensing block
        sensing_id = generate_id()
        self.blocks[sensing_id] = {
            "opcode": "sensing_keypressed",
            "next": None,
            "parent": None,  # Will be set by _infer_parents
            "inputs": {},
            "fields": {"KEY_OPTION": [key, None]},
            "shadow": False,
            "topLevel": False,
        }
        
        # Move block inside substack
        move_id = generate_id()
        self.blocks[move_id] = {
            "opcode": "motion_changexby",
            "next": None,
            "parent": None,
            "inputs": {"DX": InputBuilder.number(dx)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        # If block
        if_id = generate_id()
        self.blocks[if_id] = {
            "opcode": "control_if",
            "next": None,
            "parent": parent,
            "inputs": {
                "CONDITION": [2, sensing_id],
                "SUBSTACK": [2, move_id],
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        return if_id, move_id
    
    def _add_key_jump(self, parent: str, key: str):
        """Add if-key-pressed → change y by jump_height."""
        # Key pressed
        sensing_id = generate_id()
        self.blocks[sensing_id] = {
            "opcode": "sensing_keypressed",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {"KEY_OPTION": [key, None]},
            "shadow": False,
            "topLevel": False,
        }
        
        # Jump (change y)
        jump_id = generate_id()
        self.blocks[jump_id] = {
            "opcode": "motion_changeyby",
            "next": None,
            "parent": None,
            "inputs": {"DY": InputBuilder.number(self.jump_height)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        # If block
        if_id = generate_id()
        self.blocks[if_id] = {
            "opcode": "control_if",
            "next": None,
            "parent": parent,
            "inputs": {
                "CONDITION": [2, sensing_id],
                "SUBSTACK": [2, jump_id],
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        return if_id, jump_id


class PongPaddle(BlockTemplate):
    """
    Pong paddle controlled by keys or mouse.
    
    Generates: green flag hat → forever loop with up/down movement.
    """
    
    def __init__(
        self,
        up_key: str = "up arrow",
        down_key: str = "down arrow",
        move_speed: int = 10,
        use_mouse: bool = False,
    ):
        super().__init__()
        self.up_key = up_key
        self.down_key = down_key
        self.move_speed = move_speed
        self.use_mouse = use_mouse
        self._build()
    
    def _build(self):
        # Green flag hat
        hat_id = generate_id()
        self.blocks[hat_id] = {
            "opcode": "event_whenflagclicked",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 20,
            "y": 20,
        }
        
        if self.use_mouse:
            self._build_mouse_control(hat_id)
        else:
            self._build_key_control(hat_id)
    
    def _build_key_control(self, hat_id: str):
        """Build key-based paddle control."""
        # Forever block
        forever_id = generate_id()
        self.blocks[forever_id] = {
            "opcode": "control_forever",
            "next": None,
            "parent": hat_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = forever_id
        
        # Up key check
        up_sensing_id = generate_id()
        self.blocks[up_sensing_id] = {
            "opcode": "sensing_keypressed",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {"KEY_OPTION": [self.up_key, None]},
            "shadow": False,
            "topLevel": False,
        }
        
        up_move_id = generate_id()
        self.blocks[up_move_id] = {
            "opcode": "motion_changeyby",
            "next": None,
            "parent": None,
            "inputs": {"DY": InputBuilder.number(self.move_speed)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        up_if_id = generate_id()
        self.blocks[up_if_id] = {
            "opcode": "control_if",
            "next": None,
            "parent": forever_id,
            "inputs": {
                "CONDITION": [2, up_sensing_id],
                "SUBSTACK": [2, up_move_id],
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[forever_id]["inputs"]["SUBSTACK"] = [2, up_if_id]
        
        # Down key check
        down_sensing_id = generate_id()
        self.blocks[down_sensing_id] = {
            "opcode": "sensing_keypressed",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {"KEY_OPTION": [self.down_key, None]},
            "shadow": False,
            "topLevel": False,
        }
        
        down_move_id = generate_id()
        self.blocks[down_move_id] = {
            "opcode": "motion_changeyby",
            "next": None,
            "parent": None,
            "inputs": {"DY": InputBuilder.number(-self.move_speed)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        down_if_id = generate_id()
        self.blocks[down_if_id] = {
            "opcode": "control_if",
            "next": None,
            "parent": up_if_id,
            "inputs": {
                "CONDITION": [2, down_sensing_id],
                "SUBSTACK": [2, down_move_id],
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[up_if_id]["next"] = down_if_id
    
    def _build_mouse_control(self, hat_id: str):
        """Build mouse-based paddle control (follows mouse Y)."""
        # Forever block
        forever_id = generate_id()
        self.blocks[forever_id] = {
            "opcode": "control_forever",
            "next": None,
            "parent": hat_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = forever_id
        
        # Set y to mouse y
        mousey_id = generate_id()
        self.blocks[mousey_id] = {
            "opcode": "sensing_mousey",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        sety_id = generate_id()
        self.blocks[sety_id] = {
            "opcode": "motion_sety",
            "next": None,
            "parent": forever_id,
            "inputs": {"Y": [3, mousey_id, [4, "0"]]},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[forever_id]["inputs"]["SUBSTACK"] = [2, sety_id]


class BouncingBall(BlockTemplate):
    """
    Ball that moves and bounces off edges.
    
    Generates: green flag hat → go to center → forever (move, bounce).
    """
    
    def __init__(self, speed: int = 5):
        super().__init__()
        self.speed = speed
        self._build()
    
    def _build(self):
        # Green flag hat
        hat_id = generate_id()
        self.blocks[hat_id] = {
            "opcode": "event_whenflagclicked",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 20,
            "y": 20,
        }
        
        # Go to center (0,0)
        gotoxy_id = generate_id()
        self.blocks[gotoxy_id] = {
            "opcode": "motion_gotoxy",
            "next": None,
            "parent": hat_id,
            "inputs": {
                "X": InputBuilder.number(0),
                "Y": InputBuilder.number(0),
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = gotoxy_id
        
        # Point in random direction
        point_id = generate_id()
        self.blocks[point_id] = {
            "opcode": "motion_pointindirection",
            "next": None,
            "parent": gotoxy_id,
            "inputs": {"DIRECTION": InputBuilder.number(45)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[gotoxy_id]["next"] = point_id
        
        # Forever loop
        forever_id = generate_id()
        self.blocks[forever_id] = {
            "opcode": "control_forever",
            "next": None,
            "parent": point_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[point_id]["next"] = forever_id
        
        # Move steps
        move_id = generate_id()
        self.blocks[move_id] = {
            "opcode": "motion_movesteps",
            "next": None,
            "parent": forever_id,
            "inputs": {"STEPS": InputBuilder.number(self.speed)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        # Bounce on edge
        bounce_id = generate_id()
        self.blocks[bounce_id] = {
            "opcode": "motion_ifonedgebounce",
            "next": None,
            "parent": move_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[move_id]["next"] = bounce_id
        
        self.blocks[forever_id]["inputs"]["SUBSTACK"] = [2, move_id]


class ScoreCounter(BlockTemplate):
    """
    Stage-based score counter that responds to broadcasts.
    
    Generates: when I receive "score_up" → change score variable.
    """
    
    def __init__(self, variable_name: str = "Score", increment: int = 1):
        super().__init__()
        self.variable_name = variable_name
        self.increment = increment
        self._build()
    
    def _build(self):
        # Broadcast receiver hat
        hat_id = generate_id()
        self.blocks[hat_id] = {
            "opcode": "event_whenbroadcastreceived",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {"BROADCAST_OPTION": ["score_up", generate_id()]},
            "shadow": False,
            "topLevel": True,
            "x": 20,
            "y": 20,
        }
        
        # Change variable by increment
        var_id = generate_id()
        self.blocks[var_id] = {
            "opcode": "data_changevariableby",
            "next": None,
            "parent": hat_id,
            "inputs": {"VALUE": InputBuilder.number(self.increment)},
            "fields": {"VARIABLE": [self.variable_name, generate_id()]},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = var_id


class CatchGameItem(BlockTemplate):
    """
    Falling item for catch games (falls from top, resets when caught/missed).
    
    Generates: green flag hat → hide → forever (go to random x at top, show, fall, check caught).
    """
    
    def __init__(self, fall_speed: int = 5, catcher_sprite: str = "Player"):
        super().__init__()
        self.fall_speed = fall_speed
        self.catcher_sprite = catcher_sprite
        self._build()
    
    def _build(self):
        # Green flag hat
        hat_id = generate_id()
        self.blocks[hat_id] = {
            "opcode": "event_whenflagclicked",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 20,
            "y": 20,
        }
        
        # Hide initially
        hide_id = generate_id()
        self.blocks[hide_id] = {
            "opcode": "looks_hide",
            "next": None,
            "parent": hat_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = hide_id
        
        # Forever loop
        forever_id = generate_id()
        self.blocks[forever_id] = {
            "opcode": "control_forever",
            "next": None,
            "parent": hide_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hide_id]["next"] = forever_id
        
        # Go to random x at top
        randomx_id = generate_id()
        self.blocks[randomx_id] = {
            "opcode": "operator_random",
            "next": None,
            "parent": None,
            "inputs": {
                "FROM": InputBuilder.number(-200),
                "TO": InputBuilder.number(200),
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        gotoxy_id = generate_id()
        self.blocks[gotoxy_id] = {
            "opcode": "motion_gotoxy",
            "next": None,
            "parent": None,
            "inputs": {
                "X": [3, randomx_id, [4, "0"]],
                "Y": InputBuilder.number(180),
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        # Show
        show_id = generate_id()
        self.blocks[show_id] = {
            "opcode": "looks_show",
            "next": None,
            "parent": gotoxy_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[gotoxy_id]["next"] = show_id
        
        # Fall repeat until touching bottom or catcher
        # (Simplified: just fall with glide)
        glide_id = generate_id()
        self.blocks[glide_id] = {
            "opcode": "motion_glidesecstoxy",
            "next": None,
            "parent": show_id,
            "inputs": {
                "SECS": InputBuilder.number(2),
                "X": [3, randomx_id, [4, "0"]],  # Reuse random x
                "Y": InputBuilder.number(-180),
            },
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[show_id]["next"] = glide_id
        
        # Hide after fall
        hide2_id = generate_id()
        self.blocks[hide2_id] = {
            "opcode": "looks_hide",
            "next": None,
            "parent": glide_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[glide_id]["next"] = hide2_id
        
        self.blocks[forever_id]["inputs"]["SUBSTACK"] = [2, gotoxy_id]


class CostumeAnimation(BlockTemplate):
    """
    Simple costume-switching animation (next costume with wait).
    
    Generates: green flag hat → forever (next costume, wait).
    """
    
    def __init__(self, wait_seconds: float = 0.2):
        super().__init__()
        self.wait_seconds = wait_seconds
        self._build()
    
    def _build(self):
        # Green flag hat
        hat_id = generate_id()
        self.blocks[hat_id] = {
            "opcode": "event_whenflagclicked",
            "next": None,
            "parent": None,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": True,
            "x": 20,
            "y": 20,
        }
        
        # Forever loop
        forever_id = generate_id()
        self.blocks[forever_id] = {
            "opcode": "control_forever",
            "next": None,
            "parent": hat_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[hat_id]["next"] = forever_id
        
        # Next costume
        nextcostume_id = generate_id()
        self.blocks[nextcostume_id] = {
            "opcode": "looks_nextcostume",
            "next": None,
            "parent": forever_id,
            "inputs": {},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        
        # Wait
        wait_id = generate_id()
        self.blocks[wait_id] = {
            "opcode": "control_wait",
            "next": None,
            "parent": nextcostume_id,
            "inputs": {"DURATION": InputBuilder.number(self.wait_seconds)},
            "fields": {},
            "shadow": False,
            "topLevel": False,
        }
        self.blocks[nextcostume_id]["next"] = wait_id
        
        self.blocks[forever_id]["inputs"]["SUBSTACK"] = [2, nextcostume_id]


# Export all templates
__all__ = [
    "InputBuilder",
    "BlockTemplate",
    "PlatformerMovement",
    "PongPaddle",
    "BouncingBall",
    "ScoreCounter",
    "CatchGameItem",
    "CostumeAnimation",
]
