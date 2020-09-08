import time
import board
import busio
import adafruit_dps310
from . import SensorItem
import traceback

class DPS310Monitor(SensorItem):
    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)
        self.g_id = DBL.create_readout("DPS310", "DPS310 pressure/temperature sensor", None)
        self.T_id = DBL.create_readout("DPS310/T", "ambient temperature", "deg. C")
        self.P_id = DBL.create_readout("DPS310/P", "ambient pressure", "mbar")
        self.dps310 = None

    def read(self, SIO):
        if not self.dps310:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.dps310 = adafruit_dps310.DPS310(i2c, address=0x76)
            self.dps310.pressure_oversample_count = 6
            self.dps310.temperature_oversample_count = 6
        try:
            T = self.dps310.temperature
            P = self.dps310.pressure
        except:
            traceback.print_exc()
            self.dps310 = None
            return

        self.t = time.time()
        print("DPS310 P = %.3f mbar at %.3f C\n"%(P,T))

        SIO.log_readout(self.T_id, T, self.t)
        SIO.log_readout(self.P_id, P, self.t)
