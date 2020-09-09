#!/usr/bin/python3

import time
import board
import busio
from adafruit_ht16k33 import segments
from math import *

#    1        7
#  6   2    2   6
#    7        1
#  5   3    3   5
#    4        4
#

xletters = {
    ' ': 0b0000000,
    '_': 0b0001000,
    '-': 0b1000000,
    '=': 0b1001000,
    "'": 0b0100000,
    '"': 0b0100010,
    '`': 0b0000010,
    ',': 0b0001100,
    ';': 0b0010010,
    '?': 0b0000011,
    'a': 0b1011111,
    'A': 0b1110111,
    'b': 0b1111100,
    'c': 0b1011000,
    'C': 0b0111001,
    'd': 0b1011110,
    'E': 0b1111001,
    'e': 0b1111011,
    'F': 0b1110001,
    'g': 0b1101111,
    'h': 0b1110100,
    'H': 0b1110110,
    'i': 0b0010000,
    'j': 0b0001100,
    'J': 0b0011110,
    'K': 0b1111010,
    'L': 0b0111000,
    'M': 0b0110111,
    'n': 0b1010100,
    'o': 0b1011100,
    'P': 0b1110011,
    'q': 0b1100111,
    'r': 0b1010000,
    'S': 0b0101101,
    't': 0b1111000,
    'T': 0b0110001,
    'u': 0b0011100,
    'V': 0b0111110,
    'w': 0b1111110,
    'x': 0b1100100,
    'y': 0b1110010,
    'Z': 0b0011011,
    '0': 0b0111111,
    '1': 0b0000110,
    '2': 0b1011011,
    '3': 0b1001111,
    '4': 0b1100110,
    '5': 0b1101101,
    '6': 0b1111101,
    '7': 0b0000111,
    '8': 0b1111111,
    '9': 0b1100111
}

xambig = {
    'B': 0b1111111,
    'G': 0b1111101,
    'I': 0b0110000,
    'O': 0b0111111,
    's': 0b1101101,
    'S': 0b1101101,
    'Y': 0b1100110,
    'z': 0b1011011,
    'Z': 0b1011011
}

def xlet(c, allow_ambiguous = True):
    b = xambig.get(c, None) if allow_ambiguous else None
    if b is None: b = xletters.get(c, None)
    if b is None: b = xletters.get(c.lower(), None)
    if b is None: b = xletters.get(c.upper(), 0b1100011)
    return b

class SegDisplay:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
        self.display = segments.BigSeg7x4(i2c, auto_write = False)

    def brightness(self, b):
        self.display.brightness = b

    def show(self, t, i0=0):
        self.display.fill(0)
        n = len(t)
        for i in range(min(4, n)):
            self.display.set_digit_raw(i, xlet(t[(i0 + i)%n]))


    def test(self, t = None):
        if t is None:
            t = "The quick red fox jumped over the lazy brown dog.  "
            t += "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.  "
            t += t.upper()

        i = 0
        while True:
            self.brightness(0.3*0.5*(1 + sin(0.3*i)))

            self.show(t, i)

            self.display.top_left_dot = i%2
            self.display.bottom_left_dot = i%3
            #self.display.colon = i%3
            #self.display.ampm =

            self.display.show()
            time.sleep(0.2)
            i += 1


if __name__=="__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--bright",   type=float, help="display brightness, 0--1")
    parser.add_option("--test",     action="store_true", help="run display test")
    parser.add_option("--show",     help="display specified text")
    parser.add_option("--T",        action="store_true", help="display room temperature")

    options, args = parser.parse_args()

    SD = SegDisplay()
    if options.bright is not None: SD.brightness(options.bright)
    if options.show is not None: SD.show(options.show)
    if options.test: SD.test()

    if options.T:
        from AutologbookConfig import log_DB_host,log_xmlrpc_port
        import xmlrpc.client
        s = xmlrpc.client.ServerProxy('http://%s:%i'%(log_DB_host,log_xmlrpc_port), allow_none=True)
        T = 32 + 9*s.newest([1])[0][2]/5.
        SD.show("%4i"%int(100*T))
        SD.display.colon = True

    SD.display.show()

