import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal")

import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path
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
    get_block_help,
    validate_spec_tool,
)

load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()


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


agent = Agent(
    name="Agent Scratch",
    model=OpenAIChat(id="gpt-4o"),
    skills=Skills(loaders=[LocalSkills("skills")]),
    tools=[
        FileTools(base_dir=BASE_DIR, all=True),
        run_bash,
        list_projects,
        load_spec,
        save_spec,
        inspect_sb3,
        load_sb3_project,
        get_block_help,
        validate_spec_tool,
    ],
    instructions=[
        "Use the scratch-coder skill when users want to CREATE new Scratch games or animations.",
        "Use the scratch-editor skill when users want to EDIT or MODIFY existing Scratch projects.",
        "To list existing projects use list_projects(). To inspect an .sb3 use inspect_sb3(). To load a spec use load_spec().",
        "Use get_block_help('motion') or get_block_help('events') when unsure of correct block opcodes.",
        "Use validate_spec_tool() to check specs for errors before generating the .sb3 file.",
        "After writing the spec JSON file, use run_bash to run: python skills/scratch-coder/scripts/generate_sb3.py output/<name>_spec.json --output output/<name>.sb3",
        "To overwrite an existing .sb3 add --overwrite: python skills/scratch-coder/scripts/generate_sb3.py output/<name>_spec.json --output output/<name>.sb3 --overwrite",
        "For validation before generation, use: python skills/scratch-coder/scripts/generate_sb3.py output/<name>_spec.json --validate --output output/<name>.sb3",
        "Save all output to the 'output/' directory.",
        "NEVER use the 'empty' costume for visible sprites - it is literally invisible! Use 'cat', 'tennis', 'banana', or 'basketball' instead.",
        "Always confirm the .sb3 file was created and tell the user its location.",
    ],
    markdown=True,
)


def run_chat_loop() -> None:
    """Run an interactive multi-turn chat session in the terminal."""
    print("Scratch Agent — Interactive Chat")
    print("Type your request. Enter 'exit' or 'quit' to stop.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye!")
            break
        agent.print_response(user_input, stream=True)
        print()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--chat":
        run_chat_loop()
    elif args:
        query = " ".join(args)
        agent.print_response(query, stream=True)
    else:
        run_chat_loop()

