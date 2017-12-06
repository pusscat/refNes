import sys

import MOS6502

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
        input = sys.stdin.readline()
        if input.strip() == 'quit':
            return
        if input.strip() == 'step':
            cpu.step()
        if input.strip() == 'i':
            print cpuInfo(cpu)

cpu = MOS6502.CPU()
cpu.LoadRom("smb1.nes")
debugLoop(cpu)

