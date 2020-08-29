
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
        self.ls = [538.832955071252, 539.4398819271647, 540.085572552261, 540.7735044958038, 541.507549107634, 542.2920245043791, 543.131756633243, 544.032149781388, 544.9992681074725, 546.039930032962, 547.1618176236237, 548.3736034106453, 549.685097432107, 551.107417590376, 552.6531866657283, 554.336759406451, 556.1744828701142, 558.184992356081, 560.3895434288411, 562.8123770562887, 565.4811088921613, 568.4271241253792, 571.685945127803, 575.2975205156426, 579.3063649263813, 583.7614707327092, 588.7159414303742, 594.2263908166467, 600.3522483499054, 607.1545910759627, 614.6901177891494]


    def f(self, p):
        l = [650., 600., 570., 550., 500., 450.]
        lbar = sum([l[n]*i for n,i in enumerate(p)])/sum(p)
        return lin_interp(self.ls, self.Ts, lbar)

calcmodules = {"degF": TFahren, "absH": AbsHum, "dewpt": Dewpt,
               "AQI": AQIcalc, "lmean": SpectrumMean, "lsum": SpectrumSum, "Tc": ColorTemp}
