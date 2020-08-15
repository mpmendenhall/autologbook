import time
import board
import busio
import adafruit_shtc3
from . import SensorItem

class SHTC3Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readgroup("SHTC3", "SHTC3 temperature/humidity sensor")
        self.T_id = DBL.create_readout("T", "SHTC3", "temperature", "deg. C")
        self.RH_id = DBL.create_readout("RH", "SHTC3", "relative humidity", "%")

    def read(self, SIO):
        i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
        self.T, self.RH = adafruit_shtc3.SHTC3(i2c).measurements
        self.t = time.time()
        print("SHTC3", self.t, self.T, "C,\t", self.RH, " % Humidity")

        SIO.log_readout(self.T_id, self.T, self.t)
        SIO.log_readout(self.RH_id, self.RH, self.t)
