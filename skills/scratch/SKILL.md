---
name: scratch
description: "Create, modify, and analyze Scratch 3.0 projects (.sb3 files) using ScratchGen. Write Python code that compiles to valid Scratch projects with proper sprites, variables, sounds, and monitors."
license: Proprietary
---

# Scratch Skill

Create and modify Scratch 3.0 projects using Python and ScratchGen.

## Dependencies

```bash
pip install "ScratchGen~=1.1"
```

> Tested with ScratchGen **1.1.1**. Use `~=1.1` to allow patch updates while locking to the 1.1.x API.

## Quick Start

```python
from ScratchGen import *

project = Project()
sprite = project.createSprite('Cat')

sprite.createScript(
    WhenFlagClicked(),
    Say('Hello!')
)

project.save('hello.sb3')
```

## Scratch Direction Reference

Scratch uses a **compass-style** direction system — **not** the math convention:

| Direction | Meaning | `sin(d)` → x | `cos(d)` → y |
|-----------|---------|--------------|---------------|
| `0°`      | UP      | 0            | +1            |
| `90°`     | RIGHT   | +1           | 0             |
| `180°`    | DOWN    | 0            | -1            |
| `-90°` / `270°` | LEFT | -1      | 0             |
| `45°`     | upper-right | +0.71  | +0.71         |
| `135°`    | lower-right | +0.71  | -0.71         |
| `225°`    | lower-left  | -0.71  | -0.71         |
| `315°`    | upper-left  | -0.71  | +0.71         |

For Pong deflections:
- **Deflect RIGHT** (toward computer): `PickRandom(60, 120)` — mostly rightward
- **Deflect LEFT** (toward player): `PickRandom(240, 300)` — mostly leftward
- **Serve RIGHT**: `PickRandom(30, 60)` — right + upward diagonal
- **Serve LEFT**: `PickRandom(210, 240)` — left + downward diagonal

---

## Common Pitfalls

### Sprites are hidden by default
ScratchGen creates sprites in a hidden state. Call `Show()` in `WhenFlagClicked()` for any sprite that should start visible:

```python
sprite.createScript(
    WhenFlagClicked(),
    Show(),          # Required — sprites are hidden by default
    GoToPosition(0, 0),
)
```

Sprites that should start hidden (enemies, pop-ups, overlays) should omit `Show()` and call it only when triggered.

### Color effects on unstyled sprites
Default ScratchGen sprites have no image file — they render as plain white rectangles. `SetGraphicEffect(COLOR, 100)` shifts the hue so far that the sprite appears invisible against a white stage background. Keep color effect values in the **−30 to 30** range for a visible tint, or add a custom costume first:

```python
sprite.addCostume('paddle.png')         # Recommended: use a real image
SetGraphicEffect(COLOR, 25)             # Visible tint
# AVOID on unstyled sprites:
SetGraphicEffect(COLOR, 100)            # Appears invisible on white background
```

### Sounds require embedded files
`Play('name')` only works if the sound was embedded first. ScratchGen's `addSound()` requires a real file path. For programmatically-generated or embedded sounds, inject them directly into the `.sb3` after `project.save()` using the `wave` module:

```python
import hashlib, io, math, struct, wave, zipfile, json

def _wav(freq, duration, sample_rate=44100):
    n = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{n}h', *[
            int(32767 * math.sin(2 * math.pi * freq * k / sample_rate))
            for k in range(n)
        ]))
    return buf.getvalue()

# After project.save():
hit_wav = _wav(440, 0.08)          # 440 Hz beep
hit_id  = hashlib.md5(hit_wav).hexdigest()

with zipfile.ZipFile('game.sb3', 'r') as zf:
    proj = json.loads(zf.read('project.json'))
    assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

ball_target = next(t for t in proj['targets'] if t['name'] == 'Ball')
ball_target['sounds'] = [{
    'assetId': hit_id, 'name': 'hit', 'dataFormat': 'wav',
    'format': '', 'rate': 44100, 'sampleCount': int(44100 * 0.08),
    'md5ext': f'{hit_id}.wav'
}]
with zipfile.ZipFile('game.sb3', 'w') as zf:
    zf.writestr('project.json', json.dumps(proj))
    for f, data in assets.items(): zf.writestr(f, data)
    zf.writestr(f'{hit_id}.wav', hit_wav)

# Then in the ball script:
Play('hit')                        # Name must match sounds[].name
```

### Broadcasts have null IDs — use `ChangeVariable` for global scoring
`Broadcast()` / `WhenBroadcastReceived()` generate blocks with `null` broadcast IDs in ScratchGen. TurboWarp matches broadcast receivers by ID, **not** by name, so `WhenBroadcastReceived` **never fires**.

For scoring or any cross-sprite state update that involves a global (stage) variable, use `ChangeVariable` directly from the sprite that detects the event:

```python
# BROKEN — WhenBroadcastReceived never fires (null broadcast ID)
ball.createScript(
    ...
    Broadcast('player_scored')          # ID is null; receiver silently ignored
)
stage.createScript(
    WhenBroadcastReceived('player_scored'),
    ChangeVariable(score, 1)            # This block never runs
)

# CORRECT — change the stage variable directly from the ball sprite
ball.createScript(
    ...
    ChangeVariable(score, 1)            # Global variables are accessible from any sprite
)
```

### Sprites have no default costume — they are invisible
ScratchGen generates sprites with **zero costumes**. A sprite with no costume is completely invisible on the stage even when `Show()` is called. You must embed costume images manually after saving:

```python
import hashlib, io, json, zipfile
from PIL import Image, ImageDraw

def add_costumes(output_path, costumes):
    """Inject costume PNGs into a saved .sb3 file.

    Args:
        output_path: Path to the .sb3 file (already saved).
        costumes: Dict of {sprite_name: (costume_name, png_bytes)}.

    Example:
        def green_rect(w=20, h=120):
            img = Image.new('RGBA', (w, h), (0, 190, 0, 255))
            buf = io.BytesIO(); img.save(buf, 'PNG'); return buf.getvalue()

        add_costumes('game.sb3', {'Paddle': ('paddle', green_rect())})
    """
    with zipfile.ZipFile(output_path, 'r') as zf:
        proj = json.loads(zf.read('project.json'))
        assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

    new_assets = {}
    for target in proj['targets']:
        name = target.get('name', '')
        if name not in costumes:
            continue
        costume_name, data = costumes[name]
        asset_id = hashlib.md5(data).hexdigest()
        filename = f'{asset_id}.png'
        new_assets[filename] = data
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        target['costumes'] = [{
            'assetId': asset_id, 'name': costume_name,
            'bitmapResolution': 1, 'md5ext': filename, 'dataFormat': 'png',
            'rotationCenterX': w // 2, 'rotationCenterY': h // 2,
        }]
        target['currentCostume'] = 0

    with zipfile.ZipFile(output_path, 'w') as zf:
        zf.writestr('project.json', json.dumps(proj))
        for f, data in {**assets, **new_assets}.items():
            zf.writestr(f, data)
```

> **Save pipeline order:** `project.save()` → `add_costumes()` → `add_monitors()`

### Monitor positions are overridden by TurboWarp at runtime — use sprite HUD instead
`ShowVariable(var)` creates a variable monitor at runtime. Even if you inject a `monitors` array into `project.json` with explicit `x/y` positions, TurboWarp's runtime `ShowVariable()` call **resets every monitor's position back to `(5, 5)`**. When two variables both call `ShowVariable()`, both monitors stack at `(5, 5)` and only the top one is visible.

**Do not rely on `add_monitors()` for positioning.** Instead, use dedicated HUD sprites with `Say(Join('Label: ', var))` in a `Forever` loop. Sprites position reliably using Scratch stage coordinates:

```python
# Two score sprites in the top corners of the stage
score_left  = project.createSprite('ScoreLeft',  x=-170, y=130)
score_right = project.createSprite('ScoreRight', x=170,  y=130)

score_left.createScript(
    WhenFlagClicked(),
    Show(),
    GoToPosition(-170, 130),
    SetSize(5),                           # nearly invisible sprite body
    Forever(
        Say(Join('Player: ', player_score)),  # pass variable object directly
        Wait(0.1)
    )
)
# Repeat for score_right / computer_score
```

Add a tiny RGBA costume for each HUD sprite via `add_costumes()` so TurboWarp renders the speech bubble:
```python
def _dot_png(size=4):
    img = Image.new('RGBA', (size, size), (255, 255, 255, 80))
    buf = io.BytesIO(); img.save(buf, 'PNG'); return buf.getvalue()

costume_data = {
    ...
    'ScoreLeft':  ('dot', _dot_png()),
    'ScoreRight': ('dot', _dot_png()),
}
```

### `GetAttribute` requires the ScratchGen constant, not a string
`GetAttribute(attribute, sprite)` passes `attribute` verbatim to the `sensing_of` block's `PROPERTY` field. TurboWarp only recognises the **lowercase display name** (e.g. `'y position'`). Passing the uppercase string `'Y_POSITION'` is silently ignored — the block always returns `0`.

Always use the **imported constant** (no quotes):

```python
from ScratchGen import *          # exports Y_POSITION = 'y position', X_POSITION = 'x position', etc.

# BROKEN — string stored verbatim; TurboWarp returns 0
GetAttribute('Y_POSITION', ball)

# CORRECT — constant resolves to 'y position' at block-generation time
GetAttribute(Y_POSITION, ball)
GetAttribute(X_POSITION, ball)
GetAttribute(DIRECTION, ball)
```

### Variable objects are valid reporters — no `Variable()` wrapper needed
ScratchGen does **not** have a `Variable()` block. Variable objects created by `createVariable()` can be passed directly anywhere a reporter is accepted (`Join`, `Say`, `Add`, `If`, etc.):

```python
player_score = stage.createVariable('Player', 0)

# CORRECT — variable object used directly as a reporter
Say(Join('Score: ', player_score))
If(GreaterThan(player_score, 10), ...)

# WRONG — Variable() does not exist in ScratchGen
Say(Join('Score: ', Variable(player_score)))   # NameError
```

### `Stop(ALL)` clears speech bubbles before TurboWarp renders
`Stop(ALL)` halts execution before TurboWarp draws the current frame. A `Say()` called immediately before `Stop(ALL)` appears to show nothing — the bubble is set but never painted on screen.

**Pattern: `game_over` state variable + dedicated message sprite**

Use a dedicated sprite whose `Forever` loop stays alive, reacts to a `game_over` variable, and calls `Say()` each iteration:

```python
game_over = stage.createVariable('game_over', 0)  # 0=playing 1=lost 2=win
msg       = project.createSprite('GameMsg', x=0, y=0)

# In ball/player script — trigger end-game state:
If(LessThan(lives, 1),
    SetVariable(game_over, 1),
    Stop(THIS_SCRIPT)          # stops THIS script only; GameMsg keeps running
)
If(GreaterThan(score, MAX_SCORE),
    SetVariable(game_over, 2),
    Stop(THIS_SCRIPT)
)

# GameMsg script — independent, reacts to game_over:
msg.createScript(
    WhenFlagClicked(),
    Show(), GoToPosition(0, 0), SetSize(5),
    Forever(
        If(Equals(game_over, 1), Say('Game Over!')),
        If(Equals(game_over, 2), Say('You Win! :)')),
        If(Equals(game_over, 0), Say('')),    # clear on restart
        Wait(0.1)
    )
)

# Stage reset — clear game_over so message disappears:
stage.createScript(
    WhenFlagClicked(),
    SetVariable(game_over, 0),
    ...
)
```

Add a tiny dot costume for `GameMsg` via `add_costumes()` so TurboWarp renders its speech bubble.

### Scratch stage fence clamps sprites at y = ±180
`ChangeY()` and `GoToPosition()` are fenced by the Scratch VM to the stage boundary (y ∈ [−180, 180]). A sprite can never actually reach y = −185 or lower. A fall-detection check like `LessThan(YPosition(), -185)` **never fires** — the ball sits at y = −180, slides along the bottom edge, and the condition stays false forever.

Keep fall/ceiling detection thresholds at least **5 px inside** the stage bounds:

```python
# BROKEN — -185 is below the fence; sprite slides along the bottom forever
If(LessThan(YPosition(), -185), ChangeVariable(lives, -1))

# CORRECT — -172 is above the clamp (-180) and well below the paddle at -150
If(LessThan(YPosition(), -172), ChangeVariable(lives, -1))
```

---

## Project Structure

```python
project = Project()
stage = project.stage

# Stage coordinate bounds: x: -240 to 240, y: -180 to 180
# Sprites default to HIDDEN — call Show() in WhenFlagClicked() to make visible
# rotation_style: "all around"|ALL_AROUND  "left-right"|LEFT_RIGHT  "don't rotate"|DONT_ROTATE
# createSprite defaults: x=0, y=0, size=100, direction=90, rotation_style="all around"
sprite = project.createSprite('Name', x=0, y=0, size=100, direction=90, rotation_style="all around")

# Global variables/lists (on Stage)
global_var = stage.createVariable('score', 0)
global_list = stage.createList('items')

# Sprite variables/lists (local)
local_var = sprite.createVariable('speed', 5)

# Assets
sprite.addCostume('path/to/costume.png')
sprite.addSound('path/to/sound.wav')
stage.addBackdrop('path/to/backdrop.png')
```

## Scripts

Scripts are sequences of blocks passed to `createScript()`:

```python
sprite.createScript(
    WhenFlagClicked(),
    GoToPosition(0, 0),
    Forever(
        MoveSteps(10),
        BounceOffEdge()
    )
)
```

Multiple scripts per sprite:

```python
sprite.createScript(
    WhenFlagClicked(),
    Say('Started!')
)

sprite.createScript(
    WhenKeyPressed('space'),
    Jump()
)

sprite.createScript(
    WhenBroadcastReceived('message'),
    Say('Got it!')
)
```

## Event Blocks

| ScratchGen Block | Scratch Block |
|-----------------|---------------|
| `WhenFlagClicked()` | When green flag clicked |
| `WhenKeyPressed('space')` | When space key pressed |
| `WhenKeyPressed('up')` | When up arrow pressed |
| `WhenThisSpriteClicked()` | When this sprite clicked |
| `WhenBackdropSwitchesTo('backdrop1')` | When backdrop switches to |
| `WhenBroadcastReceived('msg')` | When I receive msg |
| `WhenStartAsClone()` | When I start as a clone |

## Key Blocks Reference

### Motion

```python
MoveSteps(10)
TurnRight(15)
TurnLeft(15)
GoToPosition(x, y)
GoTo(RANDOM) / GoTo(MOUSE) / GoTo(sprite)
GlideToPosition(seconds, x, y)
PointInDirection(90)
PointTowards(MOUSE) / PointTowards(sprite)
ChangeX(10) / SetX(0)
ChangeY(10) / SetY(0)
BounceOffEdge()
SetRotationStyle(LEFT_RIGHT) / SetRotationStyle(DONT_ROTATE) / SetRotationStyle(ALL_AROUND)
# Reporters
XPosition() / YPosition() / Direction()
```

### Looks

```python
Say('Hello!') / SayForSeconds('Hi!', 2)
Think('Hmm...') / ThinkForSeconds('...', 2)
Show() / Hide()
SwitchCostume(costume) / NextCostume()
SwitchBackdrop(backdrop) / NextBackdrop()
ChangeSize(10) / SetSize(100)
ChangeGraphicEffect(COLOR, 25) / SetGraphicEffect(GHOST, 50)
ClearGraphicEffects()
SetLayer(FRONT) / SetLayer(BACK)
ChangeLayer(FORWARD, 1) / ChangeLayer(BACKWARD, 1)
# Reporters
Size() / Costume(NUMBER) / Costume(NAME) / Backdrop(NUMBER) / Backdrop(NAME)
```

### Sound

```python
Play('Meow') / PlayUntilDone('Pop')
StopSounds()
ChangeVolume(-10) / SetVolume(100)
ChangeSoundEffect(PITCH, 10) / SetSoundEffect(PAN, 50)
ClearSoundEffects()
# Reporter
Volume()
```

### Control

```python
Wait(1)
Repeat(10, MoveSteps(10))
Forever(MoveSteps(1), Wait(0.1))
If(condition, MoveSteps(10))
If(condition, MoveSteps(10)).Else(MoveSteps(-10))
# Multiple actions (variadic — all args after condition run in sequence):
If(condition,
    MoveSteps(10),
    TurnRight(15),
    Say('Hit!')
)
If(condition,
    SetY(0),
    PointInDirection(90)
).Else(
    Say('Miss!'),
    Stop(THIS_SCRIPT)
)
WaitUntil(condition)
RepeatUntil(condition, MoveSteps(1))
Stop(ALL) / Stop(OTHER_SCRIPTS) / Stop(THIS_SCRIPT)
CreateCloneOf(MYSELF) / CreateCloneOf(sprite)
DeleteThisClone()
```

### Sensing

```python
TouchingObject(MOUSE) / TouchingObject(EDGE) / TouchingObject(sprite)
TouchingColor('#FF0000')
ColorTouchingColor('#FF0000', '#00FF00')
DistanceTo(MOUSE) / DistanceTo(sprite)
AskAndWait("What's your name?") / Answer()
KeyPressed('space') / KeyPressed('w') / KeyPressed('up')
MouseDown() / MouseX() / MouseY()
Timer() / ResetTimer()
GetAttribute(X_POSITION, sprite) / GetAttribute(Y_POSITION, sprite)   # constants, NOT strings
GetAttribute(VOLUME, sprite)
GetAttribute(BACKDROP_NUMBER, stage)
Current(YEAR) / Current(MONTH) / Current(DAY_OF_WEEK) / Current(HOUR) / Current(MINUTE) / Current(SECOND)
DaysSince2000()
Loudness() / Loud()
Username()
SetDragMode(DRAGGABLE) / SetDragMode(NOT_DRAGGABLE)
```

### Operators

```python
# Arithmetic
Add(a, b) / Subtract(a, b) / Multiply(a, b) / Divide(a, b)
PickRandom(1, 10) / Round(value) / Modulo(a, b)

# Comparison
LessThan(a, b) / GreaterThan(a, b) / Equals(a, b)

# Boolean
And(a, b) / Or(a, b) / Not(condition)

# String
Join('Hello', 'World')
LetterOf(1, 'Hello')
LengthOf('Hello')
Contains('Hello', 'ell')

# Math
Operation(ABSOLUTE, -5) / Operation(FLOOR, 3.7) / Operation(CEILING, 3.2)
Operation(SQUARE_ROOT, 16) / Operation(SINE, 45) / Operation(COSINE, 45)
Operation(TANGENT, 45) / Operation(ARCSINE, 0.5) / Operation(ARCCOSINE, 0.5)
Operation(ARCTANGENT, 1) / Operation(NATURAL_LOGARITHM, 2.718)
Operation(LOGARITHM, 100) / Operation(E_TO_THE, 2) / Operation(TEN_TO_THE, 2)
```

### Variables

```python
# Create (on stage or sprite)
var = stage.createVariable('score', 0)
var = sprite.createVariable('speed', 5)

# Blocks
SetVariable(var, 10)
ChangeVariable(var, 1)
ShowVariable(var)
HideVariable(var)
```

### Lists

```python
# Create
lst = stage.createList('items')
lst = sprite.createList('my_list')

# Blocks
AddToList('apple', lst)
DeleteOfList(1, lst)
ClearList(lst)
InsertIntoList('banana', 1, lst)
ReplaceInList(1, lst, 'cherry')
# Reporters
ItemOfList(1, lst) / ListIndexOf('apple', lst) / ListLength(lst) / ListContains(lst, 'apple')
# Show/Hide
ShowList(lst) / HideList(lst)
```

### Broadcasts

```python
Broadcast('message')
BroadcastAndWait('message')

# Handler
sprite.createScript(
    WhenBroadcastReceived('message'),
    Say('Got it!')
)
```

### Custom Blocks

```python
prototype = sprite.createCustomBlock('move %s steps in direction %s')
steps, direction = prototype.getParameters()

move_in_direction = prototype.setScript(
    PointInDirection(direction),
    MoveSteps(steps)
)

# Use it
sprite.createScript(
    WhenFlagClicked(),
    move_in_direction(50, 90)
)
```

## Monitors (Variable Display)

`ShowVariable(var)` in a `WhenFlagClicked()` stage script is **required** for TurboWarp to display the correct variable name label. Use `add_monitors()` after `project.save()` to control the monitor **position**:

```python
import json, zipfile

def add_monitors(output_path, positions=None):
    """Add variable monitor overlays to a saved .sb3 file.

    Args:
        output_path: Path to the .sb3 file (already saved).
        positions: Optional dict of {variable_name: (x, y)}.
                   If omitted, monitors auto-stack vertically at x=10.

    Note: Only stage (global) variables get monitors.
          Sprite-local variables are skipped.
    """
    with zipfile.ZipFile(output_path, 'r') as zf:
        proj = json.loads(zf.read('project.json'))
        assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

    monitors = []
    i = 0
    for t in proj['targets']:
        if not t.get('isStage'):
            continue                        # Skip sprite-local variables
        for vid, vdata in t.get('variables', {}).items():
            name = vdata[0]
            if positions and name in positions:
                x, y = positions[name]
            else:
                x, y = 10, 10 + i * 35     # Auto-stack vertically
            monitors.append({
                "id": vid,
                "mode": "default",
                "opcode": "data_showvariable",
                "params": {"VARIABLE": name},  # Must be string name, NOT array
                "spriteName": None,             # null = global (stage) variable
                "value": str(vdata[1]),         # Current value as string
                "width": 0,                     # 0 = auto-size
                "height": 0,
                "x": x, "y": y,
                "visible": True,
                "sliderMin": 0,
                "sliderMax": 100,
                "isDiscrete": True
            })
            i += 1

    proj['monitors'] = monitors

    with zipfile.ZipFile(output_path, 'w') as zf:
        zf.writestr('project.json', json.dumps(proj))
        for f, data in assets.items():
            zf.writestr(f, data)
```

**Usage:**
```python
project.save('game.sb3')

# Auto-stacked at left edge:
add_monitors('game.sb3')

# Explicit positions per variable:
add_monitors('game.sb3', positions={
    'Player Score': (10, 10),
    'AI Score':     (360, 10),
})
```

## Examples

- `examples/pong.py` — Player vs AI Pong (paddles, ball physics, sprite HUD scores, sounds)
- `examples/breakout.py` — Breakout clone (dx/dy axis-aligned physics, 24-brick grid, 3 lives, win/lose messages)

> **Physics tip — tunneling:** Keep `MoveSteps(N)` ≤ half the target sprite's pixel width. If `N` is too large, the ball skips over a paddle in one frame without triggering `TouchingObject()`. At `MoveSteps(5)` with a 20 × 60 px paddle the risk is borderline; slow the ball or widen paddles if tunneling occurs.

> **Physics tip — dx/dy variables:** For axis-aligned games (Breakout, Pong variants), storing direction as `dx`/`dy` stage variables (+1/−1) and moving with `ChangeX(Multiply(dx, speed))` is cleaner than `PointInDirection` + `MoveSteps`. Each sprite can independently flip `dy` via `SetVariable(dy, Multiply(dy, -1))`, and direction checks like `LessThan(dy, 0)` (moving down) are trivial.

## Testing

```bash
# Verify the file is valid
python -c "import zipfile; z = zipfile.ZipFile('project.sb3'); print(z.namelist())"

# Open in Turbowarp
# https://turbowarp.org/editor?tool=file
```

## See Also

- [block-reference.md](block-reference.md) - Complete block reference
- [browser-automation.md](browser-automation.md) - Browser testing guide
