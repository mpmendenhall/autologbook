import time
import board
import busio
import adafruit_shtc3
from . import SensorItem
import traceback

class SHTC3Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readgroup("SHTC3", "SHTC3 temperature/humidity sensor")
        self.T_id = DBL.create_readout("T", "SHTC3", "temperature", "deg. C")
        self.RH_id = DBL.create_readout("RH", "SHTC3", "relative humidity", "%")

        self.sens = None

    def read(self, SIO):

        try:
            if self.sens is None:
                i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
                self.sens = adafruit_shtc3.SHTC3(i2c)

            self.t = time.time()
            self.T, self.RH = self.sens.measurements

        except:
            traceback.print_exc()
            self.sens = None
            return

        print("SHTC3", self.t, self.T, "C,\t", self.RH, " % Humidity")

        SIO.log_readout(self.T_id, self.T, self.t)
        SIO.log_readout(self.RH_id, self.RH, self.t)
