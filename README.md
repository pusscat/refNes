# refNes: NES reference implementation in python3

To run:

`python3 debugger.py <rom path>`

then type 'g'

Add `--scale N` (or `-s N`) to make the window N times larger, e.g. `python3 debugger.py -s 3 game.nes` for 768x720.

Controller keys are set in `controls.cfg` (player 1: arrows, Z = B, X = A, Right Shift = Select, Enter = Start; player 2: WASD, F = B, G = A, Q = Select, E = Start). Use `--controls <file>` (or `-c`) to load a different file. The game window needs keyboard focus for keys to register.

'?' will show you debugger commands

## TODO

- [X] finish instructions
- [X] unit tests
- [X] abstract out memory from cpu
- [X] abstract out mappers from memory
- [X] create the cartridge rom parser/loader
- [X] create the PPU (scanline renderer, scrolling, sprite 0 hit, 8x16 sprites)
- [X] keyboard controls for 2 players (`controls.cfg`)
- [X] 60 fps speed limit (debugger `limit` command)
- [ ] speed up a bit more, so busy games (e.g. SMB1) don't drop frames
    - currently ~13-14 ms of the 16.6 ms frame budget; little headroom under system load
    - next ideas: trim `run()` loop overhead (`last_four` bookkeeping, attribute lookups),
      PyPy, optional frame skip
- [ ] 4:3 display option for integer scales (NES pixels are 8:7, so 256x240 shows as ~4:3 on a TV)
- [ ] create the APU (audio)
- [ ] gamepad / joystick controller support (keyboard already works)
- [ ] more mappers (only NROM / mapper 0 so far); see the contract notes in `nesMappers/mapper.py`
    - likely order by game coverage: MMC1 (1), UxROM (2), CNROM (3), MMC3 (4)
- [ ] sort out remaining instruction timing (DMA stall cycles, odd-frame dot skip)

## Python3 Changes
- Converted all syntax to be compatible with Python3.
- Cleaned up function and variable names to be consistent in case.
- Expanded debugger.
    - Operations in arguments (Ex: `d PC+0x04`)
    - Debugger scripts (Ex: `script set_breakpoints`)
    - Better screen printing to console
    - Whatever else comes to mind...
- Drawing with pygame: each frame is copied into an 8-bit surface whose palette is the NES colors.
- Miscellaneous stuff I forgot.


## Installing Dependencies

- Python 3.7 or newer (tested with 3.12)
- [pygame](https://www.pygame.org) 2.x (tested with 2.5.2); it includes SDL2, so nothing else is needed

On any platform with pip (Linux, macOS, Windows):

```shell
python3 -m pip install pygame
```

On Debian/Ubuntu you can use the system package instead:

```shell
sudo apt install python3-pygame
```

## Getting refNes

```bash
git clone https://github.com/pusscat/refNes
```

## How to Run refNes

```bash
cd refNes
python3 debugger.py /path/to/rom.nes
```

## How to Run refNes Tests

```bash
# First, place a valid smb1.nes file in the refNes directory.
cd refNes/tests
python3 instruction_tests.py
python3 cart_tests.py
```
