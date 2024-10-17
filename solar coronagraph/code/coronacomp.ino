#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>
#include <Servo.h>

LSM9DS1 imu;

Servo servo_1;
Servo servo_2;
 
int photocellPin = 0;     // the cell and 10K pulldown are connected to a0
int photocellReading;     // the analog reading from the analog resistor divider 

double roll = 0; // the rotation around the y and z axes
double prev = 0;
double current = 0;
double diff = 0;

int first_pos = 0;
int current_pos = 0;

void setup()
{
  Serial.begin(115200);

  Wire.begin();

  servo_1.attach(9);
  servo_1.write(180);

  servo_2.attach(10);
  servo_2.write(0);

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

}

void loop() {

  photocellReading = analogRead(photocellPin); 
  
  if (imu.accelAvailable())
  {
  
    imu.readAccel(); // reads the acceleration values
  
  }

  diff = prev - current;
  
  if (diff < 0) {

    diff = diff * -1;

  }

  roll = atan2f(imu.ay * 9.81, imu.az * 9.81) * (180 / 3.14); // calculates the roll from the acceleration values
  current = roll;

  Serial.println("Roll: " + String(roll)); // tests the roll value
  Serial.println("Difference: " + String(diff));
  Serial.print("Analog reading = ");
  Serial.print(photocellReading);     // the raw analog reading

   if (photocellReading < 200) { //variable to change

    foundLight = false;
    servo_1.write(180);
    servo_2.attach(10);
    servo_2.write(first_pos);

    first_pos = first_pos + 1;

    if (first_pos >= 180) {

      first_pos = 0;

    }

  }

 else {

    foundLight = true;
    current_pos = first_pos;

  } 

  if (roll < 30 && foundLight == true) { //manipulate based on what the tests show about the pointing
    
    first_pos = 0;
    servo_1.attach(9);
    servo_2.detach();
    servo_1.write(0 - roll);
    prev = current;

  } 

  delay(7);
  
}
