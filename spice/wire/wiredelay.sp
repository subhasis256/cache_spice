** A model for a repeater line with model parameters from PTM

.param supply=0.6
.temp 40
.option scale=0.022u
.option accurate post
.option dcic=0
.global vdd! vdd
.option parhier=local
.option measform=1
.option list
.op
.protect
.lib '/afs/ir.stanford.edu/class/ee313/lib/model_ptm045.lib' SS
.unprotect

V_supply vdd 0 dc=supply
V_supply_probe vdd! 0 dc=supply

.include "parameters.sp"

** a wire with ends x1 and x2 and configurable R, L, C
.subckt wiresegment x1 x2
R1 x1 x2 'Rperl*length/5'
L1 n1 x2 'Lperl*length/5'
C1 x2 0 'Cperl*length/5'
.ends

** A full wire with condigurable length and R/length, L/length, C/length
.subckt wire a b
** model as 5 segments
x1   a   n1  wiresegment
x2   n1  n2  wiresegment
x3   n2  n3  wiresegment
x4   n3  n4  wiresegment
x5   n4  b   wiresegment
.ends


** repeater element
.subckt inv a y vdd_local
m1 y a vdd_local vdd_local pmos L=2 W='iscale*3.0/4.0'
m2 y a 0   0   nmos L=2 W='iscale/4.0'
.ends

** full wire with precomputed optimal sizing and spacing of repeaters
xw1  in        n1               wire 
xr1  n1        n2         vdd   inv
xw2  n2        n3               wire
xr2  n3        probe_in   vdd   inv
xw3  probe_in  n5               wire
xr3  n5        probe_out  vdd!  inv
xw4  probe_out n7               wire
xr4  n7        n8         vdd   inv
xw5  n8        n9               wire
xr5  n9        out        vdd   inv
* add a pretty big load at the output
Cout out 0     C=2u

** stimulus
Vclk in  0 pwl(    0.000ns 0        0.125ns 0
+                  0.175ns 'supply' 0.625ns 'supply' 
+                  0.675ns 0        1.125ns 0
+                  1.175ns 'supply' 1.625ns 'supply'
+                  1.675ns 0        2.125ns 0
+                  2.175ns 'supply' 2.625ns 'supply' 
+                  2.675ns 0        3.125ns 0
+                  3.175ns 'supply' 3.625ns 'supply'
+                  3.675ns 0        6.125ns 0 )

** analysis
.tran 0.005n 8.0n sweep data=mydata
.data mydata
+ length  iscale
+100u   150
+100u   175
+100u   200
+100u   225
+100u   250
+100u   275
+100u   300
+125u   150
+125u   175
+125u   200
+125u   225
+125u   250
+125u   275
+125u   300
+150u   150
+150u   175
+150u   200
+150u   225
+150u   250
+150u   275
+150u   300
+175u   150
+175u   175
+175u   200
+175u   225
+175u   250
+175u   275
+175u   300
+200u   150
+200u   175
+200u   200
+200u   225
+200u   250
+200u   275
+200u   300
+225u   150
+225u   175
+225u   200
+225u   225
+225u   250
+225u   275
+225u   300
+250u   150
+250u   175
+250u   200
+250u   225
+250u   250
+250u   275
+250u   300
+275u   150
+275u   175
+275u   200
+275u   225
+275u   250
+275u   275
+275u   300
+300u   150
+300u   175
+300u   200
+300u   225
+300u   250
+300u   275
+300u   300
+325u   150
+325u   175
+325u   200
+325u   225
+325u   250
+325u   275
+325u   300


** measurements
.meas TRAN td_in2out
+ TRIG v(probe_in)      VAL='supply/2'  rise=3
+ TARG v(probe_out)     VAL='supply/2'  fall=3

.meas TRAN idd_switch
+ AVG  i(v_supply_probe) from=2.3n to=3.3n

.meas TRAN idd_static
+ AVG  i(v_supply_probe) from=6.5n to=7.5n

.meas TRAN e_permm_pJmm
+ PARAM='-idd_switch*supply/length'

.meas TRAN t_permm_nsmm
+ PARAM='td_in2out/(length*1000)*1g'

.meas TRAN vdd_meas
+ PARAM='supply'

.END
