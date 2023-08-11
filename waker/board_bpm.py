from struct import unpack
import numpy as np

def read_ibunch(filename, turns):
    f = open(filename,'rb')

    adc0u,adc1u,adc2u,adc3u=[],[],[],[]
    adc0,adc1,adc2,adc3=[],[],[],[]
    for i in range(turns):
        adc0u.append(f.read(4))
        adc1u.append(f.read(4))
        adc2u.append(f.read(4))
        adc3u.append(f.read(4))
    f.close()
    for i in range(turns):
        adc0.append(unpack('f',adc0u[i]))
        adc1.append(unpack('f',adc1u[i]))
        adc2.append(unpack('f',adc2u[i]))
        adc3.append(unpack('f',adc3u[i]))
    bpm0 = np.array(adc0).flatten()
    bpm1 = np.array(adc1).flatten()
    adc2 = np.array(adc2).flatten()
    adc3 = np.array(adc3).flatten()
    return bpm0, bpm1
