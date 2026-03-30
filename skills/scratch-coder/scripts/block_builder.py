#!/usr/bin/env python3
"""
Block Builder - Helper for constructing Scratch 3.0 block JSON structures.

Usage:
    from block_builder import BlockBuilder, create_hat, create_stack, create_reporter
"""

import uuid
from typing import Any


def generate_id() -> str:
    """Generate a unique block ID."""
    return uuid.uuid4().hex[:16].upper()


class BlockBuilder:
    """Helper class for building Scratch block JSON structures."""

    def __init__(self):
        self.blocks: dict[str, Any] = {}
        self._block_order: list[str] = []

    def add_block(self, block: dict, block_id: str | None = None) -> str:
        """Add a block to the builder and return its ID."""
        if block_id is None:
            block_id = generate_id()
        self.blocks[block_id] = block
        self._block_order.append(block_id)
        return block_id

    def create_hat(
        self,
        opcode: str,
        fields: dict | None = None,
        inputs: dict | None = None,
    ) -> tuple[str, dict]:
        """Create a hat block (event trigger)."""
        block_id = generate_id()
        block = {
            "opcode": opcode,
            "next": None,
            "parent": None,
            "inputs": inputs or {},
            "fields": fields or {},
            "shadow": False,
            "topLevel": True,
            "x": 0,
            "y": 0,
        }
        return block_id, block

    def create_stack(
        self,
        opcode: str,
        fields: dict | None = None,
        inputs: dict | None = None,
        next_block_id: str | None = None,
        parent_id: str | None = None,
    ) -> tuple[str, dict]:
        """Create a regular stack block."""
        block_id = generate_id()
        block = {
            "opcode": opcode,
            "next": next_block_id,
            "parent": parent_id,
            "inputs": inputs or {},
            "fields": fields or {},
            "shadow": False,
            "topLevel": False,
        }
        return block_id, block

    def create_reporter(
        self,
        opcode: str,
        fields: dict | None = None,
        inputs: dict | None = None,
        shadow: bool = True,
    ) -> tuple[str, dict]:
        """Create a reporter block (value reporter)."""
        block_id = generate_id()
        block = {
            "opcode": opcode,
            "next": None,
            "parent": None,
            "inputs": inputs or {},
            "fields": fields or {},
            "shadow": shadow,
            "topLevel": False,
        }
        return block_id, block

    def create_c_block(
        self,
        opcode: str,
        fields: dict | None = None,
        inputs: dict | None = None,
        next_block_id: str | None = None,
    ) -> tuple[str, dict, str, str]:
        """Create a C-shaped block (if, repeat, forever, etc.).
        
        Returns: (block_id, block, substack1_id, substack2_id)
        """
        block_id = generate_id()
        substack1_id = generate_id()
        substack2_id = generate_id() if "else" in opcode else None

        block = {
            "opcode": opcode,
            "next": next_block_id,
            "parent": None,
            "inputs": inputs or {"SUBSTACK": [2, substack1_id]},
            "fields": fields or {},
            "shadow": False,
            "topLevel": False,
        }

        if substack2_id:
            block["inputs"]["SUBSTACK2"] = [2, substack2_id]

        return block_id, block, substack1_id, substack2_id

    def link_blocks(self, *block_ids: str) -> None:
        """Link a chain of blocks together via 'next'."""
        for i in range(len(block_ids) - 1):
            self.blocks[block_ids[i]]["next"] = block_ids[i + 1]

    def build(self) -> dict[str, Any]:
        """Build and return the blocks dictionary."""
        return self.blocks.copy()


def input_value(value: Any) -> list:
    """Create a literal value input."""
    if isinstance(value, str):
        return [10, value]
    elif isinstance(value, bool):
        return [1, "true" if value else "false"]
    elif isinstance(value, (int, float)):
        return [4, value]
    return [10, str(value)]


def input_block(block_id: str) -> list:
    """Create an input that references another block."""
    return [2, block_id]


def input_obsured_shadow(block_id: str, shadow_value: Any) -> list:
    """Create an input with an obscured shadow block."""
    return [3, block_id, input_value(shadow_value)]


def field_value(name: str, id: str | None = None) -> list:
    """Create a field value array."""
    if id:
        return [name, id]
    return [name]


def variable_field(name: str, var_id: str) -> list:
    """Create a variable dropdown field."""
    return [name, var_id]


def broadcast_field(broadcast_id: str, broadcast_name: str) -> list:
    """Create a broadcast dropdown field."""
    return [broadcast_id, broadcast_name]


def create_sprite_blocks(builder: BlockBuilder) -> dict:
    """Create a basic sprite with event handlers."""
    blocks = {}

    flag_id, flag_block = builder.create_hat("event_whenflagclicked")
    blocks[flag_id] = flag_block

    return blocks


def create_stage_blocks(builder: BlockBuilder) -> dict:
    """Create a basic stage with green flag handler."""
    blocks = {}

    flag_id, flag_block = builder.create_hat("event_whenflagclicked")
    blocks[flag_id] = flag_block

    return blocks


def add_green_flag_script(blocks: dict, *script_blocks: tuple[str, dict]) -> str:
    """Add a green flag script and return the hat block ID."""
    hat_id = generate_id()
    blocks[hat_id] = {
        "opcode": "event_whenflagclicked",
        "next": script_blocks[0][0] if script_blocks else None,
        "parent": None,
        "inputs": {},
        "fields": {},
        "shadow": False,
        "topLevel": True,
        "x": 0,
        "y": 0,
    }

    for i, (block_id, block) in enumerate(script_blocks):
        blocks[block_id] = block
        if i > 0:
            blocks[script_blocks[i - 1][0]]["next"] = block_id

    return hat_id


def add_keypress_script(
    blocks: dict, key: str, *script_blocks: tuple[str, dict], x: int = 0, y: int = 0
) -> str:
    """Add a key press script and return the hat block ID."""
    hat_id = generate_id()
    blocks[hat_id] = {
        "opcode": "event_whenkeypressed",
        "next": script_blocks[0][0] if script_blocks else None,
        "parent": None,
        "inputs": {},
        "fields": {"KEY_OPTION": [key, None]},
        "shadow": False,
        "topLevel": True,
        "x": x,
        "y": y,
    }

    for i, (block_id, block) in enumerate(script_blocks):
        blocks[block_id] = block
        if i > 0:
            blocks[script_blocks[i - 1][0]]["next"] = block_id

    return hat_id


def add_broadcast_script(
    blocks: dict,
    message: str,
    broadcast_id: str | None = None,
    *script_blocks: tuple[str, dict],
    x: int = 0,
    y: int = 0,
) -> str:
    """Add a broadcast receive script and return the hat block ID."""
    hat_id = generate_id()
    if broadcast_id is None:
        broadcast_id = generate_id()
    blocks[hat_id] = {
        "opcode": "event_whenbroadcastreceived",
        "next": script_blocks[0][0] if script_blocks else None,
        "parent": None,
        "inputs": {},
        "fields": {"BROADCAST_OPTION": [message, broadcast_id]},
        "shadow": False,
        "topLevel": True,
        "x": x,
        "y": y,
    }

    for i, (block_id, block) in enumerate(script_blocks):
        blocks[block_id] = block
        if i > 0:
            blocks[script_blocks[i - 1][0]]["next"] = block_id

    return hat_id


if __name__ == "__main__":
    print("Block Builder module for Scratch 3.0")
    print("Import this module to create block JSON structures.")
