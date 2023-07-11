import sys
from IPMFIT import *
import time 
rootname = sys.argv[1]

# get Beam 
m = getBeam(str(rootname)+'_beam')

# get wall
time.sleep(3)
m1 = getWallCurrent(rootname)


# get ipm

m2 = getIPM(rootname)


