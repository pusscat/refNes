import instructions

class Register(object):
    def __init__(self, name, bitwidth):
        self.name = name
        self.value = 0
        self.past = [0] # maybe for rewind?
        #self.symbVal = [z3.BitVec(self.name, bitwidth)] # maybe for 
                                                        # symbolic
                                                        # execution?
    def GetValue(self):
        return self.value
    
    def SetValue(self, value):
        self.value = value & 0xFF

    def GetCurrentSymb(self):
        return self.symbVal[-1]

    def GetInitialSymb(self):
        return self.symbVal[0]

    def SetInitialSymb(self, value):
        self.symbVal[0] = value


class CPU(object):
    def __init__(self, baseAddress=0x0000, stackAddress=0x1FF):
        self.bitwidth = bitwidth = 8 # 1 byte - 8 bits
        self.regs = {  'A': Register('A', bitwidth),
                       'X': Register('X', bitwidth),
                       'Y': Register('Y', bitwidth),
                       'PC': Register('PC', bitwidth * 2),
                       'S': Register('S', bitwidth),
                       'P': Register('P', bitwidth)}

        self.pcSize = 2 # 2 bytes for PC - 16 bits
        self.memory = 0x10000 * [0x00]
        self.pastMemory = []
        #self.symbMemory = z3Array('mem', z3.BitVecSort(bitwidth), z3.BitVecSort(8))

        self.regs['PC'].SetValue(baseAddress)
        self.regs['S'].SetValue(stackAddress)

        self.cycle = 0

    def ReadMemory(self, address): # always read 1 byte
        return self.memory[address]

    def ReadRelPC(self, offset):
        return self.memory[self.GetRegister('PC')+offset]

    def SetMemory(self, address, value): # always write 1 byte
        self.memory[address] = value & 0xFF
        return value

    def initMemory(self, address, values): # write 1 at a time
        for value in values:
            self.SetMemory(address, value)
            address = address + 1

    def GetRegister(self, name):
        return self.regs[name].GetValue()

    def SetPC(self, value):
        self.regs['PC'].SetValue(value & 0xFFFF)

    def SetRegister(self, name, value):
        self.regs[name].SetValue(value & 0xFF)
        return value & 0xFF

    def PushByte(self, value):
        regS = self.GetRegister('S')
        stackAddr = 0x0100 + regS
        self.SetMemory(stackAddr, value)
        self.SetRegister('S', regS-1)
        return stackAddr

    def PushWord(self, value):
        self.PushByte((value & 0xFF00) >> 8)
        return self.PushByte(value & 0xFF)
        

    def PopByte(self):
        regS = self.GetRegister('S')
        stackAddr = 0x0100 + regS
        value = self.ReadMemory(stackAddr)
        self.SetRegister('S', regS+1)
        return value

    def PopWord(self):
        return self.PopByte() + (self.PopByte() << 8)

    def SetFlag(self, flagName, value):
        flags = {   'C':0,  # Carry
                    'Z':1,  # Zero
                    'I':3,  # Interrupt mask
                    'V':6,  # Overflow
                    'N':7}  # Negative

        flagReg = self.GetRegister('P')
        if value == 1:
            newFlag = flagReg | 1 << flags[flagName]
        else:
            newFlag = flagReg & ~(1 << flags[flagName])

        self.SetRegister('P', newFlag)

    def CreateOverflowCondition(self, oldDst, oldSrc):
        op1 = (oldDst & 0x80) >> (self.bitwidth - 1)
        op2 = (oldSrc & 0x80) >> (self.bitwidth - 1)
        ofCond = (((op1 ^ op2) ^ 0x2) & (((op1 + op2) ^ op2) & 0x2)) != 0

        return ofCond

    def CreateCarryCondition(self, oldDst, oldSrc, subOp):
        if subOp:
            return ((~oldSrc + 1) & 0xFF > oldDst)
        else:
            return ((oldSrc > 0) and (oldDst > (0xff - oldSrc)))

    def UpdateFlags(self, flags, oldDst, oldSrc, newVal, subOp):
        ofCond = self.CreateOverflowCondition(oldDst, oldSrc)
        cfCond = self.CreateCarryCondition(oldDst, oldSrc, subOp)

        validFlags = {  'C': cfCond == True,
                        'Z': newVal == 0,
                        'V': ofCond == True,
                        'N': ((newVal & 0x80) != 0)}

        for flag in flags:
            self.SetFlag(flag, validFlags[flag])
    
    def GetFlag(self, flagName):
        flags = {   'C':0,
                    'Z':1,
                    'I':3,
                    'V':6,
                    'N':7}
        flagsReg = self.GetRegister('P')
        flagIndex = flags[flagName]
        return ((flagsReg & (1 << flagIndex)) != 0)


    def incPC(self, size):
        currentPC = self.GetRegister('PC')
        self.SetRegister('PC', currentPC + size)

    def incCycles(self, cycles):
        self.cycle += cycles

    def step(self):
        opCode = self.ReadMemory(self.GetRegister('PC'))
        instruction = instructions.instructions[opCode]
        instruction.execute(self)
        self.cycle += instruction.cycles

        return self

                    
