import time
import board
import busio
import adafruit_as7341
from . import SensorItem
import traceback

class My_AS7341(adafruit_as7341.AS7341):
    def __init__(self, i2c):
        adafruit_as7341.AS7341.__init__(self,i2c)

    @property
    def all_channels_plus(self):
        """The current readings for 8 wavelength, clear, IR channels"""

        self._configure_f1_f4()
        adc_reads_f1_f4 = self._all_channels # latches readings values
        readsA = adc_reads_f1_f4[1:]

        self._configure_f5_f8()
        adc_reads_f5_f8 = self._all_channels # latches readings values
        readsB = adc_reads_f5_f8[1:]

        # extras are clear, IR
        return readsA[:-2] + readsB[:-2] + (0.5*(readsA[-2] + readsB[-2]), 0.5*(readsA[-1] + readsB[-1]))


class AS7341Monitor(SensorItem):

    def __init__(self, DBL, dt):
        SensorItem.__init__(self, dt)

        self.g_id = DBL.create_readout("AS7341", "AS7341 multispectral light sensor", None)
        self.wavelengths = [415, 445, 480, 515, 555, 590, 630, 680]
        self.FWHMs =       [26,  30,  36,  39,  39,  40,  50,  52 ]
        self.cIDs = [DBL.create_readout("AS7341/c%i"%l, "%i+-%inm band"%(l, self.FWHMs[n]), "μW/cm^2/nm") for n,l in enumerate(self.wavelengths)]
        self.cIDs.append(DBL.create_readout("AS7341/light", "clear filter light sensor", ""))
        self.cIDs.append(DBL.create_readout("AS7341/NIR", "near-infrared light sensor ~910nm", ""))
        self.wavelengths += [0, 910]
        self.sensor = None

    def read(self, SIO):

        if self.sensor is None:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = My_AS7341(i2c)
            self.sensor.astep = 999  # integration step size in 2.78us increments
            self.sensor.atime = 100  # number of integration time steps -> total (atime + 1)*(astep + 1)*2.78 us
            self.sensor.gain = 10    # binary powers 2^(g-1) for g = 0 ... 10

        try:
            self.t = time.time()
            chans = self.sensor.all_channels_plus
            T_integ = (self.sensor.atime + 1) * (self.sensor.astep + 1) * 2.78e-6

            print("AS7341 Multispectral Sensor, integration %.3f s" % T_integ)
            for i,c in enumerate(chans):
                norm = 1./(2**(self.sensor.gain - 1) * T_integ)
                print(" * %3inm [%i]\t%.4f"%(self.wavelengths[i], c, c*norm))
                SIO.log_readout(self.cIDs[i], c*norm, self.t)
            print("---------------------\n\n")

            # adjust for next readout
            cmax = max(chans)
            if cmax: self.sensor.atime = int(min(max((2**15)*(self.sensor.atime + 1)/cmax, 1), 256)) - 1

        except:
            traceback.print_exc()
            self.sensor = None
