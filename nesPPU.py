
class PPU():
    def __init__(self, cpu):
        self.cpu = cpu
        self.memory = [0x00] * 0x4000
        self.oamMemory [0x00] * 0x100

        # PPU memory addresses
        self.patternTable0  = 0x0000
        self.patternTable1  = 0x1000
        self.nameTable0     = 0x2000
        self.nameTable1     = 0x2400
        self.nameTable2     = 0x2800
        self.nameTable3     = 0x2C00
        self.nameTableEnd   = 0x3000
        self.paletteIndex   = 0x3F00

        self.nameTableSize  = 0x0400
        try:
            self.mirrorType = self.cpu.rom.mirroring # 0 horiz - 1 vert
        except:
            self.mirrorType = 0

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

    def AddressTranslation(self, addr):
        # adjust for name table mirror
        if addr >= 0x3000 and addr < 0x3F00:
            addr -= 0x1000

        # now if in nametable 2 or 3 mirror 0 or 1 based on the cart
        # dont do mirroring at all if the fourScreen bit is set
        if self.cpu.rom.fourScreen  == 0:
            if self.mirrorType = 0:     # horizontal
                if addr >= self.nameTable1 and addr < self.nameTable2:
                    addr -= self.nameTableSize
                if addr >= self.nameTable3 and addr < self.nameTableEnd:
                    addr -= self.nameTableSize
            else:                       # vertical
                if addr >= self.nameTable2 and addr < self.nameTable3:
                    addr -= (self.nameTableSize * 2)
                if addr >= self.nameTable3 and addr < self.nameTableEnd:
                    addr -= (self.nameTableSize * 2)




    def stepPPU(self):
        # each step draws one pixel
        pass

    def runPPU(self, numCPUCycles):
        # we get to run 3 PPU cycles for every 1 CPU cycle
        # we step the CPU first, then based on how long the 
        # instruction took, we step the PPU 3x that number
        for i in range(0, numCPUCycles*3):
            self.stepPPU()
