"""
Debugger: demonstrates the refNes core. Helpful in testing.
"""
import os
import sys
import signal
import traceback
import code
import re

import MOS6502
from disasm import disasm


def signal_handler(signum, frame):
    """Signal handler for asynchronous events in the debugger, like user keyboard events"""
    print('\nEmulation paused by signal ' + str(signum) + ' at ' \
        + str(frame.f_code.co_filename) \
        + ':' + str(frame.f_code.co_name) + '() line ' + str(frame.f_lineno))
    print('Use "q" or "quit" to quit.')

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
        lines = "Cycle: " + str(self.cpu.global_cycle) + "\n"
        lines += "A: " + hex(self.cpu.get_register('A')) + "\t"
        lines += "X: " + hex(self.cpu.get_register('X')) + "\t"
        lines += "Y: " + hex(self.cpu.get_register('Y')) + "\n"
        lines += "S: " + hex(self.cpu.get_register('S')) + "\t"
        lines += "PC: " + hex(self.cpu.get_register('PC')) + "\n"
        lines += "P: " + hex(self.cpu.get_register('P')) + "\t"
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
    
    def bp_info(self):
        """Returns the current list of breakpoints."""
        if len(self.breakpoints) == 0:
            return "No breakpoints set."
        lines = "BPs:\n"
        for i in range(len(self.breakpoints)):
            lines += f"{i}: {hex(self.breakpoints[i])}\t"
            if self.get_arg("PC") == self.breakpoints[i]:
                lines += "<-PC"
            lines += "\n"

        return lines
    
    def bwrite_info(self):
        """Returns the current list of break on writes."""
        if len(self.breakonwrite) == 0:
            return "No bwrites set."
        lines = "BWs:\n"
        for i in range(len(self.breakonwrite)):
            lines += f"{i}: {hex(self.breakonwrite[i])}\n"
        
        return lines
    
    def bread_info(self):
        """Returns the current list of break on reads."""
        if len(self.breakonread) == 0:
            return "No breads set."
        lines = "BRs:\n"
        for i in range(len(self.breakonread)):
            lines += f"{i}: {hex(self.breakonread[i])}"

        return lines

    def info(self, cmd_list):
        """Returns the requested info page."""
        if len(cmd_list) < 2:
            return self.cpu_info()
        choice = cmd_list[1].lower()
        if choice in ['cpu', 'c', 'reg', 'r']:
            return self.cpu_info()
        elif choice in ['break', 'bp', 'b']:
            return self.bp_info()
        elif choice in ['bwrite', 'bw']:
            return self.bwrite_info()
        elif choice in ['bread', 'br']:
            return self.bread_info()
        else:
            return "info pages: cpu, break, bwrite, bread"

    def show_last_four(self):
        """Print a disassembly context (last 4 instructions)"""
        for addr in self.cpu.last_four:
            mem = self.cpu.get_memory(addr, 3)
            print(hex(addr) + " " + disasm(mem, 1)[0])

    def step_cpu(self):
        """Step the CPU forward one instruction."""
        next_addr = self.cpu.step()
        mem = self.cpu.get_memory(next_addr, 3)

        print(hex(next_addr) + " " + disasm(mem, 1)[0] + "\t\tA: " + hex(self.cpu.get_register('A')) + " X: " + hex(self.cpu.get_register('X')) + " Y: " + hex(self.cpu.get_register('Y')) + " P:" + hex(self.cpu.get_register('P')) + " S: " + hex(self.cpu.get_register('S')))

    def get_arg(self, arg_string):
        """Decode a debugger command argument from string to, e.g., int"""

        oper_split = re.split("([+-])", arg_string)
        if len(oper_split) > 1 and len(oper_split):
            sum_arg = self.get_arg(oper_split[0])
            for i in range(1, len(oper_split), 2):
                if i+1 > len(oper_split): break
                if oper_split[i] == '+':
                    sum_arg += self.get_arg(oper_split[i+1])
                elif oper_split[i] == '-':
                    sum_arg -= self.get_arg(oper_split[i+1])
            return sum_arg
        
        arg_string = oper_split[0]

        # if a register, get the value
        registers = {
            'A': self.cpu.get_register('A'),
            'X': self.cpu.get_register('X'),
            'Y': self.cpu.get_register('Y'),
            'PC': self.cpu.get_register('PC'),
            'S': self.cpu.get_register('S') + 0x0100
            }
        for key in registers:
            if key == arg_string.upper():
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
            print("display memory: d <address> [opt: 'L'ength]")
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
            print("unassemble memory: u <address> [opt: 'L'ength]")
            return

        length = 0x8
        address = self.get_arg(cmd_list[1])

        if len(cmd_list) > 2:
            length = self.get_arg(cmd_list[2])

        mem = self.cpu.get_memory(address, length*3)
        lines = disasm(mem, length, address)
        for line in lines:
            print(line)

    def add_breakpoint(self, cmd_list):
        """Add a breakpoint."""
        self.breakpoints.append(self.get_arg(cmd_list[1]))

    def add_break_on_write(self, cmd_list):
        """Add a memory breakpoint (write)"""
        self.breakonwrite.append(self.get_arg(cmd_list[1]))

    def add_break_on_read(self, cmd_list):
        """Add a memory breakpoint (read)"""
        self.breakonread.append(self.get_arg(cmd_list[1]))

    def test_log(self, cmd_list):
        """Test execution against an execution log from another emu"""
        with open("tests/" + cmd_list[1] + ".log", "r") as log:
            # skip blank lines so a trailing newline doesn't count as an entry
            log_lines = [line for line in log if line.strip()]

        pc_start = int("0x" + log_lines[0].split()[0], 16)
        self.cpu.set_pc(pc_start)
        print("Starting at " + hex(pc_start))

        failed = False
        instruction = 1
        while failed == False and instruction < len(log_lines):
            line = log_lines[instruction]
            data = line.split()
            index = 0
            for datum in data:
                if 'A:' not in datum[:2]:
                    index += 1
                else: 
                    break
            pc = int("0x" + data[0], 16)
            a = int("0x" + data[index][2:], 16)
            x = int("0x" + data[index+1][2:], 16)
            y = int("0x" + data[index+2][2:], 16)
            p = int("0x" + data[index+3][2:], 16)
            # stack pointer is "S:FD" in some logs and "SP:FD" in others
            s = int("0x" + data[index+4].split(':')[1], 16)
            self.step_cpu()

            if (a != self.cpu.get_register('A')):
                print("A is wrong: " + hex(a))
                failed = True
            if (x != self.cpu.get_register('X')):
                print("X is wrong: " + hex(x))
                failed = True
            if (y != self.cpu.get_register('Y')):
                print("Y is wrong: " + hex(y))
                failed = True
            if (p != self.cpu.get_register('P')):
                print("P is wrong: " + hex(p))
                failed = True
            if (s != self.cpu.get_register('S')):
                print("S is wrong: " + hex(s))
                failed = True
            if (pc != self.cpu.get_register('PC')):
                print("PC is wrong: " + hex(pc))
                failed = True

            if failed:
                print(f"Mismatch at log line {instruction + 1}: {line.strip()}")

            instruction += 1

        if not failed:
            print(f"Passed: all {len(log_lines)} log lines matched.")

    def set_register(self, cmd_list):
        """Set the specified register to the specified value"""
        register = cmd_list[1]
        value = self.get_arg(cmd_list[2])
        
        if 'PC' not in register:
            self.cpu.set_register(register, value)
        else:
            self.cpu.set_pc(value)

    def run_script(self, cmd_list):
        """Loads and executes debugger commands from file."""
        if len(cmd_list) < 2:
            print("run script: script <filepath>")
            return

        file_path = cmd_list[1]
        try:
            with open(file_path, 'r') as file:
                for line in file.readlines():
                    if not line.startswith("#"):
                        print('> ', end='')
                    print(line, end='')
                    self.handle_cmd(line)
                file.close()
        except FileNotFoundError:
            print(f"{file_path} does not exist.")
            return

    @staticmethod
    def print_help():
        """Print the debugger usage reference"""
        print("help / ?\t\t - this message")
        print("step / s\t\t - step one instruction")
        print("info / i\t\t - show info pages (cpu, bp, bw, br)")
        print("go / g  \t\t - run the program until break")
        print("display / d\t\t - display memory")
        print("unasm / u\t\t - show instructions")
        print("break/ bp\t\t - add breakpoint")
        print("last / l\t\t - show last 4 instructions executed")
        print("reset   \t\t - reset the cpu")
        print("bwrite / bw\t\t - break on write")
        print("bread / br\t\t - break on read")
        print("screen\t\t\t - print screen to console")
        print("reg / r\t\t\t - set register value")
        print("test    \t\t\t - test execution against a log")
        print("script \t\t\t - run a debugger script from a file")
        print("quit / q\t\t - quit debugger")

    def print_screen(self, cmd_list):
        """Print the screen to the console"""
        screen = self.cpu.ppu.screen
        xlines = self.cpu.ppu.xlines
        ylines = self.cpu.ppu.ylines

        # Create table of letter representations for bytes on screen (may change this to something consistent across states later)
        unique = list(set(screen))
        letters = {}
        for i in range(len(unique)):
            letters[unique[i]] = chr(0x41+i)

        start_y = 0
        end_y = ylines
        if cmd_list[1]:
            start_y = min(max(0, self.get_arg(cmd_list[1])), ylines)
        if cmd_list[2]:
            end_y = min(max(start_y, self.get_arg(cmd_list[2])), ylines)

        for y in range(start_y, end_y):
            print(f"y{y}")
            print(''.join([letters[pixel] for pixel in screen[y*xlines:(y*xlines)+xlines]]))
        print(f"Letter Key: {letters}")
        if len(cmd_list) < 2:
            print("print partial screen: screen <starty> <endy>")

    def handle_cmd(self, cmd_string):
        """Process a debugger command and dispatch to the appropriate subroutine."""
        cmd_list = cmd_string.split()
        cmd = cmd_list[0]

        if cmd == 'help' or cmd == '?':
            self.print_help()

        if cmd == 'step' or cmd == 's':
            self.step_cpu()

        if cmd == 'info' or cmd == 'i':
            print(self.info(cmd_list))

        if cmd == 'go' or cmd == 'g':
            try:
                next_addr = \
                  self.cpu.run_to_break(self.breakpoints, self.breakonwrite, self.breakonread)
            except RuntimeError:
                traceback.print_exc(file=sys.stdout)
                code.interact(local=locals())
            mem = self.cpu.get_memory(next_addr, 3)

            if self.cpu.pause_reason != None:
                print(self.cpu.pause_reason)
                self.cpu.pause_reason = None
            try:
                print("\n" + hex(next_addr) + " " + disasm(mem, 1)[0])
            except IndexError:
                print(hex(next_addr) + " " + hex(mem[0]))

        if cmd == 'display' or cmd == 'd':
            self.display_memory(cmd_list)

        if cmd == 'unasm' or cmd == 'u':
            self.disasm_memory(cmd_list)

        if cmd == 'screen':
            self.print_screen(cmd_list)

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

        if cmd == 'test':
            self.test_log(cmd_list)

        if cmd == 'script':
            self.run_script(cmd_list)

    def debug_loop(self):
        """Main event loop of debugger."""
        if os.path.exists("./.dbginit"):
            print("Running .dbginit script...")
            self.run_script(["script", "./.dbginit"])
            print("")
            
        cmd = ''
        while 1:
            last_cmd = cmd
            cmd = input('> ').strip()
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
