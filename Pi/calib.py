import sensortools as s
import sys

SENSOR = 18

#Distances in [cm]
CALIB_DIST = [17,20,25,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]

FILE = 'calib_date_sensor_%s.csv'%SENSOR

f = open(FILE,'w')

for d in CALIB_DIST:
    input ("Set sensor to %s cm distance and press ENTER"%d)
    d_m = s.get_raw_voltage()
    f.write("%s;%s\n"%(d,d_m))
    print (d_m)
    

f.close()
