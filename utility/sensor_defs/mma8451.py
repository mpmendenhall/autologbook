import time
import board
import busio
import adafruit_mma8451
from . import SensorItem
import traceback

class MMA8451Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)
        self.X_id   = DBL.create_readout("MMA8451/x",  "x acceleration", "m/s^2")
        self.Y_id   = DBL.create_readout("MMA8451/y",  "y acceleration", "m/s^2")
        self.Z_id   = DBL.create_readout("MMA8451/z",  "z acceleration", "m/s^2")
        self.sensor = None

    def read(self, SIO):
        if not self.sensor:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_mma8451.MMA8451(i2c)
        try:
            x,y,z = self.sensor.acceleration
        except:
            traceback.print_exc()
            self.sensor = None
            return

        self.t = time.time()
        print("MMA8451 at t =", self.t, ": %.3f , %.3f , %.3f m/s^2\n"%(x,y,z))
        SIO.log_readout(self.X_id,   x,   self.t)
        SIO.log_readout(self.Y_id,   y,   self.t)
        SIO.log_readout(self.Z_id,   z,   self.t)
