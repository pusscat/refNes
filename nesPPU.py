import renderer


class PPU():
    def __init__(self, cpu):
        self.cpu = cpu
        self.renderer = renderer.Renderer(self)
        self.memory = [0x00] * 0x4000
        self.sprMemory = [0x00] * 0x100
        self.nt = [0x00] * (256*240*2)

        self.xlines = 256
        self.ylines = 240
        self.screen = [0x40] * (self.xlines * self.ylines)
        self.tube_x = 0
        self.tube_y = 0
        self.hblank = 0
        self.vblank = 0
        self.lastBGWrite = 0
        self.cyclesPerHBlank = 144
        self.bgIndex = 0x40

        # PPU memory addresses
        self.patternTable0  = 0x0000
        self.patternTable1  = 0x1000
        self.nameTable0     = 0x2000
        self.nameTable1     = 0x2400
        self.nameTable2     = 0x2800
        self.nameTable3     = 0x2C00
        self.nameTableEnd   = 0x3000
        self.paletteIndex   = 0x3F00
        self.paletteBG      = 0x3F10

        self.nameTableSize  = 0x0400

        self.nmi            = 0
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
        #print "Get Register " + hex(addr) + ": " + hex(self.registers[addr])
        return self.registers[addr] 

    def SetRegister(self, addr, value):
        if addr == self.sprAddr:
            self.flipflop1 ^= 1
        if addr == self.sprData:
            addr = self.registers[self.sprAddr]
            self.sprMemory[addr] = value
            self.registers[self.sprAddr]  = addr+1
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


        #print "Set Register " + hex(addr) + ": " + hex(value)
        self.registers[addr] = value & 0xFF
        return value & 0xFF

    def SpriteDMA(self, value):
        for i in range(0, 0x100):
            self.sprMemory[i] = self.cpu.ReadMemory((value << 8)+i)

    def GetVWrite(self):
        return (self.registers[self.status] >> 2) &1

    def GetVBlank(self):
        return (self.registers[self.status] >> 7) &1

    def SetVBlank(self):
        status = self.registers[self.status]
        self.registers[self.status] =  status | 0x80

    def ClearVBlank(self):
        status = self.registers[self.status]
        self.registers[self.status] =  status & 0x7F

    def GetHit(self):
        return (self.registers[self.status] >> 6) &1

    def GetImgMask(self):
        return (self.registers[self.ctrl2] >> 1) &1

    def GetSprMask(self):
        return (self.registers[self.ctrl2] >> 2) &1

    def GetScreenEnable(self):
        return (self.registers[self.ctrl2] >> 3) &1

    def GetSprEnable(self):
        return (self.registers[self.ctrl2] >> 4) &1

    def GetSprTable(self):
        return (self.registers[self.ctrl1] >> 3) &1

    def GetBGTable(self):
        return (self.registers[self.ctrl1] >> 4) &1

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
            self.lastBGWrite = value

        if addr >= self.nameTable0 and addr < self.nameTableEnd:
            self.MarkDirty(address)

        mem[addr] = value & 0xFF
        return value & 0xFF

    def DrawBackground(self):
        q = 0
        for y in range(0, self.ylines):
            ntable = self.ReadMemory(self.nameTable0 + y)
            ry = self.scroll_y + y
            name_y = ry % self.ylines

            rx = self.scroll_x
            for x in range(0, self.xlines):
                name_x = rx % self.xlines
                c = self.nt[name_x + (256 * name_y) + ((256 * 240) * ntable)]
                if c&3 != 0:
                    self.screen[q] = c
                else:
                    self.screen[q] = self.bgIndex
                q += 1
                rx += 1

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
                    if x > 0 and x < self.xlines and y > 0 and y < self.ylines:
                        if fx == 0:
                            ho = 7 - (x - sx)
                        else:
                            ho = x-sx
                        if fy == 0:
                            vo = y - sy
                        else:
                            vo = 7 - (y - sy)

                        addr = tableIndex + (p*0x10) + vo
                        c  = ((self.ReadMemory(addr)>>ho)&1)
                        c |= ((self.ReadMemory(addr+8)>>ho)&1)<<1
                        c |= hi << 2

                        if c & 3 == 0:
                            dat = 0
                        else:
                            dat = self.ReadMemory(self.paletteIndex + c)
                        
                        if dat != 0:
                            if pr == 0:
                                screen[x+(y*self.xlines)] = dat
                            else:
                                if screen[x+(y*self.xlines)] == 0x40:
                                    screen[x+(y*self.xlines)] = dat
                    


    def DrawNametable(nameTable, xTile, yTile):
        if self.GetBGTable != 0:
            tableIndex = 0x1000
        else:
            tableIndex = 0

        for y in range(yTile*8, (yTile*8)+4):
            for x in range(xTile*8, (xTile*8)+4):
                name_x = x/8
                name_7 = y/8

                sx = x%8
                sy = y%8

                addr = (((name_x%32) + (name_y%32) * 32))
                addr += nameTable * 0x400

                p = self.ReadMemory(self.nameTable0 + addr)

                cIndex = tableIndex + (p*16) + sy
                c = (self.ReadMemory(cIndex) >> (7 - sx)) & 1
                c |= (self.ReadMemory(cIndex+8) >> (7 - sx)) << 1

                name_x = x/32
                name_y = y/32
                addr = ((name_x % 8) + ((name_7 % 8) * 8)) + 0x3c0
                addr += nameTable * 0x400

                p = self.ReadMemory(self.nameTable0 + addr)

                name_x = (x / 16) % 2
                name_y = (y / 16) % 2

                c |= ((p >> 2 * (name_x + (name_y << 1))) & 3) << 2
                self.nt[x + (y * self.xlines) + (nameTable * (self.xlines * self.ylines))] = c

    def BlankScreen(self):
        self.screen = [0x00] * (self.xlines * self.ylines)

    def UpdateFrame(self):
        if self.GetScreenEnable() != 0:
            self.BlankScreen()
        else:
            self.DrawBackground()

        #if self.GetSprEnable() != 0:
        self.DrawSprites()

        if self.dirtyVram != 0 and self.GetScreenEnable() != 0:
            self.dirtyVram = 0
            for i in range(0, (32*30*2)):
                if self.vramWrites[i] != 0:
                    self.DrawNameTable(i/(32*30), i%32, (i%(32*30))/32)
                    self.vramWrites[i] = 0


    def stepPPU(self):
        # each step draws one pix, but updates only on hblank
        #self.renderer.Update(self.screen, self.tube_x, self.tube_y)
        self.tube_x += 1
        if self.tube_x == self.xlines:
            self.tube_x = 0
            self.tube_y += 1
            self.hblank = 1
            if self.tube_y < self.ylines:
                self.renderer.Update(self.screen, self.tube_y)
        if self.tube_y == self.ylines:
            self.SetVBlank()
            self.nmi = 1
            self.cpu.nmiFlipFlop = 1
        if self.tube_y == (self.ylines + 21):
            self.tube_y = 0
            self.ClearVBlank()
            self.nmi = 0
            self.cpu.nmiFlipFlop = 1


    def runPPU(self, numCPUCycles):
        # we get to run 3 PPU cycles for every 1 CPU cycle
        # we step the CPU first, then based on how long the 
        # instruction took, we step the PPU 3x that number
        self.UpdateFrame()
        for i in range(0, numCPUCycles*3):
            self.stepPPU()
