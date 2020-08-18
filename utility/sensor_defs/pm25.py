import time
import board
import busio
import adafruit_pm25
from . import SensorItem

class PMSA300IMonitor(SensorItem):
    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readgroup("PMSA300I", "PMSA300I particulate matter monitor")
        self.PM003_id = DBL.create_readout("PM0.3",  "PMSA300I", "Particles > 0.3μm / 0.1L air", "n/dl")
        self.PM005_id = DBL.create_readout("PM0.5",  "PMSA300I", "Particles > 0.5μm / 0.1L air", "n/dl")
        self.PM010_id = DBL.create_readout("PM1",    "PMSA300I", "Particles > 1.0μm / 0.1L air", "n/dl")
        self.PM025_id = DBL.create_readout("PM2.5",  "PMSA300I", "Particles > 2.5μm / 0.1L air", "n/dl")
        self.PM050_id = DBL.create_readout("PM5",    "PMSA300I", "Particles > 5.0μm / 0.1L air", "n/dl")
        self.PM100_id = DBL.create_readout("PM10",   "PMSA300I", "Particles > 10μm / 0.1L air",  "n/dl")
        self.PME10_id = DBL.create_readout("PM1.0e", "PMSA300I", "Particles d < 1μm estimated mass density",          "μg/m^3")
        self.PME25_id = DBL.create_readout("PM2.5e", "PMSA300I", "Particles 1μm < d < 2.5μm estimated mass density",  "μg/m^3")
        self.PME100_id = DBL.create_readout("PM10e", "PMSA300I", "Particles 2.5μm < d < 10μm extimated mass density", "μg/m^3")

        self.pm25 = None

    def read(self, SIO):

        if self.pm25 is None:
            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
            reset_pin = None
            self.pm25 = adafruit_pm25.PM25_I2C(i2c, reset_pin)

        self.t = time.time()
        try:
            self.aqdata = self.pm25.read()
            print("\nPMSA300I particulate matter readings:")
            for k in self.aqdata: print(" *", k, "\t", self.aqdata[k])
        except:
            traceback.print_exc()
            self.aqdata = self.pm25 = None
            return

        SIO.log_readout(self.PM003_id, self.aqdata["particles 03um"], self.t)
        SIO.log_readout(self.PM005_id, self.aqdata["particles 05um"], self.t)
        SIO.log_readout(self.PM010_id, self.aqdata["particles 10um"], self.t)
        SIO.log_readout(self.PM025_id, self.aqdata["particles 25um"], self.t)
        SIO.log_readout(self.PM050_id, self.aqdata["particles 50um"], self.t)
        SIO.log_readout(self.PM100_id, self.aqdata["particles 100um"], self.t)

        # report mass densities exclusive of lower categories
        n1 = self.aqdata["pm10 env"]
        n2 = self.aqdata["pm25 env"]
        n3 = self.aqdata["pm100 env"]
        SIO.log_readout(self.PME10_id,  n1,  self.t)
        SIO.log_readout(self.PME25_id,  n2 - n1,  self.t)
        SIO.log_readout(self.PME100_id, n3 - n2, self.t)
