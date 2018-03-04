import MOS6502
import instructions
import code

def disasm(memory, maxLines=0, address=-1):
    index = 0
    lines = []

    while index < len(memory):
        opcode = memory[index]
        if opcode not in instructions.instructions.keys():
            print "Undefined opcode: " + hex(opcode)
            code.interact(local=locals())

        currInst = instructions.instructions[memory[index]]
        
        if address > 0:
            line = format(address+index, '04x') + ": "
        else:
            line = ''
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
