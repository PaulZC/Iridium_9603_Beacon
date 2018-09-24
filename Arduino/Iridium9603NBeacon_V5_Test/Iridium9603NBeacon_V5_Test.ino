// ################################
// # Iridium 9603N Beacon V5 Test #
// ################################

// This code tests the components on V5 of the Iridium 9603N Beacon PCB

// Power the beacon PCB via USB and - if possible - monitor the current draw at the same time

// The tests won't start until the Serial Monitor is opened

#include <IridiumSBD.h> // Requires V2: https://github.com/mikalhart/IridiumSBD

#include <Adafruit_NeoPixel.h> // Support for the WB2812B: https://github.com/adafruit/Adafruit_NeoPixel

static const int ledPin = 13; // WB2812B + Red LED on pin D13
//#define swap_red_green // Uncomment this line if your WB2812B has red and green reversed
#ifdef swap_red_green
  Adafruit_NeoPixel pixels = Adafruit_NeoPixel(1, ledPin, NEO_GRB + NEO_KHZ800); // GRB WB2812B
#else
  Adafruit_NeoPixel pixels = Adafruit_NeoPixel(1, ledPin, NEO_RGB + NEO_KHZ800); // RGB WB2812B
#endif
#define LED_Brightness 128 // 0 - 255 for WB2812B

static const int GPS_EN = 11; // GPS & MPL3115A2 Enable on pin D11
#define GPS_ON LOW
#define GPS_OFF HIGH

#define VAP A7 // Bus voltage analog pin (bus voltage divided by 2)
#define VREF A0 // 1.25V precision voltage reference
#define VBUS_NORM 3.3 // Normal bus voltage for battery voltage calculations
#define VREF_NORM 1.25 // Normal reference voltage for battery voltage calculations
#define VBAT_LOW 3.05 // Minimum voltage for LTC3225

static const int set_coil = 7; // OMRON G6SK relay set coil (pull low to energise coil)
static const int reset_coil = 2; // OMRON G6SK relay reset coil (pull low to energise coil)

// eRIC CTS / BUSY (output) is connected to MISO (Digital Pin 22)
// eRIC Pin22 (wake from low power) is connected to CS (Digital Pin 4)
static const int eRIC_BUSY = 22;
static const int eRIC_WAKE = 4;

// MPL3115A2: https://github.com/adafruit/Adafruit_MPL3115A2_Library
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
HardwareSerial &ssIridium(Serial2); // Use M0 Serial2 to interface to the Iridium 9603N

// Serial3 pin and pad definitions (in Arduino files Variant.h & Variant.cpp)
// eRIC Tx (input) is connected to MOSI (Digital Pin 23, Port B Pin 10, SERCOM4 Pad 2, Serial3 Tx)
// eRIC Rx (output) is connected to SCK (Digital Pin 24, Port B Pin 11, SERCOM4 Pad 3, Serial3 Rx)
#define PIN_SERIAL3_RX       (24ul)               // Pin description number for PIO_SERCOM on D24
#define PIN_SERIAL3_TX       (23ul)               // Pin description number for PIO_SERCOM on D23
#define PAD_SERIAL3_TX       (UART_TX_PAD_2)      // SERCOM4 Pad 2 (SC4PAD2)
#define PAD_SERIAL3_RX       (SERCOM_RX_PAD_3)    // SERCOM4 Pad 3 (SC4PAD3)
// Instantiate the Serial3 class
Uart Serial3(&sercom4, PIN_SERIAL3_RX, PIN_SERIAL3_TX, PAD_SERIAL3_RX, PAD_SERIAL3_TX);
HardwareSerial &sseRIC(Serial3);

static const int ringIndicator = 17; // 9602 Ring Indicator on pin D17
static const int LTC3225shutdown = 5; // LTC3225 ~Shutdown on pin D5
static const int LTC3225PGOOD = 15; // LTC3225 PGOOD on pin A1 / D15
static const int Enable_9603N = 19; // 9603N Enable (enables EXT_PWR via P-MOSFET)
static const int IridiumSleepPin = 6; // Iridium Sleep connected to D6
IridiumSBD isbd(ssIridium, IridiumSleepPin); // This should disable the 9603

#define ssGPS Serial1 // Use M0 Serial1 to interface to the MAX-M8Q

// Globals
float vbat = 5.3;
float vref = VREF_NORM;
float vrail = VBUS_NORM;
unsigned long tnow;
int PGOOD;

// NeoPixel functions

void LED_off() // Turn NeoPixel off
{
  pixels.setPixelColor(0,0,0,0);
  pixels.show();
}

void LED_white() // Set LED to white
{
  pixels.setPixelColor(0, pixels.Color(222,222,255)); // Set color.
  pixels.show(); // This sends the updated pixel color to the hardware.
}

void LED_red() // Set LED to red
{
  pixels.setPixelColor(0, pixels.Color(222,0,0)); // Set color.
  pixels.show(); // This sends the updated pixel color to the hardware.
}

void LED_green() // Set LED to green
{
  pixels.setPixelColor(0, pixels.Color(0,222,0)); // Set color.
  pixels.show(); // This sends the updated pixel color to the hardware.
}

void LED_blue() // Set LED to blue
{
  pixels.setPixelColor(0, pixels.Color(0,0,255)); // Set color.
  pixels.show(); // This sends the updated pixel color to the hardware.
}

void set_relay()
{
  pinMode(set_coil, OUTPUT); // Make relay set_coil pin an output
  digitalWrite(set_coil, LOW); // Pull pin low
  delay(20); // Pull pin low for 20msec
  digitalWrite(set_coil, HIGH); // Pull pin high again
  pinMode(set_coil, INPUT_PULLUP); // Make relay set_coil pin high-impedance 
}

void reset_relay()
{
  pinMode(reset_coil, OUTPUT); // Make relay reset_coil pin an output
  digitalWrite(reset_coil, LOW); // Pull pin low
  delay(20); // Pull pin low for 20msec
  digitalWrite(reset_coil, HIGH); // Pull pin high again
  pinMode(reset_coil, INPUT_PULLUP); // Make relay reset_coil pin high-impedance 
}

// Interrupt handler for SERCOM1 (essential for Serial2 comms)
void SERCOM1_Handler()
{
  Serial2.IrqHandler();
}

// Interrupt handler for SERCOM4 (essential for Serial3 comms)
void SERCOM4_Handler()
{
  Serial3.IrqHandler();
}

// Read 'battery' voltage
void get_vbat() {
  // Measure the reference voltage and calculate the rail voltage
  vref = analogRead(VREF) * (VBUS_NORM / 1023.0);
  vrail = VREF_NORM * VBUS_NORM / vref;

  vbat = analogRead(VAP) * (2.0 * vrail / 1023.0); // Read 'battery' voltage from resistor divider, correcting for vrail
}

// http://forum.arduino.cc/index.php?topic=288234.0
const byte numChars = 32;
char receivedChars[numChars]; // an array to store the received data
boolean newData = false;

void recvWithEndMarker() {
  static byte ndx = 0;
  char endMarker = '\n';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (rc != endMarker) {
      receivedChars[ndx] = rc;
      ndx++;
      if (ndx >= numChars) {
        ndx = numChars - 1;
      }
    }
    else {
      receivedChars[ndx] = '\0'; // terminate the string
      ndx = 0;
      newData = true;
    }
  }
}

void waitForLF() {
  Serial.println("Press Send to continue...");
  Serial.println();
  while (newData == false) {
    recvWithEndMarker();
  }
  newData = false;
}

// Iridium SBD V2 console and diagnostic callbacks (replacing attachConsole and attachDiags)
void ISBDConsoleCallback(IridiumSBD *device, char c) { Serial.write(c); }
void ISBDDiagsCallback(IridiumSBD *device, char c) { Serial.write(c); }

void setup()
{
  pinMode(LTC3225shutdown, OUTPUT); // LTC3225 supercapacitor charger shutdown pin
  digitalWrite(LTC3225shutdown, LOW); // Disable the LTC3225 supercapacitor charger
  pinMode(LTC3225PGOOD, INPUT); // Define an input for the LTC3225 Power Good signal
  
  pinMode(Enable_9603N, OUTPUT); // 9603N enable via P-FET and NPN transistor
  digitalWrite(Enable_9603N, LOW); // Disable the 9603N
  
  pinMode(GPS_EN, OUTPUT); // GPS & MPL3115A2 enable
  digitalWrite(GPS_EN, GPS_OFF); // Disable the GPS and MPL3115A2
  
  //pinMode(IridiumSleepPin, OUTPUT); // Iridium 9603N Sleep Pin
  //digitalWrite(IridiumSleepPin, LOW); // Disable the Iridium 9603
  pinMode(ringIndicator, INPUT); // Define an input for the Iridium 9603 Ring Indicator

  pinMode(set_coil, INPUT_PULLUP); // Initialise relay set_coil pin
  pinMode(reset_coil, INPUT_PULLUP); // Initialise relay reset_coil pin

  pinMode(eRIC_BUSY, INPUT_PULLUP); // Initialise eRIC CTS / BUSY pin
  pinMode(eRIC_WAKE, OUTPUT); // Initialise eRIC WAKE pin (PIN22)
  digitalWrite(eRIC_WAKE, HIGH); // Enable eRIC

  pixels.begin(); // This initializes the NeoPixel library.
  delay(100); // Seems necessary to make the NeoPixel start reliably 
  pixels.setBrightness(LED_Brightness); // Initialize the LED brightness
  LED_off(); // Turn NeoPixel off
}

void loop()
{
  // Start the serial console
  Serial.begin(115200);
  while (!Serial) ; // Wait for the user to open the serial console

  // Send welcome message
  Serial.println("Iridium 9603N Beacon V5 Test");
  Serial.println("Includes support for the Iridium Beacon Radio Board");
  Serial.println();
  Serial.println("Check that the Serial Monitor baud rate is set to 115200");
  Serial.println("and that the line ending is set to Newline");
  Serial.println();
  Serial.println("Confirm that the beacon is being powered via USB");
  waitForLF();

  // Check VREF and VBUS
  get_vbat(); // Read 'battery' voltage
  Serial.print("VREF is ");
  Serial.print(vref);
  Serial.print("V : ");
  if ((vref >= 1.20) and (vref <= 1.30))
    Serial.println("PASS");
  else
    Serial.println("FAIL!");
  Serial.println();
  
  Serial.print("VBUS is ");
  Serial.print(vbat);
  Serial.print("V : ");
  if ((vbat >= 4.60) and (vbat <= 5.20))
    Serial.println("PASS");
  else
    Serial.println("FAIL!");
  Serial.println();

  // Check current draw
  Serial.println("If radio board is connected: check current draw is approx. 20mA");
  Serial.println("If radio board is not connected: check current draw is approx. 16mA");
  waitForLF();

  // Test eRIC radio board
  // Configure the eRIC then put it into low power mode
  // Serial data from the eRIC (apart from the serial number) is ignored
  // so the code won't hang if the radio board is not connected
  // Start the eRIC serial port
  Serial.println("Check LED1 on the radio board is flashing once per second");
  waitForLF();
  Serial.println("Configuring eRIC and requesting its serial number:");
  sseRIC.begin(19200);
  delay(1000); // Allow time for the port to open
  
  sseRIC.print("ER_CMD#R0"); // Reset Radio
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(500);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer

  sseRIC.print("ER_CMD#C5"); // Set Channel 5
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(50);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  
  sseRIC.print("ER_CMD#B0"); // Set Over-Air Baud Rate to 1200
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(50);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  
  sseRIC.print("ER_CMD#P0"); // Set Transmit Power to 0dBm
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(50);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  
  sseRIC.print("ER_CMD#D2"); // Set RX Power Saving
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(500);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  
  sseRIC.print("ER_CMD#d2"); // Set TX Power Saving
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(500);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  
  sseRIC.print("ER_CMD#L8?"); // Get eRIC serial number
  delay(50);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  sseRIC.print("ACK"); // Acknowledge
  delay(500);
  // Transmit serial number
  sseRIC.print("Iridium Beacon Radio Board ");
  while(sseRIC.available()){
    char c = sseRIC.read(); // Read a character from the eRIC
    sseRIC.write(c); // Send character back to the eRIC so it will transmit it
    Serial.write(c); // Also echo it to the console
    }
  sseRIC.println();
  Serial.println();
  // Wait for the data to be transmitted
  // We should really be checking the CTS/BUSY signal here
  // but a simple delay won't cause the code to hang if the radio board isn't connected
  delay(1500);

  Serial.println("Confirm that eRIC serial number was received");
  Serial.println("Any other messages - or no messages - is a fail");
  waitForLF();

  // Put eRIC into Low Power Mode 0
  sseRIC.print("ER_CMD#A21"); // Set Low Power Mode 0
  delay(50);
  sseRIC.print("ACK"); // Acknowledge
  delay(50);
  while(sseRIC.available()){sseRIC.read();} // Clear the serial rx buffer
  
  digitalWrite(eRIC_WAKE, LOW); // Disable eRIC

  Serial.println("Putting eRIC into low power mode");
  Serial.println("Check that current draw falls to approx. 16mA");
  waitForLF();
  Serial.println();

  // Test LED2
  Serial.println("Check LED2 is illuminated");
  digitalWrite(ledPin, HIGH);
  waitForLF();
  
  Serial.println("Check LED2 is off");
  digitalWrite(ledPin, LOW);
  waitForLF();

  // Test NeoPixel (LED1)
  Serial.println("Check NeoPixel is red");
  LED_red();
  delay(100);
  LED_red();
  waitForLF();
  
  Serial.println("Check NeoPixel is green");
  LED_green();
  waitForLF();
  
  Serial.println("Check NeoPixel is blue");
  LED_blue();
  waitForLF();
  
  LED_off();

  // Test relay
  Serial.println("Check relay is reset (COM connected to NC)");
  reset_relay();
  waitForLF();
  
  Serial.println("Check relay is set (COM connected to NO)");
  set_relay();
  waitForLF();
  
  reset_relay();

  // Power up GNSS and MPL3225
  Serial.println("Powering up MAX-M8Q and MPL3225");
  Serial.println("Check current draw rises to approx. 40mA");
  Serial.println("(Current draw will be higher if an active antenna is attached)");
  digitalWrite(GPS_EN, GPS_ON); // Enable the GPS and MPL3115A2
  waitForLF();

  // Check MPL3225

  Serial.println("Reading pressure and temperature from MPL3225...");
  Serial.println();
  
  // Start the MPL3115A2 (does Wire.begin())
  if (baro.begin()) {
    // Read pressure twice to avoid first erroneous value
    float pascals = baro.getPressure();
    pascals = baro.getPressure();
    float tempC = baro.getTemperature();
    Serial.print("Pressure (Pascals): "); Serial.print(pascals,0);
    if ((pascals >= 90000.0) and (pascals <= 110000.0))
      Serial.println(" : PASS");
    else
      Serial.println(" : FAIL!");
    Serial.print("Temperature (C): "); Serial.print(tempC,1);
    if ((tempC >= 10.0) and (tempC <= 30.0))
      Serial.println(" : PASS");
    else
      Serial.println(" : FAIL!");
  }
  else {
    Serial.println("Error initialising MPL3115A2: FAIL!");
  }
  Serial.println();

  // Check GNSS
  // Start the GPS serial port
  ssGPS.begin(9600);

  delay(1000); // Allow time for the port to open

  // Configure GNSS
  Serial.println("Configuring MAX-M8Q...");

  // Disable all messages except GGA and RMC
  ssGPS.println("$PUBX,40,GLL,0,0,0,0*5C"); // Disable GLL
  delay(100);
  ssGPS.println("$PUBX,40,ZDA,0,0,0,0*44"); // Disable ZDA
  delay(100);
  ssGPS.println("$PUBX,40,VTG,0,0,0,0*5E"); // Disable VTG
  delay(100);
  ssGPS.println("$PUBX,40,GSV,0,0,0,0*59"); // Disable GSV
  delay(100);
  ssGPS.println("$PUBX,40,GSA,0,0,0,0*4E"); // Disable GSA
  delay(1100);
      
  // Flush GNSS serial buffer
  while(ssGPS.available()){ssGPS.read();} // Flush RX buffer

  Serial.println();

  for (tnow = millis(); millis() - tnow < 1UL * 5UL * 1000UL;) {
    while(ssGPS.available()){Serial.write(ssGPS.read());}
  }

  Serial.println();
  Serial.println();
  Serial.println("Confirm that GNSS is producing _only_ GNGGA and GNRMC messages");
  Serial.println("Any other messages - or no messages - is a fail");
  waitForLF();

  digitalWrite(GPS_EN, GPS_OFF); // Disable the GPS and MPL3115A2

  // Power up the LTC3225
  Serial.println("Powering up LTC3225");
  Serial.println("Check current draw peaks at approx. 300mA");
  digitalWrite(LTC3225shutdown, HIGH); // Enable the LTC3225 supercapacitor charger
  waitForLF();

  Serial.println("Waiting for up to 60 seconds for PGOOD to go high...");

  PGOOD = digitalRead(LTC3225PGOOD);
  for (tnow = millis(); !PGOOD && millis() - tnow < 1UL * 60UL * 1000UL;) {
    PGOOD = digitalRead(LTC3225PGOOD);
  }

  if (PGOOD) Serial.println("PGOOD has gone high : PASS");
  else Serial.println("PGOOD did not go high : FAIL!");

  Serial.println();
  Serial.println("(Now would be a good time to measure the super capacitor voltage)");
  Serial.println();

  // Enable and test 9603N
  Serial.println("Powering up the Iridium 9603N");
  Serial.println("(Could take up to 240 seconds)");
  Serial.println();
  digitalWrite(Enable_9603N, HIGH); // Enable the 9603N
  delay(2000); // Wit for 9603N to power up

  ssIridium.begin(19200);
  delay(1000);

  if (isbd.begin() == ISBD_SUCCESS) { // isbd.begin powers up the 9603
    Serial.println();
    Serial.println("Iridium 9603N begin was successful : PASS");
  }
  else {
    Serial.println();
    Serial.println("Iridium 9603N begin was unsuccessful : FAIL!");
  }
  Serial.println();
  
  isbd.sleep(); // Put 9603N to sleep
  delay(1000);

  // Put processor to sleep, confirm minimal current draw

  ssIridium.end(); // Close GPS and Iridium serial ports
  ssGPS.end();

  digitalWrite(LTC3225shutdown, LOW); // Disable the LTC3225 supercapacitor charger
  digitalWrite(Enable_9603N, LOW); // Disable the 9603N
  digitalWrite(GPS_EN, GPS_OFF); // Disable the GPS and MPL3115A2
  
  Serial.println();
  Serial.println("Last test: putting the processor into deep sleep");
  Serial.println("Confirm current draw falls to approx. 3mA");
  delay(1000); // Wait for serial port to clear
  Serial.end(); // Close the serial console
  USBDevice.detach(); // Safely detach the USB prior to sleeping

  // Deep sleep...
  SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
  __WFI();

  while (true) ; // Wait for reset
}


