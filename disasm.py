import MOS6502
import instructions

def disasm(memory, maxLines=0):
    index = 0
    lines = []

    while index < len(memory):
        currInst = instructions.instructions[memory[index]]
        
        line = currInst.mnem + " "
        line += currInst.operType + " "
        if currInst.size > 1:
            if 'ABS' in currInst.operType:
                line += hex(memory[index+1] + (memory[index+2] << 8))
            else:    
                for i in range(1, currInst.size):
                    line += hex(memory[index + i]) + " "

        lines.append(line)
        index += currInst.size
        
        if maxLines != 0 and len(lines) == maxLines:
            return lines

    return lines
