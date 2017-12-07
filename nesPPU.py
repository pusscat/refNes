
class PPU():
    def __init__(self, cpu):
        self.cpu = cpu

        # shared memory registers, comprising 0x2000 - 0x2007
        # and mirrored to 0x4000 on the main cpu memory
        self.registers = [0x00] * 8

        self.ctrl       = 0
        self.mask       = 1
        self.status     = 2
        self.oamaddr    = 3
        self.oamdata    = 4
        self.scroll     = 5
        self.addr       = 6
        self.data       = 7

        # General PPU registers
        self.nameTable      = 0         # 0 - 3
        self.genInterrupts  = False     # Do we NMI
        self.vramIncrement  = 0         # how far do we inc vram per read

        # Background registers
        self.bgTileAddr     = 0         # background tileset address
        self.clipBG         = False     # hide left 8 pixels?
        self.enableBG       = False     # render background?

        # Sprite registers
        self.clipSprites    = False     # hide sprites in left 8 pixels
        self.enableSprites  = False     # render sprites?
        self.spHeight       = 8         # can be 8 or 16 pixels
        self.spTileAddr     = 0         # sprite tileset address

        

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
