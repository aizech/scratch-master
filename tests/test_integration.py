"""Integration tests for the Scratch Agent.

These tests make real LLM calls and require OPENAI_API_KEY to be set.
They are marked with pytest.mark.integration and skipped automatically
when the API key is not present.
"""

import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "scratch-coder" / "scripts"))

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def require_api_key():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping integration tests")


@pytest.fixture(scope="module")
def scratch_agent(tmp_path_factory):
    """Build an agent that writes to a temp output directory."""
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal")

    import subprocess
    from agno.models.openai import OpenAIChat
    from agno.agent import Agent
    from agno.skills import Skills
    from agno.skills.loaders.local import LocalSkills
    from agno.tools.file import FileTools
    from agno.tools import tool

    base_dir = Path(__file__).parent.parent.resolve()
    output_dir = tmp_path_factory.mktemp("output")

    # Patch scratch_tools to use temp output dir
    import tools.scratch_tools as st_mod
    st_mod._OUTPUT_DIR = output_dir

    from tools.scratch_tools import list_projects, load_spec, save_spec, inspect_sb3, load_sb3_project

    @tool
    def run_bash(command: str) -> str:
        """Run a bash command and return the output."""
        result = subprocess.run(
            command,
            shell=True,
            cwd=base_dir,
            capture_output=True,
            text=True,
        )
        return result.stdout + result.stderr

    agent = Agent(
        name="Agent Scratch",
        model=OpenAIChat(id="gpt-4o"),
        skills=Skills(loaders=[LocalSkills(str(base_dir / "skills"))]),
        tools=[
            FileTools(base_dir=base_dir, all=True),
            run_bash,
            list_projects,
            load_spec,
            save_spec,
            inspect_sb3,
            load_sb3_project,
        ],
        instructions=[
            "Use the scratch-coder skill when users want to CREATE new Scratch games or animations.",
            "After writing the spec JSON file, use run_bash to run: python skills/scratch-coder/scripts/generate_sb3.py output/<name>_spec.json --output output/<name>.sb3",
            "Save all output to the 'output/' directory.",
            "NEVER use the 'empty' costume for visible sprites - it is literally invisible! Use 'cat', 'tennis', 'banana', or 'basketball' instead.",
            "Always confirm the .sb3 file was created and tell the user its location.",
        ],
        markdown=True,
    )
    return agent, output_dir


def test_agent_creates_pong_sb3(scratch_agent):
    """Agent should produce a valid .sb3 file when asked to create a Pong game."""
    agent, output_dir = scratch_agent
    response = agent.run("Create a simple Pong game with a ball and two paddles.")
    content = getattr(response, "content", str(response))

    # Agent should report success
    assert content, "Agent returned empty response"

    # Find any .sb3 file in the base output dir as a fallback
    base_output = Path(__file__).parent.parent / "output"
    candidates = list(output_dir.glob("*.sb3")) + list(base_output.glob("*pong*.sb3"))
    assert candidates, f"No .sb3 file produced. Agent response: {content[:500]}"

    sb3_path = candidates[0]
    assert sb3_path.exists()
    assert sb3_path.stat().st_size > 100

    with zipfile.ZipFile(sb3_path) as zf:
        assert "project.json" in zf.namelist()
        project = json.loads(zf.read("project.json"))

    assert "targets" in project
    assert any(t["isStage"] for t in project["targets"])
    sprites = [t for t in project["targets"] if not t["isStage"]]
    assert len(sprites) >= 2, f"Expected ≥2 sprites, got {len(sprites)}"


def test_agent_lists_projects(scratch_agent):
    """Agent should be able to list projects without error."""
    agent, _ = scratch_agent
    response = agent.run("List all my existing Scratch projects.")
    content = getattr(response, "content", str(response))
    assert content
