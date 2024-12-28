#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>
#include <Servo.h>

LSM9DS1 imu;
Servo myservo;

double roll = 0; // the rotation around the y and z axes
double prev = 0;
double current = 0;
double diff = 0;

void setup()
{
  Serial.begin(115200);

  Wire.begin();

  if (imu.begin() == false)
  {
    Serial.println("Failed to communicate with LSM9DS1.");
    Serial.println("Double-check wiring.");
    Serial.println("Default settings in this sketch will " \
                   "work for an out of the box LSM9DS1 " \
                   "Breakout, but may need to be modified " \
                   "if the board jumpers are.");
    while (1);
  }
  myservo.attach(3);
  myservo.write(0);
}

void loop()
{
 
  if ( imu.accelAvailable())
  {
  
  imu.readAccel(); // reads the acceleration values
  
  }

  diff = prev - current;
  
  if (diff < 0) {
  diff = diff * -1;
  }

  roll = atan2f(imu.ay * 9.81, imu.az * 9.81) * (180 / 3.14); // calculates the roll from the acceleration values
  current = roll;

  Serial.println("Roll: " + String(roll)); // Tests the roll value
  Serial.println("Difference: " + String(diff));

  if (roll < 30 && diff > 5) {
  myservo.write(0 - roll); // sets servo arm degree to opposite of the amount the roll is set to
  prev = current;
  }

  delay(80);
  
}
