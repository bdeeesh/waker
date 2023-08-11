import numpy as np
import ipm as ipm
#from scipy.optimize import curve_fit
import scope as sc
import subprocess
import os

def ftp_get():
    command  = 'acl getRbeam.acl'
    p = subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
    result =  p.stdout.readlines()
    try:
        time,readings = [],[]
        for text in result:
            readings.append(float(text.rstrip('\n').split()[1]))
            time.append(float(text.rstrip('\n').split()[0]))
        return time,readings
    except:
        print ('ACL error ')



def getBeam(fname):
    os.system('acl getRbeam.acl >> '+str(fname)) 


class getWallCurrent(object):

    def __init__(self,name):
        self.fname = str(name)
        self.mitek = sc.scope('MI-TEK') #'MI-TEK' is actually the Recycler scope (19Nov21)
        #self.acquireWaveform() # adding to trigger and then copy
        self.copyData()


    def copyData(self,CH=[1]):
        self.mitek.save_channels_to_file(CH,self.fname)
        print ('saved data')







"NAME = sys.argv[1] X1 = IPM(plane='H')"

print ('Class to fit ipm data and calculate space-charge tune shift. Requires intensity and sigma z ')

class getIPM(object):
    def __init__(self,fname,plane=['H','V']):
        self.name = fname
        self.plane = plane

        self.getIPMdata()


    def getIPMdata(self):
        for i in self.plane:
            X = ipm.IPM(plane=i)
            X.read_data()
            DATA = X.data
            np.save(str(self.name+'_'+i),DATA)
            print ('finished for ',i ,' plane')


class IPMFIT(object):
    
    def __init__(self,fname):





        self.badChannel=[79]
        self.p0 = np.array([1,30,25])
        self.name = fname
        self.turns = np.arange(1024)
        self.channels = np.arange(95)

        self.Data = self.LoadData()
        self.Data = self.badMCP(self.Data)
        self.para = self.getFit(self.Data)
        self.sigma = self.para[0:,-1]
        FILTER  = np.s_[(self.sigma <10)& ((self.sigma >0))]
        fac = 0.5e-3 
        
        self.sigma = self.para[0:,-1][FILTER]*fac # factor for conversion 
        self.turns = self.turns[FILTER]
        self.sigmaAverage = np.average(self.sigma)
        print ('Average measured sigma is '+str(self.sigmaAverage))
        self.sigmaSTD = np.std(self.sigma)
        
        # for calculating nu_s
        
        self.betaIPMV, self.betaIPMH = 56.3,20.975
        self.Qs = 0.0005

        self.r0 =1.535e-18
        self.beta=0.9944
        self.gamma=9.46
        self.R=528.3019139459425
        self.fo = 89000
        self.zo = 4*30e-9
        self.To = 1/self.fo


        
        
    def LoadData(self):
        return np.load(self.name)    
    
    badMCP = lambda self,i:np.delete(i,self.badChannel,axis=1)
    
    def gaussian(self,x,a,x0,sigma):
        
        return a*np.exp(-(x-x0)**2/(2*sigma**2))
    
    def fitCurve(self,row):
        popt, _ = curve_fit(self.gaussian, self.channels, row/np.max(row),p0=self.p0,maxfev=6000,bounds=(0,np.inf))
        return popt
        
    
    
    def getFit(self,m):
        params = np.apply_along_axis(self.fitCurve, axis=1, arr=m)
        return params
    
    EmitRms = lambda self,betaIPM : self.beta*self.gamma*self.sigma**2/(betaIPM)
    
    
    def incTune(self,N,sigmaz,emit):
        #based on rms beam size 
        # and rms emittance emit = sigma**2/beta
        
        #sigma_z = sigma_t*c*beta
        S=1.596 #for gaussian

        M=1
        #fAsym = 1+ np.sqrt(emitH/emitV)
        nu_s = -(N*self.r0*self.R*S)/(8*sigmaz*M*self.beta*self.gamma*self.gamma*emit*1)
        return (nu_s)
    
    
    def incTuneAsym(self,N,sigmaz,emitV,emitH):
        S=1.596 #for gaussian
        R=528.3019139459425
        M=1
        fAsym = 1+ np.sqrt(emitH/emitV)
        nu_s = -(N*r0*R*S)/(4*sigmaz*M*beta*gamma*gamma*emitV*fAsym)
        return (nu_s)

