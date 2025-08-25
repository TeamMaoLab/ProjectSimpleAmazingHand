from machine import Pin, PWM
import time

# --- Servo Configuration ---
SERVO_PIN = 14  # GPIO pin connected to the servo's PWM signal line
servo = PWM(Pin(SERVO_PIN), freq=50) # 50Hz PWM frequency for servos

# Function to set servo angle (for limited-range servos like SG90/SG92)
# Note: This is a simplified mapping. You might need to calibrate for your specific servo.
def set_servo_angle(angle):
    # SG90/SG92 typically use a pulse width between 0.5ms (0 degrees) and 2.5ms (180 degrees)
    # 0.5ms corresponds to a duty of about 25, 2.5ms corresponds to about 125 on a 50Hz PWM (20ms period)
    # This maps 0-180 degrees to duty 25-125
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    duty = int((angle / 180) * (125 - 25) + 25)
    servo.duty(duty)

# Main test loop
print("Starting servo test on pin", SERVO_PIN)
print("Moving to 0 degrees...")
set_servo_angle(0)
time.sleep(1)

print("Moving to 90 degrees...")
set_servo_angle(90)
time.sleep(1)

print("Moving to 180 degrees...")
set_servo_angle(180)
time.sleep(1)

print("Test complete. Sweeping from 0 to 180 and back...")

# Continuous sweep for observation
try:
    while True:
        for angle in range(0, 181, 10): # 0 to 180 in steps of 10
            print(f"Setting angle to {angle} degrees")
            set_servo_angle(angle)
            time.sleep(0.5)
        for angle in range(180, -1, -10): # 180 to 0 in steps of 10
            print(f"Setting angle to {angle} degrees")
            set_servo_angle(angle)
            time.sleep(0.5)
except KeyboardInterrupt:
    print("\nTest stopped by user.")
    # Move to a neutral position
    set_servo_angle(90)