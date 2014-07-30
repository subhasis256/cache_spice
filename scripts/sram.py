import subprocess
import sys

import spiceutils

def simulate_sram(Nw, Nh):
    paramsfile = open('../spice/cell/parameters.sp', 'w')
    print >> paramsfile, '.param Nw=%d'%(Nw,)
    print >> paramsfile, '.param Nh=%d'%(Nh,)
    paramsfile.close()

    devnull = open('/dev/null', 'w')
    subprocess.call("hspice ../spice/cell/sram_cells_tb.sp", stdout=devnull,
                    stderr=subprocess.STDOUT, shell=True)
    devnull.close()

    stats = spiceutils.read_mt0('sram_cells_tb.mt0')

    for stat in stats:
        if stat["bl0_delay"] != 'failed':
            return stat
