# -*- coding: cp1252 -*-

## Iridium 9603N Beacon Mapper for RockBLOCK .bin attachments

## Written by Paul Clark: Jan-Feb, Sept 2018.

## Builds a list of all existing SBD .bin files.
## Checks periodically for the appearance of a new SBD .bin file.
## When one is found, parses the file and displays the beacon position and route
## using the Google Static Maps API.
## https://developers.google.com/maps/documentation/static-maps/intro
## You will need a Key to access the API. You can create one by following this link:
## https://developers.google.com/maps/documentation/static-maps/get-api-key
## Copy and paste it into a file called Google_Static_Maps_API_Key.txt

## The software makes extensive use of the Google Static Map API.
## The displayed map is automatically centered on a new beacon position.
## The center position can be changed by left-clicking in the image.
## A right-click will copy the click location (lat,lon) to the clipboard.
## The zoom can be changed using the buttons.

## Each beacon's path is displayed as a coloured line on the map.
## The oldest waypoints may be deleted as the map URL is limited to 8192 characters.

## A pull-down menu lists the locations of all the beacons being tracked.
## Clicking on a menu entry will center the map on that location and will copy that location
## to the clipboard.

## The GUI uses 640x480 pixel map images. Higher resolution images are available
## if you have a premium plan with Google.

# sbd file contains the following in csv format:
# (Optional) Column 0 = The Base's RockBLOCK serial number (see Iridium9603NBeacon_V4.ino)
# Column 1 = GPS Tx Time (YYYYMMDDHHMMSS)
# Column 2 = GPS Latitude (degrees) (float)
# Column 3 = GPS Longitude (degrees) (float)
# Column 4 = GPS Altitude (m) (int)
# Column 5 = GPS Speed (m/s) (float)
# Column 6 = GPS Heading (Degrees) (int)
# Column 7 = GPS HDOP (m) (float)
# Column 8 = GPS satellites (int)
# Coulmn 9 = Pressure (Pascals) (int)
# Column 10 = Temperature (C) (float)
# Column 11 = Battery (V) (float)
# Column 12 = Iteration Count (int)
# (Optional) Column 13 = The Beacon's RockBLOCK serial number (see Iridium9603NBeacon_V4.ino)

from PyQt5.QtCore import QSettings, QProcess, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, QPushButton, \
    QApplication, QLineEdit, QFileDialog, QPlainTextEdit, QCheckBox, QMessageBox, \
    QMenuBar
from PyQt5.QtGui import QCloseEvent, QTextCursor, QPixmap, QClipboard
import time
import urllib.request
import math
import numpy as np
from sys import platform
import os
import matplotlib.dates as mdates
import re

class BeaconMapper(QWidget):

   def __init__(self, parent: QWidget = None) -> None:
      ''' Init BeaconMapper: check for existing SBD .bin files; read API key; set up the Tkinter window '''
      super().__init__(parent)
      
      print('Iridium Beacon Mapper for RockBLOCK')
      print

      # Default values
      self._job = None # Keep track of timer calls
      self.zoom = '15' # Default Google Maps zoom (text)
      self.default_interval = '00:05:00' # Default update interval
      self.update_intervals = ['00:00:15', '00:00:30', '00:01:00', '00:01:30', '00:02:00', '00:02:30', '00:03:00', '00:04:00', '00:05:00'] # Update intervals
      self.sep_width = 304 # Separator width in pixels
      self.map_lat = 0.0 # Map latitude (degrees)
      self.map_lon = 0.0 # Map longitude (degrees)
      self.frame_height = 480 # Google Static Map window width
      self.frame_width = 640 # Google Static Map window height
      self.delta_limit_pixels = 200 # If base to beacon angle (delta) exceeds this many pixels, decrease the zoom level accordingly
      self.map_type = 'hybrid' # Maps can be: roadmap , satellite , terrain or hybrid
      self.enable_clicks = False # Are mouse clicks enabled? False until first map has been loaded
      self.beacons = 0 # How many beacons are currently being tracked
      self.max_beacons = 8 # Track up to this many beacons
      self.beacon_imeis = {} # Dictionary of the serial numbers of the beacons currently being tracked
      self.beacon_paths = [] # List of beacon paths for Static Map
      self.beacon_locations = [] # List of current location for each beacon
      # Colours for beacon markers and paths - supported by both Tkinter and Google Static Maps API
      self.beacon_colours = ['red','yellow','green','blue','purple','gray','brown','orange']
      self.sbd = [] # List of existing sbd filenames
      
      # Limit path lengths to this many characters depending on how many beacons are being tracked
      # (Google allows combined URLs of up to 8192 characters)
      # The first entry is redundant (i.e. would be used when tracking zero beacons)
      # These limits take into account that each pipe ('|') is expanded to '%7C' by urllib
      self.max_path_lengths = [7000, 7000, 3400, 2200, 1600, 1300, 1050, 900, 780]

      # Google static map API pixel scales to help with map moves
      # https://gis.stackexchange.com/questions/7430/what-ratio-scales-do-google-maps-zoom-levels-correspond-to
      # ---
      # Radius of the Earth at the Equator = 6378137m
      # Circumference at the Equator = 2*pi*r = 40075017m
      # Zoom level 24 uses 2^32 (4294967296) pixels at circumference
      # Pixel scale at zoom level 24 is 0.009330692m/pixel
      # Pixel scale doubles with each zoom level
      # Pixel scale at zoom level 21 is 0.074645535m/pixel
      # Pixel scale at zoom level 1 is 78271.5170m/pixel
      # ---
      # Zoom level 24 uses 2^32 (4294967296) pixels at circumference
      # Each pixel represents an angle of 2*pi/2^32 radians = 1.46291808e-9 radians
      # Angle doubles with each zoom level
      # Zoom level 21 is 1.17033446e-8 radians per pixel
      # In degrees:
      # Zoom level 21 is 6.70552254e-7 degrees per pixel
      # Zoom level 1 is 0.703125 degrees per pixel
      # ---
      # These values need to be adjusted with increasing latitude due to the Mercator projection
      self.scales = np.array([
         [1,7.03125000E-01], # Zoom level 1 is 0.703125 degrees per pixel at the Equator
         [2,3.51562500E-01],
         [3,1.75781250E-01],
         [4,8.78906250E-02],
         [5,4.39453125E-02],
         [6,2.19726562E-02],
         [7,1.09863281E-02],
         [8,5.49316406E-03],
         [9,2.74658203E-03],
         [10,1.37329102E-03],
         [11,6.86645508E-04],
         [12,3.43322754E-04],
         [13,1.71661377E-04],
         [14,8.58306885E-05],
         [15,4.29153442E-05],
         [16,2.14576721E-05],
         [17,1.07288361E-05],
         [18,5.36441803E-06],
         [19,2.68220901E-06],
         [20,1.34110451E-06],
         [21,6.70552254E-07]]) # Zoom level 21 is 6.70552254e-7 degrees per pixel at the Equator

      # Ask the user if they want to ignore any existing sbd files
      # Answer 'n' to display all sbd files - both existing and new
      try:
         ignore_old_files = input('Do you want to ignore any existing SBD .bin files? (Y/n) : ')
      except:
         ignore_old_files = 'Y'
      if (ignore_old_files != 'Y') and (ignore_old_files != 'y') and (ignore_old_files != 'N') and (ignore_old_files != 'n'):
         ignore_old_files = 'Y'
      if (ignore_old_files == 'y'): ignore_old_files = 'Y'

      if (ignore_old_files == 'Y'):
         print('Searching for existing SBD .bin files...')
         num_files = 0
         last_num_files = 0
         # Build a list of all existing sbd files
         for root, dirs, files in os.walk(".", followlinks=False):
            if num_files > last_num_files:
               print('Found',num_files,'SBD .bin files so far...')
               last_num_files = num_files
            if len(files) > 0:
               #if root != ".": # Ignore files in this directory - only process subdirectories
               #if root == ".": # Ignore subdirectories - only process this directory
                  for filename in self.sorted_nicely(files):
                     if filename[-4:] == '.bin': # check for bin file suffix
                        num_files += 1
                        longfilename = os.path.join(root, filename)
                        self.sbd.append(longfilename) # add the filename to the list
         print('Ignoring',len(self.sbd),'existing SBD .bin files')
      print

      # Read the Google Static Maps API key
      # Create one using: https://developers.google.com/maps/documentation/static-maps/get-api-key
      try:
         with open('Google_Static_Maps_API_Key.txt', 'r') as myfile:
            self.key = myfile.read().replace('\n', '')
            myfile.close()
      except:
         print('Could not read the Google Static Maps API key!')
         print('Create one here: https://developers.google.com/maps/documentation/static-maps/get-api-key')
         print('then copy and paste it into a file called Google_Static_Maps_API_Key.txt')
         raise ValueError('Could not read API Key!')

      # Set up UI
      
      row = 1 # Leave space for the menubar

      layout = QGridLayout()

      # Update interval
      interval_txt = QLabel(self.tr('Update interval (hh:mm:ss)')) # Create the label
      layout.addWidget(interval_txt, row, 0) # Add it
      self.interval = QLineEdit() # Create the value box
      self.interval.clear() # Delete any existing text (redundant?)
      self.interval.setText('00:00:15') # Initialize it
      self.interval.setAlignment(Qt.AlignHCenter) # Align it
      self.interval.setReadOnly(True) # Make it read-only
      layout.addWidget(self.interval, row, 1) # Add it
      row += 1

      # Time since last update
      time_since_last_update_txt = QLabel(self.tr('Time since last update (s)')) # Create the label
      layout.addWidget(time_since_last_update_txt, row, 0) # Add it
      self.time_since_last_update = QLineEdit() # Create the value box
      self.time_since_last_update.clear() # Delete any existing text (redundant?)
      self.time_since_last_update.setText('00:00:00') # Initialize it
      self.time_since_last_update.setAlignment(Qt.AlignHCenter) # Align it
      self.time_since_last_update.setReadOnly(True) # Make it read-only
      layout.addWidget(self.time_since_last_update, row, 1) # Add it
      row += 1

      # Beacon imei
      beacon_imei_txt = QLabel(self.tr('Beacon IMEI')) # Create the label
      layout.addWidget(beacon_imei_txt, row, 0) # Add it
      self.beacon_imei = QLineEdit() # Create the value box
      self.beacon_imei.clear() # Delete any existing text (redundant?)
      self.beacon_imei.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_imei.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_imei, row, 1) # Add it
      row += 1

      # Beacon time
      beacon_time_txt = QLabel(self.tr('Beacon time')) # Create the label
      layout.addWidget(beacon_time_txt, row, 0) # Add it
      self.beacon_time = QLineEdit() # Create the value box
      self.beacon_time.clear() # Delete any existing text (redundant?)
      self.beacon_time.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_time.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_time, row, 1) # Add it
      row += 1

      # Beacon location
      beacon_location_txt = QLabel(self.tr('Beacon location')) # Create the label
      layout.addWidget(beacon_location_txt, row, 0) # Add it
      self.beacon_location = QLineEdit() # Create the value box
      self.beacon_location.clear() # Delete any existing text (redundant?)
      self.beacon_location.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_location.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_location, row, 1) # Add it
      row += 1

      # Beacon altitude
      beacon_altitude_txt = QLabel(self.tr('Beacon altitude (m)')) # Create the label
      layout.addWidget(beacon_altitude_txt, row, 0) # Add it
      self.beacon_altitude = QLineEdit() # Create the value box
      self.beacon_altitude.clear() # Delete any existing text (redundant?)
      self.beacon_altitude.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_altitude.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_altitude, row, 1) # Add it
      row += 1

      # Beacon speed
      beacon_speed_txt = QLabel(self.tr('Beacon speed (m/s)')) # Create the label
      layout.addWidget(beacon_speed_txt, row, 0) # Add it
      self.beacon_speed = QLineEdit() # Create the value box
      self.beacon_speed.clear() # Delete any existing text (redundant?)
      self.beacon_speed.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_speed.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_speed, row, 1) # Add it
      row += 1

      # Beacon heading
      beacon_heading_txt = QLabel(self.tr("Beacon track ("+u"\u00b0"+")")) # Create the label
      layout.addWidget(beacon_heading_txt, row, 0) # Add it
      self.beacon_heading = QLineEdit() # Create the value box
      self.beacon_heading.clear() # Delete any existing text (redundant?)
      self.beacon_heading.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_heading.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_heading, row, 1) # Add it
      row += 1

      # Beacon pressure
      beacon_pressure_txt = QLabel(self.tr('Beacon pressure (mbar)')) # Create the label
      layout.addWidget(beacon_pressure_txt, row, 0) # Add it
      self.beacon_pressure = QLineEdit() # Create the value box
      self.beacon_pressure.clear() # Delete any existing text (redundant?)
      self.beacon_pressure.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_pressure.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_pressure, row, 1) # Add it
      row += 1

      # Beacon temperature
      beacon_temperature_txt = QLabel(self.tr("Beacon temperature ("+u"\u2103"+")")) # Create the label
      layout.addWidget(beacon_temperature_txt, row, 0) # Add it
      self.beacon_temperature = QLineEdit() # Create the value box
      self.beacon_temperature.clear() # Delete any existing text (redundant?)
      self.beacon_temperature.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_temperature.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_temperature, row, 1) # Add it
      row += 1

      # Beacon voltage
      beacon_voltage_txt = QLabel(self.tr('Beacon voltage (V)')) # Create the label
      layout.addWidget(beacon_voltage_txt, row, 0) # Add it
      self.beacon_voltage = QLineEdit() # Create the value box
      self.beacon_voltage.clear() # Delete any existing text (redundant?)
      self.beacon_voltage.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_voltage.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_voltage, row, 1) # Add it
      row += 1

      # Beacon MSN
      beacon_msn_txt = QLabel(self.tr('Beacon MOMSN')) # Create the label
      layout.addWidget(beacon_msn_txt, row, 0) # Add it
      self.beacon_msn = QLineEdit() # Create the value box
      self.beacon_msn.clear() # Delete any existing text (redundant?)
      self.beacon_msn.setAlignment(Qt.AlignHCenter) # Align it
      self.beacon_msn.setReadOnly(True) # Make it read-only
      layout.addWidget(self.beacon_msn, row, 1) # Add it
      row += 1

      # Buttons
      self.zoom_in_button = QPushButton(self.tr('Zoom +')) # Create the button
      self.zoom_in_button.pressed.connect(self.zoom_map_in) # Connect it to the function
      layout.addWidget(self.zoom_in_button, row, 0) # Add it
      self.zoom_out_button = QPushButton(self.tr('Zoom -')) # Create the button
      self.zoom_out_button.pressed.connect(self.zoom_map_out) # Connect it to the function
      layout.addWidget(self.zoom_out_button, row + 1, 0) # Add it
      self.quit_button = QPushButton(self.tr('Quit')) # Create the button
      self.quit_button.pressed.connect(self.close) # Connect it to the function
      layout.addWidget(self.quit_button, row, 1, 2, 1) # Add it
      row += 1

      # Map Image
      self.imageLabel = QLabel()
      filename = "map_image_blank.png"
      self.pixmap = QPixmap(filename)
      self.imageLabel.setPixmap(self.pixmap)
      layout.addWidget(self.imageLabel, 1, 2, row+1, 1)
      self.imageLabel.mousePressEvent = self.image_click # https://stackoverflow.com/a/6199330

      # Menu to list current beacon locations
      self.menubar = QMenuBar() # Create the menubar
      layout.addWidget(self.menubar,0,0,1,2) # Add it
      self.beacon_menu = self.menubar.addMenu('Beacon Locations')

      # Menu to list update intervals
      self.interval_menu = self.menubar.addMenu('Set Update Interval')
      # Add intervals
      for update_interval in self.update_intervals:
         interval_str = str(update_interval)
         action = self.interval_menu.addAction(interval_str)
         action.triggered.connect(lambda state, x=interval_str: self.set_update_interval(x)) # https://stackoverflow.com/a/35821092

      # Set the layout
      self.setLayout(layout)

      # Set up next update
      self.last_update_at = time.time() # Last time an update was requested
      self.first_update = True # Flag to indicate if an update has been performed

      # Timer
      self.timer = QTimer()
      self.timer.setInterval(250) # Set the timer interval
      self.timer.timeout.connect(self.recurring_timer)
      self.timer.start()

      # Start GUI
      self.show()

   def recurring_timer(self):
      ''' Timer function - handles map updates '''
      
      do_update = False # Initialise is it time to do an update?
      now = time.time() # Get the current time

      time_since_last_update = now - self.last_update_at # Calculate interval since last update
      last_update_str = time.strftime('%H:%M:%S', time.gmtime(time_since_last_update))
      self.time_since_last_update.setText(last_update_str) # Update the indicated time since last update

      # Check if it is time to do an update
      # Do an update if it has been at least interval seconds since the last update
      # and there are no message boxes open
      # or this is the first update
      interval = sum(float(n) * m for n, m in zip(reversed(self.interval.text().split(':')), (1, 60, 3600))) # https://stackoverflow.com/a/45971056
      if (time_since_last_update >= interval) or (self.first_update == True): 
         do_update = True # Do update
         self.first_update = False # Clear flag
         self.last_update_at = now # Update time of last update

      if do_update: # If it is time to do an update
         self.time_since_last_update.setText('In Progress...') # Update the indicated time since last update
         if self.check_for_files(): # Check for new SBD files
            self.update_map() # Update the Google Static Maps image

   def check_for_files(self):
      ''' Check for the appearance of any new SBD .bin files and parse them '''
      new_files = False # Found any new files?
      # Identify all the sbd files again 
      for root, dirs, files in os.walk("."):
         if len(files) > 0:
            #if root != ".": # Ignore files in this directory - only process subdirectories
            #if root == ".": # Ignore subdirectories - only process this directory
               for filename in self.sorted_nicely(files):
                  if (filename[-4:] == '.bin') and (filename[15:16] == '-'): # Does it have the correct format? (imei-momsn.bin)
                     longfilename = os.path.join(root, filename)
                     msnum = filename[16:-4] # Get the momsn
                     imei = filename[0:15] # Get the imei
                     ignore_me = False # Should we ignore this file?

                     # Check if this file is in the list
                     # If it isn't then this must be a new SBD file so try and process it
                     try:
                        index = self.sbd.index(longfilename)
                     except:
                        index = -1
                     if index == -1:
                        self.sbd.append(longfilename) # Add new filename to list so even if invalid we don't process it again

                        # Read the sbd file and unpack the data using numpy loadtxt
                        try: # Messages without RockBLOCK destination
                           gpstime,latitude,longitude,altitude,speed,heading,pressure,temperature,battery = \
                               np.loadtxt(longfilename, delimiter=',', unpack=True, \
                               usecols=(0,1,2,3,4,5,8,9,10), converters={0: lambda s: mdates.datestr2num(s.decode())})
                        except: # Messages with RockBLOCK destination
                           try:
                              gpstime,latitude,longitude,altitude,speed,heading,pressure,temperature,battery = \
                                  np.loadtxt(longfilename, delimiter=',', unpack=True, \
                                  usecols=(1,2,3,4,5,6,9,10,11), converters={1: lambda s: mdates.datestr2num(s.decode())})
                           except:
                              print('Ignoring',filename)
                              ignore_me = True
                        if (ignore_me == False):
                           print('Found new SBD file from beacon IMEI',imei,'with MOMSN',msnum)
                           
                           pressure = int(round(pressure)) # Convert pressure to integer
                           altitude = int(round(altitude)) # Convert altitude to integer
                           time_str = mdates.num2date(gpstime).strftime('%H:%M:%S') # Construct time
                           position_str = "{:.6f},{:.6f}".format(latitude, longitude) # Construct position

                           # Check if this new file is from a beacon imei we haven't seen before
                           if imei in self.beacon_imeis:
                              pass # We have seen this one before
                           else:
                              # This is a new beacon
                              # Check that we haven't reached the maximum number of beacons
                              if self.beacons < self.max_beacons:
                                 # Maximum hasn't been reached so get things ready for this new beacon
                                 self.beacon_imeis[imei] = self.beacons # Add this imei and its beacon number
                                 self.beacon_paths.append('&path=color:'+self.beacon_colours[self.beacons]+'|weight:5') # Append an empty path for this beacon
                                 self.beacon_locations.append('') # Append a NULL location for this beacon
                                 self.beacons += 1 # Increment the number of beacons being tracked
                                 # This is a new beacon so center map on its location this time only
                                 self.map_lat = latitude
                                 self.map_lon = longitude
                                 # Add it to the Beacon Location menu
                                 # https://stackoverflow.com/q/7542164
                                 # https://stackoverflow.com/a/35821092
                                 action = self.beacon_menu.addAction(imei)
                                 action.triggered.connect(lambda state, x=imei: self.copy_location(x))
                              else:
                                 # Maximum has been reached - don't process data from this beacon
                                 print('Unable to process file: maximum number of beacons reached!')
                                 ignore_me = True # Limit reached so ignore this file

                           if (ignore_me == False):
                              # Update beacon location
                              self.beacon_locations[self.beacon_imeis[imei]] = position_str # Update location for this beacon

##                              # Change beacon location background colour
##                              self.beacon_location_txt.setStyleSheet(background=self.beacon_colours[self.beacon_imeis[imei]])
                              
                              # Update beacon path (append this location to the path for this beacon)
                              self.beacon_paths[self.beacon_imeis[imei]] += '|' + position_str
                              
                              # Check path length hasn't exceeded the maximum
                              def find_char(s, ch): # https://stackoverflow.com/a/11122355
                                 return [i for i, ltr in enumerate(s) if ltr == ch]
                              while len(self.beacon_paths[self.beacon_imeis[imei]]) > self.max_path_lengths[self.beacons]:
                                 # Delete path from second to third pipe character ('|') (first '|' preceeds the line weight)
                                 pipes = find_char(self.beacon_paths[self.beacon_imeis[imei]],'|')
                                 self.beacon_paths[self.beacon_imeis[imei]] = self.beacon_paths[self.beacon_imeis[imei]][:pipes[1]] + self.beacon_paths[self.beacon_imeis[imei]][pipes[2]:]
                                 
                              # Update imei
                              self.beacon_imei.setText(imei)
                              # Update beacon time
                              self.beacon_time.setText(time_str)
                              # Update beacon location
                              self.beacon_location.setText(position_str)
                              # Update beacon_altitude
                              self.beacon_altitude.setText(str(altitude))
                              # Update beacon_speed
                              self.beacon_speed.setText(str(speed))
                              # Update beacon_heading
                              self.beacon_heading.setText(str(heading))
                              # Update beacon_pressure
                              self.beacon_pressure.setText(str(pressure))
                              # Update beacon_temperature
                              self.beacon_temperature.setText(str(temperature))
                              # Update beacon_voltage
                              self.beacon_voltage.setText(str(battery))
                              # Update beacon_msn
                              self.beacon_msn.setText(msnum)
##                              # Update Beacon Location menu
##                              label_str = imei + ' : ' + position_str
##                              self.beacon_menu.entryconfig(self.beacon_imeis[imei], label=label_str, background=self.beacon_colours[self.beacon_imeis[imei]])

                              new_files = True # Update new_files now that entire file has been processed
      return new_files
   
   def update_map(self):
      ''' Show beacon locations and the beacon routes using Google Maps API StaticMap '''

      # Assemble map center
      center = ("%.6f"%self.map_lat) + ',' + ("%.6f"%self.map_lon)

      # Update the Google Maps API StaticMap URL
      self.path_url = 'https://maps.googleapis.com/maps/api/staticmap?center=' # 54 chars
      self.path_url += center # 22 chars
      if self.beacons > 0: # Do we have any valid beacons?
         for beacon in range(self.beacons):
            self.path_url += '&markers=color:' + self.beacon_colours[beacon] + '|' # beacons*(15+6+3+22) chars
            self.path_url += self.beacon_locations[beacon]
         # Path 'header' is 29 chars
         # Minimum length for each waypoint is 18 chars but will grow to 20 when pipe is expanded
         # This needs to be included in the max_path_length
         for beacon in range(self.beacons): 
            self.path_url += self.beacon_paths[beacon]
      self.path_url += '&zoom=' # 8 chars
      self.path_url += self.zoom
      self.path_url += '&size=' # 13 chars
      self.path_url += str(self.frame_width)
      self.path_url += 'x'
      self.path_url += str(self.frame_height)
      self.path_url += '&maptype=' + self.map_type + '&format=png&key=' # 35 chars
      self.path_url += self.key # 40 chars

      # Download the API map image from Google
      filename = "map_image.png" # Download map to this file
      try:
         urllib.request.urlretrieve(self.path_url, filename) # Attempt map image download
      except:
         filename = "map_image_blank.png" # If download failed, default to blank image

      # Update label using image
      self.pixmap = QPixmap(filename)
      self.imageLabel.setPixmap(self.pixmap)
      
      # Enable zoom buttons and mouse clicks if a map image was displayed
      if filename == "map_image.png":
         self.zoom_in_button.setEnabled(True) # Enable zoom+
         self.zoom_out_button.setEnabled(True) # Enable zoom-
         self.enable_clicks = True # Enable mouse clicks
      else: # Else disable them again
         self.zoom_in_button.setEnabled(False) # Disable zoom+
         self.zoom_out_button.setEnabled(False) # Disable zoom-
         self.enable_clicks = False # Disable mouse clicks

   def zoom_map_in(self):
      ''' Zoom in '''
      # Increment zoom if zoom is less than 21
      if int(self.zoom) < 21:
         self.zoom = str(int(self.zoom) + 1)
         self.update_map()

   def zoom_map_out(self):
      ''' Zoom out '''
      # Decrement zoom if zoom is greater than 0
      if int(self.zoom) > 0:
         self.zoom = str(int(self.zoom) - 1)
         self.update_map()

   def image_click(self, event):
      ''' Handle mouse click event '''
      if (self.enable_clicks) and (int(self.zoom) > 0) and (int(self.zoom) <= 21): # Are clicks enabled and is zoom 1-21?
         x_move = event.pos().x() - (self.frame_width / 2) # Required x move in pixels
         y_move = event.pos().y() - (self.frame_height / 2) # Required y move in pixels
         scale_x = self.scales[np.where(int(self.zoom)==self.scales[:,0])][0][1] # Select scale from scales using current zoom
         # Compensate y scale (Mercator projection) using current latitude
         scale_multiplier_lat = math.cos(math.radians(self.map_lat))
         scale_y = scale_x * scale_multiplier_lat # Calculate y scale
         new_lat = self.map_lat - (y_move * scale_y) # Calculate new latitude
         new_lon = self.map_lon + (x_move * scale_x) # Calculate new longitude
         self.map_lat = new_lat # Update lat
         self.map_lon = new_lon # Update lon
         self.update_map() # Update map

   def copy_location(self, imei):
      ''' Move the map to the location of this imei '''
      loc = self.beacon_locations[self.beacon_imeis[imei]] # Get location
      try:
         lat,lon = loc.split(',')
         self.map_lat = float(lat)
         self.map_lon = float(lon)
         self.update_map()
      except:
         pass

   def set_update_interval(self, new_interval):
      ''' Update the update interval '''
      self.interval.setText(new_interval) # Update the indicated time since last update

   # https://stackoverflow.com/a/2669120
   def sorted_nicely(self, l): 
    """ Sort the given iterable in the way that humans expect.""" 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

   def closeEvent(self, event: QCloseEvent) -> None:
      """Handle Close event of the Widget."""
      #self.timer.stop()
      event.accept()

if __name__ == "__main__":
   from sys import exit as sysExit
   app = QApplication([])
   app.setOrganizationName('Iridium Beacon')
   app.setApplicationName('Beacon Mapper')
   w = BeaconMapper()
   sysExit(app.exec_())

