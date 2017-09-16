# Iridium 9603N Beacon

A lightweight Iridium 9603N + GNSS Beacon (Tracker)

Suitable for High Altitude Ballooning and many other remote monitoring applications.

Version 3 now includes u-blox SAM-M8Q GNSS and the option of solar power.

![Iridium_9603_Beacon_V3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_9603_Beacon_V3.JPG)

## Background

Following on from the [original work I did on the Iridium_9603_Beacon](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Archive/V2/Iridium_9603_Beacon.pdf)
which got some nice coverage on [Hackaday](http://hackaday.com/2016/12/19/a-beacon-suitable-for-tracking-santas-sleigh/)
and which flew on UBSEDS22 and sent updates all the way from the UK to China before the batteries gave up:
![UBSEDS22_KML](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/UBSEDS22_KML.JPG)
- https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/UBSEDS22I_KML/iridium_linestring.kml
I decided to set myself the challenge of modifying the design of the beacon to make it solar-powered, making the lithium batteries optional and allowing the beacon to send updates during daylight hours for as long as the balloon continues to float.
The design I’ve ended up with is based largely on V2 of the Iridium 9603 beacon but is powered by a pair of PowerFilm Solar MPT3.6-150 solar panels:
- http://www.powerfilmsolar.com/products/?mpt36150&show=product&productID=271537&productCategoryIDs=6573
These amazing little panels weigh only 3.1g each but can deliver a really useful amount of power: 100mA at 3.6V at Air Mass 1.5. This is enough to power the beacon’s SAMD21G18 processor and the GNSS receiver or the LTC3225EDDB super capacitor charger which delivers power to the Iridium 9603N.
The current status is that the V3 has worked successfully under full sun at sea level in the UK (during July) but hasn't flown yet.

I’ve tried to keep the beacon ‘general purpose’ and so you could use it for many other remote monitoring applications, perhaps relaying environmental data from remote locations using sensors connected to the I2C or SPI pins.

## The Design

See [Iridium_9603_Beacon_V3.pdf](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Iridium_9603_Beacon_V3.pdf) for the schematic,
layout and Bill Of Materials.

The [Eagle](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Eagle) directory contains the schematic and pcb design files.

The key components of V3 of the Iridium 9603N Beacon are:
- Iridium 9603N Module
-- Available (in the UK) from e.g.:
--- http://www.ast-systems.co.uk/Product-Pages/Iridium-9603-SBD—Satellite-Tracking-Transceiver.aspx
--- http://www.rock7mobile.com/products-iridium-sbd
-- Other UK and International distributors can be found at:
--- https://iridium.com/products/details/Iridium-9603?section=wtb 
-- Make sure you purchase the 9603N and not the older 9603 (the 9603N will run from 5V ± 0.5V which is important as the super capacitor charger will be set to produce 5.3V; the older 9603 is only rated to 5V ± 0.2V)
- Taoglas IP.1621.25.4.A.021 Iridium Patch Antenna
-- Available from e.g. Mouser (Part# 960-IP1621254A02)
-- This is mounted on a small PCB above the 9603N:
--- https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Eagle/Iridium_9603_Antenna.brd
-- And connect it to the 9603N with a short Molex uFL cable (part number 73412-0508, available from Farnell / Element14 (1340201))
- Atmel ATSAMD21G18 Processor
-- As used on the Adafruit Feather M0:
--- https://www.adafruit.com/products/2772
-- Available from e.g. Farnell / Element14 (2460544)
- MPL3115A2 Altitude/Pressure sensor:
-- As used on the Sparkfun SEN-11084
--- https://www.sparkfun.com/products/11084
-- Available as a bare chip from e.g. Farnell / Element14 (2009084)
- Linear Technology LTC3225EDDB SuperCapacitor Charger
-- http://www.linear.com/product/LTC3225
-- Available as a bare chip from e.g. Farnell / Element14 (1715231)
-- Charges two e.g. Bussmann HV1030-2R7106-R 10F 2.7V capacitors (Farnell / Element14 2148486)
- u-blox SAM-M8Q GNSS
-- https://www.u-blox.com/en/product/sam-m8q-module
- Two PowerFilm Solar MPT3.6-150 solar panels
-- http://www.powerfilmsolar.com/products/?mpt36150&show=product&productID=271537&productCategoryIDs=6573
-- Available (in the UK) from e.g.:
--- http://www.selectsolar.co.uk/prod/264/powerfilm-mpt36150-100ma-36v-mini-solar-panel

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
The main one is Mikal Hart’s Iridium SBD library. It was written for the Rock7 RockBLOCK, which uses the Iridium 9602 module, but it works just fine on the 9603:
- http://arduiniana.org/libraries/iridiumsbd/
- https://github.com/mikalhart/IridiumSBD
You will also need:
- https://github.com/mikalhart/TinyGPS
- http://arduiniana.org/libraries/pstring/
- https://github.com/adafruit/Adafruit_MPL3115A2_Library
- https://github.com/arduino-libraries/RTCZero

### How do I install the ATSAMD21G18 bootloader?
Get yourself a Segger J-Link programmer and connect it according to [Atmel_SAMD21_Programming_Cable.pdf](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Atmel_SAMD21_Programming_Cable.pdf).

Ignore the RST connection.

Connect the 5V-Supply output from the J-Link to one of the SOLAR+ connections to power the board while you configure it (it doesn’t need batteries or solar power for this bit).

Follow Lady Ada’s excellent instructions:
- https://learn.adafruit.com/proper-step-debugging-atsamd21-arduino-zero-m0/restoring-bootloader

## Reset Supervisor
The SAMD21G18 has a built-in power-on reset and brown-out detector circuit, but the solar panel will ramp up its output voltage very slowly at sunrise so I would recommend including a separate reset supervisor. The Microchip MCP111-195 has an open drain output which can be used to reset the processor whenever the 3.3V supply falls below 1.95V.
The SAMD21G18 datasheet isn’t much help here. Section 8.2.4.1 specifies:
Minimum Rise Rate
The integrated power-on reset (POR) circuitry monitoring the VDDANA power supply requires a minimum rise rate.
But then the supply characteristics section (37.4) specifies a maximum supply rise rate of 0.1V/µs. The solar panel rise rate will be much slower than that. 

## Power Circuitry
We use the BAT connection as it includes an MBR120 diode which will protect the solar panel when the Adalogger is powered via USB:
 
## Super Capacitor Charger

### Why 60mA?
The datasheet for the 9603N quotes: an average idle current of 34mA; and an average receive current of 39mA. We need to charge the capacitors at a higher current than this, but keep the total current draw within what the solar panel can deliver.

### Why do you need the Super Capacitors?
The Iridium 9603 module draws an average current of 145mA and a peak current of 1.3A when transmitting its short data bursts. That’s too much for the solar panel to provide. The LTC3225 super capacitor charger draws 60mA from the panel to charge two 10F 2.7V capacitors, connected in series, to 5.3V. The capacitors then deliver the 1.3A to the module when it sends the data burst.

Can I leave the Adalogger USB connected during testing?
Yes. Leaving the USB connected is useful as you can monitor the Serial messages produced by the code in the Arduino IDE Serial Monitor. If you use a standard USB cable then the Adalogger will draw its power from USB. To test the prototype running on solar power, you will need to break the USB 5V power connection. You can do this with a home-made power-break cable. Take a short male to female USB extension cable; carefully strip the outer sheath from cable somewhere near the middle; prise apart the screen connection to reveal the four USB wires (red (5V); black (GND); green and white (data)); cut and insulate the ends of the red 5V wire leaving the black, green and white wires and the screen connection intact:

## Do you recommend coating the board once it is populated?
As a minimum, I’d recommend applying a coat of acrylic protective lacquer to the processor and surrounding components (especially the crystal). If you’re using an aerosol, be careful to mask off the connectors, switch and the pressure sensor first.

## What data will I get back from the beacon?

The Arduino code included in this repository will send the following (separated by commas):
- GPS Time and Date (year, month, day, hour, minute, second)
- GPS Latitude (degrees)
- GPS Longitude (degrees)
- GPS Altitude (m)
- GPS Speed (knots)
- GPS Heading (degrees)
- Atmospheric pressure (Pa)
- Temperature (C)
- Battery / solar voltage (V)

E.g.:
_20160820152446,55.866596,-2.428457,95,0.0,303,98472,21.8,4.25_

You will receive the data as an email attachment from the Iridium system. The email itself contains extra useful information:
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
_Subject:	SBD Msg From Unit: 30043406174****_
_Attachments:	30043406174****_000029.sbd_

_MOMSN: 29_
_MTMSN: 0_
_Time of Session (UTC): Sat Aug 20 15:24:57 2016 Session Status: 00 - Transfer OK Message Size (bytes): 61_

_Unit Location: Lat = 55.87465 Long = -2.37135 CEPradius = 4_

You can adapt the code to send whatever data you like, up to a maximum of 340 bytes. The message is sent as plain text, but you could encrypt it if required.

## Acknowledgements

I’m very grateful to Richard Meadows and his fellow students at UBSEDS (University of Bristol Students for the Exploration and Development of Space).
- http://www.bristol-seds.co.uk/
I’m also very grateful to the UKHAS (UK High Altitude Society) team who provide the habhub flight tracker:
- https://ukhas.org.uk/
- http://tracker.habhub.org/
This project wouldn’t have been possible without the open source designs and code kindly provided by:
- Adafruit:
-- The Adafruit SAMD Board library
-- The design for the Feather M0 Adalogger
--- For more details, check out the product page at
--- https://www.adafruit.com/product/2772 
--- Adafruit invests time and resources providing this open source design, please support Adafruit and open-source hardware by purchasing products from Adafruit!
--- Designed by Adafruit Industries.
--- Creative Commons Attribution, Share-Alike license
-- The MPL3115A2 library
-- Sercom examples
--- https://learn.adafruit.com/using-atsamd21-sercom-to-add-more-spi-i2c-serial-ports/creating-a-new-serial
- Mikal Hart:
-- the Iridium SBD library (distributed under the terms of the GNU LGPL license)
-- TinyGPS
-- PString
- Sparkfun:
-- The MPL3115A2 Breakout
--- https://www.sparkfun.com/products/11084
- Arduino:
-- The Arduino IDE
-- Arduino SAMD Board library
-- RTCZero library
- Cave Moa:
-- The SimpleSleepUSB example
--- https://github.com/cavemoa/Feather-M0-Adalogger/tree/master/SimpleSleepUSB
- MartinL:
-- sercom examples
--- https://forum.arduino.cc/index.php?topic=341054.msg2443086#msg2443086

## Licence

This project is distributed under a Creative Commons Share-alike 4.0 licence.
Please refer to section 5 of the licence for the “Disclaimer of Warranties and Limitation of Liability”.


Enjoy!

**_Paul_**