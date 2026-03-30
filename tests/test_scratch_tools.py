"""Unit tests for tools/scratch_tools.py

Agno's @tool decorator wraps functions in a Function object.
We call the underlying Python function via ._run() or by importing the
private implementation directly from the module.
"""

import json
import sys
import zipfile
from pathlib import Path

import pytest

# Point to project root so imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "scratch-coder" / "scripts"))

import tools.scratch_tools as _st_mod


def _make_sb3(path: Path, project: dict) -> None:
    """Helper: write a minimal .sb3 zip to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("project.json", json.dumps(project))


def _call(tool_obj, *args, **kwargs):
    """Call the underlying Python function wrapped by Agno's @tool decorator."""
    fn = getattr(tool_obj, "entrypoint", None)
    if fn is None:
        fn = getattr(tool_obj, "_func", None)
    if fn is None and callable(tool_obj):
        fn = tool_obj
    if fn is None:
        raise RuntimeError(f"Cannot find callable on tool object: {type(tool_obj)}")
    return fn(*args, **kwargs)


# Patch the output dir to a tmp location for every test
@pytest.fixture(autouse=True)
def patch_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(_st_mod, "_OUTPUT_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------

class TestListProjects:
    def test_empty_output(self, tmp_path):
        result = json.loads(_call(_st_mod.list_projects))
        assert result["sb3_files"] == []
        assert result["spec_files"] == []

    def test_detects_sb3(self, tmp_path):
        (tmp_path / "game.sb3").write_bytes(b"PK")
        result = json.loads(_call(_st_mod.list_projects))
        assert "game.sb3" in result["sb3_files"]

    def test_detects_spec(self, tmp_path):
        (tmp_path / "game_spec.json").write_text("{}")
        result = json.loads(_call(_st_mod.list_projects))
        assert "game_spec.json" in result["spec_files"]

    def test_sorted_output(self, tmp_path):
        for name in ["c.sb3", "a.sb3", "b.sb3"]:
            (tmp_path / name).write_bytes(b"PK")
        result = json.loads(_call(_st_mod.list_projects))
        assert result["sb3_files"] == ["a.sb3", "b.sb3", "c.sb3"]


# ---------------------------------------------------------------------------
# load_spec
# ---------------------------------------------------------------------------

class TestLoadSpec:
    def test_load_existing(self, tmp_path):
        spec = {"name": "My Game", "sprites": []}
        (tmp_path / "game_spec.json").write_text(json.dumps(spec))
        result = json.loads(_call(_st_mod.load_spec, "game_spec.json"))
        assert result["name"] == "My Game"

    def test_missing_file(self):
        result = _call(_st_mod.load_spec, "nonexistent.json")
        assert result.startswith("Error")

    def test_wrong_extension(self, tmp_path):
        (tmp_path / "game.txt").write_text("hello")
        result = _call(_st_mod.load_spec, "game.txt")
        assert result.startswith("Error")


# ---------------------------------------------------------------------------
# save_spec
# ---------------------------------------------------------------------------

class TestSaveSpec:
    def test_save_valid_json(self, tmp_path):
        spec = {"name": "Test", "sprites": []}
        result = _call(_st_mod.save_spec, "test_spec.json", json.dumps(spec))
        assert "Saved" in result
        saved = json.loads((tmp_path / "test_spec.json").read_text())
        assert saved["name"] == "Test"

    def test_auto_adds_json_extension(self, tmp_path):
        _call(_st_mod.save_spec, "myfile", json.dumps({"x": 1}))
        assert (tmp_path / "myfile.json").exists()

    def test_invalid_json_returns_error(self):
        result = _call(_st_mod.save_spec, "bad.json", "not valid json {{")
        assert result.startswith("Error")

    def test_roundtrip(self, tmp_path):
        original = {"name": "Pong", "sprites": [{"name": "Ball"}]}
        _call(_st_mod.save_spec, "pong_spec.json", json.dumps(original))
        loaded = json.loads(_call(_st_mod.load_spec, "pong_spec.json"))
        assert loaded == original


# ---------------------------------------------------------------------------
# inspect_sb3
# ---------------------------------------------------------------------------

class TestInspectSb3:
    def _project(self) -> dict:
        return {
            "targets": [
                {
                    "isStage": True,
                    "name": "Stage",
                    "variables": {
                        "v1": ["Score", 0],
                        "v2": ["Lives", 3],
                    },
                    "costumes": [{"name": "backdrop1", "assetId": "abc", "md5ext": "abc.svg"}],
                    "sounds": [],
                    "blocks": {},
                },
                {
                    "isStage": False,
                    "name": "Ball",
                    "visible": True,
                    "x": 0,
                    "y": 0,
                    "variables": {},
                    "costumes": [{"name": "tennis ball"}],
                    "blocks": {"B1": {}, "B2": {}, "B3": {}},
                },
                {
                    "isStage": False,
                    "name": "Paddle",
                    "visible": True,
                    "x": -200,
                    "y": 0,
                    "variables": {},
                    "costumes": [{"name": "costume1"}],
                    "blocks": {},
                },
            ],
            "extensions": ["pen"],
            "meta": {"semver": "3.0.0", "agent": "scratch-coder/1.0.0"},
        }

    def test_sprite_names(self, tmp_path):
        _make_sb3(tmp_path / "test.sb3", self._project())
        result = json.loads(_call(_st_mod.inspect_sb3, "test.sb3"))
        names = [s["name"] for s in result["sprites"]]
        assert "Ball" in names
        assert "Paddle" in names

    def test_stage_variables(self, tmp_path):
        _make_sb3(tmp_path / "test.sb3", self._project())
        result = json.loads(_call(_st_mod.inspect_sb3, "test.sb3"))
        assert "Score" in result["stage_variables"]
        assert "Lives" in result["stage_variables"]

    def test_block_count(self, tmp_path):
        _make_sb3(tmp_path / "test.sb3", self._project())
        result = json.loads(_call(_st_mod.inspect_sb3, "test.sb3"))
        ball = next(s for s in result["sprites"] if s["name"] == "Ball")
        assert ball["block_count"] == 3

    def test_extensions(self, tmp_path):
        _make_sb3(tmp_path / "test.sb3", self._project())
        result = json.loads(_call(_st_mod.inspect_sb3, "test.sb3"))
        assert "pen" in result["extensions"]

    def test_missing_file(self):
        result = _call(_st_mod.inspect_sb3, "doesnotexist.sb3")
        assert result.startswith("Error")


# ---------------------------------------------------------------------------
# load_sb3_project
# ---------------------------------------------------------------------------

class TestLoadSb3Project:
    def test_loads_project_json(self, tmp_path):
        project = {"targets": [], "extensions": [], "meta": {}}
        _make_sb3(tmp_path / "game.sb3", project)
        result = json.loads(_call(_st_mod.load_sb3_project, "game.sb3"))
        assert "targets" in result

    def test_missing_file_returns_error(self):
        result = _call(_st_mod.load_sb3_project, "missing.sb3")
        assert result.startswith("Error")

    def test_corrupt_zip_returns_error(self, tmp_path):
        (tmp_path / "corrupt.sb3").write_bytes(b"not a zip file at all")
        result = _call(_st_mod.load_sb3_project, "corrupt.sb3")
        assert result.startswith("Error")
