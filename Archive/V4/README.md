# Iridium 9603N Beacon

A lightweight Iridium 9603N + GNSS Beacon (Tracker)

Suitable for high altitude ballooning, asset tracking and many other remote monitoring applications.

New hardware features for Version 4:
- Revised power options: solar; USB; or 3xAA battery
- u-blox MAX-M8Q GNSS with SMA antenna
- SMA antenna for the 9603N
- NeoPixel for status feedback
- Voltage reference so lower power voltages can be measured

New software features for Version 4:
- Beacon can be tracked from _anywhere_ with Iridium-Iridium messaging via the Rock7 RockBLOCK Gateway
- BEACON_INTERVAL is now stored in non-volatile (flash) memory
- BEACON_INTERVAL can be updated during a flight via a Mobile Terminated SBD message

![Iridium_9603_Beacon_V4](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_9603N_Beacon_V4_Top.JPG)

**See [LEARN.md](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Archive/V4/LEARN.md) for more details.**

**See [RockBLOCK.md](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md) for details on how to track your beacon from _anywhere_ using Rock7 RockBLOCK Gateway messaging.**

See [Iridium_9603_Beacon_V4.pdf](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Archive/V4/Iridium_9603_Beacon_V4.pdf) for the schematic, layout and Bill Of Materials.

The [Eagle](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Archive/V4/Eagle) directory contains the schematic and pcb design files.

The [Arduino](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Archive/V4/Arduino) directory contains the Arduino code.

The [Python](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Python) directory contains tracking/mapping software based on the Google Static Maps API.

![Mapper](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Mapper.JPG)

This project is distributed under a Creative Commons Attribution + Share-alike (BY-SA) licence.
Please refer to section 5 of the licence for the “Disclaimer of Warranties and Limitation of Liability”.

Enjoy!

**_Paul_**