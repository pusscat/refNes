import importlib
import os
import sys
import unittest
import code
import struct

code_path = os.path.dirname(__file__)
code_path = os.path.join(code_path, os.pardir)
sys.path.append(code_path)

import MOS6502

class TestCartHeaderParsing(unittest.TestCase):
    def testMagic(self):
        cpu = MOS6502.CPU()
        cpu.loadRom("../smb1.nes")
        self.assertEqual(cpu.rom != None, True)

    def testRomBanks(self):
        cpu = MOS6502.CPU()
        cpu.loadRom("../smb1.nes")
        self.assertEqual(cpu.rom.numRomBanks, 2)
        self.assertEqual(cpu.rom.numVromBanks, 1)

if __name__ == '__main__':
    unittest.main()
