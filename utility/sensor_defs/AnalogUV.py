import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from . import SensorItem
import traceback

class AnalogUVMonitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readout("AnalogUV", "UV photodiode", None)
        self.V_id = DBL.create_readout("AnalogUV/V", "voltage", "V")

        self.sens = None

    def read(self, SIO):
        try:
            if self.sens is None:
                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                self.sens = AnalogIn(ads, ADS.P0)

            self.t = time.time()
            self.V = self.sens.voltage

        except:
            traceback.print_exc()
            self.sens = None
            return

        SIO.log_readout(self.V_id, self.V, self.t)
