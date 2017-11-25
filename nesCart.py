# http://fms.komkon.org/EMUL8/NES.html#LABM

import struct

class Rom(object):
    def __init__(self, romPath, cpu):
        self.path = romPath
        self.romData = open(romPath, 'rb').read()

        if "NES" not in self.romData[0:3]:
            print "Unrecognized format!"
            return None
        
        # byte 4 - number of 16kB ROM banks
        # byte 5 - number of 8kB VROM banks
        (nrb, nvrb) = struct.unpack('BB', self.romData[4:6])
        self.numRomBanks = nrb
        self.numVromBanks = nvrb
