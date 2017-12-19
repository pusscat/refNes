import mapper

class Mapper:
    def __init__(self, cpu, rom):
        self.number = 0
        self.name = "nrom"

        self.bank1Start = 0x8000
        self.bank1End = 0xC000

        self.bank2Start = 0xC000 
        self.bank2End = 0x10000
        
        self.bank1 = rom.romBanks[0]
        self.bank2 = rom.romBanks[1]
        self.vbank = rom.vromBanks[0]

    def mapMem(self, cpu, address):
        if address >= self.bank1Start and address < self.bank1End:
            return (self.bank1, address - self.bank1Start)
        if address >= self.bank2Start and address < self.bank2End:
            return (self.bank2, address - self.bank2Start)
      
    def mapVMem(self, cpu, address):
        return (self.vbank, address)

    def ReadVMemory(self, cpu, address):
        # XXX - This is probably wrong
        return self.vbank[address]
