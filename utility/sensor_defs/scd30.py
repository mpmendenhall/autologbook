import time
import board
import adafruit_scd30
from . import SensorItem
import traceback

# pip3 install adafruit-circuitpython-scd30

class SCD30Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readout("SCD30",   "SCD30 CO_2 sensor", None)
        self.T_id = DBL.create_readout("SCD30/T", "ambient temperature", "deg. C")
        self.H_id = DBL.create_readout("SCD30/RH", "relative humidity", "%")
        self.CO2_id = DBL.create_readout("SCD30/CO2", "CO_2 level", "PPM")
        self.CO2 = self.T = self.H = self.t = None
        self.scd = None

    def read(self, SIO):
        if not self.scd:
            self.scd = adafruit_scd30.SCD30(board.I2C())
        try:
            if not self.scd.data_available: return
            self.CO2 = self.scd.CO2
            self.T = self.scd.temperature
            self.H = self.scd.relative_humidity
        except:
            traceback.print_exc()
            self.scd = None
            return

        self.t = time.time()
        print("SCD30", self.t, self.T, "C,\t", self.H, "%%rh", self.CO2, "PPM CO_2")

        SIO.log_readout(self.T_id, self.T, self.t)
        SIO.log_readout(self.H_id, self.H, self.t)
        SIO.log_readout(self.CO2_id, self.CO2, self.t)
