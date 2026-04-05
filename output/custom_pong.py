#!/usr/bin/env python3
"""Custom Pong game - pink ball, green paddles, player names, missed ball count.

Sounds are generated in-memory (WAV) and embedded in the Ball sprite.
Scoring uses direct ChangeVariable — Scratch broadcasts have null IDs in ScratchGen.
"""

from ScratchGen import *
import hashlib
import io
import json
import math
import struct
import wave
import zipfile

from PIL import Image, ImageDraw


def add_assets(output_path):
    """Inject sprite costumes and sounds into a saved .sb3 file.

    Costumes:
        Player / Computer : green rectangle (20 x 120 px)
        Ball              : pink circle    (30 x 30 px)
    Sounds (on Ball sprite):
        hit  : 440 Hz beep, 0.08 s  — played on paddle contact
        miss : 220 Hz buzz, 0.25 s  — played on score
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

    def _wav(freq, duration, sample_rate=44100):
        n = int(sample_rate * duration)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f'<{n}h', *[
                int(32767 * math.sin(2 * math.pi * freq * k / sample_rate))
                for k in range(n)
            ]))
        return buf.getvalue()

    costume_data = {
        'Player':      ('paddle', _paddle_png()),
        'Computer':    ('paddle', _paddle_png()),
        'Ball':        ('ball',   _ball_png()),
        'PlayerHUD':   ('dot',    _dot_png()),
        'ComputerHUD': ('dot',    _dot_png()),
    }
    hit_wav  = _wav(440, 0.08)
    miss_wav = _wav(220, 0.25)
    hit_id   = hashlib.md5(hit_wav).hexdigest()
    miss_id  = hashlib.md5(miss_wav).hexdigest()

    new_assets = {
        f'{hit_id}.wav':  hit_wav,
        f'{miss_id}.wav': miss_wav,
    }

    with zipfile.ZipFile(output_path, 'r') as zf:
        proj = json.loads(zf.read('project.json'))
        assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

    for target in proj['targets']:
        sprite_name = target.get('name', '')

        if sprite_name in costume_data:
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

        if sprite_name == 'Ball':
            target['sounds'] = [
                {'assetId': hit_id,  'name': 'hit',  'dataFormat': 'wav',
                 'format': '', 'rate': 44100, 'sampleCount': int(44100 * 0.08),
                 'md5ext': f'{hit_id}.wav'},
                {'assetId': miss_id, 'name': 'miss', 'dataFormat': 'wav',
                 'format': '', 'rate': 44100, 'sampleCount': int(44100 * 0.25),
                 'md5ext': f'{miss_id}.wav'},
            ]

    with zipfile.ZipFile(output_path, 'w') as zf:
        zf.writestr('project.json', json.dumps(proj))
        for f, data in {**assets, **new_assets}.items():
            zf.writestr(f, data)


def add_monitors(output_path, positions=None):
    """Position variable monitors by reading ShowVariable block IDs from the stage.

    TurboWarp resolves a monitor's label from the block referenced by monitor.id.
    By using the data_showvariable block's own ID (not the variable ID) as the
    monitor ID, TurboWarp can look up fields.VARIABLE = [name, var_id] and
    display the correct variable name as the label.

    Args:
        output_path: Path to the .sb3 file (after project.save() + add_assets()).
        positions: Optional dict of {variable_name: (x, y)}.
                   x/y are in stage screen pixels (top-left origin, stage = 480x360).
    """
    with zipfile.ZipFile(output_path, 'r') as zf:
        proj = json.loads(zf.read('project.json'))
        assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

    stage = next(t for t in proj['targets'] if t.get('isStage'))

    monitors = []
    i = 0
    for bid, block in stage.get('blocks', {}).items():
        if block['opcode'] != 'data_showvariable':
            continue
        var_field = block.get('fields', {}).get('VARIABLE', [])
        if not var_field:
            continue
        var_name = var_field[0]              # e.g. "Player"

        if positions and var_name in positions:
            x, y = positions[var_name]
        else:
            x, y = 5, 5 + i * 35            # Auto-stack vertically

        var_id = var_field[1]                # e.g. "1-Player"
        monitors.append({
            "id": var_id,                    # Variable ID — TurboWarp resolves label
            "mode": "default",               # via stage.variables[id][0]
            "opcode": "data_showvariable",
            "params": {"VARIABLE": var_name},
            "spriteName": None,
            "value": "0",
            "width": 0,
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


def create_custom_pong():
    """Create a custom Pong game with pink ball, green paddles, and player names."""
    project = Project()

    # Stage coordinate bounds: x: -240 to 240, y: -180 to 180
    # rotation_style: "don't rotate"|DONT_ROTATE  (constants available too)
    # Sprites default to HIDDEN — Show() required in WhenFlagClicked()
    player = project.createSprite('Player', x=-180, y=0, rotation_style="don't rotate")
    ball = project.createSprite('Ball', x=0, y=0)
    computer = project.createSprite('Computer', x=180, y=0, rotation_style="don't rotate")

    # Global score variables. Variable names appear as monitor labels, so
    # 'Player' and 'Computer' serve as both the player name and the score header.
    stage = project.stage
    player_score = stage.createVariable('Player', 0)
    computer_score = stage.createVariable('Computer', 0)

    # Stage: reset scores on green flag.
    # Score display is handled by PlayerHUD / ComputerHUD sprites using Say() —
    # this bypasses TurboWarp's monitor position-override behavior.
    stage.createScript(
        WhenFlagClicked(),
        SetVariable(player_score, 0),
        SetVariable(computer_score, 0)
    )

    # Player: W/S key controls with optimized movement and boundary checks
    player.createScript(
        WhenFlagClicked(),
        Show(),
        SetSize(100),
        Forever(
            # W key - move up with boundary pre-check
            If(KeyPressed('w'),
                If(LessThan(Add(YPosition(), 15), 150),
                    ChangeY(15)
                ).Else(
                    SetY(150)
                )
            ),
            # S key - move down with boundary pre-check  
            If(KeyPressed('s'),
                If(GreaterThan(Subtract(YPosition(), 15), -150),
                    ChangeY(-15)
                ).Else(
                    SetY(-150)
                )
            ),
            Wait(0.02)
        )
    )

    # Ball: movement, collision, scoring
    # Scoring uses ChangeVariable directly — Scratch broadcasts have null IDs
    # in ScratchGen and WhenBroadcastReceived never fires reliably.
    # Physics tip: keep MoveSteps <= half paddle width to avoid tunneling.
    ball.createScript(
        WhenFlagClicked(),
        Show(),
        SetRotationStyle(DONT_ROTATE),
        GoToPosition(0, 0),
        # Scratch directions: 0=UP, 90=RIGHT, 180=DOWN, 270(-90)=LEFT
        PointInDirection(PickRandom(30, 60)),  # Start going right + upward diagonal
        Forever(
            MoveSteps(5),
            BounceOffEdge(),
            # Ball went past Player paddle — PLAYER missed
            If(LessThan(XPosition(), -220),
                GoToPosition(0, 0),
                PointInDirection(PickRandom(210, 240)),
                ChangeVariable(player_score, 1),
                Play('miss')
            ),
            # Ball went past Computer paddle — COMPUTER missed
            If(GreaterThan(XPosition(), 220),
                GoToPosition(0, 0),
                PointInDirection(PickRandom(30, 60)),
                ChangeVariable(computer_score, 1),
                Play('miss')
            ),
            # Hit Player paddle — deflect toward computer (RIGHT = 60-120°)
            If(TouchingObject(player),
                PointInDirection(PickRandom(60, 120)),
                Play('hit')
            ),
            # Hit Computer paddle — deflect toward player (LEFT = 240-300°)
            If(TouchingObject(computer),
                PointInDirection(PickRandom(240, 300)),
                Play('hit')
            )
        )
    )

    # Computer: digital player — tracks ball using Y_POSITION constant ('y position')
    # which TurboWarp's sensing_of block recognises. Speed 12 px / Wait(0.02).
    computer.createScript(
        WhenFlagClicked(),
        Show(),
        SetSize(100),
        Forever(
            If(GreaterThan(GetAttribute(Y_POSITION, ball), YPosition()),
                ChangeY(12)
            ),
            If(LessThan(GetAttribute(Y_POSITION, ball), YPosition()),
                ChangeY(-12)
            ),
            If(GreaterThan(YPosition(), 150), SetY(150)),
            If(LessThan(YPosition(), -150), SetY(-150)),
            Wait(0.02)
        )
    )

    # Score HUD: two small sprites positioned at the top corners.
    # Say(Join()) continuously displays the score label + value.
    # Using sprites avoids TurboWarp's monitor position-override issue.
    player_hud   = project.createSprite('PlayerHUD',   x=-170, y=130)
    computer_hud = project.createSprite('ComputerHUD', x=170,  y=130)

    player_hud.createScript(
        WhenFlagClicked(),
        Show(),
        GoToPosition(-170, 130),
        SetSize(5),
        Forever(
            Say(Join('Player: ', player_score)),
            Wait(0.1)
        )
    )

    computer_hud.createScript(
        WhenFlagClicked(),
        Show(),
        GoToPosition(170, 130),
        SetSize(5),
        Forever(
            Say(Join('Computer: ', computer_score)),
            Wait(0.1)
        )
    )

    # Save pipeline: save → inject assets (costumes + sounds)
    project.save('custom_pong.sb3')
    add_assets('custom_pong.sb3')
    print('Created custom_pong.sb3')


if __name__ == '__main__':
    create_custom_pong()
