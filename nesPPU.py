
class PPU():
    def __init__(self, cpu):
        self.cpu = cpu

        self.registers = [0x00] * 8

        self.ctrl       = 0
        self.mask       = 1
        self.status     = 2
        self.oamaddr    = 3
        self.oamdata    = 4
        self.scroll     = 5
        self.addr       = 6
        self.data       = 7


    def ReadPPURegister(self, addr):
        addr -= 0x2000
        return self.registers[addr] 

    def SetPPURegister(self, addr, value):
        addr -= 0x2000
        self.registers[addr] = value & 0xFF
        return value & 0xFF

    def stepPPU(self):
        # each step draws one pixel
        pass

    def runPPU(self, numCPUCycles):
        # we get to run 3 PPU cycles for every 1 CPU cycle
        # we step the CPU first, then based on how long the 
        # instruction took, we step the PPU 3x that number
        for i in range(0, numCPUCycles*3):
            self.stepPPU()
