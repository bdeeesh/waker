from pyModbusTCP.client import ModbusClient

class RKAmplifier:
    def __init__(self, amp):
        if amp==1:
            self.c = ModbusClient(host="131.225.113.194", auto_open=True, auto_close=True)
        elif amp==2:
            self.c = ModbusClient(host="131.225.113.195", auto_open=True, auto_close=True)
        else:
           print('Invalid amplifier') 

    def turnOn(self):
        self.c.write_single_register(1,1)

    def turnOff(self):
        self.c.write_single_register(1,0)

    def turnRFOn(self):
        self.c.write_single_register(2,1)

    def turnRFOff(self):
        self.c.write_single_register(2,0)

    def isOn(self):
        reg=self.c.read_holding_registers(1, 2)
        if reg[0]==0:
            print('Amplifier is off')
        elif reg[0]==1:
            print('Amplifier is on')
        if reg[1]==0:
            print('RF is off')
        elif reg[1]==1:
            print('RF is on')
