import sys
import re
import models

width_mm = float(sys.argv[1])
pitch_um = width_mm/512*1e3

wire = models.WireModel(pitch=pitch_um,
                        width=0.07,
                        thickness=0.14,
                        height=0.26,
                        l=0.022)
print wire.get_capacitance()
print wire.get_resistance()
