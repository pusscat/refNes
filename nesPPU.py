import renderer

# NTSC timing, in PPU dots (3 per CPU cycle)
DOTS_PER_LINE = 341
LINES_PER_FRAME = 262
VISIBLE_LINES = 240
VBLANK_LINE = 241
PRERENDER_LINE = 261
LINE_RENDER_DOT = 257   # by this dot the visible part of a line has been drawn


class PPU():
    def __init__(self, cpu):
        self.cpu = cpu
        self.renderer = renderer.Renderer(self, cpu.render_scale)
        self.memory = [0x00] * 0x4000
        self.sprMemory = [0x00] * 0x100

        self.xlines = 256
        self.ylines = 240
        # NES color numbers (0x00-0x3F); 0x40 until a line is first drawn
        self.screen = [0x40] * (self.xlines * self.ylines)

        # beam position
        self.scanline = 0
        self.dot = 0
        self.line_done = False   # visible-line work for the current line has run
        self.frame = 0

        # PPU memory addresses
        self.patternTable0  = 0x0000
        self.patternTable1  = 0x1000
        self.nameTable0     = 0x2000
        self.nameTable1     = 0x2400
        self.nameTable2     = 0x2800
        self.nameTable3     = 0x2C00
        self.nameTableEnd   = 0x3000
        self.paletteIndex   = 0x3F00   # background palettes
        self.paletteSprite  = 0x3F10   # sprite palettes

        self.nameTableSize  = 0x0400

        self.nmi            = 0
        try:
            self.mirrorType = self.cpu.rom.mirroring # 0 horiz - 1 vert
            self.fourScreen = self.cpu.rom.fourScreen
        except:
            self.mirrorType = 0
            self.fourScreen = 0

        # where each of the 4 logical nametables lives in self.memory (same
        # mirroring as address_translation, precomputed for the renderer)
        if self.fourScreen:
            self.nt_base = [0x2000, 0x2400, 0x2800, 0x2C00]
        elif self.mirrorType == 0:      # horizontal
            self.nt_base = [0x2000, 0x2000, 0x2800, 0x2800]
        else:                           # vertical
            self.nt_base = [0x2000, 0x2400, 0x2000, 0x2400]

        # sprites on each scanline, rebuilt only after OAM or sprite size changes
        self.sprite_lines = None
        self.sprite_lines_height = 0

        # shared memory registers, comprising 0x2000 - 0x2007
        # and mirrored to 0x4000 on the main cpu memory
        self.registers = [0x00] * 8

        self.ctrl1          = 0
        self.ctrl2          = 1
        self.status         = 2
        self.sprAddr        = 3
        self.sprData        = 4
        self.vramScroll     = 5
        self.vramLatch      = 6
        self.vramData       = 7

        # Internal scroll/address registers (see nesdev "PPU scrolling"):
        #   v: current VRAM address   t: temporary address (top-left of the screen)
        #   both laid out as  yyy NN YYYYY XXXXX  (fine Y, nametable, coarse Y, coarse X)
        #   fine_x: fine X scroll (0-7)   w: write toggle shared by $2005/$2006
        self.v = 0
        self.t = 0
        self.fine_x = 0
        self.w = 0
        self.read_buffer = 0   # $2007 reads below the palette return the previous byte

        # pattern data decoded once into pixel values; see decode_chr
        self.chr_rows = [None] * (512 * 8)
        # background tile rows already converted to colors, per (tile row, palette);
        # thrown away whenever the palette or pattern data changes
        self.bg_cache = [None] * (512 * 8 * 4)
        self.bg_cache_dirty = False
        if getattr(self.cpu, 'rom', None) is not None:
            self.decode_chr()

    def get_pc(self):
        return self.cpu.get_register('PC')

    # ---- CPU-facing registers ($2000-$2007) ----

    def get_register(self, addr):
        if addr == self.status:
            value = self.registers[self.status]
            self.w = 0            # reading $2002 resets the $2005/$2006 toggle
            self.clear_vblank()   # and clears the vblank flag, as on hardware
            return value
        if addr == self.sprData:
            return self.sprMemory[self.registers[self.sprAddr]]
        if addr == self.vramData:
            return self.read_vram_data()
        return self.registers[addr]

    def set_register(self, addr, value):
        value &= 0xFF
        if addr == self.ctrl1:
            nmi_was_on = self.get_nmi_mask()
            self.registers[addr] = value
            self.t = (self.t & ~0x0C00) | ((value & 3) << 10)
            # turning NMI on during vblank raises one right away
            if not nmi_was_on and self.get_nmi_mask() and self.get_vblank():
                self.raise_nmi()
        elif addr == self.sprData:
            oam_addr = self.registers[self.sprAddr]
            self.sprMemory[oam_addr] = value
            self.registers[self.sprAddr] = (oam_addr + 1) & 0xFF
            self.sprite_lines = None
        elif addr == self.vramScroll:
            if self.w == 0:       # first write: X scroll
                self.t = (self.t & ~0x001F) | (value >> 3)
                self.fine_x = value & 7
            else:                 # second write: Y scroll
                self.t = (self.t & ~0x73E0) | ((value & 7) << 12) | ((value >> 3) << 5)
            self.w ^= 1
        elif addr == self.vramLatch:
            if self.w == 0:       # first write: high byte (6 bits; address is 14 bits)
                self.t = (self.t & 0x00FF) | ((value & 0x3F) << 8)
            else:                 # second write: low byte, then t is copied to v
                self.t = (self.t & 0x7F00) | value
                self.v = self.t
            self.w ^= 1
        elif addr == self.vramData:
            self.set_memory(self.v & 0x3FFF, value)
            self.increment_v()

        if addr not in (self.status, self.sprData):
            self.registers[addr] = value
        # the low 5 bits of $2002 show the last value written to any PPU register
        self.registers[self.status] = (self.registers[self.status] & 0xE0) | (value & 0x1F)
        return value

    def read_vram_data(self):
        addr = self.v & 0x3FFF
        if addr >= 0x3F00:
            # palette reads are immediate; the buffer gets the nametable byte "under" it
            value = self.read_memory(addr)
            self.read_buffer = self.read_memory(addr - 0x1000)
        else:
            value = self.read_buffer
            self.read_buffer = self.read_memory(addr)
        self.increment_v()
        return value

    def increment_v(self):
        self.v = (self.v + (32 if self.get_vwrite() else 1)) & 0x7FFF

    def sprite_dma(self, value):
        oam_addr = self.registers[self.sprAddr]
        for i in range(0, 0x100):
            self.sprMemory[(oam_addr + i) & 0xFF] = self.cpu.read_memory((value << 8)+i)
        self.sprite_lines = None

    def raise_nmi(self):
        self.nmi = 1
        self.cpu.nmi_flipflop = 1

    # ---- register bit helpers ----

    def get_vwrite(self):
        return (self.registers[self.ctrl1] >> 2) & 1

    def get_vblank(self):
        return (self.registers[self.status] >> 7) & 1

    def set_vblank(self):
        self.registers[self.status] |=  0x80

    def clear_vblank(self):
        self.registers[self.status] &= 0x7F

    def get_nmi_mask(self):
        return (self.registers[self.ctrl1] >> 7) & 1

    def get_hit(self):
        return (self.registers[self.status] >> 6) &1

    def get_img_mask(self):
        return (self.registers[self.ctrl2] >> 1) &1

    def get_spr_mask(self):
        return (self.registers[self.ctrl2] >> 2) &1

    def get_screen_enable(self):
        return (self.registers[self.ctrl2] >> 3) &1

    def get_spr_enable(self):
        return (self.registers[self.ctrl2] >> 4) &1

    def get_spr_table(self):
        return (self.registers[self.ctrl1] >> 3) &1

    def get_bg_table(self):
        return (self.registers[self.ctrl1] >> 4) &1

    def get_spr_height(self):
        return 16 if (self.registers[self.ctrl1] >> 5) & 1 else 8

    def rendering_enabled(self):
        return (self.registers[self.ctrl2] & 0x18) != 0

    # ---- PPU memory ----

    def address_translation(self, addr):
        addr &= 0x3FFF
        if addr < self.nameTable0:  # mapped by mapper in cart
            return self.cpu.map_vmem(addr)

        # palette: $3F20-$3FFF repeat $3F00-$3F1F, and the sprite palettes'
        # color 0 entries ($3F10/14/18/1C) are the background ones ($3F00/04/08/0C)
        if addr >= self.paletteIndex:
            addr = self.paletteIndex | (addr & 0x1F)
            if addr & 0x13 == 0x10:
                addr -= 0x10
            return (self.memory, addr)

        # adjust for name table mirror
        if addr >= 0x3000:
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

    def read_memory(self, address):
        (mem, addr) = self.address_translation(address)
        return mem[addr]

    def set_memory(self, address, value):
        (mem, addr) = self.address_translation(address)
        try:
            mem[addr] = value & 0xFF
            if (address & 0x3FFF) < 0x2000:     # pattern data (CHR RAM): re-decode the row
                self.decode_chr_row(address & 0x1FF7)
            elif addr >= self.paletteIndex:     # palette change: cached colors are stale
                self.bg_cache_dirty = True
            return value & 0xFF
        except IndexError as e:
            self.cpu.paused = True
            self.cpu.pause_reason = f"PPU OOB write @ {hex(addr)} ({hex(value&0xFF)})"
            breakpoint()
            return 0x0

    def palette_ram(self):
        """The 32 palette entries, as a list indexed 0x00-0x1F."""
        # Writes go through address_translation, so the mirrored entries
        # ($3F10/14/18/1C) are never stored; nothing here reads them.
        return [c & 0x3F for c in self.memory[0x3F00:0x3F20]]

    # ---- pattern (CHR) decoding ----
    # chr_rows[(pattern_addr >> 4) * 8 + row] is that tile row as 8 pixel
    # values (0-3), left to right. 512 tiles: $0000-$0FFF then $1000-$1FFF.

    def decode_chr_row(self, addr):
        """Decode one tile row; addr is the row's first-plane byte ($0000-$1FF7, bit 3 clear)."""
        lo = self.read_memory(addr)
        hi = self.read_memory(addr + 8)
        self.chr_rows[((addr >> 4) << 3) | (addr & 7)] = \
            [((lo >> b) & 1) | (((hi >> b) & 1) << 1) for b in range(7, -1, -1)]
        self.bg_cache_dirty = True

    def decode_chr(self):
        """Decode all pattern data. Call again after a mapper switches CHR banks."""
        for tile in range(512):
            for row in range(8):
                self.decode_chr_row(tile * 16 + row)

    # ---- drawing ----

    def render_line(self, y):
        """Draw scanline y (background, then sprites) into self.screen."""
        mask = self.registers[self.ctrl2]
        pal = self.palette_ram()
        backdrop = pal[0]

        if mask & 0x08:
            # bg_opaque: per-pixel background value (0 = transparent), used for
            # sprite priority and sprite 0 hit
            line, bg_opaque = self.render_background_line(pal)
            if not mask & 0x02:     # background hidden in the leftmost 8 pixels
                line[0:8] = [backdrop] * 8
                bg_opaque[0:8] = [0] * 8
        else:
            line = [backdrop] * 256
            bg_opaque = [0] * 256
        if mask & 0x10:
            self.render_sprite_line(y, line, bg_opaque, pal,
                                    clip_left=not mask & 0x04,
                                    check_hit=bool(mask & 0x08))

        self.screen[y*256:(y+1)*256] = line

    def render_background_line(self, pal):
        """Return (colors, pixel values) for the 256 background pixels of the current line."""
        v = self.v
        mem = self.memory
        nt_base = self.nt_base
        rows = self.chr_rows
        if self.bg_cache_dirty:
            self.bg_cache = [None] * (512 * 8 * 4)
            self.bg_cache_dirty = False
        cache = self.bg_cache
        row_base = (0x800 if self.get_bg_table() else 0) + ((v >> 12) & 7)   # table + fine Y
        b = pal[0]
        # color lookup for pixel values 0-3 in each of the 4 background palettes
        p4 = ([b, pal[1], pal[2], pal[3]], [b, pal[5], pal[6], pal[7]],
              [b, pal[9], pal[10], pal[11]], [b, pal[13], pal[14], pal[15]])
        colors = []
        values = []
        for _ in range(33):           # 33 tiles: fine X scroll can show part of a 33rd
            base = nt_base[(v >> 10) & 3]
            tile = mem[base + (v & 0x3FF)]
            attr = mem[base + 0x3C0 + ((v >> 4) & 0x38) + ((v >> 2) & 0x07)]
            shift = ((v >> 4) & 4) | (v & 2)   # which 16x16 quadrant of the 32x32 block
            row_key = row_base + (tile << 3)
            key = (row_key << 2) | ((attr >> shift) & 3)
            row_colors = cache[key]
            if row_colors is None:
                palette = p4[key & 3]
                row_colors = cache[key] = [palette[c] for c in rows[row_key]]
            colors += row_colors
            values += rows[row_key]
            # next tile; past column 31 wrap into the horizontally adjacent nametable
            if (v & 0x1F) == 31:
                v = (v & ~0x1F) ^ 0x0400
            else:
                v += 1
        fx = self.fine_x
        return colors[fx:fx + 256], values[fx:fx + 256]

    def render_sprite_line(self, y, line, bg_opaque, pal, clip_left, check_hit):
        height = self.get_spr_height()
        oam = self.sprMemory

        # the first 8 sprites on this line; a 9th sets the overflow flag
        on_line = self.sprites_on_line(y, height)
        if len(on_line) > 8:
            self.registers[self.status] |= 0x20
            on_line = on_line[:8]

        taken = [False] * 256         # lower-numbered sprites win each pixel
        rows = self.chr_rows
        for i in on_line:
            row = y - (oam[i] + 1)    # sprites appear one line below their Y byte
            tile = oam[i+1]
            attr = oam[i+2]
            sx = oam[i+3]
            if attr & 0x80:           # vertical flip
                row = height - 1 - row
            if height == 16:          # 8x16: tile bit 0 picks the pattern table
                base = 0x1000 if tile & 1 else 0
                tile = (tile & 0xFE) + (row >> 3)
                row &= 7
            else:
                base = 0x1000 if self.get_spr_table() else 0
            pixels = rows[(base >> 1) + (tile << 3) + row]
            if attr & 0x40:           # horizontal flip
                pixels = pixels[::-1]
            palette = 0x10 | ((attr & 3) << 2)
            behind = attr & 0x20

            for px in range(8):
                x = sx + px
                if x > 255:
                    break
                if clip_left and x < 8:
                    continue
                c = pixels[px]
                if c == 0 or taken[x]:
                    continue
                taken[x] = True
                if i == 0 and check_hit and bg_opaque[x] and x != 255:
                    self.registers[self.status] |= 0x40   # sprite 0 hit
                if not (behind and bg_opaque[x]):
                    line[x] = pal[palette | c]

    def sprites_on_line(self, y, height):
        """OAM offsets (in OAM order) of the sprites that cover scanline y."""
        if self.sprite_lines is None or self.sprite_lines_height != height:
            lines = [[] for _ in range(VISIBLE_LINES)]
            oam = self.sprMemory
            for i in range(0, 256, 4):
                top = oam[i] + 1
                for line in range(top, min(top + height, VISIBLE_LINES)):
                    lines[line].append(i)
            self.sprite_lines = lines
            self.sprite_lines_height = height
        return self.sprite_lines[y]

    # ---- scroll register updates done by the rendering hardware ----

    def increment_y(self):
        v = self.v
        if (v & 0x7000) != 0x7000:    # fine Y < 7
            v += 0x1000
        else:
            v &= ~0x7000
            coarse_y = (v & 0x03E0) >> 5
            if coarse_y == 29:        # bottom of nametable: wrap to the one below
                coarse_y = 0
                v ^= 0x0800
            elif coarse_y == 31:      # attribute rows: wrap without switching
                coarse_y = 0
            else:
                coarse_y += 1
            v = (v & ~0x03E0) | (coarse_y << 5)
        self.v = v

    def copy_horizontal(self):
        self.v = (self.v & ~0x041F) | (self.t & 0x041F)

    def copy_vertical(self):
        self.v = (self.v & ~0x7BE0) | (self.t & 0x7BE0)

    # ---- timing ----

    def cycles_until_event(self):
        """CPU cycles until run_ppu next has work to do (a line to draw or a line to end).
        The CPU only needs to run the PPU at these points, or before touching its registers."""
        line = self.scanline
        if not self.line_done and (line < VISIBLE_LINES or line == PRERENDER_LINE):
            target = LINE_RENDER_DOT
        else:
            target = DOTS_PER_LINE
        return max(1, -(-(target - self.dot) // 3))   # round up to whole CPU cycles

    def run_ppu(self, numCPUCycles):
        """Advance the PPU by the given number of CPU cycles (3 dots each)."""
        self.dot += numCPUCycles * 3
        while True:
            line = self.scanline
            if not self.line_done and self.dot >= LINE_RENDER_DOT \
                    and (line < VISIBLE_LINES or line == PRERENDER_LINE):
                self.line_done = True
                if line < VISIBLE_LINES:
                    self.render_line(line)
                if self.rendering_enabled():
                    self.increment_y()
                    self.copy_horizontal()
                    if line == PRERENDER_LINE:
                        self.copy_vertical()

            if self.dot < DOTS_PER_LINE:
                break
            self.dot -= DOTS_PER_LINE
            self.line_done = False
            self.scanline += 1

            if self.scanline == VISIBLE_LINES:
                self.renderer.present()
            elif self.scanline == VBLANK_LINE:
                self.set_vblank()
                if self.get_nmi_mask() == 1:
                    self.raise_nmi()
            elif self.scanline == PRERENDER_LINE:
                self.registers[self.status] &= 0x1F   # clear vblank, sprite 0 hit, overflow
                self.nmi = 0
                self.cpu.nmi_flipflop = 1
            elif self.scanline == LINES_PER_FRAME:
                self.scanline = 0
                self.frame += 1
