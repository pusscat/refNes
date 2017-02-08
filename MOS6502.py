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
    def __init__(self, bitwidth, baseAddress):
        self.regs = {  'A': Register('A', bitwidth),
                       'X': Register('X', bitwidth),
                       'Y': Register('Y', bitwidth),
                       'PC': Register('PC', bitwidth * 2),
                       'S': Register('S', bitwidth),
                       'P': Register('P', bitwidth)}

        self.bitwidth = bitwidth
        self.ptrSize = 2 # 2 bytes for PC
        self.memory = []
        self.pastMemory = []
        self.symbMemory = z3Array('mem', z3.BitVecSort(bitwidth), z3.BitVecSort(8))

        if (baseAddress):
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
