import pyvisa
import numpy as np
import time
import h5py
from struct import unpack

class scope(object):
    def __init__(self,which_scope):
        self.rm = pyvisa.ResourceManager()
        if which_scope=='RR-TEK':
            ip = '131.225.137.185'
        elif which_scope=='MI-TEK':
            ip = '131.225.137.186' 
        self.scope = self.rm.open_resource('TCPIP::'+ip+'::INSTR')
        self.scope.timeout = 30000
        #self.scope.encoding = 'latin_1'
        print(self.scope.query('*idn?'))
        self.dType, self.bigEndian = get_waveform_info(self.scope)
        self.scope.lock()

    def setHorizontalScale(self, hScale):
        self.scope.write('horizontal:mode:scale {}'.format(hScale))

    def setFastFrame(self, numFrames):
        self.scope.write('acquire:state off')
        self.scope.write('horizontal:fastframe:state on')
        self.scope.write('horizontal:fastframe:count {}'.format(numFrames))

    def setAuxTrigLevel(self, trigLevel):
        self.scope.write('trigger:a:edge:source aux')
        self.scope.write('trigger:auxlevel {}'.format(trigLevel))

    def setRecordLength(self, recordlength):
        self.scope.write('horizontal:mode manual')
        self.scope.write('horizontal:mode:recordlength {}'.format(recordlength))

    def setChannelBandwithFull(self,ch):
        if int(ch) not in [1,2,3,4]:
            print('Incompatible channel')
        else:
            self.scope.write('ch+'+str(int(ch))+':bandwidth full')


    def setVerticalScale(self, ch, scale):
        ####scale is volts per division
        if int(ch) not in [1,2,3,4]:
            print('Incompatible channel')
        else:
            self.scope.write('ch'+str(int(ch))+':scale {}'.format(scale))

    def setVerticalPosition(self, ch, pos):
        ####scale is vertical position
        if int(ch) not in [1,2,3,4]:
            print('Incompatible channel')
        else:
            self.scope.write('ch'+str(int(ch))+':position {}'.format(pos))

    def setTermination(self):
        self.scope.write(':ch1:ter 50;:ch2:ter 50;:ch3:ter 50;:ch4:ter 50')

    def setHorizontalDelayMode(self,mode):
        if mode not in [1,0]:
            print('Invalid mode')
        else:
            self.scope.write('horizontal:delay:mode {}'.format(mode))

    def setHorizontalDelay(self,delay):
        self.scope.write('horizontal:delay:time {}'.format(delay))

    def diplayChannel(self, ch):
        if ch=='all':
            for i in range(1,5):
                self.scope.write('DISplay:GLObal:CH'+str(i)+':STATE ON')
        elif int(ch) not in [1,2,3,4]:
            print('Incompatible channel')
        else:
            self.scope.write('DISplay:GLObal:CH'+str(int(ch))+':STATE ON')

    def acquireWaveform(self):
        print('Acquiring waveform.')
        self.scope.write('acquire:stopafter sequence')
        self.scope.write('acquire:state on')
        self.scope.query('*opc?')
        print('Waveform acquired.\n')
  
    def read_preamble(self,ch):
        self.scope.write('data:source ch'+str(int(ch)))
        yOffset = float(self.scope.query('wfmoutpre:yoff?'))
        yMult = float(self.scope.query('wfmoutpre:ymult?'))
        yZero = float(self.scope.query('wfmoutpre:yzero?'))
        #numPoints = int(self.scope.query('wfmoutpre:nr_pt?'))
        xIncr = float(self.scope.query('wfmoutpre:xincr?'))
        xZero = float(self.scope.query('wfmoutpre:xzero?'))
        #scaledtime = np.arange(xZero, xZero + (xIncr * numPoints*n_byts), xIncr)
        return yOffset, yMult, yZero, xIncr, xZero

    def read_channel_sliced(self,ch):
        numFrames=int(self.scope.query('horizontal:fastframe:count?'))
        byt_n = int(self.scope.query('wfmoutpre:byt_n?'))
        recordLength = int(self.scope.query('horizontal:mode:recordlength?').strip())
        print('Reading Channel '+str(ch))
        raw_data=self.read_channel_raw(ch)
        if byt_n == 1:
            unpack_str = '>'+str(recordLength) + 'b'
        elif byt_n==2:
            unpack_str = '>'+str(recordLength) + 'h'
        headlen = 2 + len(str(recordLength))
        bytes_exp = headlen + 1 + recordLength * byt_n
        raw_data_sliced = [unpack(unpack_str,raw_data[i*bytes_exp:(i+1)*bytes_exp][headlen:-1]) for i in range(numFrames)]
        return raw_data_sliced

    def save_channels_to_file(self,ch_list,fileName):
        t0 = time.time()
        hf = h5py.File(fileName+'.h5', 'w')
        for ch in ch_list:
            if ch not in [1,2,3,4]:
                print('Incompatible channel')
            else:
                byt_n = int(self.scope.query('wfmoutpre:byt_n?'))
                raw_data_sliced = self.read_channel_sliced(ch)
                print(time.time()-t0)
                g1 = hf.create_group('ch'+str(ch))
                g1.create_dataset('frames',data=np.array(raw_data_sliced,dtype='i'+str(byt_n)))
                yOffset, yMult, yZero, xIncr, xZero = self.read_preamble(ch)
                g1.create_dataset('yOffset',data=yOffset,shape=(1))
                g1.create_dataset('yMult',data=yMult,shape=(1))
                g1.create_dataset('yZero',data=yZero,shape=(1))
                g1.create_dataset('xIncr',data=xIncr,shape=(1))
                g1.create_dataset('xZero',data=xZero,shape=(1))
        hf.close()

    def read_channel_raw(self,ch):
        numFrames=int(self.scope.query('horizontal:fastframe:count?'))
        self.scope.write('data:framestart 1')
        self.scope.write('data:framestop {}'.format(numFrames))
        self.scope.write('data:start 1')
        byt_n = int(self.scope.query('wfmoutpre:byt_n?'))
        recordLength = int(self.scope.query('horizontal:mode:recordlength?').strip())
        self.scope.write('data:stop {}'.format(recordLength))
        self.scope.write('data:source ch'+str(int(ch)))
        self.scope.query('*opc?') 
        #self.scope.read_termination=None
        self.scope.write('CURVE?')
        headlen=2+len(str(recordLength))
        bytes_exp = headlen + 1 + recordLength * byt_n
        expected_length=bytes_exp*numFrames
        #self.scope.chunk_size=1000*1024
        raw_data = self.scope.read_raw()
        #self.scope.read_termination='\n'
        if len(raw_data)!=expected_length:
            print('Length does not match expectation')
        else:
            return raw_data


    def unlockAndClose(self):
        self.scope.unlock()
        print('Closing scope')
        self.scope.close()


def get_waveform_info(scope):
    """Gather waveform transfer information from scope."""
    binaryFormat = scope.query('wfmoutpre:bn_fmt?').rstrip()
    print('Binary format: ', binaryFormat)
    numBytes = scope.query('wfmoutpre:byt_nr?').rstrip()
    print('Number of Bytes: ', numBytes)
    byteOrder = scope.query('wfmoutpre:byt_or?').rstrip()
    print('Byte order: ', byteOrder)
    encoding = scope.query('data:encdg?').rstrip()
    print('Encoding: ', encoding)
    if 'RIB' in encoding or 'FAS' in encoding:
        dType = 'b'
        bigEndian = True
    elif encoding.startswith('RPB'):
        dType = 'B'
        bigEndian = True
    elif encoding.startswith('SRI'):
        dType = 'b'
        bigEndian = False
    elif encoding.startswith('SRP'):
        dType = 'B'
        bigEndian = False
    elif encoding.startswith('FP'):
        dType = 'f'
        bigEndian = True
    elif encoding.startswith('SFP'):
        dType = 'f'
        bigEndian = False
    elif encoding.startswith('ASCI'):
        raise pyvisa.InvalidBinaryFormat('ASCII Formatting.')
    else:
        raise pyvisa.InvalidBinaryFormat
    return dType, bigEndian

