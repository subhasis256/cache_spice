import decoder
import sram
import gates
import spiceutils
import models
import logic_path


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

