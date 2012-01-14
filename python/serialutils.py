#!/usr/bin/env python
import sys, threading
try:
    import serial
except ImportError, inst:
    sys.stderr.write("Couldn't import py-serial module, is it installed?")
    sys.exit(1)

USAGE = """
Usage:
    %s SERIAL_DEVICE BITRATE
""" % sys.argv[0]


def sercat(device, bitrate):
    """Opens the specified serial port at the specified bandwidth and reads
    output to stdout."""
    t = 0.01
    s = serial.Serial(device, bitrate, timeout=t)
    while True:
        sys.stdout.write(s.read(int(bitrate*t)))
    s.close()

def sertip(device, bitrate):
    """Simulates a terminal on the specified port."""
    t = 0.01
    s = serial.Serial(device, bitrate, timeout=t)
    class InputThread(threading.Thread):
        "A thread for collecting input and sending it to the device."
        def __init__(self, prompt, dest):
            self.prompt = prompt
            self.dest = dest
            self.keep_going = True

        def run(self):
            while self.keep_going:
                self.dest.write(raw_input(self.prompt))
    i = InputThread('', s)
    while True:
        sys.stdout.write(s.read(int(bitrate*t)))
    i.keep_going = False
    s.close()

if __name__ == '__main__':
    try:
        prog, device, bitrate = sys.argv
    except ValueError:
        sys.stderr.write(USAGE)
    else:
        try:
            bitrate = int(bitrate)
        except ValueError:
            sys.stderr.write(USAGE)
            sys.stderr.write("Bitrate must be an intager\n")
            sys.exit(2)
        if prog.endswith('sercat'):
            try:
                sercat(device, bitrate)
            except KeyboardInterrupt:
                sys.stdout.write('\r\n')
        elif prog.endswith('sertip'):
            try:
                sertip(device, bitrate)
            except KeyboardInterrupt:
                sys.stdout.write('\r\n')
        else:
            sys.stderr.write('serialutils.py unknown program name: "%s"\n' % prog)

