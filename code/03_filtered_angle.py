from time import sleep, perf_counter_ns
import math
import signal
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

# pip install mpu9250_jmdev, smbus2
imu = MPU9250(bus=1, gfs=GFS_250, afs=AFS_2G)
abias =  [-0.093890380859375, 0.000372314453125, 0.01622924804687509]
gbias =  [0.33931732177734375, 1.1068344116210938, -1.149749755859375]
imu.configure()

#imu.calibrateMPU6500()
#print("imu.abias: ",  imu.abias)
#print("imu.gbias: ",  imu.gbias)

startTime = perf_counter_ns()
lastGyroTime = perf_counter_ns()
lastPrintTime = perf_counter_ns()
time = 0
loopCount = 0
gyroAngle = float('nan')
filteredAngle = float('nan')
filename   = "datalog.dat"

logData = [["secondsSinceStart","accAngle","gyroAngle","filteredAngle"]]

#exit program when Ctrl-C is pressed
exitRequested = False
def sigintHandler(sig, frame):
    print("Ctrl-C pressed, exit program")
    global exitRequested
    exitRequested = True
signal.signal(signal.SIGINT, sigintHandler)
signal.signal(signal.SIGTERM, sigintHandler)

print("program started")
sleep(0.1)

while not exitRequested:

    secondsSinceStart = (perf_counter_ns() - startTime) / 1e9

    #read accelerometer
    ax, ay, az = imu.readAccelerometerMaster()  #[G]
    accAngle = math.atan(-ax / math.sqrt(pow(ay, 2) + pow(az, 2))) * 180 / math.pi  #[deg]
    
    #read gyroscope
    gx, gy, gz = imu.readGyroscopeMaster()  #[deg/s]
    timeDelta = (perf_counter_ns() - lastGyroTime) / 1e9  #[sec]
    lastGyroTime = perf_counter_ns()
    gyroAngleDelta = gz * timeDelta
    if math.isnan(gyroAngle): gyroAngle = accAngle
    gyroAngle += gyroAngleDelta  #[deg]
    
    #complementary filter
    if math.isnan(filteredAngle): filteredAngle = accAngle
    filteredAngle = 0.999 * (filteredAngle + gyroAngleDelta) + 0.001 * accAngle
    
    #debug print
    print(filteredAngle)
    sleep(0.001)
    loopCount += 1


print("log size", len(logData), "rows")
if len(logData) > 0:
    
    print("write to file:", filename)
    file = open(filename, "w")
    for logLine in logData:
        for value in logLine:
            file.write(str(value) + ' ')
        file.write('\n')
    file.close()

print("program ended")

