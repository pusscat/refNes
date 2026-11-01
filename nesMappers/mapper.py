import importlib
import mapperNumbers

class Mapper:
    def __init__(self, cpu, rom, mapperNum):
        self.mapperNum = mapperNum
        self.mapperName = mapperNumbers.mappers[mapperNum]
        self.mapperModule = importlib.import_module(self.mapperName)
        self.mapper = self.mapperModule.Mapper(cpu, rom)
        # Each mapper provides prg_windows: four 8KB lists covering $8000-$9FFF,
        # $A000-$BFFF, $C000-$DFFF and $E000-$FFFF. The CPU reads them directly, so a
        # mapper that switches banks must replace entries in this same list
        # (prg_windows[i] = ...), not assign a new list. A mapper that switches CHR
        # banks must call cpu.ppu.decode_chr() afterwards.
        self.prg_windows = self.mapper.prg_windows

    def write_prg(self, cpu, address, value):
        """CPU write to $8000-$FFFF (mapper registers on most carts)."""
        return self.mapper.write_prg(cpu, address, value)

    def map_mem(self, cpu, address):
        return self.mapper.map_mem(cpu, address)
    
    def map_vmem(self, cpu, address):
        return self.mapper.map_vmem(cpu, address)

    def read_vmemory(self, cpu, address):
        return self.mapper.read_vmemory(cpu, address)
