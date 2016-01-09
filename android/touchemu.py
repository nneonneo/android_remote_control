''' Emulate touch events on Android. '''

from .adb_shell import ADBShell
import time
import re
import os
import struct

__author__ = 'Robert Xiao <nneonneo@gmail.com>'

EV_SYN = 0
EV_KEY = 1
EV_ABS = 3

SYN_REPORT = 0
BTN_TOOL_FINGER = 0x145
BTN_TOUCH = 0x14a
ABS_MT_SLOT = 0x2f
ABS_MT_TOUCH_MAJOR = 0x30
ABS_MT_TOUCH_MINOR = 0x31
ABS_MT_WIDTH_MAJOR = 0x32
ABS_MT_WIDTH_MINOR = 0x33
ABS_MT_ORIENTATION = 0x34
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36
ABS_MT_TOOL_TYPE = 0x37
ABS_MT_BLOB_ID = 0x38
ABS_MT_TRACKING_ID = 0x39
ABS_MT_PRESSURE = 0x3a
ABS_MT_DISTANCE = 0x3b
ABS_MT_TOOL_X = 0x3c
ABS_MT_TOOL_Y = 0x3d

class InputEmulator:
    def __init__(self, shell, device):
        self.shell = shell
        self.device = device

    def send_events(self, events):
        out = bytearray()
        for type, value, code in events:
            out += struct.pack('<IIHHi', 0, 0, type, value, code)

        s = ''.join('\\x%02x' % c for c in out)
        self.shell.execute("echo -ne '%s' > %s" % (s, self.device))

class MTSlotEmulator(InputEmulator):
    ''' "Type B" multitouch emulator - uniquely identified contacts.

    Most newer devices support this mode.
    '''

    def __init__(self, shell, device, btn=False):
        InputEmulator.__init__(self, shell, device)
        self.btn = btn
        self._nextid = 1000
        self._touch_map = {}

    def touch_down(self, slot, pos):
        tid = self._nextid
        self._nextid += 1
        self._touch_map[slot] = tid

        events = [
            (EV_ABS, ABS_MT_SLOT, slot),
            (EV_ABS, ABS_MT_TRACKING_ID, tid),
        ]
        if self.btn:
            events += [
                (EV_KEY, BTN_TOUCH, 1),
                (EV_KEY, BTN_TOOL_FINGER, 1),
            ]
        events += [
            (EV_ABS, ABS_MT_POSITION_X, pos[0]),
            (EV_ABS, ABS_MT_POSITION_Y, pos[1]),
            (EV_ABS, ABS_MT_PRESSURE, 0x40),
            (EV_SYN, SYN_REPORT, 0),
        ]
        self.send_events(events)

    def touch_move(self, slot, pos):
        events = [
            (EV_ABS, ABS_MT_SLOT, slot),
            (EV_ABS, ABS_MT_POSITION_X, pos[0]),
            (EV_ABS, ABS_MT_POSITION_Y, pos[1]),
            (EV_SYN, SYN_REPORT, 0),
        ]
        self.send_events(events)

    def touch_up(self, slot):
        events = [
            (EV_ABS, ABS_MT_SLOT, slot),
            (EV_ABS, ABS_MT_TRACKING_ID, -1),
        ]
        if self.btn:
            events += [
                (EV_KEY, BTN_TOUCH, 0),
                (EV_KEY, BTN_TOOL_FINGER, 0),
            ]
        events += [
            (EV_SYN, SYN_REPORT, 0),
        ]
        self.send_events(events)

class MTAnonEmulator(InputEmulator):
    ''' "Type A" multitouch emulator - unidentified, anonymous contacts.

    This is mostly used for older devices. '''

    def __init__(self, shell, device):
        InputEmulator.__init__(self, shell, device)

    # TODO
