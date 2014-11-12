# the overall "cache" model
# we assume both the tag and the data arrays are made up of 8KB arrays
# we use global wires to route between the arrays

import sys

import array
import global_wire
import models

import yaml

def log2(x):
    if x == 1:
        return 0
    else:
        return log2(x/2)+1

# compute the array width for a given read width
# an array can be at most 256 bits wide
def get_array_width(x):
    if x <= 256:
        return x
    else:
        return get_array_width(x/2)

def get_array_height(x):
    if x <= 256:
        return x
    else:
        return get_array_height(x/2)

def get_square_matrix(x):
    if x == 1:
        return (1,1)
    sqrt = int(x**0.5)
    if sqrt * sqrt != x:
        Nw = int((x*2)**0.5)
        Nh = int((x/2)**0.5)
    else:
        Nw = sqrt*2
        Nh = sqrt/2
    return Nw, Nh

class Cache:
    def __init__(self, **kwargs):
        self.physbits = kwargs["physbits"]
        self.size = kwargs["size"]
        self.bsize = kwargs["bsize"]
        self.assoc = kwargs["assoc"]

        tech_params = {}
        tech_params["default_wire_model"] = kwargs["default_wire_model"]
        tech_params["wordline_wire_model"] = kwargs["wordline_wire_model"]
        tech_params["cell_model"] = kwargs["cell_model"]
        tech_params["cin"] = kwargs["cin"]

        self.tech_params = tech_params

        self.global_wire_model = kwargs["global_wire_model"]

    def generate_tagarray(self):
        setaddrbits = log2(self.size/self.assoc)
        self.tagbits = self.physbits - setaddrbits

        # all tags are read in parallel
        tagreadwidth = self.tagbits * self.assoc
        tagarraywidth = get_array_width(tagreadwidth)

        # compute the tag array height
        tagheight = self.size/self.assoc/self.bsize
        tagarrayheight = get_array_height(tagheight)

        numtagarrays = (tagheight * tagreadwidth
                        / tagarrayheight / tagarraywidth)

        # compute the number of arrays in x vs y directions
        # this simply does sqrt(N) x sqrt(N) array in case numtagarrays is a
        # square, else a sqrt(N*2) x sqrt(N/2) array
        Nw, Nh = get_square_matrix(numtagarrays)

        tagarrayparams = self.tech_params
        tagarrayparams["Ba"] = log2(tagarrayheight)
        tagarrayparams["Bp"] = log2(tagarrayheight)/2
        tagarrayparams["Nl"] = tagarraywidth

        self.tagarray = array.Array(**tagarrayparams)
        self.tagarray.generate()

        Lw, Lh = self.tagarray.get_size()
        htree_length = global_wire.get_htree_wire_length(Lw, Lh, Nw, Nh)

        htree_delay = self.global_wire_model.get_delay(htree_length)

        htree_energy_perbit = self.global_wire_model.get_energy(htree_length)
        htree_energy = htree_energy_perbit * tagreadwidth

        array_delay = self.tagarray.get_delay()
        array_energy = (self.tagarray.get_energy()
                        * tagreadwidth / tagarraywidth)

        # for delay we have to assume twice the htree delay: once for input and
        # then for output
        self.tagarray_energy_mat = array_energy
        self.tagarray_energy_wire = htree_energy

        self.tagarray_energy = array_energy + htree_energy
        self.tagarray_delay = array_delay + htree_delay*2
        self.tagarray_size = (Lw*Nw, Lh*Nh)


    def generate_dataarray(self):
        # assuming sequential access, that is,
        # only data of one way is read
        datareadwidth = self.bsize * 8
        dataarraywidth = get_array_width(datareadwidth)

        # compute the data array height
        dataheight = self.size/self.bsize
        dataarrayheight = get_array_height(dataheight)

        numdataarrays = (dataheight * datareadwidth
                        / dataarrayheight / dataarraywidth)

        # compute the number of arrays in x vs y directions
        Nw, Nh = get_square_matrix(numdataarrays)

        dataarrayparams = self.tech_params
        dataarrayparams["Ba"] = log2(dataarrayheight)
        dataarrayparams["Bp"] = log2(dataarrayheight)/2
        dataarrayparams["Nl"] = dataarraywidth

        self.dataarray = array.Array(**dataarrayparams)
        self.dataarray.generate()

        Lw, Lh = self.dataarray.get_size()
        htree_length = global_wire.get_htree_wire_length(Lw, Lh, Nw, Nh)

        htree_delay = self.global_wire_model.get_delay(htree_length)

        htree_energy_perbit = self.global_wire_model.get_energy(htree_length)
        htree_energy = htree_energy_perbit * datareadwidth

        array_delay = self.dataarray.get_delay()
        array_energy = (self.dataarray.get_energy()
                        * datareadwidth / dataarraywidth)

        # for delay we have to assume twice the htree delay: once for input and
        # then for output
        self.dataarray_energy_mat = array_energy
        self.dataarray_energy_wire = htree_energy

        self.dataarray_energy = array_energy + htree_energy
        self.dataarray_delay = array_delay + htree_delay*2
        self.dataarray_size = (Lw*Nw, Lh*Nh)

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

assert "cache" in yaml_doc, """yaml file should contain information about
cache"""
cache_params = yaml_doc["cache"]
cache_params["cell_model"] = cell_model
cache_params["default_wire_model"] = default_wire_model
cache_params["wordline_wire_model"] = wordline_wire_model
cache_params["global_wire_model"] = global_wire_model

#cache = Cache(physbits=40,
#              size=cachesize,
#              bsize=64,
#              assoc=8,
#              cell_model=cell_model,
#              default_wire_model=default_wire_model,
#              wordline_wire_model=wordline_wire_model,
#              cin=12)

cache = Cache(**cache_params)

cache.generate_tagarray()
cache.generate_dataarray()
print 'Dimensions = %.6f mm x %.6f mm' % (cache.dataarray_size[0]*1e3,
                 cache.dataarray_size[1]*1e3)
print 'E/access = %.6f nJ' % ((cache.dataarray_energy
                               + cache.tagarray_energy)*1e9,)
print '  Data Mat energy  = %.6f nJ' % (cache.dataarray_energy_mat*1e9,)
print '  Data Wire energy = %.6f nJ' % (cache.dataarray_energy_wire*1e9,)
print 'Tag Array Latency = %.6f ns' % (cache.tagarray_delay*1e9,)
print 'Data Array Latency = %.6f ns' % (cache.dataarray_delay*1e9,)
