# Tracking Your Beacon via the RockBLOCK Gateway

The Iridium 9603N Beacon can be used to track high altitude balloons and other mobile assets. To the best of my knowledge, it hasn't yet been used
to track an elephant. But who knows! Time will tell...

I have used Iridium 9603N modules provided by other suppliers, but I recommend [Rock7](https://www.rock7.com/shop-product-detail?productId=50) since:
- They provide excellent customer support and rapid answers to technical queries
- Their web portal is really easy to use
- You can top up message credits and the monthly line rental for your modules by credit card (you don't need to set up a monthly 'standing order' payment)
- They won't charge you line rental for months where you don't make use of your 9603N module
- They provide message forwarding via their RockBLOCK Gateway which you can use to track your beacon(s) from _anywhere_ using another beacon as a 'base'

![RockBLOCK_Operations_1](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_1.JPG)

Rock7 also provide the excellent [RockBLOCK](http://www.rock7mobile.com/products-rockblock-9603),
[RockSTAR](http://www.rock7mobile.com/products-rockstar), [RockFLEET](http://www.rock7mobile.com/products-rockfleet)
and are responsible for [YB (Yellow Brick)](https://www.ybtracking.com/products-yb3).

The beacon will send Short Burst Data messages containing its location, speed, heading, altitude, pressure and other data every five minutes by default.
Each message is automatically forwarded to whatever email address(es) you add to RockBLOCK Operations. You can simply read the email message contents and copy
and paste the position (latitude and longitude) into (e.g.) Google Maps to show where your beacon is located:

![RockBLOCK_Message](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Message.JPG)

![RockBLOCK_Operations_3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_3.JPG)

If you have an internet connection and you want to use these emails to display the location and route of your beacon(s) on a map, you can do this using the
Iridium_Beacon_GMail_Downloader_RockBLOCK.py and Iridium_Beacon_Mapper_RockBLOCK.py mapping software
[described below](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md#tracking-your-beacon-with-an-internet-connection).

![Beacon with Internet](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Beacon_with_Internet.JPG)

If you want to be able to track your beacon(s) from somewhere _without_ an internet connection, you can use another beacon as a base, use the RockBLOCK Gateway
to automatically forward messages from your mobile beacon(s) to the base, and then display the location and route of your beacon(s) on a map using the
Iridium_Beacon_Base.py mapping software
[described below](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md#tracking-your-beacon-without-an-internet-connection). Map tiles for your
destination can be downloaded before your travel.

![Beacon without Internet](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Beacon_without_Internet.JPG)

Vector graphics by [Alice Clark](https://www.alicelclark.co.uk/about)

Message delivery via an HTTP post is possible too but, as I find email easier to work with, I won't discuss HTTP options further here.

## Configuring your Beacon via RockBLOCK Operations

The beacon uses flash memory inside the ATSAMD21G18 processor to store several settings. As flash memory is non-volatile, the settings are not forgotten if
the beacon loses power or is reset. The settings are:
- INTERVAL: the (minimum) interval between message transmissions. By default, this is set to 5 minutes
- RBDESTINATION: the serial number of the destination RockBLOCK for messages forwarded via the RockBLOCK Gateway. By default, this is set to zero which disables message forwarding
- RBSOURCE: the RockBLOCK serial number of the 9603N module on the beacon. By default, this is set to 1234 as it is not required unless you want to use message forwarding to an Iridium Becon Base

If you want to change the beacon transmission interval during a flight, you can do this through RockBLOCK Operations using the _Send a Message_
function. Select the RockBLOCK serial numbers of the beacon(s) you want to update and send a plain text message using the format _[INTERVAL=nnn]_ where _nnn_
is the new message interval in _minutes_. The interval will be updated the next time the beacon wakes up for a transmit cycle.

![RockBLOCK_Operations_4](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_4.JPG)

If you want to enable message forwarding via the RockBLOCK Gateway, you can do this by including the text _[RBDESTINATION=nnnnn]_ in the RockBLOCK message where _nnnnn_
is the serial number of the destination 'base' RockBLOCK. You can disable message forwarding again by sending a message containing _[RBDESTINATION=0]_. You can change the source
serial number which is included in the messages by including the text _[RBSOURCE=nnnnn]_ in the RockBLOCK message where _nnnnn_ is the serial number of the
RockBLOCK 9603N on the beacon.

The _Send a Message_ function can also be used to control the beacon. The commands are:
- RELAY: this controls the OMRON relay on the beacon. The relay can be switched ON or OFF, or pulsed on for 1-5 seconds
- RADIO: this allows you to send a radio message from the beacon using the optional [Iridium Beacon Radio Board](https://github.com/PaulZC/Iridium_Beacon_Radio_Board)

If you want to change the state of the OMRON relay during a flight, you can do this by including the text _[RELAY=ON]_ or _[RELAY=OFF]_ in the RockBLOCK message.
The state of the relay will be updated after the next transmit cycle. If you want to pulse the relay on for 1-5 seconds, to trigger e.g. a cut-down device,
include the text _[RELAY=1]_ to pulse the relay on for 1 second then off again. _[RELAY=5]_ will pulse the relay on for five seconds then off again.
Only integer pulse durations of 1-5 seconds are valid, other values will be ignored.

If you want to send a message via the radio board, you can do this by including the text _[RADIO=nnnnnnnn]_ in the RockBLOCK message where _nnnnnnnn_ is the
message you want the eRIC radio module to transmit (e.g. the serial number of a radio-enabled cut-down device, causing it to activate). The radio board is
optional, the beacon code will work as normal without it.

The beacon can also be configured and controlled via [messages from an Iridium Beacon Base](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md#configuring-your-beacon-via-iridium-beacon-base). 

## Tracking your beacon with an internet connection

![Beacon with Internet](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Beacon_with_Internet.JPG)

![Mapper](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Mapper.JPG)

If you will be tracking your Iridium Beacon from somewhere with a good internet connection, then you can use:

[Iridium_Beacon_GMail_Downloader_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_GMail_Downloader_RockBLOCK.py)
to check for new SBD messages and download them from a Google GMail account using the Google Mail API.

Create yourself a GMail address, follow [these instructions](https://developers.google.com/gmail/api/quickstart/python) to create your credentials and enable access for Python,
add the email address to [RockBLOCK Operations](https://rockblock.rock7.com/Operations), then when you run the code it will automatically check for the arrival of any new messages
and, when it finds one, will download the SBD .bin attachment to to your computer, mark the message as seen (read) and 'move' it to a folder called SBD by changing the message labels.
You will need to manually create the SBD folder in GMail before running the code.

![RockBLOCK_Operations_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_2.JPG)

[Iridium_Beacon_Mapper_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_Mapper_RockBLOCK.py) uses the
Google Static Maps API to display the locations and paths of up to eight beacons. It will check once per minute for the appearance of new .bin
files, parse them and display the data in a Python Tkinter GUI.

You will need to download the [blank map image](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/map_image_blank.png) too. This is displayed until a .bin file is processed
or whenever the GUI isn't able to download map images from the API.

You can find more details about the Google Static Maps API [here](https://developers.google.com/maps/documentation/static-maps/intro). To use the API, you will need to create
your own API Key, which you can do by following the instructions [here](https://developers.google.com/maps/documentation/static-maps/get-api-key). Copy the Key and save it in a file
called _Google_Static_Maps_API_Key.txt_ so the mapper can read it. You will need to register payment details with Google before they will issue you with a Key,
but the Standard Plan allows you to download 25,000 map images per day for free before you start being charged.

The intention is that you have Iridium_Beacon_Mapper_RockBLOCK.py and Iridium_Beacon_GMail_Downloader_RockBLOCK.py running simultaneously.
Start Iridium_Beacon_Mapper_RockBLOCK.py first and allow it to build up a dictionary of any existing .bin files, then start Iridium_Beacon_GMail_Downloader_RockBLOCK.py.
When any new SBD messages arrive in your GMail inbox, the attachments will be downloaded and then added to the map automatically.

The displayed map is automatically centered on the position of a new beacon. The center position can be changed by left-clicking in the image.
A right-click will copy that location (lat,lon) to the clipboard. The zoom level defaults to '15' but can be changed using the zoom buttons.

A pull-down menu lists the latest locations of all beacons being tracked. Click on the entry for a beacon to center the map on its location and copy its location to the clipboard.

The beacon's path is displayed as a coloured line on the map. The oldest waypoints may not be shown as the map URL is limited to 8192 characters.

The GUI uses 640x480 pixel map images. Higher resolution images are available if you have a premium plan with Google.

The GUI has been tested with Python 2.7 on 64-bit Windows and on Linux on Raspberry Pi. You will need to install the Python libraries listed below.

## Tracking your beacon _without_ an internet connection

![Beacon without Internet](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Beacon_without_Internet.JPG)

![Iridium_Beacon_Base_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_2.JPG)

Another reason I really like Rock7 is that if you prefix your SBD message with the serial number of another 'RockBLOCK', they will automatically forward
your message to that module. This means the messages from your mobile Iridium Beacon can be automatically forwarded to another Iridium Beacon acting as a 'base'
allowing you to track the beacon from _anywhere_. See the last two pages of the
[RockBLOCK-9603-Developers-Guide](http://www.rock7mobile.com/downloads/RockBLOCK-9603-Developers-Guide.pdf) for further information.

In the [Arduino](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino) directory, you will find Arduino code for both the mobile
[Iridium9603NBeacon_V5](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino/Iridium9603NBeacon_V5) and the base
[Iridium9603NBeacon_V5_Base](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino/Iridium9603NBeacon_V5_Base).

Connect the Iridium Beacon Base directly to your computer using a USB cable (as if you were going to configure it using the Arduino IDE). The Beacon Base does not need batteries,
it will draw all of its power from the USB port. The Base Python software has been tested on both a Windows laptop and Raspberry Pi.

To enable message forwarding from beacon to base, you can:
- [Send a message to the beacon from RockBLOCK Operations](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md#configuring-your-beacon-via-rockblock-operations)
- [Send a message to the beacon from an Iridium Beacon Base](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md#configuring-your-beacon-via-iridium-beacon-base)
- Edit the Arduino code before you download it onto the beacon

To enable message forwarding in the Arduino code: edit Iridium9603NBeacon_V5.ino, and change the line which says **#define RB_destination 0** . Change the zero to the the serial
number of the destination RockBLOCK which is acting as the base. Also change the line which says **#define RB_source 1234** . Replace the 1234 with the serial
number of the RockBLOCK 9603N you are sending the messages from.

_You will be charged twice for each message: once to send it from the Beacon (Mobile Originated); and a second time to receive it on the base (Mobile Terminated)._

Before you travel, download a set of Google Static Map tiles using
[Google_Static_Maps_Tiler.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Google_Static_Maps_Tiler.py). 1 degree tiles are useful for
large areas, 0.1 degree or 0.01 degree for smaller areas. Put all the _StaticMapTile----.png_ files in the same directory as Iridium_Beacon_Base.py. By default, the
Tiler will ask Google for _roadmap_ map_type images. You can change this to _satellite_, _terrain_ or _hybrid_ by editing the Python code before you run it.

[Iridium_Beacon_Base.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_Base.py) is very similar in its operation to
Iridium_Beacon_Mapper_RockBLOCK.py except that the beacon data is received via Iridium rather than by email. The software talks to
Iridium9603NBeacon_V5_Base via Serial (over USB) and displays the beacon and base locations using the
[Google Static Maps API](https://developers.google.com/maps/documentation/static-maps/intro).

To use the Google Maps API, you will need to create your own API Key, which you can do by following the instructions [here](https://developers.google.com/maps/documentation/static-maps/get-api-key).
Copy the Key and save it in a file called _Google_Static_Maps_API_Key.txt_ so the mapper can read it. You will need to register payment details with Google before they will issue you with a Key,
but the Standard Plan allows you to download 25,000 map images per day for free before you start being charged.

Before running the Iridium_Beacon_Base.py code, plug the Iridium Beacon Base into your computer and find out its serial port number:
- Under Windows, you can run Device Manager from the Control Panel or using the search tool (magnifying glass). Open the entry for _Ports (COM & LPT)_. The base will be listed as a COM port
- Under Linux (e.g. on Raspberry Pi), you can find the port number by typing _ls /dev_ in a terminal window. The base will usually appear as _/ttyACM0_

Every 'update' seconds the GUI talks to the base beacon and:
- requests its GNSS data including time, position and altitude;
- starts an IridiumSBD session and downloads a packet from the mobile terminated queue (if any are present).

The GUI and base provide access to the RockBLOCK FLUSH_MT function, so an excess of unread Mobile Terminated messages from your beacon(s) can be discarded if required
(note that you are still charged from these messages!).

The software logs all received packets to CSV log files. Each beacon gets its own log file.

The software makes extensive use of the Google Static Map API:
- The displayed map is automatically centered on a new beacon position.
- The center position can be changed by left-clicking in the image.
- A right-click will copy the click location (lat,lon) to the clipboard.
- The zoom level is set automatically when a new beacon is displayed to show both beacon and base.
- The zoom can be changed using the buttons.

When you are online, the path of each beacon is displayed as a coloured line on the map. The oldest waypoints may be deleted as the map URL is limited to 8192 characters.

A pull-down menu lists the locations of all the beacons being tracked. Clicking on a menu entry will center the map on that location and will copy
the location to the clipboard.

A second pull-down menu shows the location of the base. Clicking it will center the map on that location and will copy that location to the clipboard.

A third pull-down menu lets you send a configuration update message to a beacon. See
[Configuring your Beacon via Iridium Beacon Base](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/RockBLOCK.md#configuring-your-beacon-via-iridium-beacon-base)
for further details.

A fourth pull-down menu lets you set the update interval of the base software. You are charged each time you check for new messages, so make sure you set
update to a sensible value. If your beacon is transmitting messages every 10 minutes, then set the update interval to 10 minutes too. If there is a backlog
of messages you want to download, then reduce update accordingly. But remember to set it back to 10 minutes afterwards to avoid being charged unnecessarily.
If you are tracking two beacons each sending messages every 10 minutes, then set update to 5 minutes.

The GUI uses 640x480 pixel map images. Higher resolution images are available if you have a premium plan with Google.

When you are online, the user interface will look like this:

![Iridium_Beacon_Base_1](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_1.JPG)

When you are offline, the software will use the map tiles from the Tiler. Base and beacon locations will be shown on the offline maps but not path information

![Iridium_Beacon_Base_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_2.JPG)

## Configuring your Beacon via Iridium Beacon Base

[Iridium_Beacon_Base.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_Base.py) has a pull-down menu which allows you to send
a message to one of your beacons so you can control or configure it.

![Iridium_Beacon_Base_3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_3.JPG)

By default, RBDESTINATION is set to zero in the Iridium Beacon code which disables message forwarding. To enable message forwarding, we need to change the RBDESTINATION
to the RockBLOCK serial number of the Iridium Beacon Base. Messages from the beacon will then be sent by email as usual, but also automatically forwarded via a second
Iridium message to the base so the base can track the beacon. _You are charged for both messages._

If the base software is not currently tracking any beacons, the Beacon Messaging pull-down menu will only contain a dummy entry for _RB0000000_. Click on that entry
and a dialogue box will appear containing the text _RB0000000[INTERVAL=5]_. Delete all of the text and replace it with:
- _RBxxxxx[RBDESTINATION=yyyyy][RBSOURCE=xxxxx]_

where
- _xxxxx_ is the RockBLOCK serial number of the 9603N _on the beacon_
- _yyyyy_ is the RockBLOCK serial number of the 9603N _on the base_

and then click OK.

Make sure you include the square brackets. Any commands not enclosed in square brackets are ignored.

The message will be sent from the 9603N on the base, through the Iridium network to the RockBLOCK Gateway. The RockBLOCK Gateway will then automatically forward
the message back through the Iridium network to beacon _xxxxx_. Beacon _xxxxx_ will receive the new RBDESTINATION and RBSOURCE the next time it wakes up and transmits a fix.

Now, each time beacon _xxxxx_ sends a message, it will be automatically prefixed with the serial number of the base (_RByyyyy_) and forwarded to the base through
the RockBLOCK Gateway.

Once the base software has received a message from beacon _xxxxx_, its serial number will appear in the Beacon Messaging pull-down menu to make it easier to send
more messages to that beacon.

If you want to disable message forwarding, send a message to beacon _xxxxx_ containing the text:
- _RBxxxxx[RBDESTINATION=0]_

If you want to change the message interval of a beacon, send it a message containing:
- _RBxxxxx[INTERVAL=nnn]_

where
- _nnn_ is the new message interval in _minutes_

Valid values are 1 to 1440 (once per minute to once per day). The beacon will download and process the message during its next transmit cycle. The new interval will take effect after the _following_ transmission.

If you want to change the status of the OMRON relay on board the beacon, add the text _[RELAY=ON]_ or _[RELAY=OFF]_ to the message. If you want to pulse the
relay on for 1-5 seconds, to trigger e.g. a cut-down device, add the text _[RELAY=1]_ to pulse the relay on for 1 second then off again. _[RELAY=5]_ will pulse
the relay on for 5 seconds then off again. Only integer pulse durations of 1-5 seconds are valid, other values will be ignored. 
The relay status will be updated at the end of the beacon's transmit cycle.

If you want the (optional) radio board to transmit a message, add the text _[RADIO=nnnnnnnn]_ to the message, where _nnnnnnnn_ is the message you want the radio
board to transmit. Usually _nnnnnnnn_ is the serial number of the eRIC radio module on a cut-down device.

## Extras

[Iridium_Beacon_Stitcher_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_Stitcher_RockBLOCK.py) will stitch the .bin SBD attachments downloaded by
[Iridium_Beacon_GMail_Downloader_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_GMail_Downloader_RockBLOCK.py) together into a single .csv
(Comma Separated Value) file which can be opened by (e.g.) Microsoft Excel.

[Iridium_Beacon_CSV_DateTime.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_CSV_DateTime.py) will convert the first column of the stitched .csv file
from YYYYMMDDHHMMSS format into DD/MM/YY,HH:MM:SS format, making the message timing easier to interpret using Excel.

[Iridium_Beacon_DateTime_CSV_to_KML_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_DateTime_CSV_to_KML_RockBLOCK.py) will convert the .csv file produced by
[Iridium_Beacon_CSV_DateTime.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_CSV_DateTime.py) into .kml files which can be opened in Google Earth.
The path of the beacon can be shown as: 2D (course over ground) or 3D (course and altitude) linestring; points (labelled with message sequence numbers); and arrows (indicating the heading of the beacon).

[Iridium_Beacon_BIN_to_KML_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_BIN_to_KML_RockBLOCK.py) will convert the individual .bin SBD attachments downloaded by
[Iridium_Beacon_GMail_Downloader_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_GMail_Downloader_RockBLOCK.py) into .kml files which can be opened in Google Earth.
The path of the beacon can be shown as: 2D (course over ground) or 3D (course and altitude) linestring; points (labelled with message sequence numbers); and arrows (indicating the heading of the beacon).

## Required Python 2.7 Libraries

To get the tools to run successfully you will need to install the following libraries:

### GMail API and oauth2client

- pip install --upgrade google-api-python-client oauth2client

### PIL ImageTk

- sudo apt-get install python-pil.imagetk

### Matplotlib

- sudo apt-get install python-matplotlib

### Kyle Lancaster's simplekml

- http://simplekml.readthedocs.io/en/latest/index.html
- https://pypi.python.org/pypi/simplekml
- pip install simplekml

###

Enjoy!

**_Paul_**


