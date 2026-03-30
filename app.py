import base64
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal")

import subprocess
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Scratch Agent",
    page_icon="🐱",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Lazy-import agent so Streamlit doesn't reload it on every rerun
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading Scratch Agent…")
def get_agent():
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal")

    from agno.models.openai import OpenAIChat
    from agno.agent import Agent
    from agno.skills import Skills
    from agno.skills.loaders.local import LocalSkills
    from agno.tools.file import FileTools
    from agno.tools import tool
    from tools.scratch_tools import (
        list_projects,
        load_spec,
        save_spec,
        inspect_sb3,
        load_sb3_project,
    )

    @tool
    def run_bash(command: str) -> str:
        """Run a bash command and return the output."""
        result = subprocess.run(
            command,
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )
        return result.stdout + result.stderr

    return Agent(
        name="Agent Scratch",
        model=OpenAIChat(id="gpt-4o"),
        skills=Skills(loaders=[LocalSkills(str(BASE_DIR / "skills"))]),
        tools=[
            FileTools(base_dir=BASE_DIR, all=True),
            run_bash,
            list_projects,
            load_spec,
            save_spec,
            inspect_sb3,
            load_sb3_project,
        ],
        instructions=[
            "Use the scratch-coder skill when users want to CREATE new Scratch games or animations.",
            "Use the scratch-editor skill when users want to EDIT or MODIFY existing Scratch projects.",
            "To list existing projects use list_projects(). To inspect an .sb3 use inspect_sb3(). To load a spec use load_spec().",
            "After writing the spec JSON file, use run_bash to run: python skills/scratch-coder/scripts/generate_sb3.py output/<name>_spec.json --output output/<name>.sb3",
            "To overwrite an existing .sb3 add --overwrite: python skills/scratch-coder/scripts/generate_sb3.py output/<name>_spec.json --output output/<name>.sb3 --overwrite",
            "Save all output to the 'output/' directory.",
            "NEVER use the 'empty' costume for visible sprites - it is literally invisible! Use 'cat', 'tennis', 'banana', or 'basketball' instead.",
            "Always confirm the .sb3 file was created and tell the user its location.",
        ],
        markdown=True,
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"|"assistant", "content": str}

if "last_output_snapshot" not in st.session_state:
    st.session_state.last_output_snapshot = set()


def get_output_files() -> dict[str, list[Path]]:
    return {
        "sb3": sorted(OUTPUT_DIR.glob("*.sb3")),
        "spec": sorted(OUTPUT_DIR.glob("*_spec.json")),
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🐱 Scratch Agent")
    st.caption("Create and edit Scratch 3.0 projects with AI")

    st.divider()
    st.subheader("📁 Output Files")

    files = get_output_files()

    if files["sb3"]:
        st.markdown("**Compiled projects (.sb3)**")
        for sb3 in files["sb3"]:
            b64 = base64.b64encode(sb3.read_bytes()).decode()
            href = (
                f'<a href="data:application/zip;base64,{b64}" '
                f'download="{sb3.name}" '
                f'style="font-size:0.85rem;text-decoration:none;">'
                f'⬇ {sb3.name}</a>'
            )
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No .sb3 files yet. Ask the agent to create a project!")

    if files["spec"]:
        st.markdown("**Spec files (_spec.json)**")
        for spec in files["spec"]:
            st.markdown(f"`{spec.name}`")

    st.divider()
    st.subheader("💡 Quick Prompts")
    prompts = [
        "Create a Pong game",
        "Make a platformer with 3 levels",
        "Build a catch game",
        "Create a cat dancing animation",
        "Make a quiz with 5 questions",
        "List my existing projects",
    ]
    for p in prompts:
        if st.button(p, use_container_width=True, key=f"prompt_{p}"):
            st.session_state["_quick_prompt"] = p
            st.rerun()

    st.divider()
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

st.header("🐱 Scratch Agent")
st.caption("Ask me to create a new Scratch project or modify an existing one.")

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Inject quick-prompt if clicked from sidebar
user_input: str | None = None
if "_quick_prompt" in st.session_state:
    user_input = st.session_state.pop("_quick_prompt")
else:
    user_input = st.chat_input("What Scratch project would you like to create or edit?")

if user_input:
    # Show and store user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Stream agent response
    agent = get_agent()
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        collected = ""
        try:
            for chunk in agent.run(user_input, stream=True):
                content = getattr(chunk, "content", None)
                if content:
                    collected += content
                    response_placeholder.markdown(collected + "▌")
            response_placeholder.markdown(collected)
        except Exception as e:
            collected = f"⚠️ Error: {e}"
            response_placeholder.markdown(collected)

    st.session_state.messages.append({"role": "assistant", "content": collected})

    # Check for new .sb3 files and show inline download links (data-URI, no rerun)
    new_files = get_output_files()
    current_sb3 = {p.name for p in new_files["sb3"]}
    new_sb3 = current_sb3 - st.session_state.last_output_snapshot
    if new_sb3:
        st.session_state.last_output_snapshot = current_sb3
        for name in sorted(new_sb3):
            path = OUTPUT_DIR / name
            b64 = base64.b64encode(path.read_bytes()).decode()
            href = (
                f'<a href="data:application/zip;base64,{b64}" '
                f'download="{name}" style="text-decoration:none;">'
                f'⬇ Download <strong>{name}</strong></a>'
            )
            st.success(f"✅ New project ready: `{name}`")
            st.markdown(href, unsafe_allow_html=True)
