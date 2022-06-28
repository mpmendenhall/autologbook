import time
import board
import busio
import adafruit_mcp9808
from . import SensorItem
import traceback

class MCP9808Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)
        self.T_id   = DBL.create_readout("MCP9808/T",  "ambient temperature", "deg. C")
        self.mcp9808 = None

    def read(self, SIO):
        if not self.mcp9808:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.mcp9808 = adafruit_mcp9808.MCP9808(i2c)
            #self.mcp9808.resolution = 3
        try:
            T   = self.mcp9808.temperature
        except:
            traceback.print_exc()
            self.mcp9808 = None
            return

        self.t = time.time()
        print("MCP9808 at t =", self.t, ": %.3fC\n"%T)
        SIO.log_readout(self.T_id,   T,   self.t)
