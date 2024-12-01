#Bibliotheken einbinden
import time
import datetime
import pymysql
#from mysqlopts import give_mysql_opts
import ast
import smbus2 as smbus
from time import sleep
import csv
from scipy.interpolate import interp1d



def get_raw_voltage (sensors,sensor):#sensor_position):
    bus = smbus.SMBus(1)#Bus definieren
    addr = 0x68

    try:
        #if sensor_position == 0:
        #    stBy = 128
        #else:
        #    stBy = 160
        stBy = sensors[sensor]["StBy"]

        #print (stBy)
        bus.write_byte(addr,stBy)
        sleep(1)
        var = bus.read_i2c_block_data(addr,0,3)
        var = var[0]*256 + var[1]
        voltage = 20/4096*var

        #print (voltage)
        return voltage
    except:
        return 0


def get_calib_value (sensors,sensor):
    calib_data = dict()
    f = 'calib_date_sensor_%s.csv'%sensors[sensor]["id"]
    calib_data["x"] = list()
    calib_data["y"] = list()

    
    with open(f) as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            #print (row)
            calib_data["x"].append(float(row[1]))
            calib_data["y"].append(float(row[0]))


    #print (calib_data["x"])
    #print (calib_data["y"])
    x_value = get_raw_voltage(sensors,sensor)
    #print (x_value)
    calib = interp1d(calib_data["x"],calib_data["y"])
    try:
        calib_value = calib(x_value)
    except:
        calib_value = 0
    #print (x_value)
    #print (calib_value)
    return calib_value
    #i = 0
#
#while i< 5:
#    i += 1
#    print (get_raw_voltage())
