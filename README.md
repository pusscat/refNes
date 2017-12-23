# refNes: NES reference implementation in python2

To run:

`python debugger.py <rom path>`

then type 'g'

'?' will show you debugger commands

Todo:

- [X] finish instructions
- [] unit tests
- [X] abstract out memory from cpu
- [X] abstract out mappers from memory
- [X] create the cartridge rom parser/loader
- [] create the PPU
- [] create the APU
- [] speed up cpu and ppu
- [] sort out instruction timing

## Supported Platforms

Tested with:

- Python 2.7.10 on macOS 10.13.2
- Python 2.7.14 on macOS 10.13.2

## Installing Dependencies

- [SDL2, the cross-platform hardware abstraction layer for media software](https://www.libsdl.org)
- Python 2
- [PySDL2, the Python bindings for SDL2](https://pysdl2.readthedocs.io/)

On macOS:

```shell
brew install sdl2
sudo python -m pip install pysdl2
```

## Getting refNes

```bash
git clone https://github.com/pusscat/refNes
```

## How to Run refNes

```bash
cd refNes
python debugger.py /path/to/rom.nes
```

## How to Run refNes Tests

```bash
# First, place a valid smb1.nes file in the refNes directory.
cd refNes/tests
python instruction_tests.py
python cart_tests.py
```
