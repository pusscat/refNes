import MOS6502
import instructions

def disasm(memory):
    index = 0
    lines = []

    while index < len(memory):
        currInst = instructions.instructions[memory[index]]
        
        line = currInst.mnem + " "
        line += currInst.operType + " "
        if currInst.size > 1:
            for i in range(1, currInst.size):
                line += hex(memory[i]) + " "

        lines.append(line)
        index += currInst.size

    return lines

code = [0x78, 0xD8, 0xA9, 0x10, 0x8D, 0x00, 0x20, 0xA2]
print disasm(code)
