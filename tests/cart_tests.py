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
import instructions
from disasm import disasm

class TestCartHeaderParsing(unittest.TestCase):
    def testMagic(self):
        cpu = MOS6502.CPU()
        cpu.LoadRom("../smb1.nes")
        self.assertEqual(cpu.rom != None, True)

    def testRomBanks(self):
        cpu = MOS6502.CPU()
        cpu.LoadRom("../smb1.nes")
        self.assertEqual(cpu.rom.numRomBanks, 2)
        self.assertEqual(cpu.rom.numVromBanks, 1)
        #print cpu.rom.vromBanks[0]

        startAddr = cpu.ReadMemWord(cpu.reset)
        firstByte = cpu.ReadMemory(startAddr)
        self.assertEqual(firstByte, 0x78)

    def testDisasmRomBank(self):
        cpu = MOS6502.CPU()
        cpu.LoadRom("../smb1.nes")

        address = cpu.ReadMemWord(cpu.reset)
        code = []
        for i in range(0, 18):
            code.append(cpu.ReadMemory(address))
            address += 1

        disassembly = disasm(code)
        for line in disassembly:
            print line

        self.assertEqual(len(disassembly) == 9, True)

if __name__ == '__main__':
    unittest.main()
