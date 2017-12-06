import sys

import MOS6502
from disasm import disasm

def cpuInfo(cpu):
    lines = ''
    lines +=  "A: " + hex(cpu.GetRegister('A')) + "\t"
    lines +=  "X: " + hex(cpu.GetRegister('X')) + "\t"
    lines +=  "Y: " + hex(cpu.GetRegister('Y')) + "\n"
    lines +=  "S: " + hex(cpu.GetRegister('S')) + "\t"
    lines +=  "PC: " + hex(cpu.GetRegister('PC')) + "\t"
    if cpu.GetFlag('C') != 0: 
        lines += "C "
    if cpu.GetFlag('Z') != 0: 
        lines += "Z "
    if cpu.GetFlag('I') != 0: 
        lines += "I "
    if cpu.GetFlag('V') != 0: 
        lines += "V "
    if cpu.GetFlag('N') != 0: 
        lines += "N"

    return lines

def debugLoop(cpu):
    while (1):
        sys.stdout.write("> ")
        cmd = sys.stdin.readline().strip()
        if cmd == 'quit':
            return
        if cmd == 'step' or cmd == 's':
            nextAddr = cpu.step()
            mem = cpu.GetMemory(nextAddr, 3)
            print hex(nextAddr) + " " + disasm(mem, 1)[0]

        if cmd == 'i':
            print cpuInfo(cpu)

        if cmd == 'run' or cmd == 'r':
            cpu.runToBreak()

cpu = MOS6502.CPU()
cpu.LoadRom("smb1.nes")
debugLoop(cpu)

