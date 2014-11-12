from gates import *
from models import *
from logic_path import LogicPath
from operator import mul
from math import log

# create a predecoder chain
# the algorithm is as follows
# start with the highest level, and recursively split it into 2
# at each level, if the size is odd, take the smaller partition
# create a branch of 2**(other branch size)
# continue until smaller branch is of size 2 or 1
def create_predecoder_chain(Bp):
    chain = []
    branch = []
    units = []
    numBits = Bp
    while numBits != 2 and numBits != 1:
        smallerBranch = numBits/2
        largerBranch = numBits-smallerBranch
        chain.insert(0, Inv())
        chain.insert(0, Nand(N=2))
        branch.insert(0, 1)
        branch.insert(0, 2**largerBranch)
        # both these gates have multiplicities of 2**numBits
        units.insert(0, 2**numBits)
        units.insert(0, 2**numBits)
        numBits = smallerBranch
    if numBits == 2:
        chain.insert(0, Inv())
        chain.insert(0, Nand(N=2))
        branch.insert(0, 1)
        units.insert(0, 2)
        units.insert(0, 2)
    else:
        chain.insert(0, Inv())
        units.insert(0, 1)
    return chain, branch, units

def nearest_even(x):
    return int(round(x/2))*2

class Decoder:
    # a decoder which is built out of three stages
    # a predecoder, a global decoder and a local decoder
    # a decoder can be built given the following parameters
    # @Ba: number of bits in address
    # @Bp: number of bits to predecode, we assume that the address is split as
    # Bp+Bp+Bl
    # @Nl: number of bits in each output word
    # Given these parameters, we can derive that
    # @Bl: Ba - 2*Bp
    # @Nw: width of memory array = Nl * (2**Bl)
    # @Nh: height of memory array = (2**Ba) / (2**Bl)

    def __init__(self, **kwargs):
        self.Ba = kwargs["Ba"]
        self.Bp = kwargs["Bp"]
        self.Nl = kwargs["Nl"]

        # load models
        self.default_wire_model = kwargs["default_wire_model"]
        self.wordline_wire_model = kwargs["wordline_wire_model"]
        self.cell_model = kwargs["cell_model"]

        # derived parameters
        self.Bl = self.Ba - 2*self.Bp
        self.Nw = self.Nl * (2**self.Bl)
        self.Nh = 2**(self.Ba - self.Bl)
        self.cin_load = kwargs["cin"]

    def get_cell_load(self):
        return self.Nl * self.cell_model.get_input_load()

    def get_lwl_load(self):
        return (self.Nl * self.wordline_wire_model.get_normalized_capacitance()
                * self.cell_model.get_wpitch())

    def get_lwl_resistance(self):
        return (self.Nl * self.wordline_wire_model.get_normalized_resistance()
                * self.cell_model.get_wpitch())

    def get_gwl_sideload(self):
        return (self.Nw * self.wordline_wire_model.get_normalized_capacitance()
                * self.cell_model.get_wpitch())

    def get_gwl_resistance(self):
        return (self.Nw * self.wordline_wire_model.get_normalized_resistance()
                * self.cell_model.get_wpitch())

    def get_predecoder_sideload(self):
        return (self.Nh * self.default_wire_model.get_normalized_capacitance()
                * self.cell_model.get_hpitch())

    def get_predecoder_resistance(self):
        return (self.Nh * self.default_wire_model.get_normalized_resistance()
                * self.cell_model.get_hpitch())


    # generate a "candidate" optimal logic path
    def generate_logic_path(self):
        # for this we follow the following procedure
        # for input to predecoder
        # split the required number of nands into nand3 and nand2s
        # insert the sideload
        # put the required number of nands from predecoder to global wordline
        # put one nand from global to local wordline (we assume that the local
        # wordline enable has been predecoded)
        # insert required number of inverters at the end

        # create the predecoder chain
        chain, branches, units = create_predecoder_chain(self.Bp)

        # get the optimal number of levels to get to the predecoder sideload
        # if that is < the current number of levels, insert a few more
        predecoder_sideload = self.get_predecoder_sideload()
        predecoder_load = predecoder_sideload * reduce(mul, branches, 1)
        le = reduce(mul, [g.get_le() for g in chain], 1)
        effort = predecoder_load/self.cin_load * le * 2
        opt_predecoder_levels = log(effort, 4)

        if opt_predecoder_levels > len(chain):
            for i in range(nearest_even(opt_predecoder_levels-len(chain))):
                chain.append(Inv())
                branches.append(1)

        # now create the predecoder branching
        branches.append(2**self.Bp)

        # only the last level has the predecoder sideload
        sideloads = [0 for i in range(len(chain)-1)] + [predecoder_sideload]

        # the last level has a resistance
        predecoder_resistance = self.get_predecoder_resistance()
        resistances = ([0 for i in range(len(chain)-1)] +
                       [predecoder_resistance])

        # done with predecoder, now do the decoder chain
        chain.append(Nand(N=2))
        chain.append(Inv())
        branches.append(1)
        sideloads.append(0)
        resistances.append(0)
        units.append(2**(2*self.Bp))
        units.append(2**(2*self.Bp))

        # from here, there are two possibilities
        # if there is a gwl to lwl partitioning, we have to consider the gwl
        # load as a sideload, else there is no gwl sideload and there is simply
        # the lwl load
        if self.Bl > 0:
            gwl_sideload = self.get_gwl_sideload()
            gwl_load = gwl_sideload * reduce(mul, branches, 1)
            gwl_and_predecoder_load = gwl_load + predecoder_load
            le = reduce(mul, [g.get_le() for g in chain], 1)
            effort = gwl_and_predecoder_load/self.cin_load * le * 2
            opt_gwl_levels = log(effort, 4)

            if opt_gwl_levels > len(chain):
                for i in range(nearest_even(opt_gwl_levels-len(chain))):
                    chain.append(Inv())
                    branches.append(1)
                    sideloads.append(0)
                    resistances.append(0)
                    units.append(2**(2*self.Bp))

            # now insert the gwl sideload and create the gwl to lwl branching
            # factor
            branches.append(2**self.Bl)
            sideloads.append(gwl_sideload)

            gwl_resistance = self.get_gwl_resistance()
            resistances.append(gwl_resistance)

            # create the lwl nand and inverter
            chain.append(Nand(N=2))
            chain.append(Inv())
            branches.append(1)
            branches.append(1)
            sideloads.append(0)
            sideloads.append(0)
            resistances.append(0)
            resistances.append(0)
            units.append(2**(self.Ba))
            units.append(2**(self.Ba))

        else:
            # case where there is no gwl
            # the previous inverter has no branch or sideload in this case
            branches.append(1)
            sideloads.append(0)
            resistances.append(0)
            gwl_and_predecoder_load = predecoder_load

        # the last part corresponding to the wordline + cells
        each_lwl_load = self.get_lwl_load() + self.get_cell_load()
        lwl_load = each_lwl_load * reduce(mul, branches, 1)
        total_load = gwl_and_predecoder_load + lwl_load
        le = reduce(mul, [g.get_le() for g in chain], 1)
        effort = total_load/self.cin_load * le * 2
        opt_levels = log(effort, 4)
        if opt_levels > len(chain):
            for i in range(nearest_even(opt_levels-len(chain))):
                chain.append(Inv())
                branches.append(1)
                sideloads.append(0)
                resistances.append(0)
                units.append(2**(self.Ba))

        each_lwl_resistance = self.get_lwl_resistance()

        # the full chain is ready now, now simply optimize it using the
        # logic_path api
        logic_path = LogicPath(chain=chain,
                               branches=branches,
                               sideloads=sideloads,
                               resistances=resistances,
                               units=units,
                               cin=self.cin_load,
                               cout=each_lwl_load,
                               rout=each_lwl_resistance)
        logic_path.optimize()
        return logic_path

    def get_width(self):
        # decoder width = width of the predecoder array
        # we assume that each of the gates are laid out with the broad side
        predecoder_wires = 2*(2**self.Bp)
        wire_pitch = 8 * self.default_wire_model.l
        return predecoder_wires * wire_pitch
