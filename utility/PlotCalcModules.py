
from sensor_defs.humidity import *
from sensor_defs.AQI import *
from PlotUtils import *

class TFahren:
    def __init__(self):
        self.rids = [1]
        self.name = "T"
        self.descrip = "indoor temperature"
        self.units = "deg F"
    def f(self, p):
        return 9*p/5 + 32

class AbsHum:
    def __init__(self):
        self.rids = [46,47]
        self.name = "H_abs"
        self.descrip = "absolute humidity"
        self.units = "g/m^3"

    def f(self, p):
        return RH_to_Abs_Humidity(p[1], p[0])

class Dewpt:
    def __init__(self):
        self.rids = [46,47]
        self.name = "T_d"
        self.descrip = "dewpoint"
        self.units = "deg. C"

    def f(self, p): return dewpoint(p[0], p[1])

class AQIcalc:
    def __init__(self):
        self.rids = [43,44]
        self.name = "AQI"
        self.descrip = "EPA Air Quality Index estimate from PM2.5"
        self.units = None

    def f(self, p): return PM25_to_AQI(p[0] + p[1])

class SpectrumMean:
    def __init__(self):
        self.rids = [21,22,23,24,25,26]
        self.name = "mean wavelength"
        self.descrip = "Average visible wavelength"
        self.units = "nm"

    def f(self, p):
        l = [650., 600., 570., 550., 500., 450.]
        return sum([l[n]*i for n,i in enumerate(p)])/sum(p)

class SpectrumSum:
    def __init__(self):
        self.rids = [21,22,23,24,25,26]
        self.name = "total light"
        self.descrip = "Summed visible light"
        self.units = "μW/cm^2"

    def f(self, p): return sum(p)

class ColorTemp:
    def __init__(self):
        self.rids = [21,22,23,24,25,26]
        self.name = "T_c"
        self.descrip = "Color temperature"
        self.units = "K"

        self.Ts = [9000, 8750, 8500, 8250, 8000, 7750, 7500, 7250, 7000, 6750, 6500, 6250, 6000, 5750, 5500, 5250, 5000, 4750, 4500, 4250, 4000, 3750, 3500, 3250, 3000, 2750, 2500, 2250, 2000, 1750, 1500]
        self.ls = [539.162105717397, 539.778748361909, 540.4335784331724, 541.1299035953488, 541.8713920423279, 542.6621190952158, 543.5066206088521, 544.4099543590015, 545.3777706142914, 546.416393424196, 547.5329143303485, 548.7353004871363, 550.0325194573977, 551.4346832375396, 552.9532143419821, 554.6010369650039, 556.3927963358952, 558.3451091300724, 560.476847151617, 562.8094550260844, 565.3672999837717, 568.178047396389, 571.2730489830609, 574.6877211972769, 578.4618797557395, 582.6399846479266, 587.2712409124756, 592.409485419424, 598.1126909127656, 604.4413585322491, 611.4525775939203]

    def f(self, p):
        l = [650., 600., 570., 550., 500., 450.]
        lbar = sum([l[n]*i for n,i in enumerate(p)])/sum(p)
        return lin_interp(self.ls, self.Ts, lbar)

calcmodules = {"degF": TFahren, "absH": AbsHum, "dewpt": Dewpt,
               "AQI": AQIcalc, "lmean": SpectrumMean, "lsum": SpectrumSum, "Tc": ColorTemp}
