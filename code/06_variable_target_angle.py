from time import sleep, perf_counter_ns
import json
import math
import signal
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250
from gpiozero import DigitalOutputDevice, PWMOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

# pip install mpu9250_jmdev, smbus2
imu = MPU9250(bus=1, gfs=GFS_250, afs=AFS_2G)
imu.abias =  [-0.02072217987804878, -0.0010539729420731708, 0.030785537347560954]
imu.gbias =  [0.3565346322408537, 1.0790941191882621, -1.2880650962271343]
imu.configure()

# Run "sudo pigpiod" to enable it.
my_factory = PiGPIOFactory()
motorPWM = PWMOutputDevice(12, pin_factory=my_factory)
motorDIR1 = DigitalOutputDevice(5)
motorDIR2 = DigitalOutputDevice(6)

motorPWM.frequency = 8000


startTime = perf_counter_ns()
lastGyroTime = perf_counter_ns()
lastPrintTime = perf_counter_ns()
time = 0
loopCount = 0
gyroAngle = float('nan')
filteredAngle = float('nan')
integral = 0
prevError = 0
targetAngle = 0

#exit program when Ctrl-C is pressed
exitRequested = False
def sigintHandler(sig, frame):
    print("Ctrl-C pressed, exit program")
    global exitRequested
    exitRequested = True
signal.signal(signal.SIGINT, sigintHandler)
signal.signal(signal.SIGTERM, sigintHandler)

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
    
    # Safety check
    if abs(filteredAngle) >= 18:
        # Stop motor
        motorDIR1.value = 0
        motorDIR2.value = 0
        motorPWM.value = 0
        break
    
    # Variable target angle
    ANGLE_FIXRATE = 2
    if filteredAngle < targetAngle:
        targetAngle += ANGLE_FIXRATE * timeDelta
    else:
        targetAngle -= ANGLE_FIXRATE * timeDelta
    
    #PID controller
    KP = 0.45
    KI = 0.5
    KD = 0.01
    error = targetAngle - filteredAngle
    integral += error * timeDelta
    derivative = (error - prevError) / timeDelta
    prevError = error
    PIDoutput = KP * error + KI * integral + KD * derivative
    
    #drive motor
    motorCtrl = min(max(PIDoutput, -1) , 1) # Limit
    motorPWM.value = abs(motorCtrl)
    motorDIR1.value = (motorCtrl > 0)
    motorDIR2.value = (motorCtrl < 0)
    
    #logData.append([secondsSinceStart,accAngle,gyroAngle,measuredAngle])
    if (perf_counter_ns() - lastPrintTime) / 1e9 >= 1.0:
        secondsSincePrint = (perf_counter_ns() - lastPrintTime) / 1e9
        lastPrintTime = perf_counter_ns()
        loopInterval = secondsSincePrint / loopCount * 1000
        loopCount = 0
        data =  {
                "accAngle": accAngle,
                "gyroAngle": gyroAngle,
                "filteredAngle": filteredAngle,
                "loopInterval": loopInterval
            }
        
        print(json.dumps(data)+',')
    
    
    sleep(0.001)
    loopCount += 1







