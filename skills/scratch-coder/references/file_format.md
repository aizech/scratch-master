# Scratch 3.0 File Format

This document describes the `.sb3` file format used by Scratch 3.0.

## Overview

An `.sb3` file is a **ZIP archive** containing:
- `project.json` - Main project data (JSON format)
- Asset files (costumes, sounds) named by MD5 hash

## Project JSON Structure

```json
{
  "targets": [...],
  "monitors": [...],
  "extensions": [...],
  "meta": {
    "semver": "3.0.0",
    "vm": "0.2.0",
    "agent": ""
  }
}
```

## Targets

A **target** is either the Stage or a Sprite.

### Stage Target
```json
{
  "isStage": true,
  "name": "Stage",
  "variables": {},
  "lists": {},
  "broadcasts": {},
  "blocks": {},
  "comments": {},
  "currentCostume": 0,
  "costumes": [...],
  "sounds": [...],
  "volume": 100,
  "layerOrder": 0,
  "tempo": 60,
  "videoTransparency": 50,
  "videoState": "on",
  "textToSpeechLanguage": null
}
```

### Sprite Target
```json
{
  "isStage": false,
  "name": "Sprite1",
  "variables": {},
  "lists": {},
  "broadcasts": {},
  "blocks": {},
  "comments": {},
  "currentCostume": 0,
  "costumes": [...],
  "sounds": [...],
  "volume": 100,
  "layerOrder": 1,
  "visible": true,
  "x": 0,
  "y": 0,
  "size": 100,
  "direction": 90,
  "draggable": false,
  "rotationStyle": "all around"
}
```

## Costumes

```json
{
  "assetId": "bcf454acf82e4504149f7ffe07081dbc",
  "name": "costume1",
  "md5ext": "bcf454acf82e4504149f7ffe07081dbc.svg",
  "dataFormat": "svg",
  "rotationCenterX": 48,
  "rotationCenterY": 50
}
```

### Built-in Costume MD5 Hashes

| Name | MD5 Hash |
|------|----------|
| Empty costume | 1fab14b135a4262c64eaf6f5009f326e |
| Scratch Cat | bcf454acf82e4504149f7ffe07081dbc |
| Banana | 0fb9be3e8397c983338cb71dc84d0b25 |
| Tennis Ball | 19307039b0315b9d74609765c99780bc |
| Basketball | 30a2740de4fc5426a5a1f3b04d537f52 |
| Soccer Ball | 83ed2c7c9d2a10eecdcc7229f70d1f0e |
| Drum | 3be9d3200f36e3f8307bd4c55ec1b9ae |
| Microphone | 1fa6a6a09f7285e77c95f2f4568fb4c3 |

## Sounds

```json
{
  "assetId": "83a9787d4cb6f3b7632b4ddfebf74367",
  "name": "pop",
  "dataFormat": "wav",
  "format": "",
  "rate": 48000,
  "sampleCount": 1123,
  "md5ext": "83a9787d4cb6f3b7632b4ddfebf74367.wav"
}
```

### Built-in Sound MD5 Hashes

| Name | MD5 Hash |
|------|----------|
| Pop | 83a9787d4cb6f3b7632b4ddfebf74367 |
| Meow | 83c36d806dc92327b9e7049a565c6bff |
| Boing | 6d7d86e0f7d3c38f8a30d4d2f8a3e8b0 |
| Gong | 6fc4e1cde4e7c3f8a2f9d4e0c8a3e8b0 |
| Chirp | e5f3d8a2b3c4e5f6a7b8c9d0e1f2a3b4 |
| Crash | f6a7e8c3b4d5e6f7a8b9c0d1e2f3a4b5 |
| Mute | 0d5a0e1c2d3e4f5a6b7c8d9e0f1a2b3c |

## Extensions

Common extensions that can be used:
- `pen` - Pen drawing
- `music` - Music instruments
- `text2speech` - Text to speech
- `videoSensing` - Camera input

## Variables and Lists

### Variable
```json
"variables": {
  "unique_id": ["Score", 0]
}
```

### List
```json
"lists": {
  "unique_id": ["High Scores", []]
}
```

### Cloud Variable (Stage only)
```json
"variables": {
  "unique_id": ["☁ Score", 0, true]
}
```

## Broadcasts

```json
"broadcasts": {
  "unique_id": "game_over"
}
```

## Creating an .sb3 File

```python
import zipfile
import json
from pathlib import Path

def create_sb3(project_json, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('project.json', json.dumps(project_json, indent=2))
```

## Coordinate System

- Center of stage: (0, 0)
- X range: -240 to 240
- Y range: -180 to 180
- Direction 0 = up, 90 = right, 180 = down, -90 = left
