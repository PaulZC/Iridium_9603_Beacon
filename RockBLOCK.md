# Tracking Your Beacon via the RockBLOCK Gateway

The Iridium 9603N Beacon can be used to track high altitude balloons and other mobile assets. To the best of my knowledge, it hasn't yet been used
to track an elephant. But who knows! Time will tell...

The beacon will send periodic Short Burst Data messages containing its location, speed, heading, altitude, pressure and other data. These messages
are delivered via the Iridium satellite network to the email address you provided to your service provider. Delivery via an HTTP post is possible too but,
as I find email easier to work with, I won't discuss HTTP options further here.

I have used Iridium 9603N modules provided by other suppliers, but I recommend [Rock7](https://www.rock7.com/shop-product-detail?productId=50) since:
- They provide excellent customer support and rapid answers to technical queries
- Their web portal is really easy to use
- You can top up message credits and the monthly line rental for your modules by credit card (you don't need to set up a monthly 'standing order' payment)
- They won't charge you line rental for months where you don't make use of your 9603N module

![RockBLOCK_Operations_1](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_1.JPG)

Rock7 also provide the excellent [RockBLOCK](http://www.rock7mobile.com/products-rockblock-9603),
[RockSTAR](http://www.rock7mobile.com/products-rockstar), [RockFLEET](http://www.rock7mobile.com/products-rockfleet)
and are responsible for [YB (Yellow Brick)](https://www.ybtracking.com/products-yb3).

Each time the beacon sends a message, the contents of the message will be forwarded to whatever email address(es) you add to RockBLOCK Operations.
You can simply read the email message contents and copy and paste the position (latitude and longitude) into (e.g.) Google Maps to show where your
beacon is located:

![RockBLOCK_Message](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Message.JPG)

![RockBLOCK_Operations_3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_3.JPG)

If you want to change the beacon transmission interval (BEACON_INTERVAL) during a flight, you can do this through RockBLOCK Operations using the _Send a Message_
function. Select the RockBLOCK serial numbers of the beacon(s) you want to update and send a plain text message using the format _[INTERVAL=nnn]_ where _nnn_
is the message interval in _minutes_. The interval will be updated the next time the beacon wakes up for a transmit cycle. The interval is stored in
non-volatile (flash) memory and so will be retained even if the Beacon is reset.

![RockBLOCK_Operations_4](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/RockBLOCK_Operations_4.JPG)

If you want to change the state of the OMRON relay during a flight, you can do this by including the text _[RELAY=ON]_ or _[RELAY=OFF]_ in the RockBLOCK message.
The state of the relay will be updated after the next transmit cycle. A future version of the code will make use of the 9603N Ring Indicator signal to
let the beacon know when a new message is waiting to be downloaded without first needing to go through a full transmit cycle. The code will also be updated to
allow the relay to be 'pulsed' on (set) then off (reset) which could then be used to trigger e.g. a cut-down device connected to the relay pins.

## Tracking your beacon with an internet connection

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
called _Google_Static_Maps_API_Key.txt_ so the mapper can read it.

The intention is that you have Iridium_Beacon_Mapper_RockBLOCK.py and Iridium_Beacon_GMail_Downloader_RockBLOCK.py running simultaneously.
Start Iridium_Beacon_Mapper_RockBLOCK.py first and allow it to build up a dictionary of any existing .bin files, then start Iridium_Beacon_GMail_Downloader_RockBLOCK.py.
When any new SBD messages arrive in your GMail inbox, the attachments will be downloaded and then added to the map automatically.

The displayed map is automatically centered on the position of a new beacon. The center position can be changed by left-clicking in the image.
A right-click will copy that location (lat,lon) to the clipboard. The zoom level defaults to '15' but can be changed using the zoom buttons.

A pull-down menu lists the latest locations of all beacons being tracked. Click on the entry for a beacon to center the map on its location and copy its location to the clipboard.

The beacon's path is displayed as a coloured line on the map. The oldest waypoints may not be shown as the map URL is limited to 8192 characters.

The GUI uses 640x480 pixel map images. Higher resolution images are available if you have a premium plan with Google.

The GUI has been tested with Python 2.7 on 64-bit Windows and on Linux on Raspberry Pi. You will need to install the Python libraries listed below.

## Tracking your beacon **without** an internet connection

![Iridium_Beacon_Base_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_2.JPG)

Another reason I really like Rock7 is that if you prefix your SBD message with the serial number of another 'RockBLOCK', they will automatically forward
your message to that module. This means the messages from your mobile Iridium Beacon can be automatically forwarded to another Iridium Beacon acting as a 'base'.
See the last two pages of the [RockBLOCK-9603-Developers-Guide](http://www.rock7mobile.com/downloads/RockBLOCK-9603-Developers-Guide.pdf) for further information.

In the [Arduino](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino) directory, you will find Arduino code for both the mobile
[Iridium9603NBeacon_V4](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino/Iridium9603NBeacon_V4) and the base
[Iridium9603NBeacon_V4_Base](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino/Iridium9603NBeacon_V4_Base).

To enable message forwarding: edit Iridium9603NBeacon_V4.ino, uncomment the line which says _#define RockBLOCK_ and enter the serial numbers for both
the sending Beacon (_#define source "RB00nnnnn"_) and the destination base (_#define destination "RB00nnnnn"_).
The serial numbers need to be seven digits long - prefix with zeros if necessary - and include the "RB" prefix.

_You will be charged twice for each message: once to send it from the Beacon (Mobile Originated); and a second time to receive it on the base (Mobile Terminated)._

Before you travel, download a set of Google Static Map tiles using
[Google_Static_Maps_Tiler.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Google_Static_Maps_Tiler.py). 1 degree tiles are useful for
large areas, 0.1 degree or 0.01 degree for smaller areas.

[Iridium_Beacon_Base.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_Base.py) is very similar in its operation to
Iridium_Beacon_Mapper_RockBLOCK.py except that the beacon data is received via Iridium rather than by email. The software talks to
Iridium_9603N_Beacon_V4_Base via Serial (over USB) and displays the beacon and base locations using the
[Google Static Maps API](https://developers.google.com/maps/documentation/static-maps/intro).

You will need a Key to access the API. You can create one by following [this link](https://developers.google.com/maps/documentation/static-maps/get-api-key).
Copy and paste it into a file called Google_Static_Maps_API_Key.txt

Every 'update' seconds the GUI talks to the base beacon and:
- requests its GNSS data including time, position and altitude;
- starts an IridiumSBD session and downloads a packet from the mobile terminated queue (if any are present).

You are charged each time you check for new messages, so make sure you set 'update' to a sensible value. If your beacon is transmitting messages every 10 minutes,
then set the update period to 10 minutes (600 seconds) too. If there is a backlog of messages you want to download, then reduce update. But remember to set it back to 10 minutes
afterwards to avoid being charged unnecessarily. If you are tracking two beacons each sending messages every 10 minutes, then set update to 5 minutes (300 seconds).

The GUI and base provide access to the RockBLOCK FLUSH_MT function, so an excess of unread Mobile Terminated messages can be discarded if required
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

A third pull-down menu lets you send a configuration update message to a beacon. Select the beacon you want to update using the pull-down menu.
A dialog box will appear allowing you to edit the message before it is sent. If you want to change the transmission interval (BEACON_INTERVAL) of the beacon,
change the default value of '5' (minutes) to whatever you want the new interval to be. If you want to change the status of the OMRON relay on board the beacon,
add the text _[RELAY=ON]_ or _[RELAY=OFF]_ to the message.
Click 'OK' and the base will send the message to the RockBLOCK Gateway where it will be automatically forwarded to the chosen beacon. The beacon will download and
process the message during its next transmit cycle. The relay status will be updated at the end of the transmit cycle. The new BEACON_INTERVAL value will
take effect after the _following_ transmission.

![Iridium_Beacon_Base_3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_3.JPG)

The GUI uses 640x480 pixel map images. Higher resolution images are available if you have a premium plan with Google.

When you are online, the user interface will look like this:

![Iridium_Beacon_Base_1](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_1.JPG)

When you are offline, the software will use the map tiles from the Tiler. Base and beacon locations will be shown on the offline maps but not path information

![Iridium_Beacon_Base_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Iridium_Beacon_Base_2.JPG)

## Extras

[Iridium_Beacon_Stitcher_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_Stitcher_RockBLOCK.py) will stitch the .bin SBD attachments downloaded by
[Iridium_Beacon_GMail_Downloader_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_GMail_Downloader_RockBLOCK.py) together into a single .csv
(Comma Separated Value) file which can be opened by (e.g.) Microsoft Excel.

[Iridium_Beacon_CSV_DateTime.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_CSV_DateTime.py) will convert the first column of the stitched .csv file
from YYYYMMDDHHMMSS format into DD/MM/YY,HH:MM:SS format, making the message timing easier to interpret using Excel.

[Iridium_Beacon_BIN_to_KML_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_BIN_to_KML_RockBLOCK.py) will convert the .bin SBD attachments downloaded by
[Iridium_Beacon_GMail_Downloader_RockBLOCK.py](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/Python/Iridium_Beacon_GMail_Downloader_RockBLOCK.py) into .kml files which can be opened in Google Earth.
The path of the beacon can be shown as: 2D (course over ground) or 3D (course and altitude) linestring; points (labelled with message sequence numbers); and arrows (indicating the heading of the beacon).

## Required Python 2.7 Libraries

To get the tools to run successfully you will need to install the following libraries:

### GMail API

- pip install --upgrade google-api-python-client

### PIL ImageTk

- sudo apt-get install python-pil.imagetk

### Matplotlib

- sudo apt-get install python-matplotlib

### Kyle Lancaster's simplekml

- http://simplekml.readthedocs.io/en/latest/index.html
- https://pypi.python.org/pypi/simplekml
- pip install simplekml

Enjoy!

**_Paul_**


