class Register(object):
    def __init__(self, name, bitwidth):
        self.name = name
        self.value = 0
        self.past = [0] # maybe for rewind?
        self.symbVal = [z3.BitVec(self.name, bitwidth)] # maybe for 
                                                        # symbolic
                                                        # execution?
    def GetValue(self):
        return self.value
    
    def SetValue(self, value):
        self.value = value

    def GetCurrentSymb(self):
        return self.symbVal[-1]

    def GetInitialSymb(self):
        return self.symbVal[0]

    def SetInitialSymb(self, value):
        self.symbVal[0] = value


class CPU(object):
    def __init__(self, baseAddress=0x0000):
        self.regs = {  'A': Register('A', bitwidth),
                       'X': Register('X', bitwidth),
                       'Y': Register('Y', bitwidth),
                       'PC': Register('PC', bitwidth * 2),
                       'S': Register('S', bitwidth),
                       'P': Register('P', bitwidth)}

        self.bitwidth = 8 # 1 byte - 8 bits
        self.pcSize = 2 # 2 bytes for PC - 16 bits
        self.memory = []
        self.pastMemory = []
        self.symbMemory = z3Array('mem', z3.BitVecSort(bitwidth), z3.BitVecSort(8))

        self.regs['PC'].SetValue(baseAddress)

        def ReadMemory(self, address): # always read 1 byte
            return self.memory[address]

        def SetMemory(self, address, value): # always write 1 byte
            self.memory[address] = value
            return value

        def GetRegister(name):
            return self.regs[name].GetValue()

        def SetRegister(self, name, value):
            self.regs[name].SetValue(value)
            return value

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

        def CreateOverflowCondition(oldDst, oldSrc):
            op1 = (oldDst & 0x80) >> (self.bitwidth - 1)
            op2 = (oldSrc & 0x80) >> (self.bitwidth - 1)
            ofCond = (((op1 ^ op2) ^ 0x2) & (((op1 + op2) ^ op2) & 0x2)) != 0

            return ofCond

        def CreatecarryCondition(oldDst, oldSrc, subOp):
            if subOp:
                return ((~oldSrc + 1) > oldDst)
            else:
                return ((oldSrc > 0) and (oldDst > (0xff - oldSrc)))

        def UpdateFlags(self, flags, oldDst, oldSrc, newVal, carry, subOp):
            ofCond = self.CreateOverflowCondition(oldDst, oldSrc)
            cfConf = self.CreateCarryCondition(oldDst, oldSrc, subOp)

            validFlags = {  'C': cfCond == True,
                            'Z': newVal == 0,
                            'V': ofCond == True,
                            'N': ((newVal & 0x80) != 0)}

            for flag in flags:
                self.SetFlag(flag, validFlags[flag])


                        
