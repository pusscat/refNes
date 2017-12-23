"""
Debugger: demonstrates the refNes core. Helpful in testing.
"""

import sys
import signal
import traceback
import code


import MOS6502
from disasm import disasm

BREAKPOINTS = []
BREAKONWRITE = []
BREAKONREAD = []


def signal_handler(signal, frame):
    """Python signal handler for asynchronous events in the debugger, like user keyboard events"""
    global cpu

    cpu.paused = True


def cpu_info(cpu):
    """Returns the current register values / CPU state in a string."""
    lines = ''
    lines += "A: " + hex(cpu.GetRegister('A')) + "\t"
    lines += "X: " + hex(cpu.GetRegister('X')) + "\t"
    lines += "Y: " + hex(cpu.GetRegister('Y')) + "\n"
    lines += "S: " + hex(cpu.GetRegister('S')) + "\t"
    lines += "PC: " + hex(cpu.GetRegister('PC')) + "\t"
    if cpu.GetFlag('C') != 0:
        lines += "C "
    if cpu.GetFlag('Z') != 0:
        lines += "Z "
    if cpu.GetFlag('I') != 0:
        lines += "I "
    if cpu.GetFlag('V') != 0:
        lines += "V "
    if cpu.GetFlag('N') != 0:
        lines += "N"

    return lines


def show_last_four(cpu):
    """Print a disassembly context (last 4 instructions)"""
    for addr in cpu.lastFour:
        mem = cpu.GetMemory(addr, 3)
        print hex(addr) + " " + disasm(mem, 1)[0]


def step_cpu(cpu):
    """Step the CPU forward one instruction."""
    next_addr = cpu.step()
    mem = cpu.GetMemory(next_addr, 3)
    print hex(next_addr) + " " + disasm(mem, 1)[0]


def get_arg(cpu, arg_string):
    """Decode a debugger command argument from string to, e.g., int"""
    # if a register, get the value
    registers = {
        'A': cpu.GetRegister('A'),
        'X': cpu.GetRegister('X'),
        'Y': cpu.GetRegister('Y'),
        'PC': cpu.GetRegister('PC'),
        'S': cpu.GetRegister('S') + 0x0100
        }
    for key in registers:
        if key in arg_string:
            return registers[key]

    # if a length arg, remove the L and cast to hex int
    if arg_string[0] == 'L':
        return int(arg_string[1:], 16)

    # if a number, it's always hex
    return int(arg_string, 16)


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

def display_memory(cpu, cmd_list):
    """Print a specified amount of memory at the specified address"""
    if len(cmd_list) < 2:
        print "display memory: d <address> [opt: 'L'ength]"
        return

    lineLen = 0x10
    length = 0x40 # default length to show
    address = get_arg(cpu, cmd_list[1])

    if len(cmd_list) > 2:
        length = get_arg(cpu, cmd_list[2])

    index = 0
    while index < length:
        data_line = []
        line_addr = address + index
        for i in range(0, lineLen):
            data_line.append(cpu.ReadMemory(address + index))
            index += 1
            if index == length:
                print_mem_line(line_addr, data_line)
                return
        print_mem_line(line_addr, data_line)


def disasm_memory(cpu, cmd_list):
    """Disassemble a specified amount of memory at the specified address"""
    if len(cmd_list) < 2:
        print "unassemble memory: u <address> [opt: 'L'ength]"
        return

    length = 0x8
    address = get_arg(cpu, cmd_list[1])
    
    if len(cmd_list) > 2:
        length = get_arg(cpu, cmd_list[2])

    mem = cpu.GetMemory(address, length*3)
    lines = disasm(mem, length, address)
    for line in lines:
        print line


def add_breakpoint(cpu, cmd_list):
    """Add a breakpoint."""
    global BREAKPOINTS
    BREAKPOINTS.append(get_arg(cpu, cmd_list[1]))


def add_break_on_write(cpu, cmd_list):
    """Add a memory breakpoint (write)"""
    global BREAKONWRITE
    BREAKONWRITE.append(get_arg(cpu, cmd_list[1]))


def add_break_on_read(cpu, cmd_list):
    """Add a memory breakpoint (read)"""
    global BREAKONREAD
    BREAKONREAD.append(get_arg(cpu, cmd_list[1]))


def set_register(cpu, cmd_list):
    """Set the specified register to the specified value"""
    register = cmd_list[1]
    value = get_arg(cpu, cmd_list[2])

    cpu.set_register(register, value)


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
    print "reg / r\t\t - set register value"


def print_screen(cpu):
    """Print the screen (?)"""
    print cpu.ppu.screen


def handle_cmd(cpu, cmd_string):
    """Process a debugger command and dispatch to the appropriate subroutine."""
    global BREAKPOINTS, BREAKONWRITE, BREAKONREAD
    cmd_list = cmd_string.split()
    cmd = cmd_list[0]

    if cmd == 'help' or cmd == '?':
        print_help()

    if cmd == 'step' or cmd == 's':
        step_cpu(cpu)

    if cmd == 'info' or cmd == 'i':
        print cpu_info(cpu)

    if cmd == 'go' or cmd == 'g':
        try:
            next_addr = cpu.runToBreak(BREAKPOINTS, BREAKONWRITE, BREAKONREAD)
        except:
            traceback.print_exc(file=sys.stdout)
            code.interact(local=locals())
        mem = cpu.GetMemory(next_addr, 3)

        if cpu.pauseReason != None:
            print cpu.pauseReason
            cpu.pauseReason = None
        try:
            print "\n" + hex(next_addr) + " " + disasm(mem, 1)[0]
        except IndexError:
            print hex(next_addr) + " " + hex(mem[0])

    if cmd == 'display' or cmd == 'd':
        display_memory(cpu, cmd_list)

    if cmd == 'unasm' or cmd == 'u':
        disasm_memory(cpu, cmd_list)

    if cmd == 'screen':
        print_screen(cpu)

    if cmd == 'bp' or cmd == 'break':
        add_breakpoint(cpu, cmd_list)

    if cmd == 'bw' or cmd == 'bwrite':
        add_break_on_write(cpu, cmd_list)

    if cmd == 'l' or cmd == 'last':
        show_last_four(cpu)

    if cmd == 'reset':
        cpu.Reset()
        step_cpu(cpu)

    if cmd == 'reg' or cmd == 'r':
        if len(cmd_list) == 3:
            set_register(cpu, cmd_list)


def debug_loop(cpu):
    """Main event loop of debugger."""
    signal.signal(signal.SIGINT, signal_handler)
    cmd = ''
    while 1:
        sys.stdout.write("> ")
        last_cmd = cmd
        cmd = sys.stdin.readline().strip()
        if cmd == '':
            cmd = last_cmd
        if cmd == 'quit' or cmd == 'q':
            return
        handle_cmd(cpu, cmd)


# Start here:
cpu = MOS6502.CPU()
cpu.LoadRom("smb1.nes")
cpu.Reset()
debug_loop(cpu)
