#!/bin/bash

if [ -f /usr/bin/gcc-4.4 ]; then
export J_CC=gcc-4.4
else
export J_CC=gcc
fi

source /hd/cad/modules/tcl/init/bash
module load base
module load hspice
module load cx
module load cscope
