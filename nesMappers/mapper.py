import importlib
import mapperNumbers

class Mapper:
    def __init__(self, cpu, rom, mapperNum):
        self.mapperNum = mapperNum
        self.mapperName = mapperNumbers.mappers[mapperNum]
        self.mapperModule = importlib.import_module(self.mapperName)
        self.mapper = self.mapperModule.Mapper(cpu, rom)

    def mapMem(self, cpu, address):
        return self.mapper.mapMem(cpu, address)

    def ReadVMemory(self, cpu, address):
        return self.mapper.ReadVMemory(cpu, address)
