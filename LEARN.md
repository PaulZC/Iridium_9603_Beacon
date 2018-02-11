# Iridium 9603N Beacon

A lightweight Iridium 9603N + GNSS Beacon (Tracker)

Suitable for high altitude ballooning, asset tracking and many other remote monitoring applications.

Version 4 now includes:
- Revised power options: solar; USB; or 3xAA battery
- u-blox MAX-M8Q GNSS with SMA antenna
- SMA antenna for the 9603N
- NeoPixel for status feedback
- Voltage reference so lower power voltages can be measured

![Iridium_9603_Beacon_V4](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_9603N_Beacon_V4_Top.JPG)

## Background

In response to feedback received from balloon enthusiasts, version 4 of the Iridium 9603N Beacon provides:
robust SMA antenna connections so helical antennas can be fitted to both the u-blox MAX-M8Q GNSS and Iridium 9603N;
extended battery power from three AA Energiser® Ultimate Lithium batteries;
a tri-colour NeoPixel LED for better status feedback.

Version 4 is slightly heavier than version 3. So, if you are looking for a very lightweight (60g) solar tracker for your long-duration high alitude balloon
flight, you might be better off with [version 3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Archive/V3/README.md). If you want a more robust
tracker for shorter-duration, battery-powered flights where the tracker stands a better chance of continuing to transmit while on the ground,
then version 4 is probably for you.

## The Design

See [Iridium_9603_Beacon_V4.pdf](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Iridium_9603_Beacon_V4.pdf) for the schematic,
layout and Bill Of Materials.

The [Eagle](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Eagle) directory contains the schematic and pcb design files.

Here's how the completed PCB looks when configured for USB power (using 1F super capacitors):

![V4_Beacon_Top.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Top.JPG)
![V4_Beacon_Bottom.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Bottom.JPG)

And here's how it looks from underneath when configured for battery power:

![Iridium_9603_Beacon_V4_Bottom](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_9603N_Beacon_V4_Bottom.JPG)

The key components of V4 of the Iridium 9603N Beacon are:

### Iridium 9603N Module
![V4_Beacon_Assembly.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Assembly.JPG)

Available from:
- https://www.rock7.com/shop-product-detail?productId=50

Other UK and International distributors can be found at:
- https://iridium.com/products/details/Iridium-9603?section=wtb 

Make sure you purchase the 9603N and not the older 9603. The 9603N will run from 5V ± 0.5V which is important as the super capacitor charger is set to produce 5.3V; the older 9603 is only rated to 5V ± 0.2V.
If you do have the older 9603, you can change the super capacitor voltage to 4.8V by reconfiguring the split pads next to the super capacitors.

### SMA Iridium Antenna
![V4_Beacon_Iridium.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Iridium.JPG)

An Iridium SMA helical antenna (e.g. the Maxtena M1621HCT-SMA, available from Farnell / Element 14 (2281619)) can be connected to the 9603N with a short Molex uFL cable (part number 73412-0508, available from Farnell / Element14 (1340201))

### Atmel ATSAMD21G18 Processor
![V4_Beacon_SAMD.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_SAMD.JPG)

As used on the Adafruit Feather M0:
- https://www.adafruit.com/products/2772

Available from e.g. Farnell / Element14 (2460544)

### MPL3115A2 Altitude/Pressure sensor:
![V4_Beacon_Sensor.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Sensor.JPG)

As used on the Sparkfun SEN-11084
- https://www.sparkfun.com/products/11084

Available as a bare chip from e.g. Farnell / Element14 (2009084)

### Linear Technology LTC3225EDDB SuperCapacitor Charger
![V4_Beacon_SuperCap_Top.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_SuperCap.JPG)

- http://www.linear.com/product/LTC3225

Available as a bare chip from e.g. Farnell / Element14 (1715231)

### u-blox MAX-M8Q GNSS
![V4_Beacon_GNSS.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_GNSS.JPG)

- https://www.u-blox.com/en/product/max-m8-series

### MCP111T-240 Reset Supervisor
![V4_Beacon_ResetSupervisor.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_ResetSupervisor.JPG)

The SAMD21G18 has a built-in power-on reset and brown-out detector circuit, but it doesn't work properly if the supply voltage rises very slowly.
The SAMD21G18 datasheet isn’t much help here. Section 8.2.4.1 specifies:
- _Minimum Rise Rate_

   _The integrated power-on reset (POR) circuitry monitoring the VDDANA power supply requires a minimum rise rate._

But then the supply characteristics section (37.4) specifies a _maximum_ supply rise rate of 0.1V/µs, not a minimum.

Tests I've carried out show that the processor will reset correctly if the power supply ramps up at 0.3 V/s or more, but fails to reset correctly at 0.2 V/s or less.
As the solar panel voltage will ramp up very slowly at sunrise, I've included a separate reset supervisor.
The Microchip MCP111-240 has an open drain output which holds the processor in reset until the supply rises above 2.4V, ensuring a clean start.

### SPX3819-3.3 Voltage Regulator
![V4_Beacon_Regulator.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Regulator.JPG)

The SPX3819-3.3 Voltage Regulator regulates the output from the two solar panels, or the batteries, or the USB port, providing 3.3V for the processor, GNSS and pressure sensor.

The LTC3225EDDB SuperCapacitor Charger draws its power directly from the solar panels, batteries or USB without going through the regulator.

MBR120 diodes protect the solar panels, USB port and the batteries from each other.

### WS2812B "NeoPixel"
![V4_Beacon_NeoPixel.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_NeoPixel.JPG)

A tri-colour NeoPixel has been included on Version 4 to show the status of the beacon:
- Magenta at power up (loop_step == init) (~10 seconds)
- Blue when waiting for a GNSS fix (loop_step == start_GPS or read_GPS or read_pressure) (could take 5 mins)
- Cyan when waiting for supercapacitors to charge (loop_step == start_LTC3225 or wait_LTC3225) (could take 7 mins)
- White during Iridium transmit (loop_step == start_9603) (could take 5 mins)
- Green flash (2 seconds) indicates successful transmission
- Red flash (2 seconds) entering sleep
- LED will flash Red after: Iridium transmission (successful or failure); low battery detected; no GNSS data; supercapacitors failed to charge

### LT1634BCMS8-1.25 1.25V Voltage Reference
![V4_Beacon_Reference.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Reference.JPG)

The SAMD21G18 processor is powered from a low drop-out 3.3V regulator. The solar / USB / battery voltage is measured via an analog pin connected to the mid point
of two 100K resistors configured as a voltage divider. The voltage measured by the analog pin is relative to the regulator voltage. When the power voltage drops below approximately
3.7V, the regulator voltage starts to collapse. The analog voltage appears to never drop below approximately 3.4V even when the actual voltage is lower than this.

By adding a 1.25V voltage reference and connecting it to a second analog pin, its constant voltage will appear to increase as the regulator voltage starts to collapse.
This voltage increase can be used to correct the power voltage measurement.

## How much does the V4 beacon weigh?

Configured for battery operation, including three Energiser® Ultimate Lithium AA batteries and the Maxtena SMA antennas listed in the BOM, it weighs 110.4g.

![V4_Beacon_Weight.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Weight.JPG)

The weight breaks down as follows:
- Batteries: 45.3g
- Populated PCB with 1F supercapacitors and battery clips: 27.3g
- Iridium module with mounting hardware and uFL cable: 13.0g
- Iridium antenna: 12.5g
- GNSS antenna: 12.3g

Running from solar power, the total weight would be approximately 74g:
- Populated PCB with 10F supercapacitors: 25.0g
- Iridium module with mounting hardware and uFL cable: 13.0g
- Iridium antenna: 12.5g
- GNSS antenna: 12.3g
- Solar panels (2): 6.3g
- Support hardware for the solar panels: 5g

## Power Options 
V4 of the Iridium 9603N Beacon can draw power from: the solar panels; three AA batteries; or USB.
It is possible to connect all three or any two simultaneously, the beacon will simply draw power from whichever is providing the higher voltage.

If you are going to use solar power, use 10F super capacitors and a charge current of 60mA.

If you are going to run exclusively from batteries or USB, then 1F super capacitors will suffice with a charge current of 150mA.

The charge current can be changed by reconfiguring the split pads next to the super capacitors.

(The LTC3225 draws approximately _twice_ the chosen charge current. 300mA would be way too much for the PowerFilm solar panels.)

### Two PowerFilm Solar MPT3.6-150 solar panels
![Iridium_9603N_Beacon_Solar.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_9603N_Beacon_Solar.JPG)

![V4_Beacon_Solar.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_Solar.JPG)

- http://www.powerfilmsolar.com/products/?mpt36150&show=product&productID=271537&productCategoryIDs=6573

Available (in the UK) from e.g.:
- http://www.selectsolar.co.uk/prod/264/powerfilm-mpt36150-100ma-36v-mini-solar-panel

You will want to angle the solar panels at +/- 45 degrees with respect to the circuit board so that at least one panel will collect sunlight while the sun is low in the sky.
When the sun is overhead, both panels will collect sunlight.

### Why do you need the Super Capacitors?
The Iridium 9603 module draws an average current of 145mA and a peak current of 1.3A when transmitting its short data bursts. That’s too much for the solar panels to provide.
The LTC3225 super capacitor charger draws a lower current from the panels to slowly charge two 2.7V capacitors, connected in series, to 5.3V. The capacitors then deliver the 1.3A to the module when it sends the data burst.

### Why is the Super Capacitor Charger charge current set to 60mA / 150mA?
The datasheet for the 9603N quotes: an average idle current of 34mA; and an average receive current of 39mA.

For solar operation, we need to charge the capacitors at a higher current than 39mA, but keep the total current draw within what the solar panels can deliver.
(Remember that the LTC3225 draws approximately _twice_ the chosen charge current.)
The 10F capacitors provide the majority of the higher current draw during the transmit cycle.

For USB or battery operation, setting the super capacitor charge current to 150mA results in the capacitors only being needed to provide the 1.3A peak current when the 9603N is actually transmitting a data burst.
This means smaller (1F) capacitors are adequate.

### Can I leave the USB connected during testing?
Yes. Leaving the USB connected is useful as you can monitor the Serial messages produced by the code in the Arduino IDE Serial Monitor.
If you use a standard USB cable then the beacon will draw power from USB. To test the beacon running on solar power, you will need to break the USB 5V power connection.
You can do this with a home-made power-break cable.

Take a short male to female USB extension cable; carefully strip the outer sheath from cable somewhere near the middle;
prise apart the screen connection to reveal the four USB wires (red (5V); black (GND); green and white (data)); cut and insulate the ends of the red 5V wire leaving the black, green and white wires and the screen connection intact:

![USB_Power_Break.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/USB_Power_Break.JPG)

### Which AA batteries should I use?
Energiser® Ultimate Lithium batteries. These are rated down to -40°C but tests I’ve done (using dry ice) show that they continue to work much colder than that.
Please see the [V2 documentation](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Archive/V2/Iridium_9603_Beacon.pdf) for further details.

## IO Pins
![V4_Beacon_IO.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V4_Beacon_IO.JPG)

**SWCLK** and **SWDIO** are used during [programming of the SAMD bootloader](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/LEARN.md#how-do-i-install-the-atsamd21g18-bootloader)

**3V3SW** is the 3.3V power rail switched by Q1 and which provides power for the MAX-M8Q GNSS and MPL3115A2 altitude sensor.
You can use this pin to provide power for a peripheral which you want to be able to disable to save power.

**SDA** and **SCL** are the I2C bus data and clock signals.
You can use these to connect another I2C sensor but be aware that it will share the bus with the MPL3115A2.

**3V3** is the 3.3V power rail from the SPX3819-3.3 voltage regulator.
Any peripherals connected to this will be continuously powered when power is available from the solar panels, batteries or USB.

**MISO**, **SCK**, **MOSI** and **SD_CS** are the SPI bus data, clock and enable connections.
You could use these to connect SD storage or another SPI peripheral.

## Do you recommend coating the board once it is populated?
As a minimum, I’d recommend applying a coat of acrylic protective lacquer to the processor and surrounding components (especially the crystal).
If you’re using an aerosol, be careful to mask off the connectors, switch and the pressure sensor first.

## Arduino Code
The [Arduino](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino) directory contains the Arduino code.

The code is based extensively on Mikal Hart’s IridiumSBD Beacon example:
- https://github.com/mikalhart/IridiumSBD/tree/master/examples/Beacon

The main loop is structured around a large switch / case statement which:
- Initialises the serial ports; checks the solar panel voltage
- Powers up the GPS and MPL3115A2; checks the solar panel voltage
- Waits until the GPS establishes a fix; checks the solar panel voltage
- Reads the temperature and pressure from the MPL3115A2
- Powers down the GPS and powers up the LTC3225EDDB supercapacitor charger; checks the solar panel voltage
- Waits for the supercapacitors to charge; checks the solar panel voltage
- Queues the Iridium message transmission; checks the solar panel voltage
- Powers everything down and puts the processor to sleep until the next alarm interrupt

If the solar panel voltage falls below a useful level at any time, the code jumps to the sleep case and waits for the next alarm interrupt.

### How do I upload the Arduino code?
The 9603 Beacon is based on the Adafruit Feather M0 (Adalogger):
- https://www.adafruit.com/products/2796
- https://www.adafruit.com/products/2772

You can follow Lady Ada’s excellent instructions:
- https://cdn-learn.adafruit.com/downloads/pdf/adafruit-feather-m0-adalogger.pdf

### What other libraries do I need?
The main one is Mikal Hart’s Iridium SBD library (V2.0) written for the Rock7 RockBLOCK:
- http://arduiniana.org/libraries/iridiumsbd/
- https://github.com/mikalhart/IridiumSBD

You will also need:
- https://github.com/mikalhart/TinyGPS
- http://arduiniana.org/libraries/pstring/
- https://github.com/adafruit/Adafruit_MPL3115A2_Library
- https://github.com/arduino-libraries/RTCZero
- https://github.com/adafruit/Adafruit_NeoPixel

### How do I install the ATSAMD21G18 bootloader?
Get yourself a Segger J-Link programmer and connect it according to [Atmel_SAMD21_Programming_Cable.pdf](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Atmel_SAMD21_Programming_Cable.pdf).

Ignore the RST connection.

Connect the 5V-Supply output from the J-Link to VBUS to power the board while you configure it (it doesn’t need external power for this bit).

Follow Lady Ada’s excellent instructions:
- https://learn.adafruit.com/proper-step-debugging-atsamd21-arduino-zero-m0/restoring-bootloader

## What data will I get back from the beacon?

The Arduino code included in this repository will send the following (separated by commas):
- GPS Time and Date (year, month, day, hour, minute, second)
- GPS Latitude (degrees)
- GPS Longitude (degrees)
- GPS Altitude (m)
- GPS Speed (m/s)
- GPS Heading (degrees)
- GPS HDOP (m)
- GPS Satellites
- Atmospheric pressure (Pa)
- Temperature (C)
- Battery / solar voltage (V)
- Iteration count

E.g.:

   _20170729144631,55.866573,-2.428458,103,0.1,0,3.0,5,99098,25.3,4.98,0_

You can opt to receive the data as an email attachment from the Iridium system. The email itself contains extra useful information:
- Message sequence numbers (so you can identify if any messages have been missed)
- The time and date the message session was processed by the Iridium system
- The status of the message session (was it successful or was the data corrupt)
- The size of the message in bytes
- The approximate latitude and longitude the message was sent from
- The approximate error radius of the transmitter’s location

E.g.:

   _From:	sbdservice@sbd.iridium.com_  
   _Sent:	20 August 2016 16:25_  
   _To:_  
   _Subject:	SBD Msg From Unit: 30043406174_  
   _Attachments:	30043406174-000029.sbd_  
  
   _MOMSN: 29_  
   _MTMSN: 0_  
   _Time of Session (UTC): Sat Aug 20 15:24:57 2016 Session Status: 00 - Transfer OK Message Size (bytes): 61_  
  
   _Unit Location: Lat = 55.87465 Long = -2.37135 CEPradius = 4_

You can adapt the code to send whatever data you like, up to a maximum of 340 bytes. The message is sent as plain text, but you could encrypt it if required.

You can opt to receive the data via HTTP instead of email. Your service provider will provide further details.

## Acknowledgements

I’m very grateful to Richard Meadows and his fellow students at UBSEDS (University of Bristol Students for the Exploration and Development of Space) who flew the V1 beacon on [UBSEDS22](http://www.bristol-seds.co.uk/hab/flight/2017/03/13/ubseds22.html).
- http://www.bristol-seds.co.uk/

I’m also very grateful to the UKHAS (UK High Altitude Society) team who provide the habhub flight tracker:
- https://ukhas.org.uk/
- http://tracker.habhub.org/

This project wouldn’t have been possible without the open source designs and code kindly provided by:
- Adafruit:

   The Adafruit SAMD Board library  
   The design for the Feather M0 Adalogger  
   For more details, check out the product page at:
   - https://www.adafruit.com/product/2772  

   Adafruit invests time and resources providing this open source design, please support Adafruit and open-source hardware by purchasing products from Adafruit!  
   Designed by Adafruit Industries.  
   Creative Commons Attribution, Share-Alike license

   The MPL3115A2 library
   The NeoPixel library

   Sercom examples:
   - https://learn.adafruit.com/using-atsamd21-sercom-to-add-more-spi-i2c-serial-ports/creating-a-new-serial

- Mikal Hart:

   The Iridium SBD library (distributed under the terms of the GNU LGPL license)  
   TinyGPS  
   PString

- Sparkfun:

   The MPL3115A2 Breakout:
   - https://www.sparkfun.com/products/11084

- Arduino:

   The Arduino IDE  
   Arduino SAMD Board library  
   RTCZero library

- Cave Moa:

   The SimpleSleepUSB example:
   - https://github.com/cavemoa/Feather-M0-Adalogger/tree/master/SimpleSleepUSB

- MartinL:

   Sercom examples:
   - https://forum.arduino.cc/index.php?topic=341054.msg2443086#msg2443086

## Licence

This project is distributed under a Creative Commons Share-alike 4.0 licence.
Please refer to section 5 of the licence for the “Disclaimer of Warranties and Limitation of Liability”.
  

Enjoy!

**_Paul_**