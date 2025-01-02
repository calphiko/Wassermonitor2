# LEGACY --> Will be replaced with API variant

#Bibliotheken einbinden
import time
import datetime
import pymysql
from mysqlopts import give_mysql_opts

import smbus2 as smbus
from time import sleep
from Pi.legacy import sensortools as st

bus = smbus.SMBus(1)                                    #Bus definieren

CNT_MEASUREMENTS = 5
SLEEP = 300

addr = 0x68

sensors = list()

sensors.append(dict())
sensors[0]["name"] = "0"
sensors[0]["id"] = "13"
sensors[0]["StBy"] = 128

sensors.append(dict())
sensors[1]["name"] = "1"
sensors[1]["id"] = "18"
sensors[1]["StBy"] = 160

 
def distance (sensors,sensor):
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(5)

    try:
        stBy = sensors[sensor]["StBy"]
        #print (str(sensor) +":\t ")
        #print ("\n\nStBy: %s"%stBy)
        bus.write_byte(addr,stBy)
        sleep(1)
        var = bus.read_i2c_block_data(addr,0,3)
        #print (var)
        var = var[0]*256 + var[1]
        #var = var[1]
        #print (var)
        spg = 20/4096*var
        #print (spg)
        #print ("\n\n")
        
        
        distanz = spg * 100
        #print  (distanz)
        signal.alarm(0)
        return distanz
    except:
        return 0

def stat_dist(sensors, sensor, cnt):
    distances = list()
    try:
        for i in range (0,cnt):
            distances.append(distance(sensors, sensor))
            time.sleep(1)
    except:
        print ("Warning, not measured!")
    return distances

def stat_dist_calib(sensors, sensor, cnt):
    distances = list()
    distances.append(st.get_calib_value(sensors,sensor))

    try:
        for i in range (0,cnt):
            distances.append(st.get_calib_value(sensors,sensor))
            time.sleep(1)
    except:
        print ("Warning, not measured!")
    return distances

def write_measurement_to_db (distances, sensors, sensor):
    class color:
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'
    print ("begin writing")
    #try:
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(120)
    #try:
    mysql_opts = give_mysql_opts()
    mysql = pymysql.connect(mysql_opts['host'], mysql_opts['user'], mysql_opts['pass'], mysql_opts['db'], connect_timeout=60)
    cur = mysql.cursor()
    
    
    now = datetime.datetime.now()
    now = now.strftime('%Y-%m-%d %H:%M:%S')
    #print now
    sql = "INSERT INTO messung (date, sensor) VALUES ('%s',%s);"%(now,sensor)
    #print sql
    cur.execute(sql)
    mysql.commit()
    
    sql = "SELECT id FROM messung WHERE date = '%s'"%now
    #print sql
    cur.execute(sql)
    sens_id = cur.fetchone()[0]
    
    for i in range(0,len(distances)):
        if not distances[i] == 0:
            sql = "INSERT INTO werte (messung_id, comment, wert) VALUES (%s,'%s',%s);"%(sens_id, sensors[sensor]["name"],distances[i])
            cur.execute(sql )
            mysql.commit()
            print ("Data " + color.GREEN+ "successfully" + color.END +" uploaded at %s"%now)
        else:
            print ("Not sumitted")
    mysql.close()

    signal.alarm(0)
#except:
#        print ("Not uploaded! :-(")
    
        
    #except:
    #    now = datetime.datetime.now()
    #    now = now.strftime('%Y-%m-%d %H:%M:%S')
        
    #    print color.BOLD+ " " + color.RED+"Warning: Data can't be uploaded at %s"%now +color.END
        

#def init_db(DB_NAME, db_schema_file):

def handler (signum, frame):
    print ("TIMEOUT")
    raise Exception ("EOT")

#if __name__ == '__main__':
#sensor = 0
import signal
while True:
    #if sensor ==1:
    #    sensor =0
    #else:
    #    sensor = 1
    for sensor in range (0,2):
        print ("starting measurement on sensor %s..."%sensors[sensor]["name"])
        distances = list()
        distances =  stat_dist_calib(sensors,sensor,CNT_MEASUREMENTS)
        print (distances)
        print ("measurement on sensor %s completed"%sensors[sensor]["name"])
    
        write_measurement_to_db(distances,sensors,sensor)
        signal.alarm(0)
    time.sleep(SLEEP)


mysql.close()

    
