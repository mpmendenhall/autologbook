import time
import board
import busio
import adafruit_pm25
from . import SensorItem

class PMSA300IMonitor(SensorItem):
    def __init__(self, DBL):
        SensorItem.__init__(self)

        self.g_id = DBL.create_readgroup("PMSA300I", "PMSA300I particulate matter monitor")
        self.PM003_id = DBL.create_readout("PM0.3", "PMSA300I", "Particles > 0.3um / 0.1L air", "n/dl")
        self.PM005_id = DBL.create_readout("PM0.5", "PMSA300I", "Particles > 0.5um / 0.1L air", "n/dl")
        self.PM010_id = DBL.create_readout("PM1",  "PMSA300I", "Particles > 1.0um / 0.1L air", "n/dl")
        self.PM025_id = DBL.create_readout("PM2.5","PMSA300I", "Particles > 2.5um / 0.1L air", "n/dl")
        self.PM050_id = DBL.create_readout("PM5",  "PMSA300I", "Particles > 5.0um / 0.1L air", "n/dl")
        self.PM100_id = DBL.create_readout("PM10", "PMSA300I", "Particles > 10um / 0.1L air",  "n/dl")
        self.PME10_id = DBL.create_readout("PM1.0e", "PMSA300I", "Estimated PM1.5 mass density",  "μg/m^3")
        self.PME25_id = DBL.create_readout("PM2.5e", "PMSA300I", "Estimated PM2.5 mass density",  "μg/m^3")
        self.PME100_id = DBL.create_readout("PM10e", "PMSA300I", "Estimated PM10 mass density",   "μg/m^3")
        self.i2c = None

    def read(self, SIO):
        #from digitalio import DigitalInOut, Direction, Pull
        # If you have a GPIO, its not a bad idea to connect it to the RESET pin
        # reset_pin = DigitalInOut(board.G0)
        # reset_pin.direction = Direction.OUTPUT
        # reset_pin.value = False

        i2c = busio.I2C(board.SCL, board.SDA, frequency=100000) # freq slower for pm25
        reset_pin = None
        pm25 = adafruit_pm25.PM25_I2C(i2c, reset_pin)
        self.t = time.time()
        try:
            self.aqdata = pm25.read()
            print("\nPMSA300I particulate matter readings:")
            for k in self.aqdata: print(" *", k, "\t", self.aqdata[k])
        except:
            traceback.print_exc()
            self.aqdata = None
            return

        SIO.log_readout(self.PM003_id, self.aqdata["particles 03um"], self.t)
        SIO.log_readout(self.PM005_id, self.aqdata["particles 05um"], self.t)
        SIO.log_readout(self.PM010_id, self.aqdata["particles 10um"], self.t)
        SIO.log_readout(self.PM025_id, self.aqdata["particles 25um"], self.t)
        SIO.log_readout(self.PM050_id, self.aqdata["particles 50um"], self.t)
        SIO.log_readout(self.PM100_id, self.aqdata["particles 100um"], self.t)

        SIO.log_readout(self.PME10_id,  self.aqdata["pm10 env"],  self.t)
        SIO.log_readout(self.PME25_id,  self.aqdata["pm25 env"],  self.t)
        SIO.log_readout(self.PME100_id, self.aqdata["pm100 env"], self.t)
