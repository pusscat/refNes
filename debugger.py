"""
Debugger: demonstrates the refNes core. Helpful in testing.
"""

import sys
import signal
import traceback
import code


import MOS6502
from disasm import disasm


def signal_handler(signum, frame):
    """Signal handler for asynchronous events in the debugger, like user keyboard events"""
    print '\nEmulation paused by signal ' + str(signum) + ' at ' \
        + str(frame.f_code.co_filename) \
        + ':' + str(frame.f_code.co_name) + '() line ' + str(frame.f_lineno)
    print 'Use "q" or "quit" to quit.'

    DEBUG_SESSION.cpu.paused = True


class NesDebugger(object):
    """Command-line NES debugger"""
    def __init__(self, rom_file):
        self.cpu = MOS6502.CPU()
        self.cpu.load_rom(rom_file)
        self.cpu.reset()
        self.breakpoints = []
        self.breakonwrite = []
        self.breakonread = []

    def cpu_info(self):
        """Returns the current register values / CPU state in a string."""
        lines = ''
        lines += "A: " + hex(self.cpu.get_register('A')) + "\t"
        lines += "X: " + hex(self.cpu.get_register('X')) + "\t"
        lines += "Y: " + hex(self.cpu.get_register('Y')) + "\n"
        lines += "S: " + hex(self.cpu.get_register('S')) + "\t"
        lines += "PC: " + hex(self.cpu.get_register('PC')) + "\t"
        if self.cpu.get_flag('C') != 0:
            lines += "C "
        if self.cpu.get_flag('Z') != 0:
            lines += "Z "
        if self.cpu.get_flag('I') != 0:
            lines += "I "
        if self.cpu.get_flag('V') != 0:
            lines += "V "
        if self.cpu.get_flag('N') != 0:
            lines += "N"

        return lines

    def show_last_four(self):
        """Print a disassembly context (last 4 instructions)"""
        for addr in self.cpu.last_four:
            mem = self.cpu.get_memory(addr, 3)
            print hex(addr) + " " + disasm(mem, 1)[0]

    def step_cpu(self):
        """Step the CPU forward one instruction."""
        next_addr = self.cpu.step()
        mem = self.cpu.get_memory(next_addr, 3)
        print hex(next_addr) + " " + disasm(mem, 1)[0]

    def get_arg(self, arg_string):
        """Decode a debugger command argument from string to, e.g., int"""
        # if a register, get the value
        registers = {
            'A': self.cpu.get_register('A'),
            'X': self.cpu.get_register('X'),
            'Y': self.cpu.get_register('Y'),
            'PC': self.cpu.get_register('PC'),
            'S': self.cpu.get_register('S') + 0x0100
            }
        for key in registers:
            if key in arg_string:
                return registers[key]

        # if a length arg, remove the L and cast to hex int
        if arg_string[0] == 'L':
            return int(arg_string[1:], 16)

        # if a number, it's always hex
        return int(arg_string, 16)

    @staticmethod
    def print_mem_line(line_addr, data_line):
        """Print a line (?) of memory"""
        sys.stdout.write("0x" + format(line_addr, '04x') + ": ")
        for byte in data_line:
            sys.stdout.write(format(byte & 0xFF, '02x') + " ")
        sys.stdout.write("\n")
    '''
        sys.stdout.write("\t |")
        for byte in data_line:
            print byte
            sys.stdout.write(format(byte, 'c'))
        print "|"
    '''

    def display_memory(self, cmd_list):
        """Print a specified amount of memory at the specified address"""
        if len(cmd_list) < 2:
            print "display memory: d <address> [opt: 'L'ength]"
            return

        line_len = 0x10
        bytes_to_display = 0x40 # default amount of memory to show
        address = self.get_arg(cmd_list[1])

        if len(cmd_list) > 2:
            bytes_to_display = self.get_arg(cmd_list[2])

        index = 0
        while index < bytes_to_display:
            data_line = []
            line_addr = address + index
            for _ in range(0, line_len):
                data_line.append(self.cpu.read_memory(address + index))
                index += 1
                if index == bytes_to_display:
                    self.print_mem_line(line_addr, data_line)
                    return
            self.print_mem_line(line_addr, data_line)

    def disasm_memory(self, cmd_list):
        """Disassemble a specified amount of memory at the specified address"""
        if len(cmd_list) < 2:
            print "unassemble memory: u <address> [opt: 'L'ength]"
            return

        length = 0x8
        address = self.get_arg(cmd_list[1])

        if len(cmd_list) > 2:
            length = self.get_arg(cmd_list[2])

        mem = self.cpu.get_memory(address, length*3)
        lines = disasm(mem, length, address)
        for line in lines:
            print line

    def add_breakpoint(self, cmd_list):
        """Add a breakpoint."""
        self.breakpoints.append(self.get_arg(cmd_list[1]))

    def add_break_on_write(self, cmd_list):
        """Add a memory breakpoint (write)"""
        self.breakonwrite.append(self.get_arg(cmd_list[1]))

    def add_break_on_read(self, cmd_list):
        """Add a memory breakpoint (read)"""
        self.breakonread.append(self.get_arg(cmd_list[1]))

    def set_register(self, cmd_list):
        """Set the specified register to the specified value"""
        register = cmd_list[1]
        value = self.get_arg(cmd_list[2])
        
        if 'PC' not in register:
            self.cpu.set_register(register, value)
        else:
            self.cpu.set_pc(value)

    @staticmethod
    def print_help():
        """Print the debugger usage reference"""
        print "help / ?\t\t - this message"
        print "step / s\t\t - step one instruction"
        print "info / i\t\t - show cpu registers"
        print "go / g  \t\t - run the program until break"
        print "display / d\t\t - display memory"
        print "unasm / u\t\t - show instructions"
        print "break/ bp\t\t - add breakpoint"
        print "last / l\t\t - show last 4 instructions executed"
        print "reset   \t\t - reset the cpu"
        print "bwrite / bw\t\t - break on write"
        print "bread / br\t\t - break on read"
        print "reg / r\t\t\t - set register value"
        print "quit / q\t\t - quit debugger"

    def print_screen(self):
        """Print the screen (?)"""
        print self.cpu.ppu.screen

    def handle_cmd(self, cmd_string):
        """Process a debugger command and dispatch to the appropriate subroutine."""
        cmd_list = cmd_string.split()
        cmd = cmd_list[0]

        if cmd == 'help' or cmd == '?':
            self.print_help()

        if cmd == 'step' or cmd == 's':
            self.step_cpu()

        if cmd == 'info' or cmd == 'i':
            print self.cpu_info()

        if cmd == 'go' or cmd == 'g':
            try:
                next_addr = \
                  self.cpu.run_to_break(self.breakpoints, self.breakonwrite, self.breakonread)
            except StandardError:
                traceback.print_exc(file=sys.stdout)
                code.interact(local=locals())
            mem = self.cpu.get_memory(next_addr, 3)

            if self.cpu.pause_reason != None:
                print self.cpu.pause_reason
                self.cpu.pause_reason = None
            try:
                print "\n" + hex(next_addr) + " " + disasm(mem, 1)[0]
            except IndexError:
                print hex(next_addr) + " " + hex(mem[0])

        if cmd == 'display' or cmd == 'd':
            self.display_memory(cmd_list)

        if cmd == 'unasm' or cmd == 'u':
            self.disasm_memory(cmd_list)

        if cmd == 'screen':
            self.print_screen()

        if cmd == 'bp' or cmd == 'break':
            self.add_breakpoint(cmd_list)

        if cmd == 'bw' or cmd == 'bwrite':
            self.add_break_on_write(cmd_list)

        if cmd == 'l' or cmd == 'last':
            self.show_last_four()

        if cmd == 'reset':
            self.cpu.reset()
            self.step_cpu()

        if cmd == 'reg' or cmd == 'r':
            if len(cmd_list) == 3:
                self.set_register(cmd_list)

    def debug_loop(self):
        """Main event loop of debugger."""
        cmd = ''
        while 1:
            sys.stdout.write("> ")
            last_cmd = cmd
            cmd = sys.stdin.readline().strip()
            if cmd == '':
                cmd = last_cmd
            if cmd == 'quit' or cmd == 'q':
                return
            self.handle_cmd(cmd)

# Start here:
if __name__ == "__main__":
    DEBUG_SESSION = NesDebugger(sys.argv[1])
    signal.signal(signal.SIGINT, signal_handler)
    DEBUG_SESSION.debug_loop()
