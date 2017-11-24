
class Memory(object):
    def __init__(self):
        # some of this isnt used due to mirroring
        # some of this changes due to mappers
        self.memory = 0x10000 * [0]

    def AddressTranslation(self, address):
        # handle basic mirroring here
        if address > 0x7FF and address < 0x2000:
            address &= 0x7FF

        # handle ppu i/o register mirroring here
        if address > 0x2007 and address < 0x4000:
            address = 0x2000 + (address % 8)
       
        # handle nametable mirroring here - XXX

        # handle all other mapper specific mirroring - XXX
        
        # pass back both memory block and address so mappers 
        # dont have to copy to base memory, and can pass their 
        # own blocks
        return (self.memory, address)


    def ReadMemory(self, address):
        (mem, addr) = self.AddressTranslation(address)
        return mem[addr]

    def SetMemory(self, address, value):
        (mem, addr) = self.AddressTranslation(address)
        mem[addr] = value & 0xFF
        return value & 0xFF
