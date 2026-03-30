# Scratch Agent

An AI-powered agent for creating and editing [Scratch 3.0](https://scratch.mit.edu) projects (`.sb3` files) using the [Agno](https://github.com/agno-agi/agno) framework.

Chat with the agent in your terminal or via a Streamlit web UI — describe the game or animation you want, and the agent generates a ready-to-open `.sb3` file.

---

## Features

- **Create** new Scratch projects from a plain-language description
- **Edit** existing `.sb3` projects — add sprites, modify blocks, change variables
- **CLI chat loop** — interactive multi-turn terminal session
- **Streamlit UI** — browser-based chat with sidebar file browser and download buttons
- **Offline asset bundling** — SVG costumes embedded directly in the zip; no Scratch CDN dependency
- **72 unit tests** covering the block builder, project generator, and file tools

---

## Project Structure

```
scratch/
├── agent_scratch.py              # Agent definition + CLI entry point
├── app.py                        # Streamlit web UI
├── requirements.txt
├── pytest.ini
│
├── tools/
│   └── scratch_tools.py          # Agno @tool functions (list/load/save/inspect)
│
├── skills/
│   ├── scratch-coder/            # Skill: create new Scratch projects
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── generate_sb3.py   # Spec → .sb3 compiler
│   │   │   ├── block_builder.py  # Scratch block construction helpers
│   │   │   └── assets/           # Bundled SVG costume files
│   │   ├── references/           # Block opcode reference, example specs
│   │   └── evals/                # Evaluation prompts and criteria
│   └── scratch-editor/           # Skill: edit existing projects
│       └── SKILL.md
│
├── output/                       # Generated .sb3 and _spec.json files
└── tests/                        # Unit + integration tests
```

---

## Quickstart

### 1. Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/account/api-keys)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
```

### 4. Run

**Interactive terminal chat (default):**

```bash
python agent_scratch.py
```

**Single-shot query:**

```bash
python agent_scratch.py "Create a Pong game with a ball and two paddles"
```

**Streamlit web UI:**

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage Examples

```
You: Create a simple Pong game with a ball and two paddles
You: Make a cat animation where the cat walks across the screen
You: Build a quiz game with 5 questions and a score counter
You: List my existing projects
You: Edit pong_game.sb3 — add a score variable that increases when the ball hits a paddle
```

Generated `.sb3` files are saved to `output/` and can be opened directly in:
- [Scratch online editor](https://scratch.mit.edu) — File → Load from your computer
- [Scratch Desktop](https://scratch.mit.edu/download)

---

## Available Tools

| Tool | Description |
|---|---|
| `list_projects()` | List all `.sb3` and spec files in `output/` |
| `load_spec(filename)` | Load a `_spec.json` project specification |
| `save_spec(filename, json)` | Save a project specification to `output/` |
| `inspect_sb3(filename)` | Summarise sprites, variables, block counts in an `.sb3` |
| `load_sb3_project(filename)` | Load raw `project.json` from an `.sb3` for editing |

---

## Running Tests

```bash
# Unit tests only (no API key required)
pytest tests/ -v -m "not integration"

# All tests including integration (requires OPENAI_API_KEY)
pytest tests/ -v
```

---

## How It Works

1. **You describe** what you want in plain language.
2. The agent selects the **`scratch-coder`** skill (new project) or **`scratch-editor`** skill (existing project).
3. It writes a **JSON spec file** describing the stage, sprites, costumes, and block scripts.
4. It runs `generate_sb3.py` to compile the spec into a valid **`.sb3` zip file** with all costume SVGs bundled.
5. The `.sb3` is saved to `output/` — ready to open in Scratch.

### Spec format (excerpt)

```json
{
  "name": "Pong",
  "stage": { "variables": { "v1": ["Score", 0] } },
  "sprites": [
    {
      "name": "Ball",
      "costume": "tennis",
      "x": 0, "y": 0,
      "blocks": {
        "start": [
          { "opcode": "event_whenflagclicked" },
          { "opcode": "control_forever", "inputs": {
            "SUBSTACK": [2, "move"]
          }},
          { "opcode": "motion_movesteps", "inputs": { "STEPS": [4, 5] } }
        ]
      }
    }
  ]
}
```

---

## Available Costumes

| Key | Description |
|---|---|
| `cat` | Scratch cat (2 walk frames) |
| `tennis` | Tennis ball |
| `banana` | Banana |
| `basketball` | Basketball |
| `empty` | Invisible (blank 2×2 SVG — for non-visible sprites only) |

---

## License

MIT
