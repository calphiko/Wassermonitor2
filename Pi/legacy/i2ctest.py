import ast
import smbus2 as smbus
bus = smbus.SMBus(1)                                    #Bus definieren

from time import sleep

stBy = 0

addr = 0x68

adrOp_v = "104"
auflOp_v = "12"
versOp_v = "1"


def wert():
    def read():
        stBy = 0
        #adrOp_v = var1.get()
        #auflOp_v = var2.get()
        #versOp_v = var3.get()
        
        if versOp_v == "1":
            stBy = stBy+0
        elif versOp_v == "2":
            stBy = stBy+1
        elif versOp_v == "4":
            stBy = stBy+2
        elif versOp_v == "8":
            stBy = stBy+3
            
        if auflOp_v == "12":
            stBy = stBy+0
        elif auflOp_v == "14":
            stBy = stBy+4
        elif auflOp_v == "16":
            stBy = stBy+8
        elif auflOp_v == "18":
            stBy = stBy+12
            
        stBy = stBy+128
        print(stBy)
        
        addr = ast.literal_eval(adrOp_v)
        

        addr = 0x68
        bus.write_byte(addr,stBy)
        sleep(0.05)


        
        if auflOp_v == "12" or auflOp_v == "14" or auflOp_v == "16":
            var = bus.read_i2c_block_data(addr,0,3)
            print(var)
            var = var[1]
        if auflOp_v == "18":
            var = bus.read_i2c_block_data(addr,0,4)
            var = bus.read_byte_data(addr,4)
            print(var)
            var = var[3]*65536+var[2]+256+var[1]
        
        print(var)
            
    read()
    

stBy = 128

while (1):
    if stBy == 128:
        stBy = stBy + 32
    else:
        stBy = stBy - 32

    print ("\n\nStBy: %s"%stBy)
    bus.write_byte(addr,stBy)
    sleep(1)
    var = bus.read_i2c_block_data(addr,0,3)
    print (var)
    var = var[0]*256 + var[1]
    #var = var[1]
    print (var)
    spg = 20/4096*var
    print (spg)
    print ("\n\n")
    sleep(1)
#mainWin.mainloop()
