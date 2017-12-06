# http://fms.komkon.org/EMUL8/NES.html#LABM

import sys
import os

code_path = os.path.dirname(__file__)
code_path = os.path.join(code_path, "nesMappers")
sys.path.append(code_path)

import struct
import mapper

class Rom(object):
    def __init__(self, romPath, cpu):
        self.path = romPath
        romData = open(romPath, 'rb').read()

        headerSize = 0x10
        bankSize = 0x4000
        vromBankSize = 0x2000

        if "NES" not in romData[0:4]:
            print "Unrecognized format!"
            return None
        
        # byte 4 - number of 16kB ROM banks
        # byte 5 - number of 8kB VROM banks
        (nrb, nvrb) = struct.unpack('BB', romData[4:6])
        self.numRomBanks = nrb
        self.numVromBanks = nvrb

        (flags6, flags7, flags8, flags9) = \
            struct.unpack('BBBB', romData[6:10])
        
        # byte 6 flags
        self.mirroring = flags6 & 1
        self.battRam = flags6 & 2
        self.trainer = flags6 & 4
        self.fourScreen = flags6 & 8
        lowMapper = flags6 >> 4

        # byte 7 flags
        self.vsSystem = flags7 & 1
        hiMapper = flags7 >> 4

        self.mapperNum = hiMapper << 4 + lowMapper

        # byte 8 - num 8kB RAM banks
        self.numRamBanks = flags8 if flags8 != 0 else 1

        # byte 9 flags
        self.pal = flags9 & 1

        index = headerSize
        if self.trainer == 1:
            self.trainerData = romData[index:index+512]
            cpu.initMemory(0x7000, self.trainderData)
            index += 512

        self.romBanks = []
        for i in range(0, self.numRomBanks):
            data = romData[index:index+bankSize]
            dataBytes = []
            for c in data:
                dataBytes.append(struct.unpack('B', c)[0])
            self.romBanks.append(dataBytes)
            index += bankSize

        self.vromBanks = []
        for i in range(0, self.numVromBanks):
            data = romData[index:index+vromBankSize]
            dataBytes = []
            for c in data:
                dataBytes.append(struct.unpack('B', c)[0])
            self.vromBanks.append(dataBytes)
            index += vromBankSize

        # do this last so romBanks already exist ;)
        self.mapper = mapper.Mapper(cpu, self, self.mapperNum)
    
    def mapMem(self, cpu, address):
        return self.mapper.mapMem(cpu, address)
