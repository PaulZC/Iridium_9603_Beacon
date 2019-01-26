# Iridium 9603N Beacon

A lightweight Iridium 9603N + GNSS Beacon (Tracker)

Suitable for high altitude ballooning, asset tracking and many other remote monitoring applications.

New hardware features for Version 5:
- Includes an OMRON G6SK relay to allow the beacon to control external equipment (e.g. a cut-down device)
- 9603N EXT_PWR is now switched via a P-MOSFET

New software features for Version 5:
- Relay can be configured during a flight via a Mobile Terminated SBD message
- Relay can be 'pulsed' on for 1-5 seconds or turned on/off indefinitely
- RockBLOCK Gateway message forwarding can be enabled/disabled via a Mobile Terminated SBD message
- Includes support for the optional [Iridium Beacon Radio Board](https://github.com/PaulZC/Iridium_Beacon_Radio_Board)

![Iridium_9603N_Beacon_V5](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_9603N_Beacon_V5.JPG)

![Beacon with Internet](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Beacon_with_Internet.JPG)

![Beacon without Internet](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Beacon_without_Internet.JPG)

**See [LEARN.md](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/LEARN.md) for more details.**

**See [ASSEMBLY.md](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/ASSEMBLY.md) for details on how to assemble the PCB.**

**See [RockBLOCK.md](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md) for details on how to track your beacon from _anywhere_ using Rock7 RockBLOCK Gateway messaging.**

See [Iridium_9603_Beacon_V5.pdf](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Iridium_9603_Beacon_V5.pdf) for the schematic, layout and Bill Of Materials.

See [Iridium_9603_Beacon_V5_BOM.xls](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Iridium_9603_Beacon_V5_BOM.xls) for the Bill Of Materials in Excel format.

The [Eagle](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Eagle) directory contains the schematic and pcb design files.

The [Gerber](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Gerber) directory contains the Gerber files for the PCB. These files have been checked and used to manufacture a batch of circuit boards.

The [Arduino](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino) directory contains the Arduino code.

The [OpenSCAD](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/OpenSCAD) directory contains the .stl and .scad files for the 3D-printed covers.

The [Python](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Python) directory contains tracking/mapping software based on the Google Static Maps API.

![Mapper](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Mapper.JPG)

See [Iridium Beacon Radio Board](https://github.com/PaulZC/Iridium_Beacon_Radio_Board) for details of the optional radio board.

Vector graphics by [Alice Clark](https://www.alicelclark.co.uk/about)

This project is distributed under a Creative Commons Attribution + Share-alike (BY-SA) licence.
Please refer to section 5 of the licence for the "Disclaimer of Warranties and Limitation of Liability".

Enjoy!

**_Paul_**