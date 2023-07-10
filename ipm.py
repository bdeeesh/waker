import acsys.dpm
import numpy as np

async def read_settings(con,param_list,event_list):
    data=[None] * len(param_list)
    async with acsys.dpm.DPMContext(con) as dpm:
        for index, request in enumerate(param_list):
                    # The @I event string makes the data request immediately, once
            await dpm.add_entry(index, request + event_list[index])
        await dpm.start()
        async for ii in dpm:
            #print(ii)
            data[ii.tag]=ii.data
            if data.count(None) ==0:
                break
        return data

class IPM:
    def __init__(self,plane='V'):
        if plane=='V':
            self.name = 'R:3VP'
        elif plane=='H':
            self.name = 'R:4HP'
        else:
            print('Invalid plane')
        self.list_of_devices()
        self.channels=96.0

    def list_of_devices(self):
        self.device_list=[]
        device_mid=['MR','MB','MC']
        for mid in device_mid:
            for i in range(1,9):
                self.device_list.append(self.name+mid+str(i)+"[0:4095]")

    def read_data(self):
        data = acsys.run_client(read_settings, param_list=self.device_list, event_list=['.scaled']*len(self.device_list))
        data=np.array(data)
        extra = int(data.flatten().shape[0] % self.channels) 
        if extra!=0:
            turns = data.flatten()[:-extra].shape[0]/self.channels
            self.data = data.flatten()[:-extra].reshape((int(turns),int(self.channels))) 
        else:
            turns = data.flatten().shape[0]/self.channels
            self.data = data.flatten().reshape((int(turns),int(self.channels))) 
