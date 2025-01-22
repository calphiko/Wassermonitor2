from legacy import sensortools as s
import termplotlib as tmpl
import csv

SENSOR = 1
CHANNEL = 'c1'

#Distances in [cm]
CALIB_DIST = [17,20,25,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]

FILE = 'calib_date_sensor_%s.csv'%SENSOR


sensors = {
    "c1": {"StBy": 128},
    "c2": {"StBy": 160},
    "c3": {"StBy": 192},
    "c4": {"StBy": 224}
}


def create_calib():
    f = open(FILE,'w')

    for d in CALIB_DIST:
        input ("Set sensor to %s cm distance and press ENTER"%d)
        d_m = s.get_raw_voltage(sensors, CHANNEL)
        f.write("%s;%s\n"%(d,d_m))
        print (d_m)


    f.close()

def get_termplot():
    cd = {
        "x":[],
        "y":[]
    }
    with open(FILE, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            # print (row)
            cd["x"].append(float(row[1]))
            cd["y"].append(float(row[0]))

    fig = tmpl.figure()
    print (cd)
    fig.plot(cd["x"], cd["y"])#, width=60, height=20)
    fig.show()

if __name__ == '__main__':
    create_calib()
    get_termplot()
