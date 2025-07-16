import importlib
import mapperNumbers

class Mapper:
    def __init__(self, cpu, rom, mapperNum):
        self.mapperNum = mapperNum
        self.mapperName = mapperNumbers.mappers[mapperNum]
        self.mapperModule = importlib.import_module(self.mapperName)
        self.mapper = self.mapperModule.Mapper(cpu, rom)

    def map_mem(self, cpu, address):
        return self.mapper.map_mem(cpu, address)
    
    def map_vmem(self, cpu, address):
        return self.mapper.map_vmem(cpu, address)

    def read_vmemory(self, cpu, address):
        return self.mapper.read_vmemory(cpu, address)
