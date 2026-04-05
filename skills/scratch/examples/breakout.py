#!/usr/bin/env python3
"""Breakout game — paddle, pink ball, 6×4 orange brick grid, score HUD.

Ball physics uses dx/dy stage variables (+1/-1) so direction is always
axis-aligned and bricks can flip dy independently from parallel scripts.
Sounds are generated in-memory and embedded on the Ball sprite.
Scoring uses direct ChangeVariable — ScratchGen broadcasts have null IDs.
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

# ── Layout constants ─────────────────────────────────────────────────────────
ROWS      = 4
COLS      = 6
BRICK_W   = 56          # px
BRICK_H   = 18          # px
BRICK_STEP_X = 58       # col centre-to-centre  (BRICK_W + 2 gap)
BRICK_STEP_Y = 22       # row centre-to-centre  (BRICK_H + 4 gap)
BRICK_START_X = -145    # centre of leftmost column
BRICK_START_Y = 150     # centre of top row
BRICK_COLOR = '#ff8c00' # orange — used for TouchingColor sound trigger

PADDLE_W  = 100
PADDLE_H  = 14
BALL_SIZE = 18
BALL_SPEED = 4          # px per step (≤ BRICK_H/2 prevents tunnelling)


def add_assets(output_path):
    """Inject costumes (paddle, ball, bricks, HUD dot) and sounds into .sb3."""

    def _paddle_png():
        img = Image.new('RGBA', (PADDLE_W, PADDLE_H), (30, 100, 255, 255))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    def _ball_png():
        img = Image.new('RGBA', (BALL_SIZE, BALL_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, BALL_SIZE - 1, BALL_SIZE - 1], fill=(255, 105, 180, 255))
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    def _brick_png():
        img = Image.new('RGBA', (BRICK_W, BRICK_H), (255, 140, 0, 255))  # #ff8c00
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()

    def _dot_png():
        img = Image.new('RGBA', (4, 4), (255, 255, 255, 80))
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

    paddle_wav = _wav(440, 0.06)
    brick_wav  = _wav(660, 0.04)
    paddle_id  = hashlib.md5(paddle_wav).hexdigest()
    brick_id   = hashlib.md5(brick_wav).hexdigest()

    brick_png_data = _brick_png()

    costume_data = {
        'Paddle':   ('paddle', _paddle_png()),
        'Ball':     ('ball',   _ball_png()),
        'ScoreHUD': ('dot',    _dot_png()),
        'GameMsg':  ('dot',    _dot_png()),
    }
    for r in range(ROWS):
        for c in range(COLS):
            costume_data[f'Brick{r}{c}'] = ('brick', brick_png_data)

    new_assets = {
        f'{paddle_id}.wav': paddle_wav,
        f'{brick_id}.wav':  brick_wav,
    }

    with zipfile.ZipFile(output_path, 'r') as zf:
        proj   = json.loads(zf.read('project.json'))
        assets = {f: zf.read(f) for f in zf.namelist() if f != 'project.json'}

    for target in proj['targets']:
        name = target.get('name', '')

        if name in costume_data:
            cname, data = costume_data[name]
            aid   = hashlib.md5(data).hexdigest()
            fname = f'{aid}.png'
            new_assets[fname] = data
            img = Image.open(io.BytesIO(data))
            w, h = img.size
            target['costumes'] = [{
                'assetId': aid, 'name': cname, 'bitmapResolution': 1,
                'md5ext': fname, 'dataFormat': 'png',
                'rotationCenterX': w // 2, 'rotationCenterY': h // 2,
            }]
            target['currentCostume'] = 0

        if name == 'Ball':
            target['sounds'] = [
                {'assetId': paddle_id, 'name': 'paddle', 'dataFormat': 'wav',
                 'format': '', 'rate': 44100, 'sampleCount': int(44100 * 0.06),
                 'md5ext': f'{paddle_id}.wav'},
                {'assetId': brick_id,  'name': 'brick',  'dataFormat': 'wav',
                 'format': '', 'rate': 44100, 'sampleCount': int(44100 * 0.04),
                 'md5ext': f'{brick_id}.wav'},
            ]

    with zipfile.ZipFile(output_path, 'w') as zf:
        zf.writestr('project.json', json.dumps(proj))
        for f, data in {**assets, **new_assets}.items():
            zf.writestr(f, data)


def create_breakout():
    """Create a complete Breakout game."""
    project = Project()
    stage   = project.stage

    # Global variables — readable/writable from any sprite
    score     = stage.createVariable('Score', 0)
    lives     = stage.createVariable('Lives', 3)
    ball_dx   = stage.createVariable('dx', 1)       # +1 = right, -1 = left
    ball_dy   = stage.createVariable('dy', 1)       # +1 = up,    -1 = down
    game_over = stage.createVariable('game_over', 0) # 0=playing 1=lost 2=win

    # Sprites
    paddle    = project.createSprite('Paddle',   x=0, y=-150, rotation_style="don't rotate")
    ball      = project.createSprite('Ball',     x=0, y=-80)
    score_hud = project.createSprite('ScoreHUD', x=-170, y=160)
    game_msg  = project.createSprite('GameMsg',  x=0, y=0)

    # Brick grid — store (sprite, x, y) so we can set positions in scripts
    brick_list = []
    for r in range(ROWS):
        for c in range(COLS):
            bx = BRICK_START_X + c * BRICK_STEP_X
            by = BRICK_START_Y - r * BRICK_STEP_Y
            bk = project.createSprite(f'Brick{r}{c}', x=bx, y=by,
                                      rotation_style="don't rotate")
            brick_list.append((bk, bx, by))

    # ── Stage: reset on green flag ────────────────────────────────────────────
    stage.createScript(
        WhenFlagClicked(),
        SetVariable(score,     0),
        SetVariable(lives,     3),
        SetVariable(ball_dx,   1),
        SetVariable(ball_dy,   1),
        SetVariable(game_over, 0)
    )

    # ── Paddle: left/right arrows with boundary clamp ─────────────────────────
    paddle.createScript(
        WhenFlagClicked(),
        Show(),
        SetSize(100),
        GoToPosition(0, -150),
        Forever(
            If(KeyPressed('left arrow'),
                If(GreaterThan(XPosition(), -175),
                    ChangeX(-10)
                )
            ),
            If(KeyPressed('right arrow'),
                If(LessThan(XPosition(), 175),
                    ChangeX(10)
                )
            ),
            Wait(0.02)
        )
    )

    # ── Ball: movement + wall/paddle bounces + sound ──────────────────────────
    # Brick physics (dy flip + score) are handled by each brick's own script.
    # Ball only needs to detect: walls, paddle, and brick colour (for sound).
    ball.createScript(
        WhenFlagClicked(),
        Show(),
        SetSize(100),
        SetRotationStyle(DONT_ROTATE),
        GoToPosition(0, -80),
        SetVariable(ball_dx, 1),
        SetVariable(ball_dy, 1),
        Forever(
            ChangeX(Multiply(ball_dx, BALL_SPEED)),
            ChangeY(Multiply(ball_dy, BALL_SPEED)),
            # Left / right wall
            If(GreaterThan(XPosition(), 232),  SetVariable(ball_dx, -1)),
            If(LessThan(XPosition(), -232),    SetVariable(ball_dx, 1)),
            # Top wall
            If(GreaterThan(YPosition(), 175),  SetVariable(ball_dy, -1)),
            # Paddle — only redirect when moving downward (ball_dy = -1)
            If(And(TouchingObject(paddle), LessThan(ball_dy, 0)),
                SetVariable(ball_dy, 1),
                Play('paddle')
            ),
            # Brick sound (physics handled by the brick sprite itself)
            If(TouchingColor(BRICK_COLOR), Play('brick')),
            # Win — all bricks cleared (24 × 10 = 240)
            If(GreaterThan(score, 239),
                SetVariable(game_over, 2),
                Stop(THIS_SCRIPT)
            ),
            # Ball fell below paddle — lose a life.
            # Scratch fence clamps at y=-180, so use -172 as threshold.
            If(LessThan(YPosition(), -172),
                ChangeVariable(lives, -1),
                If(LessThan(lives, 1),
                    SetVariable(game_over, 1),
                    Stop(THIS_SCRIPT)
                ).Else(
                    GoToPosition(0, -80),
                    SetVariable(ball_dx, 1),
                    SetVariable(ball_dy, 1)
                )
            ),
            Wait(0.02)
        )
    )

    # ── Bricks: each handles its own collision independently ──────────────────
    # When ball touches a brick: flip dy, add score, hide.
    # GoToPosition + Show() on WhenFlagClicked restores bricks on restart.
    for bk, bx, by in brick_list:
        bk.createScript(
            WhenFlagClicked(),
            Show(),
            SetSize(100),
            GoToPosition(bx, by),
            Forever(
                If(TouchingObject(ball),
                    SetVariable(ball_dy, Multiply(ball_dy, -1)),
                    ChangeVariable(score, 10),
                    Hide()
                ),
                Wait(0.02)
            )
        )

    # ── Score / Lives HUD ──────────────────────────────────────────────────────
    score_hud.createScript(
        WhenFlagClicked(),
        Show(),
        GoToPosition(-170, 160),
        SetSize(5),
        Forever(
            Say(Join(Join('Score: ', score), Join('   Lives: ', lives))),
            Wait(0.1)
        )
    )

    # ── Game message sprite — stays alive, shows win/lose text ────────────────
    # Stop(ALL) clears speech bubbles before TurboWarp renders the frame.
    # This sprite runs independently and reacts to the game_over variable.
    game_msg.createScript(
        WhenFlagClicked(),
        Show(),
        GoToPosition(0, 0),
        SetSize(5),
        Forever(
            If(Equals(game_over, 1), Say('Game Over!')),
            If(Equals(game_over, 2), Say('You Win! :)')),
            If(Equals(game_over, 0), Say('')),
            Wait(0.1)
        )
    )

    # Save pipeline: save → inject costumes + sounds
    project.save('breakout.sb3')
    add_assets('breakout.sb3')
    print('Created breakout.sb3')


if __name__ == '__main__':
    create_breakout()
