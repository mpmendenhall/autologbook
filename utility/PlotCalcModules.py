
from sensor_defs.humidity import *
from sensor_defs.AQI import *

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

calcmodules = {"degF": TFahren, "absH": AbsHum, "dewpt": Dewpt,
               "AQI": AQIcalc, "lmean": SpectrumMean, "lsum": SpectrumSum}

