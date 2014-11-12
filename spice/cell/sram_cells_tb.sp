*************************
** INCLUDES *************
*************************
.param supply=1
.option scale=0.022u
.option accurate post
.option dcic=0
.global vdd!
.option parhier=local
.option measform=1
.option list
.op
.protect
.lib '/afs/ir.stanford.edu/class/ee313/lib/opConditions.lib' TTTT
.unprotect

V_supply vdd! 0 dc=supply

.param vhalf='supply*0.5'
.param vdiff=0.150

************************
** PARAMETERS **********
************************
** Cwl is set to 0 sice memory cells contain
** WL cap already
.param cwl=0f

.include "parameters.sp"

.param thalf=1n

************************
** STIMULI *************
************************

Vclk clk 0 pwl(    0.000n        0         'thalf' 0
+                    'thalf+5p'    'supply'  '2*thalf+5p' 'supply'
+                    '2*thalf+10p' 0         '4*thalf'    0)

Vwl0 wl0 0 pwl(    0.000n  0                'thalf+20p'   0
+                    'thalf+25p'    'supply'  '2*thalf' 'supply'
+                    '2*thalf+5p'   0         '4*thalf' 0)

Vwln wln 0 0

***********************
** NETLIST ************
***********************

.include "sram_cells.ckt"

**********************
** INITIAL CONDITION *
**********************

.IC v(xctl.bit) = 'supply'
.IC v(xctr.bit) = 0
.IC v(xcbl.bit) = 0
.IC v(xcbr.bit) = 'supply'
.ic v(xi5.bit) = 0
.ic v(xi4.bit) = 0
.ic v(xi3.bit) = 0
.ic v(xi2.bit) = 0
.IC v(xctl.bit_b) = 0
.IC v(xctr.bit_b) = 'supply'
.IC v(xcbl.bit_b) = 'supply'
.IC v(xcbr.bit_b) = 0
.ic v(xi5.bit_b) = 'supply'
.ic v(xi4.bit_b) = 'supply'
.ic v(xi3.bit_b) = 'supply'
.ic v(xi2.bit_b) = 'supply'


***********************
** ANALYSIS ***********
***********************
.tran 0.005ns 20.0ns sweep thalf 0.125n 4n 0.125n

.measure tran bl0_delay    trig v(wl0) val='vhalf' rise=1
+                          targ PAR('abs(v(bl0)-v(bl_b0))') val='vdiff' rise=1

.measure tran bl0_max
+ MAX    PAR('abs(v(bl0)-v(bl_b0))') from='thalf' to='3*thalf'

.measure tran iavg
+ AVG    i(v_supply)  from='thalf*1.5'  to='3*thalf'

.measure tran ileak
+ AVG    i(v_supply)  from='3*thalf'  to='4*thalf'

.measure tran e_peracc
+ PARAM='-(iavg-ileak)*supply*1.5*thalf'

.measure tran p_leak
+ PARAM='-ileak*supply'

.END
