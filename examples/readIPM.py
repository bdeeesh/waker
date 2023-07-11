import numpy as np
from ipm import *
import sys
"""
read IPM data and save them 
based on Rob script ipm
"""



NAME = sys.argv[1]

X1 = IPM(plane='H')

X1.read_data()

DATA = X1.data

print (DATA.shape)

np.save(str(NAME),DATA)



