import instructions
from nesPPU import PPU
from nesMemory import Memory
from nesCart import Rom

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
        self.value = value

    def GetCurrentSymb(self):
        return self.symbVal[-1]

    def GetInitialSymb(self):
        return self.symbVal[0]

    def SetInitialSymb(self, value):
        self.symbVal[0] = value


class CPU(object):
    def __init__(self, baseAddress=0x8000):
        self.bitwidth = bitwidth = 8 # 1 byte - 8 bits
        self.regs = {  'A': Register('A', bitwidth),
                       'X': Register('X', bitwidth),
                       'Y': Register('Y', bitwidth),
                       'PC': Register('PC', bitwidth * 2),
                       'S': Register('S', bitwidth),
                       'P': Register('P', bitwidth)}

        self.pcSize = 2 # 2 bytes for PC - 16 bits
        self.memory = Memory()
        self.pastMemory = []
        #self.symbMemory = z3Array('mem', z3.BitVecSort(bitwidth), z3.BitVecSort(8))

        self.regs['PC'].SetValue(0)
        self.regs['S'].SetValue(0)

        self.cycle = 0

        self.stackBase  = 0x0100
        self.ppuMem     = 0x2000
        self.apuMem     = 0x4000
        self.programRom = 0x8000
        self.nmi        = 0xFFFA
        self.reset      = 0xFFFC
        self.irqBrk     = 0xFFFE
        self.frameIrq   = 0x4017
        self.channels   = 0x4015

        self.rom = None
        self.ppu = PPU(self)

    def ClearMemory(self):
        self.memory.ClearMemory()

    def Reset(self):
        # https://wiki.nesdev.com/w/index.php/CPU_power_up_state 
        start = self.ReadMemWord(self.reset)
        self.SetPC(start)
        self.SetRegister('S', 0xFD)
        self.SetRegister('P', 0x00)
        self.ClearMemory()

    def mapMem(self, address):
        return self.rom.mapMem(self, address)

    def LoadRom(self, romPath):
        self.rom = Rom(romPath, self)
        return self.rom

    def ReadMemory(self, address): # always read 1 byte
        return self.memory.ReadMemory(self, address)

    def ReadMemWord(self, address):
        value  = self.ReadMemory(address)
        value += self.ReadMemory(address + 1) << 8 
        return value

    def ReadRelPC(self, offset):
        return self.ReadMemory(self.GetRegister('PC')+offset)

    def SetMemory(self, address, value): # always write 1 byte
        #self.memory[address] = value & 0xFF
        return self.memory.SetMemory(self, address, value)

    def initMemory(self, address, values): # write 1 at a time
        for value in values:
            self.SetMemory(address, value)
            address = address + 1

    def GetMemory(self, address, size):
        mem = []
        for i in range(0, size):
            mem.append(self.ReadMemory(address+i))

        return mem

    def GetRegister(self, name):
        return self.regs[name].GetValue()

    def SetPC(self, value):
        self.regs['PC'].SetValue(value & 0xFFFF)
        return value & 0xFFFF

    def SetRegister(self, name, value):
        self.regs[name].SetValue(value & 0xFF)
        return value & 0xFF

    def PushByte(self, value):
        regS = self.GetRegister('S') - 1
        self.SetMemory(regS + self.stackBase, value)
        self.SetRegister('S', regS)
        return regS + self.stackBase

    def PushWord(self, value):
        self.PushByte((value & 0xFF00) >> 8)
        return self.PushByte(value & 0xFF)
        

    def PopByte(self):
        regS = self.GetRegister('S')
        value = self.ReadMemory(regS + self.stackBase)
        self.SetRegister('S', regS+1)
        return value

    def PopWord(self):
        return self.PopByte() + (self.PopByte() << 8)

    def SetFlag(self, flagName, value):
        flags = {   'C':0,  # Carry
                    'Z':1,  # Zero
                    'I':2,  # Interrupt mask
                    'D':3,  # Decimal
                    'B':4,  # Break
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
                    'I':2,
                    'D':3,
                    'B':4,
                    'V':6,
                    'N':7}
        flagsReg = self.GetRegister('P')
        flagIndex = flags[flagName]
        return ((flagsReg & (1 << flagIndex)) != 0)


    def incPC(self, size):
        currentPC = self.GetRegister('PC')
        self.SetPC(currentPC + size)

    def incCycles(self, cycles):
        self.cycle += cycles

    def step(self):
        addr = self.GetRegister('PC')
        opCode = self.ReadMemory(addr)
        try:
            instruction = instructions.instructions[opCode]
        except:
            print "Bad Instruction: " + hex(opCode) + " @ " + hex(addr)
            self.SetFlag('B', 1)
            return addr
        instruction.execute(self)
        self.cycle += instruction.cycles

        return self.GetRegister('PC')

    def runToBreak(self):
        while self.GetFlag('B') == 0:
            self.step()

                    
