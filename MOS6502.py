"""
MOS6502: implements an emulated MOS 6502 processor.
"""

from collections import deque

import instructions
from nesPPU import PPU
from nesMemory import Memory
from nesCart import Rom
from nesControllers import Controllers

# register names used by get_register/set_register, and the CPU attribute for each
REGISTER_ATTRS = {'A': 'a', 'X': 'x', 'Y': 'y', 'S': 's', 'P': 'p', 'PC': 'pc'}

# status register bit for each flag name
FLAG_BITS = {'C': 0x01,  # Carry
             'Z': 0x02,  # Zero
             'I': 0x04,  # Interrupt mask
             'D': 0x08,  # Decimal
             'B': 0x10,  # Break
             'V': 0x40,  # Overflow
             'N': 0x80}  # Negative


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
        self.bitwidth = 8 # 1 byte - 8 bits
        # Registers are plain ints for speed; get_register/set_register take names
        self.a = 0
        self.x = 0
        self.y = 0
        self.s = 0
        self.p = 0
        self.pc = 0

        self.base_address = baseAddress  # unused for now

        self.pc_size = 2 # 2 bytes for PC - 16 bits
        self.memory = Memory()
        # Fast-path views used by read_memory/set_memory for the common cases
        self.ram = self.memory.memory   # $0000-$07FF (mirrored to $1FFF)
        self.prg_windows = None         # $8000-$FFFF in 8KB windows, set by load_rom
        self.past_memory = []
        #self.symbMemory = z3Array('mem', z3.BitVecSort(bitwidth), z3.BitVecSort(8))

        self.cycle = 0
        self.global_cycle = 0
        self.ppu_cycle = 0         # see sync_ppu
        self.ppu_event_cycle = 0
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
        self.break_on_nmi = False  # debugger option: stop when an NMI is taken
        self.render_scale = 1      # window size multiplier, used when the PPU is created
        self.controls_path = None  # controller key config; None = controls.cfg next to the code
        self.show_fps = False      # debugger option: FPS overlay in the game window
        self.limit_speed = True    # debugger option: hold emulation to 60.1 fps

        self.last_four = deque([0x00] * 4, maxlen=4)   # addresses of the last 4 instructions
        # opcode -> Instruction, None for undefined opcodes
        self.optable = [instructions.instructions.get(op) for op in range(256)]
        self.bwrites = []
        self.breads = []

    def clear_memory(self):
        """Clear (zero out) emulated memory"""
        self.memory.clear_memory()

    def reset(self):
        """Reset CPU. Note: reset state is not the same as the initial power-on state"""
        # https://wiki.nesdev.com/w/index.php/CPU_power_up_state
        ctrl_start = self.read_mem_word(self.reset_vector)
        self.set_pc(ctrl_start)
        self.set_register('S', 0xFD)
        self.set_register('P', 0x24)  # MMM: documentation says P = P | 0x04 ?
        self.clear_memory()           # MMM: documentation says memory is unchanged
        self.set_memory(0x01FE, 0xFF)
        self.set_memory(0x01FF, 0xFF)

        # https://wiki.nesdev.com/w/index.php/PPU_power_up_state
        self.ppu = PPU(self)          # MMM: PPU object should probably have its own reset() method
        self.ppu_cycle = self.global_cycle        # CPU cycle the PPU has been run up to
        self.ppu_event_cycle = self.global_cycle + self.ppu.cycles_until_event()

        self.controllers = Controllers(self, self.controls_path)

    def map_mem(self, address):
        """Map program memory from the NES ROM into the CPU's memory space"""
        return self.rom.map_mem(self, address)

    def map_vmem(self, address):
        """Map VMem from the NES ROM into the CPU's memory space"""
        return self.rom.map_vmem(self, address)

    def load_rom(self, rom_path):
        """Load an NES cartridge ROM from the given .nes file path"""
        self.rom = Rom(rom_path, self)
        mapper = getattr(self.rom, 'mapper', None)
        self.prg_windows = mapper.prg_windows if mapper else None
        return self.rom

    def read_memory(self, address):
        """Return a read of 1 byte of main memory from the given address"""
        address = address & 0xFFFF
        if self.breads and address in self.breads:
            self.paused = True
            self.pause_reason = 'Read at ' + hex(address)
        # fast paths: internal RAM and cartridge ROM
        if address < 0x2000:
            return self.ram[address & 0x7FF]
        if address >= 0x8000:
            return self.prg_windows[(address >> 13) & 3][address & 0x1FFF]
        return self.memory.read_memory(self, address)

    def read_vmemory(self, address):
        """Return a read of 1 byte of video memory from the given address"""
        # MMM: isn't VRAM a property of the PPU?
        return self.rom.read_vmemory(self, address)

    def read_mem_word(self, address):
        """Return a read of one 16-bit word of memory from the given address"""
        value = self.read_memory(address)
        value += self.read_memory(address + 1) << 8
        return value

    def read_mem_word_bug(self, addr):
        addr = addr % 0xFFFF
        hi_addr = (addr & 0xFF00) | ((addr + 1) & 0xFF)
        lo_byte = self.read_memory(addr)
        hi_byte = self.read_memory(hi_addr)

        return ((hi_byte << 8) | lo_byte)

    def read_rel_pc(self, offset):
        """Return 1 byte of memory read using PC-relative addressing"""
        return self.read_memory(self.pc + offset) & 0xFF

    def set_memory(self, address, value):
        """Write the given 1 byte value to the given address in NES memory"""
        if self.bwrites and address in self.bwrites:
            self.paused = True
            self.pause_reason = 'Write at ' + hex(address)
        # fast path: internal RAM
        if address < 0x2000:
            value &= 0xFF
            self.ram[address & 0x7FF] = value
            return value
        return self.memory.set_memory(self, address, value)
    
    def set_memory_debug(self, address, value):
        if address in self.bwrites:
            self.paused = True
            self.pause_reason = 'Write at ' + hex(address)
        return self.memory.set_memory_debug(self, address, value)

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
        return getattr(self, REGISTER_ATTRS[name])

    def set_pc(self, value):
        """Set the Program Counter of the emulated CPU to the given 16-bit value."""
        self.pc = value & 0xFFFF
        return self.pc

    def set_register(self, name, value):
        """Set the given 8-bit register (A, X, Y, S, or P registers only)"""
        if name == 'P':
            value = value | (1 << 5)

        value &= 0xFF
        setattr(self, REGISTER_ATTRS[name], value)
        return value

    def push_byte(self, value):
        """Push the given byte value onto the emulated CPU stack."""
        reg_s = self.s
        self.set_memory(reg_s + 0x100, value)
        self.s = (reg_s - 1) & 0xFF
        return reg_s + 0x100 - 1

    def push_word(self, value):
        """Push the given 16-bit word value onto the emulated CPU stack."""
        self.push_byte((value & 0xFF00) >> 8)
        return self.push_byte(value & 0xFF)

    def pop_byte(self):
        """Return a byte value popped from the emulated CPU stack."""
        reg_s = (self.s + 1) & 0xFF   # the stack wraps within page $01
        self.s = reg_s
        return self.read_memory(reg_s + 0x100)

    def pop_word(self):
        """Return a 16-bit word value popped from the emulated CPU stack."""
        return self.pop_byte() + (self.pop_byte() << 8)

    def set_flag(self, flag_name, value):
        """Set the current emulated 8-bit status (flags) register to the given value"""
        if value == 1:
            self.p = (self.p | FLAG_BITS[flag_name] | 0x20) & 0xFF
        else:
            self.p = (self.p & ~FLAG_BITS[flag_name] | 0x20) & 0xFF

    def create_overflow_condition(self, old_dst, old_src, new_val, sub_op):
        """Return boolean value whether operation creates an overflow condition"""
        if not sub_op:
            of_cond = (old_dst^old_src)&0x80 == 0 and (old_dst^new_val) & 0x80 != 0
        else:
            of_cond = (old_dst^old_src)&0x80 != 0 and (old_dst^new_val) & 0x80 != 0
        return of_cond

    @staticmethod
    def create_carry_condition(new_val, sub_op):
        """Return boolean value whether operation creates a carry condition"""
        if not sub_op:
            carry_cond = new_val > 0xFF
        else:
            carry_cond = new_val >= 0
        return carry_cond

    def ctrl_update_flags(self, flags, old_dst, old_src, new_val, sub_op):
        """Update the named flags from an operation's result (general form; the
        instructions compute their flags directly)."""
        for flag in flags:
            if flag == 'C':
                cond = self.create_carry_condition(new_val, sub_op)
            elif flag == 'V':
                cond = self.create_overflow_condition(old_dst, old_src, new_val, sub_op)
            elif flag == 'Z':
                cond = new_val & 0xFF == 0
            else:
                cond = (new_val & 0x80) != 0
            self.set_flag(flag, cond)

    def get_flag(self, flag_name):
        """Return the current emulated 8-bit status (flags) register"""
        return 1 if self.p & FLAG_BITS[flag_name] else 0

    def inc_pc(self, size):
        """Increment the emulated CPU's Program Counter by specified number of bytes."""
        self.pc = (self.pc + size) & 0xFFFF

    def inc_cycles(self, cycles):
        """NES emulation timing is defined by emulated CPU cycles. Increment the cycle count."""
        self.cycle += cycles
        self.global_cycle += cycles

    def handle_nmi(self):
        """Non-Maskable Interrupt handler routine. NMI is generated by PPU upon each V-Blank."""
        self.push_word(self.pc)
        self.push_byte(self.p)
        self.p |= 0x04  # I flag

        # MMM: somewhere we should check if NMIs are disabled in the status register?
        # jump to the NMI vector
        target = self.read_mem_word(self.nmi_vector)
        self.set_pc(target)
        if self.break_on_nmi:
            self.paused = True
            self.pause_reason = 'NMI'
        return True

    def run(self, breaks=(), max_steps=None):
        """Execute instructions until paused, the PC reaches an address in `breaks`,
        or `max_steps` instructions have run. Returns the PC of the next instruction.

        This is the emulator's inner loop, so it is written for speed: things it
        uses on every instruction are copied into local variables first, and the
        work of Instruction.execute() is done inline."""
        optable = self.optable
        read = self.read_memory
        ppu = self.ppu
        last_four = self.last_four
        steps = 0
        while True:
            addr = self.pc
            instruction = optable[read(addr)]
            if instruction is None:
                print("Failed to decode instruction: " + hex(read(addr)) + " @ " + hex(addr))
                self.paused = True
                self.sync_ppu()
                return addr

            # execute; functions return False when they didn't change PC themselves
            if instruction.function(self, instruction) is False:
                self.pc = (self.pc + instruction.size) & 0xFFFF
            cycles = instruction.cycles + instruction.extraCycles
            instruction.extraCycles = 0
            cycle = self.global_cycle + cycles
            self.global_cycle = cycle
            last_four.append(addr)

            # The PPU only runs when it has something to do (see sync_ppu); any
            # access to its registers brings it up to date first.
            if cycle >= self.ppu_event_cycle:
                self.sync_ppu()
            if self.nmi_flipflop == 1:
                self.nmi_flipflop = 0
                if ppu.nmi == 1:
                    self.handle_nmi()

            steps += 1
            pc = self.pc
            if self.paused or pc in breaks or steps == max_steps:
                self.sync_ppu()     # leave the PPU current for the debugger
                return pc

    def sync_ppu(self):
        """Run the PPU up to the current CPU cycle and note when it next needs to run.

        Called when the CPU reaches the PPU's next event (a line to draw, vblank,
        ...), and before anything that reads or changes PPU state: PPU register
        access, sprite DMA and cartridge (mapper) writes. That gives the same
        results as running the PPU after every instruction, with far fewer calls."""
        cycle = self.global_cycle
        pending = cycle - self.ppu_cycle
        if pending:
            self.ppu.run_ppu(pending)
            self.ppu_cycle = cycle
        self.ppu_event_cycle = cycle + self.ppu.cycles_until_event()

    def step(self):
        """Step the emulated CPU: read, decode, and emulate execution of an instruction."""
        return self.run(max_steps=1)

    def run_to_break(self, breaks, bwrites, breads):
        """Run the emulated CPU by stepping it until it hits a breakpoint."""
        self.paused = False
        self.bwrites = bwrites
        self.breads = breads
        return self.run(breaks=set(breaks))
