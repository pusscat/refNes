import renderer

class PPU():
    def __init__(self, cpu):
        self.cpu = cpu
        self.renderer = renderer.Renderer()
        self.memory = [0x00] * 0x4000
        self.sprMemory = [0x00] * 0x100

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
            self.fourScreen = self.cpu.rom.fourScreen 
        except:
            self.mirrorType = 0
            self.fourScreen = 0

        # shared memory registers, comprising 0x2000 - 0x2007
        # and mirrored to 0x4000 on the main cpu memory
        self.registers = [0x00] * 8
        self.flipflop0 = 0
        self.flipflop1 = 0

        self.ctrl1          = 0
        self.ctrl2          = 1
        self.status         = 2
        self.sprLatch       = 3     
        self.sprData        = 4
        self.vramScroll     = 5
        self.vramLatch      = 6
        self.vramData       = 7

        self.scanline = 0
        self.scroll_x = 0
        self.scroll_y = [0x00] * 240
        self.latch_lo = 0
        self.latch_hi = 0

    def GetRegister(self, addr):
        return self.registers[addr] 

    def SetRegister(self, addr, value):
        if addr == self.sprLatch:
            self.flipflop1 = 0
        if addr == self.sprData:
            newLatch = self.GetRegister(self.sprLatch)+1
            self.SetRegister(self.sprLatch, newLatch)
        if addr == self.vramScroll:
            if self.flipflop0 == 0:
                if value < 240:
                    self.scroll_y[self.scanline] = value
            else:
                self.scroll_x = value
            self.flipflop0 = 1
        if addr == self.vramLatch:
            if self.flipflop1 == 0:
                self.latch_lo = value
            else:
                self.latch_hi = value
            self.flipflop1 = 1
        if addr == self.vramData:
            storAddr = self.latch_lo | (self.latch_hi << 8)
            self.SetMemory(storAddr, value)
            if self.GetVWrite() == 1:
                storAddr += 32
            else:
                storAddr += 1
            self.latch_lo = storAddr & 0xFF
            self.latch_hi = (storAddr >> 8) & 0xFF

        self.registers[addr] = value & 0xFF
        return value & 0xFF

    def SpriteDMA(self, value):
        for i in range(0, 0x100):
            self.sprMemory[i] = self.cpu.ReadMemory[(value << 8)+i]

    def GetVWrite(self):
        return self.GetRegister(self.ctrl1) & (1 << 2)

    def GetVBlank(self):
        return self.GetRegister(self.status) & (1 << 7)

    def GetHit(self):
        return self.GetRegister(self.status) & (1 << 6)

    def AddressTranslation(self, addr):
        if addr < self.nameTable0:  # mapped by mapper in cart
            return self.cpu.mapVMem(addr)

        # adjust for name table mirror
        if addr >= 0x3000 and addr < 0x3F00:
            addr -= 0x1000

        # now if in nametable 2 or 3 mirror 0 or 1 based on the cart
        # dont do mirroring at all if the fourScreen bit is set
        if self.fourScreen == 0:
            if self.mirrorType == 0:     # horizontal
                if addr >= self.nameTable1 and addr < self.nameTable2:
                    addr -= self.nameTableSize
                if addr >= self.nameTable3 and addr < self.nameTableEnd:
                    addr -= self.nameTableSize
            else:                       # vertical
                if addr >= self.nameTable2 and addr < self.nameTable3:
                    addr -= (self.nameTableSize * 2)
                if addr >= self.nameTable3 and addr < self.nameTableEnd:
                    addr -= (self.nameTableSize * 2)

        return (self.memory, addr)

    def ReadMemory(self, address):
        (mem, addr) = self.AddressTranslation(address)
        return mem[addr]

    def SetMemory(self, address, value):
        (mem, addr) = self.AddressTranslation(address)
        mem[addr] = value & 0xFF
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
