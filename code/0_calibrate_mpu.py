from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

imu = MPU9250(bus=1)
imu.calibrateMPU6500()
print("imu.abias = ", imu.abias)
print("imu.gbias = ", imu.gbias)
