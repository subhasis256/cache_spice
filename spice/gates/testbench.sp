*************************
** INCLUDES *************
*************************
.param supply=1
.option scale=0.022u
.option accurate post
.option dcic=0
.option measform=1
.global vdd! gnd vdd
.option parhier=local
.option list
.op
.protect
.lib '/afs/ir.stanford.edu/class/ee313/lib/opConditions.lib' SSSS
.unprotect

V_supply vdd 0 dc=supply
V_supply_probe vdd_probe 0 dc=supply


************************
** PARAMETERS and DUT **
************************
.include "parameters.sp"

***********************
** NETLIST ************
***********************

** the testbench
.subckt inv_buffer a y
mp  y  a  vdd  vdd  pmos L=2 W=3
mn  y  a  0    0    nmos L=2 W=1
.ends

** FO = Wload/(Wn+Wp)
** Thus, first inv size = (Wn+Wp)*(Wn+Wp)/Wload/4
** second inv size = Wload/4
** third inv size = Wload*Wload/(Wn+Wp)/4'
** final large cap = 2u
x0    clk        probe_in  inv_buffer M='(Wn+Wp)*(Wn+Wp)/Wload/4'
xdut  probe_in   probe_out vdd_probe  dut
xout  probe_out  n1        inv_buffer M='Wload/4'
xout2 n1         n2        inv_buffer M='Wload*Wload/(Wn+Wp)/4'
cf    n2         0         2u

************************
** STIMULI *************
************************

Vclk clk 0   pwl(    0.000ns 0        0.125ns 0
+                    0.175ns 'supply' 0.625ns 'supply' 
+                    0.675ns 0        1.125ns 0
+                    1.175ns 'supply' 1.625ns 'supply'
+                    1.675ns 0        2.125ns 0
+                    2.175ns 'supply' 2.625ns 'supply' 
+                    2.675ns 0        3.125ns 0
+                    3.175ns 'supply' 3.625ns 'supply'
+                    3.675ns 0        6.125ns 0 )

**********************
** INITIAL CONDITION *
**********************

***********************
** ANALYSIS ***********
***********************
.tran 0.005ns 8.0ns
.meas TRAN fall_out
+ TRIG v(probe_in)      VAL='supply/2'  rise=3
+ TARG v(probe_out)     VAL='supply/2'  fall=3

.meas TRAN rise_out
+ TRIG v(probe_in)      VAL='supply/2'  fall=3
+ TARG v(probe_out)     VAL='supply/2'  rise=3

.meas TRAN idd_switch
+ AVG  i(v_supply_probe) from=2.3n to=3.3n

.meas TRAN idd_static
+ AVG  i(v_supply_probe) from=6.5n to=7.5n

.meas TRAN e_switch_nj
+ PARAM='-supply*idd_switch'

.meas TRAN p_static_w
+ PARAM='-supply*idd_static'

.END
