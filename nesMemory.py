import struct

class Memory(object):
    def __init__(self):
        # 7FF - 4000 and 6000+ isnt even used
        self.memory = 0x8000 * [0]

    def ClearMemory(self):
        self.memory = 0x8000 * [0]

    def AddressTranslation(self, cpu, address):
        # handle basic mirroring here
        if address > 0x7FF and address < 0x2000:
            address &= 0x7FF

        # handle ppu i/o register mirroring here
        if address > 0x2007 and address < 0x4000:
            address = 0x2000 + (address % 8)
            return (None, address)
       
        # handle nametable mirroring here - XXX

        # handle all other mapper specific stuff
        if address > 0x7FFF and address < 0x10000:
            return cpu.mapMem(address)
        
        # pass back both memory block and address so mappers 
        # dont have to copy to base memory, and can pass their 
        # own blocks
        if address > 0x10000:
            print "WTF??? Read @ " + hex(address)

        return (self.memory, address)


    def ReadMemory(self, cpu, address):
        (mem, addr) = self.AddressTranslation(cpu, address)
        
        # Read from PPU registers
        if address >= 0x2000 and address < 0x2008:
            address -= 0x2000
            return cpu.ppu.GetRegister(address)
        
        return mem[addr]

    def SetMemory(self, cpu, address, value):
        (mem, addr) = self.AddressTranslation(cpu, address)
        
        # Write to PPU registers
        if address >= 0x2000 and address < 0x2008:
            address -= 0x2000
            return cpu.ppu.SetRegister(address, value)

        mem[addr] = value & 0xFF
        return value & 0xFF
