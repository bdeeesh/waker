import numpy as np
import sys
from time import time
import xml.etree.ElementTree as ET
from scipy.optimize import curve_fit
import h5py
from os import path
import matplotlib.pyplot as plt
import matplotlib.animation


print ('New version, updated June')
print ('Adding H data analysis')
print ('add ed number of channel')
class scopeData(object):
    
    def __init__(self,rootname,window=False,save=False,IFile='_beam',plan='V',num_of_chan=4):
        self.num_of_chan = num_of_chan
        self.plan = plan
        self.name = rootname
        self.IFile = IFile
        self.save = save
        t = time()
        self.window = window
        self.FILENAME,self.HeaderName = self.name+'.Wfm.bin',self.name+'.bin'
        self.Header = self.readHEADER(self.HeaderName)
        print (self.N)
        if self.COV == 64768:
            self.Dtype = np.int16
            self.nd = 4
        elif self.COV == 253:
            self.Dtype = np.int8
            self.nd = 8
        else:
            print ('data type unknown')
            exit()
        # get bin data	
        self.getBinData(self)

        #print (time() - t)
        if self.num_of_chan == 2:
            self.BCH1,self.BCH2 = self.BINWFM.reshape(int(len(self.BINWFM)/self.num_of_chan),self.num_of_chan).T
        elif self.num_of_chan == 4:
            self.BCH1,self.BCH2,self.BCH3,self.BCH4 = self.BINWFM.reshape(int(len(self.BINWFM)/self.num_of_chan),self.num_of_chan).T

        

        self.CH1_FAC,self.CH1_VOL_OFF = self.CONfactor(self.CH1_dVpD,self.dV_COUNT,self.COV,self.CH1_OFF,self.CH1_POS)
        self.CH2_FAC,self.CH2_VOL_OFF = self.CONfactor(self.CH2_dVpD,self.dV_COUNT,self.COV,self.CH2_OFF,self.CH2_POS)
        # get voltage data from bin
        self.CH3_FAC,self.CH3_VOL_OFF = self.CONfactor(self.CH3_dVpD,self.dV_COUNT,self.COV,self.CH4_OFF,self.CH3_POS)
        self.CH4_FAC,self.CH4_VOL_OFF = self.CONfactor(self.CH4_dVpD,self.dV_COUNT,self.COV,self.CH4_OFF,self.CH4_POS)
        if self.plan == 'V':
            self.CH1V,self.CH2V =  self.getVoltage(self.BCH1,self.CH1_FAC,self.CH1_VOL_OFF),self.getVoltage(self.BCH2,self.CH2_FAC,self.CH2_VOL_OFF)
        elif self.plan == 'H':
            self.CH1V,self.CH2V =  self.getVoltage(self.BCH1,self.CH3_FAC,self.CH3_VOL_OFF),self.getVoltage(self.BCH2,self.CH4_FAC,self.CH4_VOL_OFF)
        else:
            print ('Wrong plan, either H or V')
            exit()



        self.CH1V,self.CH2V = self.CH1V.reshape(self.N,self.nt),self.CH2V.reshape(self.N,self.nt)
        self.TIME = np.linspace(-1*self.dt*self.nt/2,self.dt*self.nt/2,self.nt)
        if window:
            self.TIMEN = self.TIME[(self.TIME>self.window[0])& (self.TIME<self.window[1])]
            self.CH1V = np.array(self.CH1V[:, (self.TIME > self.window[0]) & (self.TIME < self.window[1])])
            self.CH2V = np.array(self.CH2V[:, (self.TIME > self.window[0]) & (self.TIME < self.window[1])])
            self.nt = int(len(self.TIMEN))
        if not window:
            self.TIMEN = self.TIME

        self.CH1BGR = self.removeBaseLine(self.CH1V)
        #print (time()-t)
        self.CH1VINT = self.IntegratedData(self.CH1BGR)
        #print (time()-t)
        self.CH2VINT = self.IntegratedData(self.CH2V)
        
        self.POScenter = self.getPosition(self.CH1VINT,int(self.nt/2))
        self.POShead   = self.getPosition(self.CH1VINT,int(self.nt/3))

        self.POStail   = self.getPosition(self.CH1VINT,int(self.nt/1.5))


        self.getTuneSpec()
        self.filterTune()
        argMax = np.argmax(self.PowSpecFiler)

        self.tunePeak = self.tuneFilter[np.argmax(self.PowSpecFiler)]
        print (f'processing time is {time()-t}')
        
        self.IFILE = self.name+self.IFile

        self.intensity(self.IFILE)
        print(f'{self.tunePeak} is the highest tune peak at {self.I} intensity')

        if self.save:
            self.saveData(self.name)




    
    def saveData(self,outputFile):
        np.save(outputFile,np.array([self.CH1VINT,self.CH2VINT],dtype=np.float16))
        np.save(outputFile+'_tune',np.array([self.TIMEN,self.tune,self.PowSpec,self.tunePeak,self.I],dtype=object))



    def readHEADER(self,HeaderName):
            """
            Given a filename of .bin, the measurement information is extracted. The following is assumed:
            MultiChannel is active (2 channels are considered)
            """
            self.tree = ET.parse(self.HeaderName)
            self.root = self.tree.getroot()
            self.data = {}
            for child in self.root:
                for subelem in child:
                    for x in subelem.iter('Prop'):
                        name = x.get('Name')
                        if name == 'NumberOfAcquisitions':
                            self.N = int(x.get('Value'))
                        elif name == 'NofQuantisationLevels':
                            self.COV = float(x.get('Value'))
                        elif name == 'Resolution':
                            self.dt = float(x.get('Value'))
                        elif name == 'RecordLength':
                            self.nt = int(x.get('Value'))
                        elif name == 'VerticalDivisionCount':
                            self.dV_COUNT = int(x.get('Value'))
                        elif name == 'TimeScale':
                            pass
                        elif name == 'MultiChannelVerticalPosition':
                            self.CH1_POS = float(x.get('I_0'))
                            self.CH2_POS = float(x.get('I_1'))
                            self.CH3_POS = float(x.get('I_2'))
                            self.CH4_POS = float(x.get('I_3'))
                        elif name == 'MultiChannelVerticalScale':
                            self.CH1_dVpD = float(x.get('I_0'))
                            self.CH2_dVpD = float(x.get('I_1'))
                            self.CH3_dVpD = float(x.get('I_2'))
                            self.CH4_dVpD = float(x.get('I_3'))
                        elif name == 'MultiChannelVerticalOffset':
                            self.CH1_OFF = float(x.get('I_0'))
                            self.CH2_OFF = float(x.get('I_1'))
                            self.CH3_OFF = float(x.get('I_2'))
                            self.CH4_OFF = float(x.get('I_3'))
    def intensity(self,IFILE):
        if path.isfile(IFILE):
            try:
                X = np.loadtxt(IFILE)
            except :
                self.I = np.nan
                self.BeamData =False
                pass



            self.I = np.average(X[0:,1][(X[0:,0]>0.58) & (X[0:,0]<0.59)])
            self.Beam = X[0:,1]
            self.BeamTime = X[0:,0]
            self.BeamData = True

        else:
            self.I = np.nan
            self.BeamData = False
            

    def IntegratedData(self,CHVOLT):
            
        INTEGCH = np.cumsum(CHVOLT,axis=1)
        #polyfit to extract slope 
        #print (np.shape(TIMEN))
        Tf = np.array([self.TIMEN[0],self.TIMEN[-1]])
        CHF = INTEGCH[:, [0, -1]] # first values 
        #CHF = np.array([INTEGCH[0:,0],INTEGCH[0:,-1]])                                         

        coef = np.array([np.polyfit(Tf,CHF[i],1) for i in range(self.N)])

        #poly1d_fn = [np.poly1d(coef[i]) for i in range(self.N)]
        """
            if np.average(INTEGCH[i]) < 0 :
                factor = -1
            elif np.average(INTEGCH[i]) > 0 :
                factor = 1
            else:
                print ('Error ')
        """
        poly1d_fn = [np.poly1d(coef[i]) for i in range(self.N)]
        BCK = [poly1d_fn[i](self.TIMEN) for i in range(self.N)]

        #BGK = np.polynomial.polynomial.polyval(self.TIMEN, coef.T)

        INTEGCH = INTEGCH - BCK
            # dc offset
            #INTEGCH[i] = factor*INTEGCH[i] - np.min(INTEGCH[i])
                
                
        return INTEGCH
    
        
    def removeBaseLineO(self,CHVOLT,M=10):
        """
        For each array (N x nt): 
        BaseLine = np.empty_like(CHVOLT)
            take the average of N-M, N+ M to get the base line
            remove the base line from the N data
            return the new array
        """
        # create empty arrays for baseline and new data:
        # assuming reShapeData was applied first
        BaseLine = np.empty_like(CHVOLT)
        NEWCH = np.empty_like(CHVOLT)


        for i in range(M,self.N-M):
            I = np.arange(i-M,i+M) # index to average over

            BaseLine[i] = np.average(np.array([CHVOLT[(v):(v+1)] for v in I]),axis=0) # the average 
            NEWCH[i] = CHVOLT[i]-BaseLine[i]

        return NEWCH
        

    def removeBaseLine(self,CHVOLT,M=10):
        """
        For each array (N x nt): 
        BaseLine = np.empty_like(CHVOLT)
            take the average of N-M, N+ M to get the base line
            remove the base line from the N data
            return the new array
        """
        # create empty arrays for baseline and new data:
        # assuming reShapeData was applied first

        BaseLine = np.empty_like(CHVOLT)
        CHBGR = np.empty_like(CHVOLT)
        #
        # 
        #


        for i in range(M,self.N-M):
            I = np.arange(i-M,i+M) # index to average over
            #BaseLine[i] = np.mean(CHVOLT[I], axis=0)
            BaseLine[i] = np.average(np.array([CHVOLT[(v):(v+1)] for v in I]),axis=0) # the average 
            CHBGR[i] = CHVOLT[i]-BaseLine[i]
        return (CHBGR)
    
    def getBinData(self,Dtype):
    # data can be int.8 or int.16 
        with open(self.FILENAME,'rb') as f: #BIN files with int8 (can be int16)
            self.BINWFM = np.fromfile(f,dtype=self.Dtype)
            self.BINWFM = self.BINWFM[self.nd:] 
    def CONfactor(self,CH_dVpD,dV_COUNT,COV,CH_OFF,CH_POS):
        CH_FAC = (CH_dVpD* dV_COUNT/COV)
        CH_VOL_OFF = CH_OFF - (CH_dVpD*CH_POS)

        return (CH_FAC,CH_VOL_OFF)


    splitCH = lambda self: self.BINDATA.reshape(self.N,2).T #where N is the number of samples in one channel (rearrange data)


    getTime = lambda self: np.linspace(-1*self.dt*self.nt/2,self.dt*self.nt/2,self.nt)
    
    
    def getPosition(self,CH,point):
        POS = CH[:, point]
        return POS 
    
    def getTuneSpec(self,dn=1):
        self.PowSpec = np.absolute(np.fft.rfft(self.POScenter))
        self.tune = np.fft.rfftfreq(self.N,dn)
        return (self.tune,self.PowSpec)
    
    def filterTune(self,pi=0.42,pf=0.48,plot=False):
        freq1 = self.tune[:int(self.N/2+1)]
        self.tuneFilter,self.PowSpecFiler = self.getTuneSpec(dn=1)[0][((freq1 > pi) & (freq1 < pf))],self.getTuneSpec(dn=1)[1][((freq1 > pi) & (freq1 < pf))]

    def plotconsBeam(self,frame,ti=0.58,offset=0):
        """
        ti = trigger time (set to 0.58)
        offset = voltage offset to A+B channel to avoid zeros 
        generates 3 x 2 plots: 
        A+B          (A-B)/(A+B) -> center
        (A-B)/(A+B)  (A-B)/(A+B) -> head 
        RBEAM        (A-B)/(A+B) -> tail
        """
        fig,ax = plt.subplots(3,2,dpi=100,figsize=(6,6),tight_layout=True)
        dt = 1.11e-5
        self.chargeOffset = self.CH1VINT/(self.CH2VINT+offset)
        [ax[0,0].plot(self.TIMEN,(self.CH2VINT[i]+offset)) for i in range(frame,frame+5)]
        [ax[1,0].plot(self.TIMEN,self.chargeOffset[i]) for i in range(frame,frame+5)]

        position = self.getPosition(self.chargeOffset,int(self.nt/2))
        positionH = self.getPosition(self.chargeOffset,int(self.nt/3))
        positionT = self.getPosition(self.chargeOffset,int(self.nt/(1.5)))

        ax[1,0].set_xlabel(r'Time (s)',fontsize=20)
        ax[0,0].set_ylabel(r'I (a.u.)',fontsize=20)
        ax[1,0].set_ylabel(r'y (a.u.)',fontsize=20)
        if self.BeamData:
            ax[2,0].plot(self.BeamTime,self.Beam)
        else:
            print ('no intesnity data')
        ax[2,0].axvline(x=ti+(frame*dt))
        ax[2,0].set_xlim(ti,ti+(self.nt)*dt)
        ax[2,0].set_ylabel(r'PPB ($\times 10^{12}$)',fontsize=20)
        ax[2,0].set_xlabel(r'Event time (s)',fontsize=20)
        ax[0,1].plot(ti+(np.arange(0,len(position))*dt),position,alpha=0.5,c='r',label='center')
        ax[0,1].legend()
        ax[1,1].plot(ti+(np.arange(0,len(position))*dt),positionH,alpha=0.5,c='b',label='head')
        ax[1,1].legend()
        ax[2,1].plot(ti+(np.arange(0,len(position))*dt),positionT,alpha=0.5,c='k',label='tail')
        ax[2,1].legend()
        ax[2,0].set_xlabel(r'Event time (s)',fontsize=20)
        ax[0,1].axvline(x=ti+(frame*dt))
        ax[1,1].axvline(x=ti+(frame*dt))
        ax[2,1].axvline(x=ti+(frame*dt))

        ax[0,1].set_ylim(ax[2,1].get_ylim()[0],ax[2,1].get_ylim()[1])
        ax[1,1].set_ylim(ax[2,1].get_ylim()[0],ax[2,1].get_ylim()[1])
        ax[2,1].set_xlabel(r'Event time (s)',fontsize=20)




        

    getVoltage = lambda self,ADC,CH_N_FAC,CH_N_VOL_OFF: (ADC*CH_N_FAC) + CH_N_VOL_OFF # use convertsion factors for the voltage
# example CH1VOLT,CH2VOLT = getVoltage(BINCH1,CH1_FAC,CH1_VOL_OFF),getVoltage(BINCH2,CH2_FAC,CH2_VOL_OFF)

    ch2Beam = lambda self: np.trapz(self.CH2VINT,axis=1)


# usually the first 4 entries are useless:
# remove the first N points (need to be done for each CH, after the split)
#fixCHdata = lambda CHVOLT,N : CHVOLT[N:]

# data analysis:

#reShapeData = lambda CH,N,bt: CH.reshape(N,bt)
