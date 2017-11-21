import importlib
import os
import sys
import unittest
import code
import struct

code_path = os.path.dirname(__file__)
code_path = os.path.join(code_path, os.pardir)
sys.path.append(code_path)

import instructions
import MOS6502

class TestADC(unittest.TestCase):
    def testAcdImm(self):
        cpu = MOS6502.CPU()
        instruction_bytes = [0x69, 0xA1] # ADC 0x41
        #cpu.SetMemory(0, instruction_bytes[0])
        #cpu.SetMemory(1, instruction_bytes[1])
        cpu.initMemory(0, instruction_bytes)

        cpu.SetPC(0)
        cpu.SetRegister('A', 0xA1)
        cpu.step()

        self.assertEqual(cpu.GetRegister('A'), 0x42)
        self.assertEqual(cpu.GetFlag('C'), 1)

if __name__ == '__main__':
    unittest.main()

