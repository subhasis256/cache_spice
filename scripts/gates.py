import subprocess
import sys
import spiceutils

# a generic gate
# has a logical effort
# has a parasitic delay

class Gate:
    def __init__(self, **kwargs):
        pass

    def get_le(self):
        pass

    def get_gamma(self):
        pass

    def get_input_load(self):
        pass

    def set_size(self):
        pass

    def get_type(self):
        pass

    def write_spice_params(self, pfile):
        pass

# an inverter
class Inv(Gate):
    # one can either specify nothing, in which case the default values of ratio,
    # LE and gamma will be used
    # otherwise one must provide all of ratio, gamma and LE for the critical
    # edge

    def __init__(self, **kwargs):
        # LE = logical effort
        # ratio = ratio of pwidth : nwidth
        # gamma = parasitic delay of gate
        self.LE = 1.0
        self.ratio = 3.0
        self.gamma = 1.0

        if ("ratio" in kwargs) or ("LE" in kwargs) or ("gamma" in kwargs):
            assert "LE" in kwargs, """you must specify ratio, LE and gamma or none
            of them"""
            assert "gamma" in kwargs, """you must specify ratio, LE and gamma or
            none of them"""

            self.ratio = float(kwargs["ratio"])
            self.LE = float(kwargs["LE"])
            self.gamma = float(kwargs["gamma"])

    def get_le(self):
        return self.LE

    def get_gamma(self):
        return self.gamma

    def set_size(self, Cin):
        self.Wn = Cin/(self.ratio + 1.0)
        self.Wp = Cin*self.ratio/(self.ratio + 1.0)

    def get_input_load(self):
        return self.Wn + self.Wp

    def get_type(self):
        return "inv"

    def write_spice_params(self, pfile):
        print >> pfile, ".param Wn=%.2f"%(self.Wn,)
        print >> pfile, ".param Wp=%.2f"%(self.Wp,)

    def __repr__(self):
        return ("Inv(ratio=%.4f,LE=%.4f,gamma=%.4f,Wn=%.4f,Wp=%.4f)"
                % (self.ratio, self.LE, self.gamma, self.Wn, self.Wp))


# a nand gate with configurable number of inputs
class Nand(Gate):
    # one can either specify N, in which case the analytical values of ratio,
    # LE and gamma will be used
    # otherwise one must provide all of ratio, gamma and LE for the critical
    # edge

    def __init__(self, **kwargs):
        # N = number of inputs
        # LE = logical effort
        # ratio = ratio of pwidth : nwidth
        # gamma = intrinsic parasitic delay
        self.N = 2
        self.LE = 1.0
        self.ratio = 3.0
        self.gamma = 1.0

        if "N" in kwargs:
            self.N = kwargs["N"]
            self.ratio = 3.0/self.N
            self.LE = (3.0 + self.N)/4.0
            self.gamma = 1.0

        if ("ratio" in kwargs) or ("LE" in kwargs) or ("gamma" in kwargs):
            assert "LE" in kwargs, """you must specify ratio, LE and gamma or none
            of them"""
            assert "gamma" in kwargs, """you must specify ratio, LE and gamma or
            none of them"""

            self.ratio = float(kwargs["ratio"])
            self.LE = float(kwargs["LE"])
            self.gamma = float(kwargs["gamma"])

    def get_le(self):
        return self.LE

    def get_gamma(self):
        return self.gamma

    def set_size(self, Cin):
        self.Wn = Cin/(self.ratio + 1.0)
        self.Wp = Cin*self.ratio/(self.ratio + 1.0)

    def get_input_load(self):
        return self.Wn + self.Wp

    def get_type(self):
        return "nand"+str(self.N)

    def write_spice_params(self, pfile):
        print >> pfile, ".param Wn=%.2f"%(self.Wn,)
        print >> pfile, ".param Wp=%.2f"%(self.Wp,)

    def __repr__(self):
        return ("Nand(N=%d,ratio=%.4f,LE=%.4f,gamma=%.4f,Wn=%.4f,Wp=%.4f)"
                % (self.N, self.ratio, self.LE, self.gamma, self.Wn, self.Wp))


def simulate_gate(gate, load, rload):
    paramsfile = open('../spice/gates/parameters.sp', 'w')
    gate.write_spice_params(paramsfile)
    print >> paramsfile, ".param Wload=%s"%(spiceutils.spice_format(load),)
    print >> paramsfile, ".param Rload=%s"%(spiceutils.spice_format(rload),)
    print >> paramsfile, ".include \"%s.ckt\""%(gate.get_type(),)
    paramsfile.close()

    devnull = open('/dev/null', 'w')
    subprocess.call("hspice ../spice/gates/wiredriver.sp", stdout=devnull,
                    stderr=subprocess.STDOUT, shell=True)
    devnull.close()

    return spiceutils.read_mt0('wiredriver.mt0')[0]
