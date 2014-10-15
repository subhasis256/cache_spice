# a very simplistic model for global wires
# assuming constant delay and energy per length
class GlobalWire:
    def __init__(self, **kwargs):
        self.e_per_l = kwargs["eperl"]*1e-9
        self.t_per_l = kwargs["tperl"]*1e-6

    def get_delay(self, l):
        return self.t_per_l * l

    def get_energy(self, l):
        return self.e_per_l * l

# get the H-tree wire length for a given cache config
# parameters
# Lw: width of each array in SI units
# Lh: height of each array
# Nw: number of arrays along width dimension (x)
# Nh: number of arrays along height dimension (y)
# we assume that the H tree brings data to the middle bottom edge
def get_htree_wire_length(Lw, Lh, Nw, Nh):
    W = Lw * Nw
    H = Lh * Nh
    arrays_served = Nw*Nh
    length = 0
    direction = 0
    while arrays_served > 2:
        if direction == 0:
            length += W/2
            W /= 2
        else:
            length += H/2
            H /= 2
        direction = 1-direction
        arrays_served /= 2
    # actual distance traversed is only half of this
    length /= 2
    # account for the final output branch
    length += (Lh * Nh)/2
    return length
