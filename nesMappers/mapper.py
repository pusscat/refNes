import importlib
import mapperNumbers

class Mapper:
    def __init__(self, cpu, mapperNum):
        self.mapperNum = mapperNum
        self.mapperName = mapperNumbers.mappers[mapperNum]
        self.mapperModule = importlib.import_module(self.mapperName)
        self.mapper = self.mapperModule.Mapper(cpu)

    def mapMem(self, cpu, address):
        return self.mapper.mapMem(cpu, address)

