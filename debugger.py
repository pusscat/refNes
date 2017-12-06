import sys
import struct

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

def stepCPU(cpu):
    nextAddr = cpu.step()
    mem = cpu.GetMemory(nextAddr, 3)
    print hex(nextAddr) + " " + disasm(mem, 1)[0]

def getArg(cpu, argString):
    # if a register, get the value
    registers = {   
            'A': cpu.GetRegister('A'),
            'X': cpu.GetRegister('X'),
            'Y': cpu.GetRegister('Y'),
            'PC': cpu.GetRegister('PC'),
            'S': cpu.GetRegister('S') }
    for key in registers:
        if key in argString:
            return register[key]

    # if a length arg, remove the L and cast to hex int
    if argString[0] == 'L':
        return int(argString[1:], 16)

    # if a number, its always hex
    return int(argString, 16)

def printMemLine(lineAddr, dataLine):
    sys.stdout.write(hex(lineAddr & 0xFFFF) + ": ")
    for byte in dataLine:
        sys.stdout.write(format(byte & 0xFF, '02x') + " ")
    sys.stdout.write("\n")
'''    
    sys.stdout.write("\t |")
    for byte in dataLine:
        print byte
        sys.stdout.write(format(byte, 'c'))
    print "|"
'''

def displayMemory(cpu, cmdList):
    if len(cmdList) < 2:
        print "display memory: d <address> [opt: 'L'ength]"
        return

    lineLen = 0x10
    length = 0x40 # default length to show
    address = getArg(cpu, cmdList[1])
    if len(cmdList) > 2:
        length = getArg(cpu, cmdList[2])

    index = 0
    while index < length:
        dataLine = []
        lineAddr = address + index
        for i in range(0, lineLen):
            dataLine.append(cpu.ReadMemory(address + index))
            index += 1
            if index == length:
                printMemLine(lineAddr, dataLine)
                return
        printMemLine(lineAddr, dataLine)

def handleCmd(cpu, cmdString):
    cmdList = cmdString.split()
    cmd = cmdList[0]

    if cmd == 'step' or cmd == 's':
        stepCPU(cpu)

    if cmd == 'i':
        print cpuInfo(cpu)

    if cmd == 'go' or cmd == 'g':
        cpu.runToBreak()

    if cmd == 'display' or cmd == 'd':
        displayMemory(cpu, cmdList)



def debugLoop(cpu):
    cmd = ''
    while (1):
        sys.stdout.write("> ")
        lastCmd = cmd
        cmd = sys.stdin.readline().strip()
        if cmd == '':
            cmd = lastCmd
        if cmd == 'quit':
            return
        handleCmd(cpu, cmd)

cpu = MOS6502.CPU()
cpu.LoadRom("smb1.nes")
debugLoop(cpu)

