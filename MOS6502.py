"""
MOS6502: implements an emulated MOS 6502 processor.
"""

import instructions
from nesPPU import PPU
from nesMemory import Memory
from nesCart import Rom
from nesControllers import Controllers

class Register(object):
    """Representation of a MOS 6502 register. 8-bit except the program counter, which is 16-bit."""
    def __init__(self, name, bitwidth):
        self.name = name
        self.value = 0
        self.past = [0] # maybe for rewind?
        self.bitwidth = bitwidth # currently unused
        self.symb_val = [0] # placeholder until symbolic execution is added
        #self.symb_val = [z3.BitVec(self.name, bitwidth)] # maybe for
                                                        # symbolic
                                                        # execution?
    def get_value(self):
        """Return register's current value"""
        return self.value

    def set_value(self, value):
        """Set register's new value"""
        self.value = value

    def get_current_symb(self):
        """Return register's current symbolic value"""
        return self.symb_val[-1]

    def get_initial_symb(self):
        """Return register's initial symbolic value"""
        return self.symb_val[0]

    def set_initial_symb(self, value):
        """Set register's initial symbolic value"""
        self.symb_val[0] = value


class CPU(object):
    """The emulated NES CPU core"""
    def __init__(self, baseAddress=0x8000):
        self.bitwidth = bitwidth = 8 # 1 byte - 8 bits
        self.regs = {'A': Register('A', bitwidth),
                     'X': Register('X', bitwidth),
                     'Y': Register('Y', bitwidth),
                     'PC': Register('PC', bitwidth * 2),
                     'S': Register('S', bitwidth),
                     'P': Register('P', bitwidth)}

        self.base_address = baseAddress  # unused for now

        self.pc_size = 2 # 2 bytes for PC - 16 bits
        self.memory = Memory()
        self.past_memory = []
        #self.symbMemory = z3Array('mem', z3.BitVecSort(bitwidth), z3.BitVecSort(8))

        self.regs['PC'].set_value(0)
        self.regs['S'].set_value(0)

        self.cycle = 0
        self.global_cycle = 0
        self.nmi_flipflop = 0

        self.stack_base = 0x0100
        self.ppu_mem = 0x2000
        self.apu_mem = 0x4000
        self.spr_dma = 0x4014
        self.channels = 0x4015
        self.ctrl1 = 0x4016
        self.ctrl2 = 0x4017
        self.nmi_vector = 0xFFFA
        self.reset_vector = 0xFFFC
        self.irq_brk_vector = 0xFFFE

        self.ctrl_a = 7
        self.ctrl_b = 6
        self.ctrl_select = 5
        self.ctrl_start = 4
        self.ctrl_up = 3
        self.ctrl_down = 2
        self.ctrl_left = 1
        self.ctrl_right = 0

        self.rom = None
        self.ppu = None
        self.controllers = None
        self.paused = False
        self.pause_reason = None

        self.last_four = [0x00] * 4
        self.bwrites = []
        self.breads = []

    def clear_memory(self):
        """Clear (zero out) emulated memory"""
        self.memory.ClearMemory()

    def reset(self):
        """Reset CPU. Note: reset state is not the same as the initial power-on state"""
        # https://wiki.nesdev.com/w/index.php/CPU_power_up_state
        ctrl_start = self.read_mem_word(self.reset_vector)
        self.set_pc(ctrl_start)
        self.set_register('S', 0xFD)
        self.set_register('P', 0x00)  # MMM: documentation says P = P | 0x04 ?
        self.clear_memory()           # MMM: documentation says memory is unchanged

        # https://wiki.nesdev.com/w/index.php/PPU_power_up_state
        self.ppu = PPU(self)          # MMM: PPU object should probably have its own reset() method

        self.controllers = Controllers(self)

    def map_mem(self, address):
        """Map program memory from the NES ROM into the CPU's memory space"""
        return self.rom.mapMem(self, address)

    def map_vmem(self, address):
        """Map VMem from the NES ROM into the CPU's memory space"""
        return self.rom.mapVMem(self, address)

    def load_rom(self, rom_path):
        """Load an NES cartridge ROM from the given .nes file path"""
        self.rom = Rom(rom_path, self)
        return self.rom

    def read_memory(self, address):
        """Return a read of 1 byte of main memory from the given address"""
        if address in self.breads:
            self.paused = True
            self.pause_reason = 'Read at ' + hex(address)
        return self.memory.ReadMemory(self, address)

    def read_vmemory(self, address):
        """Return a read of 1 byte of video memory from the given address"""
        # MMM: isn't VRAM a property of the PPU?
        return self.rom.ReadVMemory(self, address)

    def read_mem_word(self, address):
        """Return a read of one 16-bit word of memory from the given address"""
        value = self.read_memory(address)
        value += self.read_memory(address + 1) << 8
        return value

    def read_rel_pc(self, offset):
        """Return 1 byte of memory read using PC-relative addressing"""
        return self.read_memory(self.get_register('PC')+offset)

    def set_memory(self, address, value):
        """Write the given 1 byte value to the given address in NES memory"""
        #self.memory[address] = value & 0xFF
        if address in self.bwrites:
            self.paused = True
            self.pause_reason = 'Write at ' + hex(address)
        return self.memory.SetMemory(self, address, value)

    def init_memory(self, address, values):
        """Initialize a region of emulated memory to the bytes specified in 'values'"""
        for value in values: # writing 1 byte at a time
            self.set_memory(address, value)
            address = address + 1

    def get_memory(self, address, size):
        """Return an arbitrarily sized region of the emulated memory space"""
        mem = []
        for i in range(0, size):
            mem.append(self.read_memory(address+i))

        return mem

    def get_register(self, name):
        """Return the value of the given register (valid values: A, X, Y, S, P, PC)"""
        return self.regs[name].get_value()

    def set_pc(self, value):
        """Set the Program Counter of the emulated CPU to the given 16-bit value."""
        self.regs['PC'].set_value(value & 0xFFFF)
        return value & 0xFFFF

    def set_register(self, name, value):
        """Set the given 8-bit register (A, X, Y, S, or P registers only)"""
        self.regs[name].set_value(value & 0xFF)
        return value & 0xFF

    def push_byte(self, value):
        """Push the given byte value onto the emulated CPU stack."""
        reg_s = self.get_register('S') - 1
        self.set_memory(reg_s + self.stack_base, value)
        self.set_register('S', reg_s)
        return reg_s + self.stack_base

    def push_word(self, value):
        """Push the given 16-bit word value onto the emulated CPU stack."""
        self.push_byte((value & 0xFF00) >> 8)
        return self.push_byte(value & 0xFF)

    def pop_byte(self):
        """Return a byte value popped from the emulated CPU stack."""
        reg_s = self.get_register('S')
        value = self.read_memory(reg_s +self.stack_base)
        self.set_register('S', reg_s+1)
        return value

    def pop_word(self):
        """Return a 16-bit word value popped from the emulated CPU stack."""
        return self.pop_byte() + (self.pop_byte() << 8)

    def set_flag(self, flag_name, value):
        """Set the current emulated 8-bit status (flags) register to the given value"""
        flags = {'C':0,  # Carry
                 'Z':1,  # Zero
                 'I':2,  # Interrctrl_upt mask
                 'D':3,  # Decimal
                 'B':4,  # Break
                 'V':6,  # Overflow
                 'N':7}  # Negative

        flag_reg = self.get_register('P')
        if value == 1:
            new_flag = flag_reg | 1 << flags[flag_name]
        else:
            new_flag = flag_reg & ~(1 << flags[flag_name])

        self.set_register('P', new_flag)

    def create_overflow_condition(self, old_dst, old_src):
        """Return boolean value whether operation creates an overflow condition"""
        op1 = (old_dst & 0x80) >> (self.bitwidth - 1)
        op2 = (old_src & 0x80) >> (self.bitwidth - 1)
        of_cond = (((op1 ^ op2) ^ 0x2) & (((op1 + op2) ^ op2) & 0x2)) != 0

        return of_cond

    @staticmethod
    def create_carry_condition(old_dst, old_src, sub_op):
        """Return boolean value whether operation creates a carry condition"""
        if sub_op:
            return ((~old_src) + 1) > old_dst
        else:
            return (old_src > 0) and (old_dst > (0xff - old_src))

    def ctrl_update_flags(self, flags, old_dst, old_src, new_val, sub_op):
        """Update, as needed, the C or V bits in the emulated flags register"""
        of_cond = self.create_overflow_condition(old_dst, old_src)
        cf_cond = self.create_carry_condition(old_dst, old_src, sub_op)

        valid_flags = {'C': cf_cond is True,
                       'Z': new_val == 0,
                       'V': of_cond is True,
                       'N': ((new_val & 0x80) != 0)}

        for flag in flags:
            self.set_flag(flag, valid_flags[flag])

    def get_flag(self, flag_name):
        """Return the current emulated 8-bit status (flags) register"""
        flags = {'C':0,  # Carry
                 'Z':1,  # Zero
                 'I':2,  # Interrctrl_upt mask
                 'D':3,  # Decimal
                 'B':4,  # Break
                 'V':6,  # Overflow
                 'N':7}  # Negative

        flags_reg = self.get_register('P')
        flag_index = flags[flag_name]
        return (flags_reg >> flag_index) & 1

    def inc_pc(self, size):
        """Increment the emulated CPU's Program Counter by specified number of bytes."""
        current_pc = self.get_register('PC')
        self.set_pc(current_pc + size)

    def inc_cycles(self, cycles):
        """NES emulation timing is defined by emulated CPU cycles. Increment the cycle count."""
        self.cycle += cycles
        self.global_cycle += cycles

    def handle_nmi(self):
        """Non-Maskable Interrupt handler routine. NMI is generated by PPU upon each V-Blank."""
        print "NMI HANDLER"
        self.push_word(self.get_register('PC'))
        self.push_byte(self.get_register('P'))
        self.set_flag('I', 1)

        # MMM: somewhere we should check if NMIs are disabled in the status register?
        # jump to the NMI vector
        target = self.read_mem_word(self.nmi_vector)
        self.set_pc(target)
        return True

    def step(self):
        """Step the emulated CPU: read, decode, and emulate execution of an instruction."""
        addr = self.get_register('PC')
        opcode = self.read_memory(addr)
        try:
            instruction = instructions.instructions[opcode]
        except StandardError:
            print "Failed to decode instruction: " + hex(opcode) + " @ " + hex(addr)
            self.paused = True
            return addr
        instruction.execute(self)
        self.last_four.pop(0)
        self.last_four.append(addr)
        self.cycle += instruction.cycles
        self.global_cycle += instruction.cycles
        if self.cycle % 4 == 0:
            self.controllers.getInput()

        if self.cycle > self.ppu.cyclesPerHBlank:
            self.ppu.runPPU(self.cycle)
            self.cycle = 0
            if self.nmi_flipflop == 1:
                self.nmi_flipflop = 0
                if self.ppu.nmi == 1:
                    self.handle_nmi()

        return self.get_register('PC')

    def run_to_break(self, breaks, bwrites, breads):
        """Run the emulated CPU by stepping it until it hits a breakpoint."""
        self.paused = False
        self.bwrites = bwrites
        self.breads = breads
        while self.paused is False:
            next_inst = self.step()
            if next_inst in breaks:
                return next_inst
            # sleep the ctrl_right amount here after CPU and PPU are stepped

        return next_inst
