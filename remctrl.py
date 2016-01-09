''' Control a connected Android phone by injecting touch events.

This can be useful to control a phone that has a dead touchscreen, for example. '''

from cStringIO import StringIO
import threading
import Queue
import time

import pygame
from pygame.locals import *
from PIL import Image

from android.adb_shell import ADBShell
from android.touchemu import MTSlotEmulator

# Settings
SCALE = 0.5
DEVICE = "/dev/input/event2"
BTN_EVENT = True

def get_screenshot(shell):
    data = shell.execute("screencap -p")
    im = Image.open(StringIO(data))
    w, h = im.size
    return im.resize((int(w*SCALE), int(h*SCALE)), Image.ANTIALIAS).convert('RGBA')

def screenshot_thread(shell, queue):
    while 1:
        queue.put(get_screenshot(shell))

def screen_to_touchpos(pos):
    return (pos[0]/SCALE, pos[1]/SCALE)

def main(args):
    print "Starting up..."
    s1 = ADBShell()
    sshot = get_screenshot(s1)
    w, h = sshot.size

    s2 = ADBShell()
    emu = MTSlotEmulator(s2, DEVICE, BTN_EVENT)

    screen = pygame.display.set_mode((w, h))
    queue = Queue.Queue()
    t = threading.Thread(target=screenshot_thread, args=(s1, queue))
    t.daemon = True
    t.start()

    clock = pygame.time.Clock()

    print "Ready."

    while 1:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1: # left
                    emu.touch_down(0, screen_to_touchpos(event.pos))
            elif event.type == MOUSEMOTION:
                if event.buttons[0]:
                    emu.touch_move(0, screen_to_touchpos(event.pos))
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1: # left
                    emu.touch_up(0)
            elif event.type == QUIT:
                return

        try:
            im = queue.get_nowait()
            surf = pygame.image.fromstring(im.tostring(), (w, h), 'RGBA')
            screen.blit(surf, (0, 0))
            pygame.display.flip()
        except Queue.Empty:
            continue

if __name__ == '__main__':
    import sys
    exit(main(sys.argv[1:]))
