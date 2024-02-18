from time import sleep
from gpiozero import DigitalOutputDevice, PWMOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

# Run "sudo pigpiod" to enable it.
my_factory = PiGPIOFactory()
motorPWM = PWMOutputDevice(12, pin_factory=my_factory)
motorDIR1 = DigitalOutputDevice(5)
motorDIR2 = DigitalOutputDevice(6)

motorPWM.frequency = 8000

print("Drive motor 0-100 CCW")
motorDIR1.value = 0
motorDIR2.value = 1
motorPWM.value = 0
for i in range(101):
    motorPWM.value = i / 100
    print(f"   pwm {motorPWM.value:,.2f} %%")
    sleep(0.04)
sleep(2)
for i in range(101):
    motorPWM.value = 1.0 - i / 100
    print(f"   pwm {motorPWM.value:,.2f} %%")
    sleep(0.04)

print("Stop motor")
motorDIR1.value = 0
motorDIR2.value = 0
motorPWM.value = 0
