"""
nesControllers: standard NES controllers on $4016 (player 1) and $4017 (player 2),
driven by the keyboard. Keys are set in a config file (see controls.cfg).
"""
import configparser
import os

import pygame

# The order the NES reads buttons out: bit 0 of the first read is A, and so on.
BUTTONS = ['a', 'b', 'select', 'start', 'up', 'down', 'left', 'right']

DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'controls.cfg')

# Used when the config file is missing, or for any button it leaves out.
DEFAULT_KEYS = {
    'player1': {'a': 'x', 'b': 'z', 'select': 'right shift', 'start': 'return',
                'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right'},
    'player2': {'a': 'g', 'b': 'f', 'select': 'q', 'start': 'e',
                'up': 'w', 'down': 's', 'left': 'a', 'right': 'd'},
}


def load_keymap(path=None):
    """Read the controls config and return, per player, a list of key codes for each button."""
    path = path or DEFAULT_CONFIG
    config = configparser.ConfigParser()
    if os.path.exists(path):
        config.read(path)
    else:
        print(f"Controls file {path} not found; using default keys.")

    keymap = []
    for player in ('player1', 'player2'):
        section = config[player] if config.has_section(player) else {}
        buttons = []
        for button in BUTTONS:
            names = section.get(button, DEFAULT_KEYS[player][button])
            codes = []
            # a button can have several keys, separated by commas
            for name in (n.strip() for n in names.split(',')):
                if not name:
                    continue
                try:
                    codes.append(pygame.key.key_code(name))
                except ValueError:
                    print(f"Controls: unknown key '{name}' for {player} {button}; ignored.")
            buttons.append(codes)
        keymap.append(buttons)
    return keymap


class Controllers():
    def __init__(self, cpu, config_path=None):
        self.cpu = cpu
        self.keymap = load_keymap(config_path)
        self.strobe = 0
        self.shift = [0, 0]   # buttons not yet read out, per port

    def poll(self, player):
        """Return the 8 button bits for a player from the current keyboard state."""
        keys = pygame.key.get_pressed()
        state = 0
        for bit, codes in enumerate(self.keymap[player]):
            if any(keys[code] for code in codes):
                state |= 1 << bit
        # a real d-pad can't press opposite directions; some games misbehave if both are set
        if state & 0x30 == 0x30:    # up + down
            state &= ~0x30
        if state & 0xC0 == 0xC0:    # left + right
            state &= ~0xC0
        return state

    def latch(self):
        self.shift = [self.poll(0), self.poll(1)]

    def write(self, value):
        """CPU write to $4016: bit 0 high keeps reloading the buttons; going low latches them."""
        self.strobe = value & 1
        self.latch()

    def read(self, port):
        """CPU read from $4016 (port 0) or $4017 (port 1): next button bit."""
        if self.strobe:
            self.latch()          # while strobe is high, every read returns A
        bit = self.shift[port] & 1
        self.shift[port] = (self.shift[port] >> 1) | 0x80   # after 8 reads, returns 1s
        return 0x40 | bit         # upper bits are open bus, usually $40 on hardware
