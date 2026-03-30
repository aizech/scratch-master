# Scratch 3.0 Block Opcodes

Reference for all Scratch 3.0 block opcodes used in the JSON format.

## Motion Blocks

| Block | Opcode |
|-------|--------|
| move () steps | `motion_movesteps` |
| turn cw () degrees | `motion_turnright` |
| turn ccw () degrees | `motion_turnleft` |
| go to ( v) | `motion_goto` |
| go to x: () y: () | `motion_gotoxy` |
| glide () secs to ( v) | `motion_glideto` |
| glide () secs to x: () y: () | `motion_glidesecstoxy` |
| point in direction () | `motion_pointindirection` |
| point towards ( v) | `motion_pointtowards` |
| change x by () | `motion_changexby` |
| set x to () | `motion_setx` |
| change y by () | `motion_changeyby` |
| set y to () | `motion_sety` |
| if on edge, bounce | `motion_ifonedgebounce` |
| set rotation style [ v] | `motion_setrotationstyle` |
| (x position) | `motion_xposition` |
| (y position) | `motion_yposition` |
| (direction) | `motion_direction` |

## Looks Blocks

| Block | Opcode |
|-------|--------|
| say () for () seconds | `looks_sayforsecs` |
| say () | `looks_say` |
| think () for () seconds | `looks_thinkforsecs` |
| think () | `looks_think` |
| switch costume to ( v) | `looks_switchcostumeto` |
| next costume | `looks_nextcostume` |
| switch backdrop to ( v) | `looks_switchbackdropto` |
| switch backdrop to ( v) and wait | `looks_switchbackdroptoandwait` |
| next backdrop | `looks_nextbackdrop` |
| change size by () | `looks_changesizeby` |
| set size to ()% | `looks_setsizeto` |
| change [ v] effect by () | `looks_changeeffectby` |
| set [ v] effect to () | `looks_seteffectto` |
| clear graphic effects | `looks_cleargraphiceffects` |
| show | `looks_show` |
| hide | `looks_hide` |
| go to [ v] layer | `looks_gotofrontback` |
| go [ v] () layers | `looks_goforwardbackwardlayers` |
| (costume [ v]) | `looks_costumenumbername` |
| (backdrop [ v]) | `looks_backdropnumbername` |
| (size) | `looks_size` |

## Sound Blocks

| Block | Opcode |
|-------|--------|
| play sound ( v) until done | `sound_playuntildone` |
| start sound ( v) | `sound_play` |
| stop all sounds | `sound_stopallsounds` |
| change [ v] effect by () | `sound_changeeffectby` |
| set [ v] effect to () | `sound_seteffectto` |
| clear sound effects | `sound_cleareffects` |
| change volume by () | `sound_changevolumeby` |
| set volume to ()% | `sound_setvolumeto` |
| (volume) | `sound_volume` |

## Events Blocks

| Block | Opcode |
|-------|--------|
| when gf clicked | `event_whenflagclicked` |
| when [ v] key pressed | `event_whenkeypressed` |
| when this sprite clicked | `event_whenthisspriteclicked` |
| when stage clicked | `event_whenstageclicked` |
| when backdrop switches to [ v] | `event_whenbackdropswitchesto` |
| when [ v] > () | `event_whengreaterthan` |
| when I receive [ v] | `event_whenbroadcastreceived` |
| broadcast ( v) | `event_broadcast` |
| broadcast ( v) and wait | `event_broadcastandwait` |

## Control Blocks

| Block | Opcode |
|-------|--------|
| wait () seconds | `control_wait` |
| repeat () | `control_repeat` |
| forever | `control_forever` |
| if <> then | `control_if` |
| if <> then else | `control_if_else` |
| wait until <> | `control_wait_until` |
| repeat until <> | `control_repeat_until` |
| stop [ v] | `control_stop` |
| when I start as a clone | `control_start_as_clone` |
| create clone of ( v) | `control_create_clone_of` |
| delete this clone | `control_delete_this_clone` |

## Sensing Blocks

| Block | Opcode |
|-------|--------|
| <touching ( v)?> | `sensing_touchingobject` |
| <touching color (#)?> | `sensing_touchingcolor` |
| <color () is touching ()?> | `sensing_coloristouchingcolor` |
| (distance to ( v)) | `sensing_distanceto` |
| ask () and wait | `sensing_askandwait` |
| (answer) | `sensing_answer` |
| <key ( v) pressed?> | `sensing_keypressed` |
| <mouse down?> | `sensing_mousedown` |
| (mouse x) | `sensing_mousex` |
| (mouse y) | `sensing_mousey` |
| set drag mode [ v] | `sensing_setdragmode` |
| (loudness) | `sensing_loudness` |
| (timer) | `sensing_timer` |
| reset timer | `sensing_resettimer` |
| [ v] of ( v) | `sensing_of` |
| (current [ v]) | `sensing_current` |
| (days since 2000) | `sensing_dayssince2000` |
| <online?> | `sensing_online` |
| (username) | `sensing_username` |

## Operators Blocks

| Block | Opcode |
|-------|--------|
| () + () | `operator_add` |
| () - () | `operator_subtract` |
| () * () | `operator_multiply` |
| () / () | `operator_divide` |
| (pick random () to ()) | `operator_random` |
| <() > ()> | `operator_gt` |
| <() < ()> | `operator_lt` |
| <() = ()> | `operator_equals` |
| <<> and <>> | `operator_and` |
| <<> or <>> | `operator_or` |
| <not <>> | `operator_not` |
| (join()()) | `operator_join` |
| (letter () of ()) | `operator_letter_of` |
| (length of ()) | `operator_length` |
| <() contains ()?> | `operator_contains` |
| (() mod ()) | `operator_mod` |
| (round()) | `operator_round` |
| [ v] of () | `operator_mathop` |

## Variables Blocks

| Block | Opcode |
|-------|--------|
| ( ::variables) | `data_variable` |
| set [ v] to () | `data_setvariableto` |
| change [ v] by () | `data_changevariableby` |
| show variable [ v] | `data_showvariable` |
| hide variable [ v] | `data_hidevariable` |

## List Blocks

| Block | Opcode |
|-------|--------|
| ( ::list) | `data_listcontents` |
| add () to [ v] | `data_addtolist` |
| delete () of [ v] | `data_deleteoflist` |
| delete all of [ v] | `data_deletealloflist` |
| insert () at () of [ v] | `data_insertatlist` |
| replace item () of [ v] with () | `data_replaceitemoflist` |
| (item () of [ v]) | `data_itemoflist` |
| (item # of () in [ v]) | `data_itemnumoflist` |
| (length of [ v]) | `data_lengthoflist` |
| <[ v] contains ()?> | `data_listcontainsitem` |
| show list [ v] | `data_showlist` |
| hide list [ v] | `data_hidelist` |

## My Blocks (Custom Blocks)

| Block | Opcode |
|-------|--------|
| define | `procedures_definition` |
| (:: custom) | `procedures_call` |
| ( :: custom) | `argument_reporter_string_number` |
| < :: custom> | `argument_reporter_boolean` |

## Pen Extension

| Block | Opcode |
|-------|--------|
| erase all | `pen_clear` |
| stamp | `pen_stamp` |
| pen down | `pen_pendown` |
| pen up | `pen_penup` |
| set pen color to (#) | `pen_setPenColorToColor` |
| change pen ( v) by () | `pen_changePenColorParamBy` |
| set pen ( v) to () | `pen_setPenColorParamTo` |
| change pen size by () | `pen_changePenSizeBy` |
| set pen size to () | `pen_setPenSizeTo` |

## Music Extension

| Block | Opcode |
|-------|--------|
| play drum ( v) for () beats | `music_playDrumForBeats` |
| rest for () beats | `music_restForBeats` |
| play note () for () beats | `music_playNoteForBeats` |
| set instrument to ( v) | `music_setInstrument` |
| set tempo to () | `music_setTempo` |
| change tempo by () | `music_changeTempo` |
| (tempo) | `music_getTempo` |

## Text to Speech Extension

| Block | Opcode |
|-------|--------|
| speak () | `text2speech_speakAndWait` |
| set voice to ( v) | `text2speech_setVoice` |
| set language to ( v) | `text2speech_setLanguage` |

## Common Dropdown Menus

### Sprite/Mouse Dropdowns
- `motion_goto_menu` - "random position", sprite names
- `motion_pointtowards_menu` - sprite names, "mouse-pointer"
- `looks_costume` - costume names
- `looks_backdrops` - backdrop names
- `sensing_touchingobjectmenu` - sprite names, "mouse-pointer", "edge"
- `sensing_keyoptions` - "space", "up arrow", "down arrow", etc.
- `sensing_of_object_menu` - sprite names

### Rotation Styles
- `all around`
- `left-right`
- `don't rotate`

### Stop Options
- `all`
- `this script`
- `other scripts in sprite`

### Video State
- `on`
- `off`
- `on-flipped`
