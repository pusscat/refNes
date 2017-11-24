
class Memory(object):
    def __init__(self):
        # some of this isnt used due to mirroring
        # some of this changes due to mappers
        self.memory = 0x10000 * [0]

    def AddressTranslation(self, address):
        # handle mirroring here
        newAddr = address
        return newAddr


    def ReadMemory(self, address):
        addr = self.AddressTranslation(address)
        return self.memory[addr]

    def SetMemory(self, address, value):
        addr = self.AddressTranslation(address)
        self.memory[addr] = value & 0xFF
        return value & 0xFF
