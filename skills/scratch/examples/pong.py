#!/usr/bin/env python3
"""Pong game - complete working example using ScratchGen."""

from ScratchGen import *
import hashlib
import io
import json
import zipfile

from PIL import Image, ImageDraw


def add_costumes(output_path):
    """Inject sprite costume images into a saved .sb3 file.

    ScratchGen generates sprites with no costume by default — sprites are
    invisible without one. Call after project.save() and before add_monitors().

    Costumes:
        Player / AI : green rectangle (20 x 120 px)
        Ball        : pink circle    (30 x 30 px)
    """
    def _paddle_png(width=20, height=120):
        img = Image.new('RGBA', (width, height), (0, 190, 0, 255))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    def _ball_png(size=30):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size - 1, size - 1], fill=(255, 105, 180, 255))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    def _dot_png(size=4):
        img = Image.new('RGBA', (size, size), (255, 255, 255, 80))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    costume_data = {
        'Player':      ('paddle', _paddle_png()),
        'AI':          ('paddle', _paddle_png()),
        'Ball':        ('ball',   _ball_png()),
        'ScoreLeft':   ('dot',    _dot_png()),
        'ScoreRight':  ('dot',    _dot_png()),
    }

    with zipfile.ZipFile(output_path, 'r') as zf:
        proj = json.loads(zf.read('project.json'))
        assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

    new_assets = {}
    for target in proj['targets']:
        sprite_name = target.get('name', '')
        if sprite_name not in costume_data:
            continue
        costume_name, data = costume_data[sprite_name]
        asset_id = hashlib.md5(data).hexdigest()
        filename = f'{asset_id}.png'
        new_assets[filename] = data
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        target['costumes'] = [{
            'assetId': asset_id,
            'name': costume_name,
            'bitmapResolution': 1,
            'md5ext': filename,
            'dataFormat': 'png',
            'rotationCenterX': w // 2,
            'rotationCenterY': h // 2,
        }]
        target['currentCostume'] = 0

    with zipfile.ZipFile(output_path, 'w') as zf:
        zf.writestr('project.json', json.dumps(proj))
        for f, data in {**assets, **new_assets}.items():
            zf.writestr(f, data)


def add_monitors(output_path, positions=None):
    """Add variable monitor overlays to a saved .sb3 file.

    WARNING: TurboWarp's ShowVariable() runtime call overrides all injected
    x/y positions back to (5, 5). With multiple monitors they stack invisibly.
    Prefer the sprite Say(Join()) HUD pattern for reliable positioned display.
    This function is retained for single-variable or non-TurboWarp use cases.

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


def create_pong():
    """Create a complete Pong game."""
    project = Project()

    # Create sprites
    player = project.createSprite('Player', x=-180, y=0, rotation_style="don't rotate")
    ball = project.createSprite('Ball', x=0, y=0)
    ai = project.createSprite('AI', x=180, y=0, rotation_style="don't rotate")

    # Global score variables on Stage
    stage = project.stage
    player_score = stage.createVariable('Player Score', 0)
    ai_score = stage.createVariable('AI Score', 0)

    # Stage: reset scores on green flag.
    # Score display is handled by ScoreLeft / ScoreRight sprite HUD using Say() —
    # ShowVariable() stacks all monitors at (5,5) in TurboWarp, hiding one behind the other.
    # NOTE: Broadcasts have null IDs in ScratchGen — WhenBroadcastReceived never fires.
    # Score updates use ChangeVariable directly from the ball sprite instead.
    stage.createScript(
        WhenFlagClicked(),
        SetVariable(player_score, 0),
        SetVariable(ai_score, 0)
    )

    # Player: W/S key controls
    # Sprites are hidden by default — Show() is required
    player.createScript(
        WhenFlagClicked(),
        Show(),
        Forever(
            If(KeyPressed('w'),
                ChangeY(15)
            ),
            If(KeyPressed('s'),
                ChangeY(-15)
            ),
            If(GreaterThan(YPosition(), 150),
                SetY(150)
            ),
            If(LessThan(YPosition(), -150),
                SetY(-150)
            ),
            Wait(0.02)
        )
    )

    # Ball: movement, collision, scoring
    # Scratch directions: 0=UP, 90=RIGHT, 180=DOWN, 270(-90)=LEFT
    # Physics tip: keep MoveSteps <= half the paddle width to avoid tunneling.
    ball.createScript(
        WhenFlagClicked(),
        Show(),
        SetRotationStyle(DONT_ROTATE),
        GoToPosition(0, 0),
        PointInDirection(PickRandom(30, 60)),  # Start going right + upward diagonal
        Forever(
            MoveSteps(5),
            BounceOffEdge(),
            # Ball went past Player paddle — Player missed
            If(LessThan(XPosition(), -220),
                GoToPosition(0, 0),
                PointInDirection(PickRandom(210, 240)),
                ChangeVariable(player_score, 1)  # Direct change — broadcasts broken
            ),
            # Ball went past AI paddle — AI missed
            If(GreaterThan(XPosition(), 220),
                GoToPosition(0, 0),
                PointInDirection(PickRandom(30, 60)),
                ChangeVariable(ai_score, 1)      # Direct change — broadcasts broken
            ),
            # Hit Player paddle — deflect toward AI (RIGHT = 60-120°)
            If(TouchingObject(player),
                PointInDirection(PickRandom(60, 120))
            ),
            # Hit AI paddle — deflect toward player (LEFT = 240-300°)
            If(TouchingObject(ai),
                PointInDirection(PickRandom(240, 300))
            )
        )
    )

    # AI: follows ball — use Y_POSITION constant (= 'y position'), NOT the string 'Y_POSITION'.
    # Passing the string stores it verbatim; TurboWarp's sensing_of returns 0 for unknown names.
    ai.createScript(
        WhenFlagClicked(),
        Show(),
        Forever(
            If(GreaterThan(
                GetAttribute(Y_POSITION, ball),
                Add(YPosition(), 10)
            ),
                ChangeY(6)
            ),
            If(LessThan(
                GetAttribute(Y_POSITION, ball),
                Subtract(YPosition(), 10)
            ),
                ChangeY(-6)
            ),
            If(GreaterThan(YPosition(), 150),
                SetY(150)
            ),
            If(LessThan(YPosition(), -150),
                SetY(-150)
            ),
            Wait(0.02)
        )
    )

    # Score HUD: two tiny sprites positioned at the top corners.
    # Say(Join()) reliably displays score at a fixed stage coordinate position.
    score_left  = project.createSprite('ScoreLeft',  x=-170, y=130)
    score_right = project.createSprite('ScoreRight', x=170,  y=130)

    score_left.createScript(
        WhenFlagClicked(),
        Show(),
        GoToPosition(-170, 130),
        SetSize(5),
        Forever(
            Say(Join('Player: ', player_score)),
            Wait(0.1)
        )
    )

    score_right.createScript(
        WhenFlagClicked(),
        Show(),
        GoToPosition(170, 130),
        SetSize(5),
        Forever(
            Say(Join('AI: ', ai_score)),
            Wait(0.1)
        )
    )

    # Save pipeline: save → inject costumes (includes tiny dot costumes for HUD sprites)
    project.save('pong.sb3')
    add_costumes('pong.sb3')
    print('Created pong.sb3')


if __name__ == '__main__':
    create_pong()
