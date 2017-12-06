
class PPU():
    def __init__(self, cpu):
        self.cpu = cpu

        self.ctrl       = 0x2000
        self.mask       = 0x2001
        self.status     = 0x2002
        self.oamaddr    = 0x2003
        self.scroll     = 0x2005
        self.addr       = 0x2006
        self.data       = 0x2007

    def stepPPU(self):
        # each step draws one pixel
        pass

    def runPPU(self, numCPUCycles):
        # we get to run 3 PPU cycles for every 1 CPU cycle
        # we step the CPU first, then based on how long the 
        # instruction took, we step the PPU 3x that number
        for i in range(0, numCPUCycles*3):
            self.stepPPU()
