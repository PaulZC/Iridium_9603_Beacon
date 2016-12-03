// ####################################
// # Paul Clark's Iridium 9603 Beacon #
// ####################################

// With grateful thanks to Mikal Hart:
// Based on Mikal's IridiumSBD Beacon example: https://github.com/mikalhart/IridiumSBD
// Requires Mikal's TinyGPS library: https://github.com/mikalhart/TinyGPS
// and PString: http://arduiniana.org/libraries/pstring/

// With grateful thanks to:
// Adafruit: https://learn.adafruit.com/using-atsamd21-sercom-to-add-more-spi-i2c-serial-ports/creating-a-new-serial
// MartinL: https://forum.arduino.cc/index.php?topic=341054.msg2443086#msg2443086

// The Iridium_9603_Beacon PCB is based extensively on the Adafruit Feather M0 (Adalogger)
// https://www.adafruit.com/products/2796
// GPS data provided by Adafruit Ultimate GPS
// https://www.adafruit.com/products/790
// Pressure (altitude) and temperature provided by MPL3115A2
// Requires Adafruit's MPL3115A2 library
// https://github.com/adafruit/Adafruit_MPL3115A2_Library

// Uses RTCZero to provide sleep functionality (on the M0)
// https://github.com/arduino-libraries/RTCZero

// With grateful thanks to CaveMoa for his SimpleSleepUSB example
// https://github.com/cavemoa/Feather-M0-Adalogger
// https://github.com/cavemoa/Feather-M0-Adalogger/tree/master/SimpleSleepUSB
// Note: you will need to close and re-open your serial monitor each time the M0 wakes up

// Iridium 9603 is interfaced to the M0 using Serial2
// D6 (Port A Pin 20) = Enable (Sleep) : Connected to 9603 ON/OFF Pin 5
// D10 (Port A Pin 18) = Serial2 TX : Connected to 9603 Pin 6
// D12 (Port A Pin 19) = Serial2 RX : Connected to 9603 Pin 7
// A3 / D17 (Port A Pin 4) = Network Available : Connected to 9603 Pin 19

// Iridium 9603 is powered from Linear Technology LTC3225 SuperCapacitor Charger
// (fitted with 2 x 1F 2.7V caps e.g. Bussmann HV0810-2R7105-R)
// to provide the 1.3A peak current when the 9603 is transmitting
// http://www.linear.com/product/LTC3225
// D5 (Port A Pin 15) = LTC3225 ~Shutdown
// A1 / D15 (Port B Pin 8) = LTC3225 PGOOD

// Ultimate GPS is interfaced to the M0 using Serial1
// D1 (Port A Pin 10) = Serial1 TX : Connected to GPS RX
// D0 (Port A Pin 11) = Serial1 RX : Connected to GPS TX
// D11 (Port A Pin 16) = GPS ENable : Connected to Q1 (DMG3415U-7) Gate

// MPL3115A2 Pressure (Altitude) and Temperature Sensor
// D20 (Port A Pin 22) = SDA : Connected to MPL3115A2 SDA
// D21 (Port A Pin 23) = SCL : Connected to MPL3115A2 SCL

// D13 (Port A Pin 17) = Red LED
// D9 (Port A Pin 7) = AIN 7 : Battery Voltage / 2

#include <IridiumSBD.h>
#include <TinyGPS.h> // NMEA parsing: http://arduiniana.org
#include <PString.h> // String buffer formatting: http://arduiniana.org

#include <RTCZero.h> // M0 Real Time Clock
RTCZero rtc; // Create an rtc object
int BEACON_INTERVAL = 10; // Define how often messages are sent initially in MINUTES (suggested values: 10,12,15,20,30,60,120,180,240) (max 1440)
// BEACON_INTERVAL can be modified during code execution e.g. when iterationCounter reaches a value [Line 251-252]

// MPL3115A2
#include <Wire.h>
#include <Adafruit_MPL3115A2.h>
Adafruit_MPL3115A2 baro = Adafruit_MPL3115A2();

// Serial2 pin and pad definitions (in Arduino files Variant.h & Variant.cpp)
#define PIN_SERIAL2_RX       (34ul)               // Pin description number for PIO_SERCOM on D12
#define PIN_SERIAL2_TX       (36ul)               // Pin description number for PIO_SERCOM on D10
#define PAD_SERIAL2_TX       (UART_TX_PAD_2)      // SERCOM pad 2 (SC1PAD2)
#define PAD_SERIAL2_RX       (SERCOM_RX_PAD_3)    // SERCOM pad 3 (SC1PAD3)
// Instantiate the Serial2 class
Uart Serial2(&sercom1, PIN_SERIAL2_RX, PIN_SERIAL2_TX, PAD_SERIAL2_RX, PAD_SERIAL2_TX);
HardwareSerial &ssIridium(Serial2);

#define ssGPS Serial1 // Use M0 Serial1 to interface to the Ultimate GPS

IridiumSBD isbd(ssIridium, 6); // Iridium Sleep connected to D6
TinyGPS tinygps;
static const int ledPin = 13; // Red LED on pin D13
long iterationCounter = 0;

static const int networkAvailable = 17; // 9602 Network Available on pin D17
static const int LTC3225shutdown = 5; // LTC3225 ~Shutdown on pin D5
static const int LTC3225PGOOD = 15; // LTC3225 PGOOD on pin A1 / D15
static const int GPS_EN = 11; // Ultimate GPS Enable on pin D11
#define GPS_ON LOW
#define GPS_OFF HIGH

// IridiumSBD Callback
bool ISBDCallback()
{
  digitalWrite(ledPin, (millis() / 1000) % 2 == 1 ? HIGH : LOW);
  return true;
}

// Interrupt handler for SERCOM1 (essential for Serial2 comms)
void SERCOM1_Handler()
{
  Serial2.IrqHandler();
}

// RTC alarm interrupt
void alarmMatch()
{
  int rtc_mins = rtc.getMinutes(); // Read the RTC minutes
  int rtc_hours = rtc.getHours(); // Read the RTC hours
  if (BEACON_INTERVAL > 1440) BEACON_INTERVAL = 1440; // Limit BEACON_INTERVAL to one day
  rtc_mins = rtc_mins + BEACON_INTERVAL; // Add the BEACON_INTERVAL to the RTC minutes
  while (rtc_mins >= 60) { // If there has been an hour roll over
    rtc_mins = rtc_mins - 60; // Subtract 60 minutes
    rtc_hours = rtc_hours + 1; // Add an hour
  }
  rtc_hours = rtc_hours % 24; // Check for a day roll over
  rtc.setAlarmMinutes(rtc_mins); // Set next alarm time (minutes)
  rtc.setAlarmHours(rtc_hours); // Set next alarm time (hours)
}

void setup()
{
  rtc.begin(); // Start the RTC
  rtc.setAlarmSeconds(rtc.getSeconds()); // Initialise RTC Alarm Seconds
  alarmMatch(); // Set next alarm time
  rtc.enableAlarm(rtc.MATCH_HHMMSS); // Alarm Match on hours, minutes and seconds
  rtc.attachInterrupt(alarmMatch); // Attach alarm interrupt
  
  pinMode(ledPin, OUTPUT); // Adalogger Red LED

  pinMode(LTC3225shutdown, OUTPUT); // LTC3225 supercapacitor charger shutdown pin
  digitalWrite(LTC3225shutdown, HIGH); // Enable the LTC3225 supercapacitor charger
  pinMode(LTC3225PGOOD, INPUT); // Define an input for the LTC3225 Power Good signal
  
  pinMode(GPS_EN, OUTPUT); // Adafruit Ultimate GPS enable
  digitalWrite(GPS_EN, GPS_ON); // Enable the GPS and MPL3115A2
  
  pinMode(networkAvailable, INPUT); // Define an input for the Iridium 9603 Network Available signal
  
  // Start the serial console
  Serial.begin(115200);

  // flash red LED on reset
  for (int i=0; i <= 4; i++) {
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
  delay(18000); // Wait remainder of 20secs - allow time for super caps to charge and for user to open serial monitor

  // Send welcome message
  Serial.println("Iridium9603Beacon");
  // Check LTC3225 PGOOD
  Serial.println("Checking LTC3225 PGOOD...");
  int PGOOD = digitalRead(LTC3225PGOOD);
  while (PGOOD == LOW) {
    Serial.println("Waiting for PGOOD to go HIGH...");
    delay(1000);
    PGOOD = digitalRead(LTC3225PGOOD);
  }
  Serial.println("LTC3225 PGOOD OK!");

  // Setup the IridiumSBD
  isbd.attachConsole(Serial);
  isbd.attachDiags(Serial);
  isbd.setPowerProfile(1);
  isbd.useMSSTMWorkaround(false);
}

void loop()
{
  int year;
  byte month, day, hour, minute, second, hundredths;
  unsigned long dateFix, locationFix;
  float latitude, longitude;
  long altitude;
  bool fixFound = false;
  bool charsSeen = false;
  unsigned long loopStartTime = millis();

  // Step 0: Start the serial ports
  ssIridium.begin(19200);
  ssGPS.begin(9600);

  // Configure Ultimate GPS
  Serial.println("Configuring GPS...");
  ssGPS.println("$PMTK220,1000*1F"); // Set NMEA Update Rate to 1Hz
  delay(100);
  ssGPS.println("$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28"); // Set NMEA Output to GGA and RMC
  delay(100);
  ssGPS.println("$PGCMD,33,0*6D"); // Disable Antenna Updates
  delay(1100); // Delay for > 1 second

  // Step 1: Reset TinyGPS and begin listening to the GPS
  Serial.println("Beginning to listen for GPS traffic...");
  tinygps = TinyGPS();
  
  // Step 2: Look for GPS signal for up to 7 minutes
  for (unsigned long now = millis(); !fixFound && millis() - now < 7UL * 60UL * 1000UL;)
  {
    if (ssGPS.available())
    {
      charsSeen = true;
      if (tinygps.encode(ssGPS.read()))
      {
        tinygps.f_get_position(&latitude, &longitude, &locationFix);
        tinygps.crack_datetime(&year, &month, &day, &hour, &minute, &second, &hundredths, &dateFix);
        altitude = tinygps.altitude();
        fixFound = locationFix != TinyGPS::GPS_INVALID_FIX_TIME && 
                   dateFix != TinyGPS::GPS_INVALID_FIX_TIME && 
                   altitude != TinyGPS::GPS_INVALID_ALTITUDE &&
                   year != 2000;
      }
    }
    ISBDCallback(); // We can call it during our GPS loop too.

    // if we haven't seen any GPS in 5 seconds, then the wiring is wrong.
    if (!charsSeen && millis() - now > 5000)
    break;
  }

  Serial.println(charsSeen ? fixFound ? F("A GPS fix was found!") : F("No GPS fix was found.") : F("Wiring error: No GPS data seen."));

  // Start the MPL3115A2 (does Wire.begin())
  float pascals, tempC;
  if (baro.begin()) {
    pascals = baro.getPressure();
    if (pascals > 110000) pascals = 0.0; // Correct wrap-around if pressure drops too low
    tempC = baro.getTemperature();
  }
  else {
    Serial.println("Error initialising MPL3115A2!");
    pascals = 0.0;
    tempC = 0.0;
  }

  // Read battery voltage
  float vbat = analogRead(A7) * (2.0 * 3.3 / 1023.0);
  // check if voltage is >= 3.55V
  if (vbat < 3.55) {
    Serial.println("!!LOW BATTERY!!"); // Warn the user but keep going...
  }

  // Step 3: Start talking to the 9603 and power it up
  Serial.println("Beginning to talk to the 9603...");
  
  ++iterationCounter; // Increment iterationCounter

  // Update BEACON_INTERVAL if required (comment these lines out if you want BEACON_INTERVAL to remain constant)
  if (iterationCounter > 12) BEACON_INTERVAL = 60; // Send every 10 mins for the first two hours then drop to once per hour
  if (iterationCounter > 250) BEACON_INTERVAL = 360; // After ten days, drop to once every six hours
  
  if (isbd.begin() == ISBD_SUCCESS)
  {
    char outBuffer[80]; // Always try to keep message short

    if (fixFound)
    {
      sprintf(outBuffer, "%d%02d%02d%02d%02d%02d,", year, month, day, hour, minute, second);
      int len = strlen(outBuffer);
      PString str(outBuffer + len, sizeof(outBuffer) - len);
      str.print(latitude, 6);
      str.print(",");
      str.print(longitude, 6);
      str.print(",");
      str.print(altitude / 100);
      str.print(",");
      str.print(tinygps.f_speed_knots(), 1);
      str.print(",");
      str.print(tinygps.course() / 100);
      str.print(",");
      str.print(pascals, 0);
      str.print(",");
      str.print(tempC, 1);
      str.print(",");
      str.print(vbat, 2);
    }

    else
    {
      sprintf(outBuffer, "%d: No GPS fix found!", iterationCounter);
    }

    Serial.print("Transmitting message '");
    Serial.print(outBuffer);
    Serial.println("'");
    isbd.sendSBDText(outBuffer);

    Serial.println("Putting 9603 in sleep mode...");
    isbd.sleep();
  }

  // Get ready for sleep
  Serial.println("Going to sleep until next alarm time...");
  ssIridium.end();
  ssGPS.end();
  delay(1000); // Wait for serial ports to clear

  // Disable LEDs
  digitalWrite(ledPin, LOW);
  pinMode(ledPin, INPUT);

  // Save power by disabling both GPS and Iridium supercapacitor charger
  Wire.end(); // Stop I2C comms
  digitalWrite(GPS_EN, GPS_OFF); // Disable the GPS and MPL3115A2
  digitalWrite(LTC3225shutdown, LOW); // Disable the LTC3225 supercapacitor charger

  // Close and detach the serial console (as per CaveMoa's SimpleSleepUSB)
  Serial.end(); // Close the serial console
  USBDevice.detach(); // Safely detach the USB prior to sleeping

  // Sleep until next alarm match
  rtc.standbyMode();

  // Check battery voltage after sleep
  // If voltage is <3.55V, everything is still powered down so go back to sleep and wait for battery to recharge
  delay(1100); // Let things stabilise and make sure rtc moves on by at least 1 second (redundant?)
  vbat = analogRead(A7) * (2.0 * 3.3 / 1023.0); // Read battery voltage
  while (vbat < 3.55) { // Is voltage <3.55V?
    rtc.standbyMode(); // Sleep again
    delay(1100); // Let things stabilise again
    vbat = analogRead(A7) * (2.0 * 3.3 / 1023.0); // Read battery voltage again
  }

  // Attach and reopen the serial console
  USBDevice.attach(); // Re-attach the USB
  delay(1000);  // Delay added to make serial more reliable
  Serial.begin(115200); // Restart serial console
  Serial.println("Wake up!");

  // Enable LEDs
  pinMode(ledPin, OUTPUT);

  // Re-enable GPS and Iridium supercapacitor charger
  digitalWrite(GPS_EN, GPS_ON); // Enable the GPS and MPL3115A2
  digitalWrite(LTC3225shutdown, HIGH); // Enable the LTC3225 supercapacitor charger

  // flash red LED on wake
  for (int i=0; i <= 4; i++) {
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
  delay(18000); // Wait remainder of 20secs - allow time for super caps to recharge

  // Check LTC3225 PGOOD
  Serial.println("Checking LTC3225 PGOOD...");
  int PGOOD = digitalRead(LTC3225PGOOD);
  while (PGOOD == LOW) {
    Serial.println("Waiting for PGOOD to go HIGH...");
    delay(1000);
    PGOOD = digitalRead(LTC3225PGOOD);
  }
  Serial.println("LTC3225 PGOOD OK!");
}


