import MOS6502
import instructions

def disasm(memory, maxLines=0, address=-1):
    index = 0
    lines = []

    while index < len(memory):
        opcode = memory[index]
        if address >= 0:
            prefix = format(address+index, '04x') + ": "
        else:
            prefix = ''

        currInst = instructions.instructions.get(opcode)
        # Unknown opcode (data, or a start address in the middle of an
        # instruction): show the byte as data and move on one byte.
        if currInst is None:
            lines.append(prefix + ".db " + hex(opcode))
            index += 1
            if maxLines != 0 and len(lines) == maxLines:
                return lines
            continue

        # operand bytes run past the end of what we were given: stop here
        if index + currInst.size > len(memory):
            break

        line = prefix
        line += currInst.mnem + " "
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
