"""Unit tests for skills/scratch-coder/scripts/generate_sb3.py"""

import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "scratch-coder" / "scripts"))

from generate_sb3 import (
    BUILT_IN_COSTUMES,
    convert_blocks_from_agent_format,
    create_project,
    create_sprite,
    create_stage,
    get_required_assets,
    resolve_backdrop,
    save_sb3,
)


class TestCreateStage:
    def test_is_stage(self):
        stage = create_stage({})
        assert stage["isStage"] is True
        assert stage["name"] == "Stage"

    def test_default_backdrop(self):
        stage = create_stage({})
        assert len(stage["costumes"]) >= 1

    def test_variables_passed_through(self):
        spec = {"variables": {"var_id": ["Score", 0]}}
        stage = create_stage(spec)
        assert "var_id" in stage["variables"]
        assert stage["variables"]["var_id"] == ["Score", 0]

    def test_broadcasts_passed_through(self):
        spec = {"broadcasts": {"b_id": "start"}}
        stage = create_stage(spec)
        assert stage["broadcasts"] == {"b_id": "start"}

    def test_custom_backdrop_string(self):
        stage = create_stage({"backdrops": ["cat"]})
        assert any(c["name"] == "cat" for c in stage["costumes"])

    def test_empty_spec(self):
        stage = create_stage({})
        assert stage["layerOrder"] == 0
        assert stage["volume"] == 100


class TestCreateSprite:
    def test_basic_sprite(self):
        sprite = create_sprite("Player")
        assert sprite["name"] == "Player"
        assert sprite["isStage"] is False
        assert sprite["visible"] is True

    def test_position(self):
        sprite = create_sprite("Ball", x=100, y=-50)
        assert sprite["x"] == 100
        assert sprite["y"] == -50

    def test_cat_costume_resolves(self):
        sprite = create_sprite("Cat", costume="cat")
        assert len(sprite["costumes"]) == 2
        assert sprite["costumes"][0]["name"] == "costume1"

    def test_tennis_costume_resolves(self):
        sprite = create_sprite("Ball", costume="tennis")
        assert sprite["costumes"][0]["name"] == "tennis ball"

    def test_unknown_costume_falls_back_to_cat(self):
        sprite = create_sprite("X", costume="nonexistent_costume")
        assert sprite["costumes"][0]["name"] == "costume1"

    def test_direction(self):
        sprite = create_sprite("Arrow", direction=180)
        assert sprite["direction"] == 180

    def test_rotation_style(self):
        sprite = create_sprite("Car", rotation_style="left-right")
        assert sprite["rotationStyle"] == "left-right"

    def test_variables_passed(self):
        sprite = create_sprite("P", variables={"v1": ["Speed", 5]})
        assert sprite["variables"]["v1"] == ["Speed", 5]


class TestConvertBlocksFromAgentFormat:
    def test_list_format_creates_hat(self):
        blocks_spec = {
            "script1": [
                {"opcode": "motion_movesteps", "inputs": {"STEPS": [4, 10]}, "fields": {}},
            ]
        }
        blocks = convert_blocks_from_agent_format(blocks_spec)
        hat_blocks = [b for b in blocks.values() if b.get("topLevel")]
        assert len(hat_blocks) == 1
        assert hat_blocks[0]["opcode"] == "event_whenflagclicked"

    def test_dict_format_passthrough(self):
        blocks_spec = {
            "BLOCK_A": {
                "opcode": "event_whenflagclicked",
                "next": None,
                "parent": None,
                "inputs": {},
                "fields": {},
                "shadow": False,
                "topLevel": True,
                "x": 0,
                "y": 0,
            }
        }
        blocks = convert_blocks_from_agent_format(blocks_spec)
        assert "BLOCK_A" in blocks

    def test_chain_linked(self):
        blocks_spec = {
            "s": [
                {"opcode": "motion_movesteps", "inputs": {"STEPS": [4, 5]}, "fields": {}},
                {"opcode": "motion_turnright", "inputs": {"DEGREES": [4, 15]}, "fields": {}},
            ]
        }
        blocks = convert_blocks_from_agent_format(blocks_spec)
        stack_blocks = [b for b in blocks.values() if not b.get("topLevel")]
        assert len(stack_blocks) == 2
        first_id = next(
            bid for bid, b in blocks.items()
            if not b.get("topLevel") and b["opcode"] == "motion_movesteps"
        )
        assert blocks[first_id]["next"] is not None


class TestCreateProject:
    def test_always_has_stage(self):
        project = create_project({})
        assert any(t["isStage"] for t in project["targets"])

    def test_sprites_added(self):
        spec = {
            "sprites": [
                {"name": "Ball", "costume": "tennis", "x": 0, "y": 0},
                {"name": "Paddle", "costume": "cat", "x": -200, "y": 0},
            ]
        }
        project = create_project(spec)
        names = [t["name"] for t in project["targets"]]
        assert "Ball" in names
        assert "Paddle" in names

    def test_extensions(self):
        spec = {"extensions": ["pen"]}
        project = create_project(spec)
        assert "pen" in project["extensions"]

    def test_meta_present(self):
        project = create_project({})
        assert "semver" in project["meta"]

    def test_layer_order_unique(self):
        spec = {
            "sprites": [
                {"name": f"S{i}", "costume": "cat"} for i in range(3)
            ]
        }
        project = create_project(spec)
        orders = [t["layerOrder"] for t in project["targets"]]
        assert len(orders) == len(set(orders))


class TestGetRequiredAssets:
    def test_collects_costume_assets(self):
        project = create_project(
            {"sprites": [{"name": "Cat", "costume": "cat"}]}
        )
        assets = get_required_assets(project)
        assert "bcf454acf82e4504149f7ffe07081dbc.svg" in assets

    def test_collects_sound_assets(self):
        project = {"targets": [{"costumes": [], "sounds": [
            {"assetId": "abc", "md5ext": "abc.wav"}
        ]}]}
        assets = get_required_assets(project)
        assert "abc.wav" in assets


class TestSaveSb3:
    def test_creates_zip(self, tmp_path):
        project = create_project(
            {"sprites": [{"name": "Cat", "costume": "cat"}]}
        )
        out = tmp_path / "test.sb3"
        result = save_sb3(project, out)
        assert result == out
        assert out.exists()
        with zipfile.ZipFile(out) as zf:
            assert "project.json" in zf.namelist()

    def test_project_json_valid(self, tmp_path):
        project = create_project({})
        out = tmp_path / "out.sb3"
        save_sb3(project, out)
        with zipfile.ZipFile(out) as zf:
            data = json.loads(zf.read("project.json"))
        assert "targets" in data
        assert any(t["isStage"] for t in data["targets"])

    def test_creates_parent_dirs(self, tmp_path):
        project = create_project({})
        out = tmp_path / "nested" / "deep" / "test.sb3"
        save_sb3(project, out)
        assert out.exists()


class TestResolveBackdrop:
    def test_string_known(self):
        result = resolve_backdrop("cat")
        assert isinstance(result, dict)
        assert result["name"] == "cat"
        assert "assetId" in result

    def test_string_unknown_falls_back_to_blank_stage(self):
        result = resolve_backdrop("unknown_backdrop_xyz")
        assert isinstance(result, dict)
        assert result["assetId"] == "cd21514d0531fdffb22204e0ec5ed84a"
        assert result["name"] == "unknown_backdrop_xyz"

    def test_dict_with_costume_key(self):
        result = resolve_backdrop({"costume": "tennis", "name": "bg"})
        assert isinstance(result, dict)
        assert result["name"] == "bg"
        assert "assetId" in result

    def test_dict_with_asset_id(self):
        spec = {"assetId": "abc", "md5ext": "abc.svg", "name": "bg"}
        result = resolve_backdrop(spec)
        assert result == spec

    def test_dict_unknown_costume_falls_back_to_blank(self):
        result = resolve_backdrop({"costume": "nonexistent", "name": "MyLevel"})
        assert isinstance(result, dict)
        assert result["assetId"] == "cd21514d0531fdffb22204e0ec5ed84a"
        assert result["name"] == "MyLevel"
