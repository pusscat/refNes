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
    def testAdcImm(self):
        cpu = MOS6502.CPU()
        instruction_bytes = [0x69, 0xA1] # ADC 0x41
        cpu.set_memory_debug(cpu.get_register('PC')+1, instruction_bytes)

        cpu.set_register('A', 0xA1)
        cpu.step()

        self.assertEqual(cpu.get_register('A'), 0x42)
        self.assertEqual(cpu.get_flag('C'), 1)

if __name__ == '__main__':
    unittest.main()

