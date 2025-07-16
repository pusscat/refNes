"""
nesMemory: represents the emulated NES memory space.
"""

#import struct

class Memory(object):
    """Manages the emulated representation of NES memory."""
    def __init__(self):
        # 7FF - 4000 and 6000+ isnt even used
        self.memory = 0x8000 * [0]

    def clear_memory(self):
        self.memory = 0x8000 * [0]

    def address_translation(self, cpu, address):
        # handle basic mirroring here
        if address > 0x7FF and address < 0x2000:
            address &= 0x7FF

        # handle ppu i/o register mirroring here
        if address >= 0x2000 and address < 0x4000:
            address = (address % 8)
            return (None, address)

        # handle all other mapper specific stuff
        if address > 0x7FFF and address < 0x10000:
            return cpu.map_mem(address)

        # pass back both memory block and address so mappers
        # dont have to copy to base memory, and can pass their
        # own blocks
        if address > 0x10000:
            print("WTF??? Read @ " + str(hex(address)))

        return (self.memory, address)


    def read_memory(self, cpu, address):
        (mem, addr) = self.address_translation(cpu, address)

        # Read from PPU registers
        if mem is None:
            return cpu.ppu.get_register(addr)

        return mem[addr]

    def set_memory(self, cpu, address, value):
        (mem, addr) = self.address_translation(cpu, address)
        
        # Write to PPU registers
        if mem is None:
            return cpu.ppu.set_register(addr, value)

        if address == cpu.spr_dma:
            cpu.ppu.sprite_dma(value)

        mem[addr] = value & 0xFF
        return value & 0xFF
    
    def set_memory_debug(self, cpu, address, value):
        # No checks, SEND IT (I trust you <3)
        self.memory[address] = value
        return value
