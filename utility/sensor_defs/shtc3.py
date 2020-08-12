import time
import board
import busio
import adafruit_shtc3

class SHTC3Monitor:
    def __init__(self, DBL):
        self.g_id = DBL.create_readgroup("SHTC3", "SHTC3 temperature/humidity sensor")
        self.T_id = DBL.create_readout("T", "SHTC3", "temperature", "deg. C")
        self.RH_id = DBL.create_readout("RH", "SHTC3", "relative humidity", "%")
        self.i2c = None

    def read(self, SIO):
        self.T, self.RH = adafruit_shtc3.SHTC3(SIO.i2c).measurements
        self.t = time.time()
        print("SHTC3", self.t, self.T, "C,\t", self.RH, " % Humidity")

        SIO.DBL.log_readout(self.T_id, self.T, self.t)
        SIO.DBL.log_readout(self.RH_id, self.RH, self.t)
