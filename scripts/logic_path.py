from operator import mul

# we are trying to optimize a logic chain
# a logic chain consists of the constituent gates,
# the branching factors at each node
# and the sideloads at each node
class LogicPath:
    def __init__(self, **kwargs):
        # one has to specify a "chain" while creating a decoder
        # this is in the form of a vector of gates, with each gate
        # having its own LE
        # we also need the input load, the output load, the branching factors
        # and the sideloads, if any
        # the branching factors and sideloads are both specified as a map
        # where the key is the stage at whoose output the branching or the
        # sideload occurs and the value is the sideload or branching factor

        self.chain = kwargs["chain"]
        self.branch = kwargs["branches"]
        self.sideloads = kwargs["sideloads"]
        self.resistances = kwargs["resistances"]
        self.units = kwargs["units"]
        self.cload_input = kwargs["cin"]
        self.cload_output = kwargs["cout"]
        self.rload_output = kwargs["rout"]

    def get_output_load_at_stage(self, i):
        if i == len(self.chain)-1:
            load = self.cload_output
        else:
            load = self.chain[i+1].get_input_load()
        return self.branch[i] * load + self.sideloads[i]

    def get_output_resistance_at_stage(self, i):
        if i == len(self.chain)-1:
            return self.rload_output + self.resistances[i]
        else:
            return self.resistances[i]

    def get_input_load_at_stage(self, i):
        if i == 0:
            return self.cload_input
        else:
            return self.chain[i].get_input_load()

    def size_stages(self, begin, end, cin, cout):
        # size all gates in the range [begin,end] (both inclusive)
        # consider edge case where begin == end
        if begin == end:
            self.chain[begin].set_size(cin)
            return

        # any branching at output is not considered, only branching within the
        # range [begin,end-1] is considered
        path_LE = reduce(mul,
                         [g.get_le() for g in self.chain[begin:(end+1)]],
                         1)
        path_BE = reduce(mul, self.branch[begin:end], 1)
        path_effort = path_BE * path_LE * cout / cin

        # now calculate the stage effort
        numstages = end - begin + 1
        stage_effort = path_effort ** (1/float(numstages))

        # size each gate
        # the first gate will have size = Cin
        # subsequent gates will have size =
        # C_{n-1}*stage_effort/BE_{n-1}/LE_{n-1}
        self.chain[begin].set_size(cin)

        for i in range(begin+1, end+1):
            size = (self.chain[i-1].get_input_load() * stage_effort
                    / self.chain[i-1].get_le() / self.branch[i-1])
            self.chain[i].set_size(size)

    def optimize_nosideload(self):
        # let us optimize without the sideloads first
        self.size_stages(0, len(self.chain)-1,
                         self.cload_input,
                         self.cload_output)

    def optimize(self):
        # in order to do optimization with sideload,
        # we first optimize with sideload,
        # then we go back and at each stage with sideload,
        # create a new stage effort considering the new output load
        self.optimize_nosideload()

        # split chain at each sideload
        # organize the splits from begin -> end
        # as we will be doing the optimization in that order
        splits = []
        last_begin = 0
        for i in range(len(self.chain)):
            if self.sideloads[i] != 0:
                splits.append((last_begin, i))
                last_begin = i

        # if no sideloads have been found, we are done
        if len(splits) != 0:

            # append the last split, which ends at len(chain)
            splits.append( (last_begin, len(self.chain)-1) )

            # for each split, do an optimization
            # repeat for 3 times, in general once is enough to get a very close
            # approximation, but do it thrice just in case
            for i in range(3):
                for begin, end in splits:
                    self.size_stages(begin,
                                     end,
                                     self.get_input_load_at_stage(begin),
                                     self.get_output_load_at_stage(end))


    def estimate_delay(self):
        total_delay = 0
        for i in range(len(self.chain)):
            delay = (self.get_output_load_at_stage(i) /
                     self.get_input_load_at_stage(i) *
                     self.chain[i].get_le() +
                     self.chain[i].get_gamma())
            total_delay += delay

        return total_delay

    def dump(self):
        for i,g in enumerate(self.chain):
            print g.get_type(), g.get_params(), self.get_output_load_at_stage(i)
