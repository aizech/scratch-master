---
name: scratch-coder
description: >
  Create Scratch 3.0 games, animations, and interactive projects. Use this skill
  when users want to make games (platformers, shooters, puzzles), animations,
  drawing programs, quizzes, or any Scratch project. Generates .sb3 files that
  can be opened in the Scratch editor.
compatibility: >
  Works with Scratch 3.0 editor. Output files are .sb3 format, compatible with
  both online and offline Scratch editors.
---

# Scratch Coder

Create Scratch 3.0 projects including games, animations, and interactive programs.

## When to Use This Skill

Use this skill when the user wants to:
- Create a **game** (platformer, shooter, puzzle, arcade, etc.)
- Build an **animation** or story
- Make an **interactive project** (quiz, drawing tool, simulation)
- Design a **creative project** (art, music, interactive art)

### Trigger Examples

- "make a platformer game"
- "create a Pong game"
- "build an animation of a cat dancing"
- "I want a drawing program"
- "make a quiz game with 5 questions"
- "create a simple game where you catch things"

## Workflow (Automated)

When you have file tools available, follow this automated workflow:

### Step 1: Write the JSON Spec File

First, create the project specification JSON file in the `output/` directory:

- Use `save_file` to write the JSON spec to `output/<project_name>_spec.json`
- The JSON format should follow the structure shown in Step 3 below

### Step 2: Generate the .sb3 File

Run the generator script using the Bash tool:

```
python skills/scratch-coder/scripts/generate_sb3.py output/<project_name>_spec.json --output output/<project_name>.sb3
```

Use the Bash tool to execute this command.

### Step 3: Verify and Report

- Verify the .sb3 file was created in the output directory
- Report success to the user with the file location

---

## Workflow (Manual)

### Step 1: Understand the Request

Clarify if needed:
- What type of project? (game, animation, interactive)
- Key features or mechanics
- Number of sprites/characters
- Any specific requirements (scoring, levels, animations)

### Step 2: Design the Project

Plan the structure:
1. **Sprites needed**: Characters, obstacles, UI elements
2. **Variables**: Score, lives, game state
3. **Backdrops**: Stages/scenes
4. **Scripts**: Event handlers, game logic
5. **Extensions**: Pen, music, text-to-speech if needed

### Step 3: Create the Project Specification

Build a JSON specification following the format in `references/example_specs/`:

```json
{
  "name": "Project Name",
  "description": "Brief description",
  "extensions": ["pen"],
  "stage": {
    "variables": {},
    "broadcasts": {},
    "backdrops": []
  },
  "sprites": [
    {
      "name": "SpriteName",
      "costume": "cat",
      "x": 0,
      "y": 0,
      "blocks": {}
    }
  ]
}
```

### Step 4: Generate the .sb3 File

Use the generator script to create the .sb3 file:

```bash
python skills/scratch-coder/scripts/generate_sb3.py <spec.json> --output output/<name>.sb3
```

Or import as a module:

```python
import sys
sys.path.insert(0, "skills/scratch-coder/scripts")
from generate_sb3 import create_project, save_sb3

project = create_project(spec)
save_sb3(project, "output/my_game.sb3")
```

### Step 5: Save and Report

1. Save the .sb3 file to `output/` directory
2. Report what was created
3. Explain how to use the file

## Built-in Resources

### Templates

Located in `references/example_specs/`:
- `platformer.json` - Side-scrolling platformer with jumping
- `pong.json` - Classic paddle game
- `animation.json` - Dancing character animation
- `drawing_tool.json` - Pen-based drawing program

### Built-in Costumes

| Name | Description | Visible? |
|------|-------------|----------|
| `cat` | Scratch Cat (2 costumes for animation) | Yes |
| `empty` | Blank sprite (requires pen drawing to be visible) | No - invisible! |
| `banana` | Banana sprite | Yes |
| `tennis` | Tennis ball | Yes |
| `basketball` | Basketball | Yes |

**IMPORTANT:** The `empty` costume is literally blank/invisible! Use `cat` for sprites or use pen blocks to draw shapes on empty sprites.

### Built-in Sounds

| Name | Description |
|------|-------------|
| `pop` | Pop sound |
| `meow` | Cat meow |
| `boing` | Bounce sound |
| `crash` | Impact sound |

## Block Reference

See `references/block_opcodes.md` for complete list of Scratch 3.0 blocks.

### Common Block Patterns

**Green Flag Start:**
```json
{
  "opcode": "event_whenflagclicked",
  "next": "<next_block_id>",
  "parent": null,
  "inputs": {},
  "fields": {},
  "shadow": false,
  "topLevel": true,
  "x": 0,
  "y": 0
}
```

**Key Press:**
```json
{
  "opcode": "event_whenkeypressed",
  "inputs": {},
  "fields": {"KEY_OPTION": ["space", null]}
}
```

**Forever Loop:**
```json
{
  "opcode": "control_forever",
  "inputs": {"SUBSTACK": [2, "<substack_id>"]}
}
```

**If Then:**
```json
{
  "opcode": "control_if",
  "inputs": {
    "CONDITION": [2, "<condition_id>"],
    "SUBSTACK": [2, "<then_id>"]
  }
}
```

## Block Templates (Recommended)

For complex game mechanics, use the pre-built templates in `scripts/templates.py` instead of hand-crafting block JSON. These provide validated, tested patterns.

### Available Templates

| Template | Purpose | Key Parameters |
|----------|---------|----------------|
| `PlatformerMovement` | Arrow key movement + jumping | `left_key`, `right_key`, `jump_key`, `move_speed` |
| `PongPaddle` | Paddle controlled by keys or mouse | `up_key`, `down_key`, `use_mouse` |
| `BouncingBall` | Ball that moves and bounces off edges | `speed` |
| `ScoreCounter` | Stage script that responds to score broadcasts | `variable_name`, `increment` |
| `CatchGameItem` | Falling item that resets when caught | `fall_speed` |
| `CostumeAnimation` | Next costume with wait loop | `wait_seconds` |

### Template Usage Example

```python
# In your spec generation, use templates for common patterns:
from templates import PlatformerMovement, BouncingBall, ScoreCounter

player_sprite = {
    "name": "Player",
    "costume": "cat",
    "x": 0, "y": -100,
    "blocks": PlatformerMovement(
        left_key="left arrow",
        right_key="right arrow",
        jump_key="space",
        move_speed=5,
        jump_height=10
    ).build()
}

ball_sprite = {
    "name": "Ball",
    "costume": "tennis",
    "blocks": BouncingBall(speed=6).build()
}

stage = {
    "variables": {"Score": ["Score", 0]},
    "blocks": ScoreCounter(variable_name="Score", increment=1).build()
}
```

### Input Builder

Use `InputBuilder` for canonical Scratch input formats:

```python
from templates import InputBuilder

# Number literal: [1, [4, "10"]]
InputBuilder.number(10)

# String literal: [1, [10, "hello"]]
InputBuilder.string("hello")

# Block reference: [2, block_id]
InputBuilder.block_ref(some_block_id)

# Obscured shadow: [3, block_id, [4, "0"]]
InputBuilder.obscured_shadow(reporter_id, 0)
```

## Spec Validation

Before generating, validate your spec to catch errors early:

```bash
python skills/scratch-coder/scripts/generate_sb3.py my_spec.json --validate
```

Or use the strict mode to fail on errors:

```bash
python skills/scratch-coder/scripts/generate_sb3.py my_spec.json --validate --strict
```

Common issues caught:
- Unknown opcodes
- Invalid input formats (e.g., `[4, 10]` instead of `[1,[4,"10"]]`)
- Missing hat blocks (scripts that won't run)
- Duplicate sprite names
- Unknown costume names
- Malformed variables

## Output Format

Always save output files to the `output/` directory with `.sb3` extension.

**File location:** `output/<project-name>.sb3`

**Instructions for user:**
1. Download the .sb3 file
2. Go to scratch.mit.edu or open Scratch desktop
3. Click "File" > "Load from your computer"
4. Select the .sb3 file

## Tips for Good Scratch Projects

1. **Start simple**: Get basic mechanics working first
2. **Use broadcasts**: Communicate between sprites for coordinated behavior
3. **Test early**: Build a minimal version, test, then add features
4. **User feedback**: Show score, lives, and game state clearly
5. **Win/lose conditions**: Define clear goals and endings
6. **Polish**: Add sounds, animations, and visual effects

## Common Project Types

### Game Mechanics

- **Movement**: Arrow keys, WASD, or mouse
- **Jumping**: Gravity simulation with ground detection
- **Collision**: Touching sprites or colors
- **Scoring**: Points for collecting, avoiding, or completing
- **Lives**: Health system with game over

### Animation Patterns

- **Costume switching**: For character animation
- **Movement**: Gliding, rotating, bouncing
- **Scene changes**: Backdrop switching
- **Timing**: Wait blocks for pacing

### Interactive Projects

- **User input**: Ask/answer blocks, key/mouse detection
- **State management**: Variables track progress
- **Branching**: If blocks for choices
- **Lists**: Store quiz questions, high scores
