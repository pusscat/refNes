
class PPU():
    def __init__(self, cpu):
        self.cpu = cpu

        self.ctrl       = 0
        self.mask       = 0
        self.status     = 0
        self.oamaddr    = 0
        self.oamdata    = 0
        self.scroll     = 0
        self.addr       = 0
        self.data       = 0

        self.regAddrs = {
                    0 : 'ctrl',
                    1 : 'mask',
                    2 : 'status',
                    3 : 'oamaddr',
                    4 : 'oamdata',
                    5 : 'scroll',
                    6 : 'addr',
                    7 : 'data'}


    def ReadPPURegister(self, addr):
        addr -= 0x2000
        return getattr(self, self.regAddrs[addr])

    def SetPPURegister(self, addr, value):
        addr -= 0x2000
        setattr(self, self.regAddrs[addr], value & 0xFF)
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
