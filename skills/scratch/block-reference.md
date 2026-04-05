# ScratchGen Block Reference

Complete reference for all ScratchGen blocks. Import with `from ScratchGen import *`.

## Events

| Scratch Block | ScratchGen |
|--------------|------------|
| When green flag clicked | `WhenFlagClicked()` |
| When space key pressed | `WhenKeyPressed('space')` |
| When up arrow pressed | `WhenKeyPressed('up')` |
| When down arrow pressed | `WhenKeyPressed('down')` |
| When left arrow pressed | `WhenKeyPressed('left')` |
| When right arrow pressed | `WhenKeyPressed('right')` |
| When [key] pressed | `WhenKeyPressed('a')` |
| When this sprite clicked | `WhenThisSpriteClicked()` |
| When backdrop switches to | `WhenBackdropSwitchesTo('backdrop1')` |
| When I receive [msg] | `WhenBroadcastReceived('msg')` |
| When I start as a clone | `WhenStartAsClone()` |
| Broadcast [msg] | `Broadcast('msg')` |
| Broadcast [msg] and wait | `BroadcastAndWait('msg')` |

## Motion

### Commands

```python
MoveSteps(10)
TurnRight(15)
TurnLeft(15)
GoToPosition(x, y)
GoTo(RANDOM)
GoTo(MOUSE)
GoTo(sprite)
GlideToPosition(seconds, x, y)
GlideTo(seconds, RANDOM)
GlideTo(seconds, MOUSE)
GlideTo(seconds, sprite)
PointInDirection(90)
PointTowards(MOUSE)
PointTowards(sprite)
ChangeX(10)
SetX(0)
ChangeY(10)
SetY(0)
BounceOffEdge()
SetRotationStyle(LEFT_RIGHT)
SetRotationStyle(DONT_ROTATE)
SetRotationStyle(ALL_AROUND)
```

### Reporters

```python
XPosition()
YPosition()
Direction()
```

## Looks

### Commands

```python
Say('Hello!')
SayForSeconds('Hi!', 2)
Think('Hmm...')
ThinkForSeconds('...', 2)
Show()
Hide()
SwitchCostume(costume)
NextCostume()
SwitchBackdrop(backdrop)
NextBackdrop()
SwitchBackdropAndWait(backdrop)
ChangeSize(10)
SetSize(100)
ChangeGraphicEffect(COLOR, 25)
ChangeGraphicEffect(FISHEYE, 25)
ChangeGraphicEffect(WHIRL, 25)
ChangeGraphicEffect(PIXELATE, 25)
ChangeGraphicEffect(MOSAIC, 25)
ChangeGraphicEffect(BRIGHTNESS, 25)
ChangeGraphicEffect(GHOST, 25)
SetGraphicEffect(COLOR, 50)
SetGraphicEffect(GHOST, 50)
ClearGraphicEffects()
SetLayer(FRONT)
SetLayer(BACK)
ChangeLayer(FORWARD, 1)
ChangeLayer(BACKWARD, 1)
```

### Reporters

```python
Size()
Costume(NUMBER)
Costume(NAME)
Backdrop(NUMBER)
Backdrop(NAME)
```

## Sound

### Commands

```python
Play('Meow')
PlayUntilDone('Pop')
StopSounds()
ChangeVolume(-10)
SetVolume(100)
ChangeSoundEffect(PITCH, 10)
ChangeSoundEffect(PAN, 50)
SetSoundEffect(PITCH, 100)
SetSoundEffect(PAN, 0)
ClearSoundEffects()
```

### Reporters

```python
Volume()
```

## Control

```python
Wait(1)
Repeat(10, MoveSteps(10))
Forever(MoveSteps(1), Wait(0.1))
If(condition, MoveSteps(10))
If(condition, MoveSteps(10)).Else(MoveSteps(-10))
# Multiple actions — all args after condition run in sequence:
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
Stop(ALL)
Stop(OTHER_SCRIPTS)
Stop(THIS_SCRIPT)
CreateCloneOf(MYSELF)
CreateCloneOf(sprite)
DeleteThisClone()
```

## Sensing

### Touching

```python
TouchingObject(MOUSE)
TouchingObject(EDGE)
TouchingObject(sprite)
TouchingColor('#FF0000')
ColorTouchingColor('#FF0000', '#00FF00')
DistanceTo(MOUSE)
DistanceTo(sprite)
```

### Input

```python
AskAndWait("What's your name?")
Answer()
KeyPressed('space')
KeyPressed('w')
KeyPressed('up')
MouseDown()
MouseX()
MouseY()
Loudness()
Loud()
```

### Timer

```python
Timer()
ResetTimer()
```

### Sprite Attributes

Use the **ScratchGen constants** (no quotes) — they resolve to the lowercase Scratch attribute names that TurboWarp recognises. Passing the uppercase string (e.g. `'Y_POSITION'`) stores it verbatim and the block always returns `0`.

```python
GetAttribute(X_POSITION, sprite)      # constant = 'x position'
GetAttribute(Y_POSITION, sprite)      # constant = 'y position'
GetAttribute(DIRECTION, sprite)       # constant = 'direction'
GetAttribute(COSTUME_NUMBER, sprite)  # constant = 'costume #'
GetAttribute(COSTUME_NAME, sprite)    # constant = 'costume name'
GetAttribute(SIZE, sprite)            # constant = 'size'
GetAttribute(VOLUME, sprite)          # constant = 'volume'
GetAttribute(BACKDROP_NUMBER, stage)  # constant = 'backdrop #'
GetAttribute(BACKDROP_NAME, stage)    # constant = 'backdrop name'
GetAttribute('variable_name', stage)  # global variable — string OK here
GetAttribute('variable_name', sprite) # local variable  — string OK here
```

### Time

```python
Current(YEAR)
Current(MONTH)
Current(DATE)
Current(DAY_OF_WEEK)
Current(HOUR)
Current(MINUTE)
Current(SECOND)
DaysSince2000()
```

### Other

```python
Username()
SetDragMode(DRAGGABLE)
SetDragMode(NOT_DRAGGABLE)
```

## Operators

### Arithmetic

```python
Add(a, b)
Subtract(a, b)
Multiply(a, b)
Divide(a, b)
Modulo(a, b)
PickRandom(1, 10)
Round(value)
```

### Comparison

```python
LessThan(a, b)
GreaterThan(a, b)
Equals(a, b)
```

### Boolean

```python
And(a, b)
Or(a, b)
Not(condition)
```

### String

```python
Join('Hello', 'World')
LetterOf(1, 'Hello')
LengthOf('Hello')
Contains('Hello', 'ell')
```

### Math Operations

```python
Operation(ABSOLUTE, -5)
Operation(FLOOR, 3.7)
Operation(CEILING, 3.2)
Operation(SQUARE_ROOT, 16)
Operation(SINE, 45)
Operation(COSINE, 45)
Operation(TANGENT, 45)
Operation(ARCSINE, 0.5)
Operation(ARCCOSINE, 0.5)
Operation(ARCTANGENT, 1)
Operation(NATURAL_LOGARITHM, 2.718)
Operation(LOGARITHM, 100)
Operation(E_TO_THE, 2)
Operation(TEN_TO_THE, 2)
```

## Variables

```python
# Create
var = stage.createVariable('score', 0)      # global
var = sprite.createVariable('speed', 5)     # local

# Blocks
SetVariable(var, 10)
ChangeVariable(var, 1)
ShowVariable(var)
HideVariable(var)
```

## Lists

```python
# Create
lst = stage.createList('items')             # global
lst = sprite.createList('my_list')          # local

# Blocks
AddToList('apple', lst)
DeleteOfList(1, lst)
ClearList(lst)
InsertIntoList('banana', 1, lst)
ReplaceInList(1, lst, 'cherry')

# Reporters
ItemOfList(1, lst)
ListIndexOf('apple', lst)
ListLength(lst)
ListContains(lst, 'apple')

# Show/Hide
ShowList(lst)
HideList(lst)
```

## Custom Blocks

```python
# Define
prototype = sprite.createCustomBlock('move %s steps in direction %s')
steps, direction = prototype.getParameters()
my_block = prototype.setScript(
    PointInDirection(direction),
    MoveSteps(steps)
)

# Use
sprite.createScript(
    WhenFlagClicked(),
    my_block(50, 90)
)
```

Use `%s` for string/number input, `%b` for boolean input.

## Constants

```python
# Targets
RANDOM
MOUSE
EDGE
MYSELF

# Rotation styles
LEFT_RIGHT
DONT_ROTATE
ALL_AROUND

# Layers
FRONT
BACK
FORWARD
BACKWARD

# Keys
SPACE
ENTER
UP_ARROW
DOWN_ARROW
LEFT_ARROW
RIGHT_ARROW

# Effects
COLOR
FISHEYE
WHIRL
PIXELATE
MOSAIC
BRIGHTNESS
GHOST
PITCH
PAN

# Stop modes
ALL
OTHER_SCRIPTS
THIS_SCRIPT

# Drag modes
DRAGGABLE
NOT_DRAGGABLE

# Costume/backdrop options
NUMBER
NAME

# Math operations
ABSOLUTE
FLOOR
CEILING
SQUARE_ROOT
SINE
COSINE
TANGENT
ARCSINE
ARCCOSINE
ARCTANGENT
NATURAL_LOGARITHM
LOGARITHM
E_TO_THE
TEN_TO_THE

# Time options
YEAR
MONTH
DATE
DAY_OF_WEEK
HOUR
MINUTE
SECOND
```
