import time
import board
import busio
import adafruit_veml6070
from . import SensorItem
import traceback

class VEML6070Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readout("VEML6070", "UVA photodiode", None)
        self.UV_id = DBL.create_readout("VEML6070/UV", "UV(A) level reading", None)

        self.sens = None

    def read(self, SIO):
        try:
            if self.sens is None:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.sens = adafruit_veml6070.VEML6070(i2c)

            self.t = time.time()
            self.UV = self.sens.uv_raw

        except:
            traceback.print_exc()
            self.sens = None
            return

        SIO.log_readout(self.UV_id, self.UV, self.t)
