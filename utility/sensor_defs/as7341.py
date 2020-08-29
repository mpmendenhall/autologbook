import time
import board
import busio
import adafruit_as7341
from . import SensorItem
import traceback

class AS7341Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readgroup("AS7341", "AS7341 multispectral light sensor")
        self.wavelengths = [415, 445, 480, 515, 555, 590, 630, 680]
        self.FWHMs =       [26,  30,  36,  39,  39,  40,  50,  52 ]
        self.cIDs = [DBL.create_readout("c%i"%l, "AS7341", "%i+-%inm band"%(l, self.FWHMs[n]), "μW/cm^2/nm") for n,l in enumerate(self.wavelengths)]
        self.sensor = None

    def read(self, SIO):

        if self.sensor is None:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_as7341.AS7341(i2c)
            self.sensor.astep = 999  # integration step size in 2.78us increments
            self.sensor.atime = 100  # number of integration time steps -> total (atime + 1)*(astep + 1)*2.78 us
            self.sensor.gain = 10    # binary powers 2^(g-1) for g = 0 ... 10

        try:
            self.t = time.time()
            chans = self.sensor.all_channels
            T_integ = (self.sensor.atime + 1) * (self.sensor.astep + 1) * 2.78e-6

            print("AS7341 Multispectral Sensor, integration %.3f s" % T_integ)
            for i,c in enumerate(chans):
                norm = 1./(2**(self.sensor.gain - 1) * T_integ * self.FWHMs[i])
                print(" * %inm [%i]\t%.4f"%(self.wavelengths[i], c, c*norm))
                #SIO.log_readout(self.cIDs[i], c*norm, self.t)
            print("---------------------\n\n")

            # adjust for next readout
            cmax = max(chans)
            if cmax: self.sensor.atime = min(max((2**15)*(self.sensor.atime + 1)/cmax, 1), 256) - 1

        except:
            traceback.print_exc()
            self.sensor = None
