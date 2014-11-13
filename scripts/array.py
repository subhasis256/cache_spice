import decoder
import sram
import gates
import spiceutils
import models
import logic_path
import sys
import yaml
import global_wire


class Array:
    def __init__(self, **kwargs):
        # array contains a decoder and a sram
        self.decoder = decoder.Decoder(**kwargs)
        self.Nw = self.decoder.Nw
        self.Nh = self.decoder.Nh

    def generate(self):
        self.logic_path = self.decoder.generate_logic_path()
        self.sram_stats = sram.simulate_sram(self.Nw, self.Nh)
        self.crit_delay = 0

        self.gate_stats = []

        for i,g in enumerate(self.logic_path.chain):
            load = self.logic_path.get_output_load_at_stage(i)
            rload = self.logic_path.get_output_resistance_at_stage(i)
            gate_stat = gates.simulate_gate(g, load, rload)
            self.gate_stats.append(gate_stat)

    def get_delay(self):
        crit_delay = float(self.sram_stats["bl0_delay"])
        for i,s in enumerate(self.gate_stats):
            if i % 2 == 0:
                crit_delay += float(s["fall_out"])
            else:
                crit_delay += float(s["rise_out"])
        return crit_delay

    def get_energy(self):
        # estimate the gate energy from the logic path
        total_energy = 0
        for i,s in enumerate(self.gate_stats):
            e = float(s["e_switch_nj"])
            total_energy += e
        # estimate the array energy from the array simulation
        # note that the array simulation assumes activation of all the cells in
        # a wordline, so we have to divide by the global->local decoding factor
        sram_row_energy = float(self.sram_stats["e_peracc"])/1e-9
        sram_energy = sram_row_energy / (2**self.decoder.Bl)
        total_energy += sram_energy

        # convert to SI units
        total_energy *= 1e-9
        return total_energy

    # return Lw, Lh: the width and height of the array
    def get_size(self):
        # get the sram size
        sram_w = (self.decoder.Nw * self.decoder.cell_model.get_wpitch()
                  * self.decoder.default_wire_model.l)
        sram_h = (self.decoder.Nh * self.decoder.cell_model.get_hpitch()
                  * self.decoder.default_wire_model.l)
        # get the decoder width
        # decoder height = array height
        decoder_w = self.decoder.get_width()
        total_w = decoder_w + sram_w
        total_h = sram_h

        # we assume a packing efficiency with everything of ~ 64%, which
        # translates to dividing both the dimensions by 0.8
        # TODO this is hacky
        return total_w/0.8, total_h/0.8

if __name__ == '__main__':
    yaml_config_file = open(sys.argv[1])
    yaml_doc = yaml.load(yaml_config_file)

    # these values are in lambda,
    # cin = total input capacitance of the wordline transistors
    # w = width (along the wordline)
    # h = height (along the bitline)
    cell_model_params = {"cin": 8,
                         "w": 16,
                         "h": 40}
    if "cell_model" in yaml_doc:
        cell_model_params = yaml_doc["cell_model"]

    cell_model = models.CellModel(**cell_model_params)

    # the minimum pitch version
    # min feature size
    if "technology" in yaml_doc:
        l = yaml_doc["technology"]["lambda"]*1e-6
    else:
        l = 0.022e-6

    # these parameters can be overriden via the yaml file
    # note that these are in um
    wire_model_params = {"pitch": 0.14,
                         "width": 0.07,
                         "height": 0.26,
                         "thickness": 0.125,
                         "l": l}

    if "wire_model" in yaml_doc:
        wire_model_params = yaml_doc["wire_model"]
        wire_model_params["l"] = l

    default_wire_model = models.WireModel(**wire_model_params)

    # the wordlines
    # we need a separate model for this since the wordlines have a different pitch
    # and width
    wordline_pitch = cell_model.h * default_wire_model.l / 1e-6

    wordline_wire_model = models.WireModel(pitch=wordline_pitch,
                                           width=wordline_pitch/2,
                                           thickness=wire_model_params["thickness"],
                                           height=wire_model_params["height"],
                                           l=l)

    # the global wire model
    # eperl = energy per bit per mm in pJ/mm assuming activity factor of 0.25
    # tperl = delay per mm in ns/mm
    global_wire_params = {"eperl": 0.1,
                          "tperl": 0.4}
    if "global_wire_model" in yaml_doc:
        global_wire_params = yaml_doc["global_wire_model"]

    global_wire_model = global_wire.GlobalWire(**global_wire_params)

    tech_params = {}
    tech_params["default_wire_model"] = default_wire_model
    tech_params["wordline_wire_model"] = wordline_wire_model
    tech_params["cell_model"] = cell_model

    tech_params["cin"] = yaml_doc["array"]["cin"]
    # create an approximately square array
    num_words = yaml_doc["array"]["num_words"]
    word_width = yaml_doc["array"]["word_width"]
    total_bits = num_words * word_width

    def floor_sqrt_pwr2(x):
        sqrt = int(x**0.5)
        if sqrt*sqrt != x:
            return int((x/2)**0.5)
        else:
            return sqrt

    def log2(x):
        if x == 1:
            return 0
        else:
            return log2(x/2) + 1

    height = floor_sqrt_pwr2(total_bits)

    Ba = log2(num_words)
    Bp = log2(height)/2
    Nl = word_width

    tech_params["Ba"] = Ba
    tech_params["Bp"] = Bp
    tech_params["Nl"] = Nl

    array = Array(**tech_params)
    array.generate()

    print 'Delay = ', array.get_delay(), 'Energy = ', array.get_energy()
    print 'Size = ', ['%.3f mm ' % (x*1e3,) for x in array.get_size()]
