# taken from PTM website
# we assume height from ground is inf
# the "height" mentioned here is the height from the lower layer
def get_wire_cap(pitch, width, thickness, height):
    epsilon = 2.2
    epsilon0 = 8.854e-12
    # horizontal cap
    spacing = pitch - width
    t1 = 1.41*thickness/spacing
    t2 = 2.37*( (width/(width+0.31*spacing))**0.28 )
    c_horiz = (t1 + t2)*epsilon*epsilon0
    # vertical cap
    # here, earlier thickness == width
    # earlier width == thickness
    h = height - thickness
    t1 = width/h
    t2 = 2.04*(( (thickness/(thickness+4.53*h))**0.28 )
               * ( (spacing/(spacing+0.54*h))**1.77 ))
    c_vert = (t1 + t2)*epsilon*epsilon0
    return 2*(c_horiz + c_vert)

class WireModel:
    def __init__(self, **kwargs):
        self.pitch = kwargs["pitch"]
        self.width = kwargs["width"]
        self.thickness = kwargs["thickness"]
        self.height = kwargs["height"]
        self.l = kwargs["l"]
        self.c_per_l = get_wire_cap(self.pitch,
                                    self.width,
                                    self.thickness,
                                    self.height)

    def get_normalized_capacitance(self):
        return self.c_per_l / 1.4e-9

    def get_capacitance(self):
        return self.c_per_l

    def get_normalized_resistance(self):
        # assume a Rpersq of 0.28 Ohm
        # also normalize to lambda
        return 0.28/(self.width*1e-6) * self.l

    def get_resistance(self):
        # assume a Rpersq of 0.28 Ohm
        return 0.28/(self.width*1e-6)

class CellModel:
    def __init__(self, **kwargs):
        self.cin = kwargs["cin"]
        self.w = kwargs["w"]
        self.h = kwargs["h"]

    def get_input_load(self):
        return self.cin

    def get_wpitch(self):
        return self.w

    def get_hpitch(self):
        return self.h

