import renderer


class PPU():
    def __init__(self, cpu):
        self.cpu = cpu
        self.renderer = renderer.Renderer()
        self.memory = [0x00] * 0x4000
        self.sprMemory = [0x00] * 0x100

        self.xlines = 256
        self.ylines = 240
        self.screen = [0x00] * (self.xlines * self.ylines)
        self.tube_x = 0
        self.tube_y = 0
        self.hblank = 0
        self.vblank = 0
        self.lastBGWrite = 0

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

        self.dirtyVram      = 0
        self.vramWrites     = [0x00] * (32*30*2)
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
        self.sprAddr        = 3     
        self.sprData        = 4
        self.vramScroll     = 5
        self.vramLatch      = 6
        self.vramData       = 7

        self.scanline = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.latch_lo = 0
        self.latch_hi = 0

    def GetRegister(self, addr):
        return self.registers[addr] 

    def SetRegister(self, addr, value):
        if addr == self.sprAddr:
            self.flipflop1 ^= 1
        if addr == self.sprData:
            addr = self.GetRegister(self.sprAddr)
            self.sprMemory[addr] = value
            self.SetRegister(self.sprAddr, addr+1)
        if addr == self.vramScroll:
            if self.flipflop0 == 0:
                self.scroll_x = value
            else:
                self.scroll_y = value
            self.flipflop0 ^= 1
        if addr == self.vramLatch:
            if self.flipflop1 == 0:
                self.latch_lo = value
            else:
                self.latch_hi = value
            self.flipflop1 ^= 1
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

    def GetBGColor(self):
        return self.memory[self.lastBGWrite]

    def GetVWrite(self):
        return self.GetRegister(self.ctrl1) & (1 << 2)

    def GetVBlank(self):
        return self.GetRegister(self.status) & (1 << 7)

    def GetHit(self):
        return self.GetRegister(self.status) & (1 << 6)

    def GetImgMask(self):
        return self.GetRegister(self.ctrl2) & (1 << 1)

    def GetSprMask(self):
        return self.GetRegister(self.ctrl2) & (1 << 2)

    def GetScreenEnable(self):
        return self.GetRegister(self.ctrl2) & (1 << 3)

    def GetSprEnable(self):
        return self.GetRegister(self.ctrl2) & (1 << 4)

    def GetSprTable(self):
        return self.GetRegister(self.ctrl1) & (1 << 3)

    def GetBGTable(self):
        return self.GetRegister(self.ctrl1) & (1 << 4)

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

    def MarkDirty(self, address):
        self.dirtyVram = 1
        base = (((address % 0x800)/0x400)*(32*30))
        if (address % 0x400) < 0x3c0:
            self.vramWrites[base + (address % 0x499)] = 1
        else:
            i = (address % 0x400) - 0x3c0
            x = (i % 8) * 4
            y = (i / 8) * 4
            for ys in range(y, y+4):
                for xs in range(x, x+4):
                    self.vramWrites[base + xs + (ys * 32)] = 1

    def ReadMemory(self, address):
        (mem, addr) = self.AddressTranslation(address)
        return mem[addr]

    def SetMemory(self, address, value):
        (mem, addr) = self.AddressTranslation(address)
        
        if addr >= 0x3F10 and addr < 0x3F20:
            self.lastBGWrite = addr

        if addr >= self.nameTable0 and addr < self.nameTableEnd:
            self.MarkDirty(address)

        mem[addr] = value & 0xFF
        return value & 0xFF

    def DrawBackground(self):
        pass

    def DrawSprites(self):
        if self.GetSprTable() != 0:
            tableIndex = 0x1000
        else:
            tableIndex = 0x0000

        for i in range(0, 64):
            index = i * 4
            sy = self.sprMemory[index]
            sx = self.sprMemory[index+3]
            fy = (self.sprMemory[index+2]>>7)&1
            fx = (self.sprMemory[index+2]>>6)&1
            pr = (self.sprMemory[index+2]>>5)&1
            hi = self.sprMemory[index+2]&3
            p  = self.sprMemory[index+1]

            for y in range(sy, sy+8):
                for x in range(sx, sx+8):
                    if x > 0 and x < 256 and y > 0 and y < 240:
                        if fx == 0:
                            ho = 7 - (x - sx)
                        else:
                            ho = x-sx
                        if fy == 0:
                            vo = y - sy
                        else:
                            vo = 7 - (y - sy)

                        addr = tableIndex + (p*0x10) + vo
                        c  = ((self.GetMemory(addr)>>ho)&1)
                        c |= ((self.GetMemory(addr+8)>>ho)&1)<<1
                        c |= hi << 2

    def DrawNametable(nameTable, xTile, yTile):
        pass

    def BlankScreen(self):
        self.screen = [0x00] * (self.xlines * self.ylines)

    def UpdateFrame(self):
        if self.GetScreenEnable() != 0:
            self.BlankScreen()
        else:
            self.DrawBackground()

        if self.GetSprEnable() != 0:
            self.DrawSprites()

        if self.dirtyVram != 0 and self.GetScreenEnable() != 0:
            self.dirtyVram = 0
            for i in range(0, (32*30*2)):
                if self.vramWrites[i] != 0:
                    self.DrawNameTable(i/(32*30), i%32, (i%(32*30))/32)
                    self.vramWrites[i] = 0


    def stepPPU(self):
        # each step draws one pixel
        self.hblank = 0
        self.UpdateFrame()

        self.renderer.Update(self.screen, self.tube_x, self.tube_y)
        self.tube_x += 1
        if self.tube_x == 256:
            self.tube_x = 0
            self.tube_y += 1
            self.hblank = 1
        if self.tube_y == 239:
            self.tube_y = 0
            self.vblank = 1


    def runPPU(self, numCPUCycles):
        # we get to run 3 PPU cycles for every 1 CPU cycle
        # we step the CPU first, then based on how long the 
        # instruction took, we step the PPU 3x that number
        for i in range(0, numCPUCycles*3):
            self.stepPPU()
