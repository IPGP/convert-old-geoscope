# -*- coding: utf-8 -*-
"""
Created on Fri May 20 14:30:21 2016

@author: leroy
"""

from obspy import read
import numpy as np
st = read("AGD.G..MHE.1987.218")
trace_float = st[0].data*2**7
trace_int = trace_float.astype(np.int32)
st[0].data = trace_int
st[0].stats.location = '00'
st[0].write("AGD.G.00.MHE.1987.218", format = 'MSEED', reclen=4096,encoding='STEIM2')


