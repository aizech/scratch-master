"""Unit tests for skills/scratch-coder/scripts/block_builder.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "scratch-coder" / "scripts"))

from block_builder import (
    BlockBuilder,
    generate_id,
    input_value,
    input_block,
    input_obsured_shadow,
    field_value,
    add_green_flag_script,
    add_keypress_script,
)


def test_generate_id_format():
    id_ = generate_id()
    assert len(id_) == 16
    assert id_ == id_.upper()
    int(id_, 16)  # must be valid hex


def test_generate_id_unique():
    ids = {generate_id() for _ in range(100)}
    assert len(ids) == 100


class TestBlockBuilder:
    def setup_method(self):
        self.bb = BlockBuilder()

    def test_create_hat_top_level(self):
        block_id, block = self.bb.create_hat("event_whenflagclicked")
        assert block["topLevel"] is True
        assert block["opcode"] == "event_whenflagclicked"
        assert block["parent"] is None
        assert block["next"] is None

    def test_create_hat_with_fields(self):
        _, block = self.bb.create_hat(
            "event_whenkeypressed",
            fields={"KEY_OPTION": ["space", None]},
        )
        assert block["fields"]["KEY_OPTION"] == ["space", None]

    def test_create_stack_not_top_level(self):
        block_id, block = self.bb.create_stack("motion_movesteps")
        assert block["topLevel"] is False
        assert block["opcode"] == "motion_movesteps"

    def test_create_stack_with_parent(self):
        _, block = self.bb.create_stack("motion_movesteps", parent_id="PARENT123")
        assert block["parent"] == "PARENT123"

    def test_create_reporter(self):
        _, block = self.bb.create_reporter("motion_xposition")
        assert block["topLevel"] is False
        assert block["shadow"] is True

    def test_create_c_block_forever(self):
        block_id, block, sub1, sub2 = self.bb.create_c_block("control_forever")
        assert block["inputs"]["SUBSTACK"] == [2, sub1]
        assert sub2 is None

    def test_create_c_block_if_else(self):
        block_id, block, sub1, sub2 = self.bb.create_c_block("control_if_else")
        assert block["inputs"]["SUBSTACK"] == [2, sub1]
        assert block["inputs"]["SUBSTACK2"] == [2, sub2]
        assert sub2 is not None

    def test_add_block_returns_id(self):
        _, block = self.bb.create_stack("motion_movesteps")
        block_id = self.bb.add_block(block)
        assert block_id in self.bb.blocks

    def test_link_blocks(self):
        _, b1 = self.bb.create_stack("motion_movesteps")
        id1 = self.bb.add_block(b1)
        _, b2 = self.bb.create_stack("motion_turnright")
        id2 = self.bb.add_block(b2)
        self.bb.link_blocks(id1, id2)
        assert self.bb.blocks[id1]["next"] == id2

    def test_build_returns_copy(self):
        built = self.bb.build()
        assert built is not self.bb.blocks


class TestInputHelpers:
    def test_input_value_string(self):
        assert input_value("hello") == [10, "hello"]

    def test_input_value_int(self):
        assert input_value(5) == [4, 5]

    def test_input_value_float(self):
        assert input_value(3.14) == [4, 3.14]

    def test_input_value_bool(self):
        assert input_value(True) == [1, "true"]
        assert input_value(False) == [1, "false"]

    def test_input_block(self):
        assert input_block("BLOCK_ID") == [2, "BLOCK_ID"]

    def test_input_obscured_shadow(self):
        result = input_obsured_shadow("BLOCK_ID", 10)
        assert result[0] == 3
        assert result[1] == "BLOCK_ID"
        assert result[2] == [4, 10]


class TestScriptHelpers:
    def test_add_green_flag_script(self):
        blocks = {}
        bb = BlockBuilder()
        move_id, move_block = bb.create_stack("motion_movesteps")
        hat_id = add_green_flag_script(blocks, (move_id, move_block))
        assert blocks[hat_id]["opcode"] == "event_whenflagclicked"
        assert blocks[hat_id]["topLevel"] is True
        assert blocks[hat_id]["next"] == move_id
        assert move_id in blocks

    def test_add_keypress_script(self):
        blocks = {}
        bb = BlockBuilder()
        move_id, move_block = bb.create_stack("motion_movesteps")
        hat_id = add_keypress_script(blocks, "space", (move_id, move_block))
        assert blocks[hat_id]["opcode"] == "event_whenkeypressed"
        assert blocks[hat_id]["fields"]["KEY_OPTION"] == ["space", None]
        assert move_id in blocks

    def test_add_green_flag_links_chain(self):
        blocks = {}
        bb = BlockBuilder()
        id1, b1 = bb.create_stack("motion_movesteps")
        id2, b2 = bb.create_stack("motion_turnright")
        add_green_flag_script(blocks, (id1, b1), (id2, b2))
        assert blocks[id1]["next"] == id2
