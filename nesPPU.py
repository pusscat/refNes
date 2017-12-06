
class PPU():
    def __init__(self, cpu):
        self.cpu = cpu

    def stepPPU():
        numCycles = 0

        return numCycles

    def runPPU(numCPUCycles):
        # we get to run 3 PPU cycles for every 1 CPU cycle
        # we step the CPU first, then based on how long the 
        # instruction took, we step the PPU 3x that number
        numCycles = 0
        while numCycles < (numCPUCycles * 3):
            numCycles += stepPPU()
