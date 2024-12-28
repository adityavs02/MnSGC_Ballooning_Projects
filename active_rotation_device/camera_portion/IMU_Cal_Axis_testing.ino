  #include <Wire.h>
  #include <SPI.h>
  #include <SparkFunLSM9DS1.h>

  LSM9DS1 imu;

  #define PRINT_CALCULATED

  #define PRINT_SPEED 100

  static unsigned long lastPrint = 0; 

  #define DECLINATION 0.02

  void printGyro();
  void printAccel();
  void printMag();
  void printAttitude(float ax, float ay, float az, float mx, float my, float mz);

  double m[3] = {0}; //array that will hold all calibrated mag values
  int aveHeadingLength = 50;

  double aveHeading[50] = {0};
  
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
}

void loop()
{
  if ( imu.gyroAvailable() )
  {
    imu.readGyro();
  }
  if ( imu.accelAvailable() )
  {
    imu.readAccel();
  }
  if ( imu.magAvailable() )
  {
    imu.readMag();
  }

  if ((lastPrint + PRINT_SPEED) < millis())
  {
    printGyro();
    printAccel();
    printMag();
    magCal();
    
    String rawDataLog = String(imu.mx) + "," + String(imu.my) + "," + String(imu.mz);
    rawDataLog += "," + String(m[0]) + "," + String(m[1]) + "," + String(m[2]);
    
    printAttitude((-1*imu.ax), imu.ay, imu.az, -m[1], -m[0], m[2]);
    
    Serial.println();

    lastPrint = millis();
  }
}

void printGyro()
{

  Serial.print("G: ");
#ifdef PRINT_CALCULATED

  Serial.print(imu.calcGyro(imu.gx), 2);
  Serial.print(", ");
  Serial.print(imu.calcGyro(imu.gy), 2);
  Serial.print(", ");
  Serial.print(imu.calcGyro(imu.gz), 2);
  Serial.println(" deg/s");
#elif defined PRINT_RAW
  Serial.print(imu.gx);
  Serial.print(", ");
  Serial.print(imu.gy);
  Serial.print(", ");
  Serial.println(imu.gz);
#endif
}

void printAccel()
{

  Serial.print("A: ");
#ifdef PRINT_CALCULATED
  Serial.print(imu.calcAccel((-1*imu.ax)), 2);
  Serial.print(", ");
  Serial.print(imu.calcAccel(imu.ay), 2);
  Serial.print(", ");
  Serial.print(imu.calcAccel(imu.az), 2);
  Serial.println(" g");
#elif defined PRINT_RAW
  Serial.print(imu.ax);
  Serial.print(", ");
  Serial.print(imu.ay);
  Serial.print(", ");
  Serial.println(imu.az);
#endif

}

void printMag()
{

  Serial.print("Non Cal M: ");
  Serial.print(imu.calcMag(imu.mx), 4);
  Serial.print(", ");
  Serial.print(imu.calcMag(imu.my), 4);
  Serial.print(", ");
  Serial.print(imu.calcMag(imu.mz), 4);
  Serial.println(" gauss");

  Serial.print("Yes Cal M: ");
  Serial.print(imu.calcMag(m[0]), 4);
  Serial.print(", ");
  Serial.print(imu.calcMag(m[1]), 4);
  Serial.print(", ");
  Serial.print(imu.calcMag(m[2]), 4);
  Serial.println(" gauss");

  Serial.print("Raw M: ");
  Serial.print(imu.mx);
  Serial.print(", ");
  Serial.print(imu.my);
  Serial.print(", ");
  Serial.println(imu.mz);

  Serial.print("Cal M: ");
  Serial.print(m[0]);
  Serial.print(", ");
  Serial.print(m[1]);
  Serial.print(", ");
  Serial.println(m[2]);
}

void printAttitude(float ax, float ay, float az, float mx, float my, float mz)
{
  
  float roll;
  float pitch;
  
  float newroll;
  float newpitch;
  
  float rollrad;
  float pitchrad;
  float heading;

  float AccelEx, AccelEy, AccelEz, MagEx, MagEy, MagEz; // E is for the original acceleration values, and E2 is for the original magnetometer values.
  float AccelIx, AccelIy, AccelIz, MagIx, MagIy, MagIz; // I is for the new acceleration values, and I2 is for the new magneotmeter values.

  AccelIx = imu.calcAccel(ax);
  AccelIy = imu.calcAccel(ay);
  AccelIz = imu.calcAccel(az);

  MagIx = imu.calcMag(m[1]);
  MagIy = imu.calcMag(m[2]);
  MagIz = imu.calcMag(m[3]);

  roll = atan2(ax, ay);
  pitch = atan2(-ax, sqrt(ay * ay + az * az));

  rollrad = roll * (PI/float(180));
  pitchrad = pitch * (PI/float(180));

  AccelEx = (cos(pitchrad) * AccelIx) - ((sin(pitchrad)) * AccelIz); // These equations still give similar readings to the original acceleration values, disregarding heading, pitch, and roll.
  AccelEy = (sin(rollrad) * sin(pitchrad) * AccelIx) + (cos(rollrad) * AccelIy) + (sin(rollrad)*cos(pitchrad) * AccelIz);
  AccelEz = (cos(rollrad) * sin(pitchrad) * AccelIx) - (sin(rollrad) * AccelIy) + (cos(rollrad) * cos(pitchrad) * AccelIz);

  MagEx = (cos(pitchrad) * MagIx) - (sin(pitchrad) * MagIz); // These equations still give similar readings to the original magnetometer values, disregarding heading, pitch, and roll.
  MagEy = (sin(rollrad) * sin(pitchrad) * MagIx + (cos(rollrad) * MagIy + (sin(rollrad)*cos(pitchrad) * MagIz)));
  MagEz = (cos(rollrad) * sin(pitchrad) * MagIx + (-1 * sin(rollrad) * MagIy) + (cos(rollrad) * cos(pitchrad) * MagIz));

  newroll = atan2(AccelEx, AccelEy);
  newpitch = atan2(-AccelEx, sqrt(AccelEy * AccelEy + AccelEz * AccelEz));

  heading = atan2(MagEy, MagEx) * (180 / PI); // I was just messing around with new functions for heading.
  
  heading *= 180.0 / PI;
  pitch *= 180.0 / PI;
  roll  *= 180.0 / PI;

  Serial.print("Pitch, Roll: ");
  Serial.print(pitch, 2);
  Serial.print(", ");
  Serial.println(roll, 2);
  Serial.print("Calibrated Heading: "); Serial.println(heading, 2);

  Serial.print("MagEx is: ");
  Serial.print(MagEx,5); 
  Serial.print("  MagEy is: ");
  Serial.print(MagEy,5);
  Serial.print("  MagEz is: ");
  Serial.print(MagEz,5);
  Serial.println("");

}
