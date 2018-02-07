# -*- coding: cp1252 -*-

## Multi Iridium Beacon Base

## Written by Paul Clark: Dec 2017 - Feb 2018.

## This project is distributed under a Creative Commons Attribution + Share-alike (BY-SA) licence.
## Please refer to section 5 of the licence for the “Disclaimer of Warranties and Limitation of Liability”.

## Talks to an Iridium_9603N_Beacon_V4_Base via Serial.
## Displays beacon and base locations using the Google Static Maps API:
## https://developers.google.com/maps/documentation/static-maps/intro
## You will need a Key to access the API. You can create one by following this link:
## https://developers.google.com/maps/documentation/static-maps/get-api-key
## Copy and paste it into a file called Google_Static_Maps_API_Key.txt

## Each beacon sends a data packet to the base via Iridium, forwarded by Rock7's RockBLOCK network.
## The serial number of the destination base is set in Iridium9603NBeacon_V4.ino

## Every 'update' seconds the GUI talks to the base beacon and:
## requests its GNSS data including time, position and altitude;
## starts an IridiumSBD session and downloads a packet from the mobile terminated queue
## (if any are present).

## The GUI and base provide access to the RockBLOCK FLUSH_MT function, so an excess of
## unread Mobile Terminated messages can be discarded if required
## (note that you are still charged from these messages!).

## The software logs all received packets to CSV log files. Each beacon gets its own log file.

## The software makes extensive use of the Google Static Map API.
## The displayed map is automatically centered on a new beacon position.
## The center position can be changed by left-clicking in the image.
## A right-click will copy the click location (lat,lon) to the clipboard.
## The zoom level is set automatically when a new beacon is displayed to show both beacon and base.
## The zoom can be changed using the buttons.

## Each beacon's path is displayed as a coloured line on the map.
## The oldest waypoints may be deleted as the map URL is limited to 8192 characters.

## A pull-down menu lists the locations of all the beacons being tracked.
## Clicking on a menu entry will center the map on that location and will copy the location
## to the clipboard.
## A second pull-down menu shows the location of the base. Clicking it will center the map on that
## location and will copy that location to the clipboard.

## The GUI uses 640x480 pixel map images. Higher resolution images are available if you have a
## premium plan with Google.

## Offline maps can be collected using Google_Static_Map_Tiler.py
## Base and beacon locations will be shown on the offline maps but not path information

import Tkinter as tk
import tkMessageBox
import tkFont
import serial
import time
import urllib
from PIL import Image, ImageTk, ImageDraw
import math
import numpy as np
from sys import platform
from shutil import copyfile
import os

class BeaconBase(object):

   def __init__(self):
      ''' Init BeaconBase: read API key; open the serial port; set up the Tkinter window '''
      print 'Multi Iridium 9603N Beacon Base'
      print

      # Default values
      self._job = None # Keep track of timer calls
      self.zoom = '15' # Default Google Maps zoom (text)
      self.default_interval = 120 # Default update interval (secs)
      self.beacon_timeout = 65 # Default timeout for Iridium comms (needs to be > IridiumSBD.adjustSendReceiveTimeout)
      self.gnss_timeout = 35 # Default timeout for GNSS update (needs to be > timeout in Iridium9603NBeacon_V4_Base)
      self.console_height = 2 # Console window height in lines
      self.sep_width = 304 # Separator width in pixels
      self.map_lat = 0.0 # Map latitude (degrees)
      self.map_lon = 0.0 # Map longitude (degrees)
      self.frame_height = 480 # Google Static Map window width
      self.frame_width = 640 # Google Static Map window height
      self.delta_limit_pixels = 200 # If base to beacon angle (delta) exceeds this many pixels, decrease the zoom level accordingly
      self.map_type = 'hybrid' # Maps can be: roadmap , satellite , terrain or hybrid
      self.base_choice = '2\r' # Send this choice to the beacon base to request the base GNSS position etc.
      self.beacon_choice = '4\r' # Send this choice to the beacon base to request the beacon data via Iridium
      self.flush_mt_choice = '5\r' # Send this choice to the beacon base to request a flush of the mobile terminated queue
      self.enable_clicks = False # Are mouse clicks enabled? False until first map has been loaded
      self.beacons = 0 # How many beacons are currently being tracked
      self.max_beacons = 8 # Track up to this many beacons
      self.beacon_serials = {} # Dictionary of the serial numbers of the beacons currently being tracked
      self.beacon_log_files = [] # List of log file names
      self.beacon_paths = [] # List of beacon paths for Static Map
      self.beacon_locations = [] # List of current location for each beacon
      self.beacon_colours = ['red','yellow','green','blue','purple','gray','brown','orange'] # Colours for beacon markers and paths
      self.base_colour = 'white' # Use this colour for the base marker
      self.first_base = True # Is this the first time we have received a base location?
      self.do_zoom = False # Should we set the map zoom? (When a new beacon is detected)
      self.do_map_update = False # Should we update the map? (When new data is detected)
      self.offline_marker_radius = 5 # Radius of the offline marker circle (int)
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

      # Read the Google Static Maps API key
      # Create one using: https://developers.google.com/maps/documentation/static-maps/get-api-key
      try:
         with open('Google_Static_Maps_API_Key.txt', 'r') as myfile:
            self.key = myfile.read().replace('\n', '')
            myfile.close()
      except:
         print 'Could not read the API key!'
         print 'Create one here: https://developers.google.com/maps/documentation/static-maps/get-api-key'
         print 'then copy and paste it into a file called Google_Static_Maps_API_Key.txt'
         raise ValueError('Could not read API Key!')

      # Get the serial port name
      if platform.startswith('linux'):
         # linux
         defcom = '/dev/ttyACM0'
      elif platform.startswith('darwin'):
         # OS X
         defcom = '/dev/tty.usbmodem'
      elif platform.startswith('win'):
         # Windows...
         defcom = 'COM1'
      else:
         defcom = 'COM1'

      # Ask the user to confirm the serial port name
      com_port = raw_input('Which serial port do you want to use (default '+defcom+')? ')
      if com_port == '': com_port = defcom
      print

      # Open port
      try:
         self.ser = serial.Serial(com_port, 115200, timeout=0.25)
      except:
         raise NameError('COULD NOT OPEN SERIAL PORT!')
      self.ser.flushInput() # Flush RX buffer

      # Check for offline map tiles
      self.tile_num = 0 # tile number
      self.tile_filenames = [] # tile long filenames
      self.tile_lats = [] # tile latitudes
      self.tile_lons = [] # tile longitudes
      self.tile_zooms = [] # tile zooms
      for root, dirs, files in os.walk("."):
         if len(files) > 0:
            #if root != ".": # Ignore files in this directory - only process subdirectories
            #if root == ".": # Ignore subdirectories - only process this directory
               for filename in files:
                  if (filename[:13] == 'StaticMapTile') and (filename[-4:] == '.png'): # check for tile file
                     fields = filename.split("_") # split the filename into fields
                     longfilename = os.path.join(root, filename)
                     self.tile_filenames.append(longfilename) # add the filename to the dictionary
                     self.tile_zooms.append(fields[2])
                     self.tile_lats.append(float(fields[4]))
                     self.tile_lons.append(float(fields[6]))
                     self.tile_num += 1 # increment the tile number
      print 'Found',self.tile_num,'offline map tiles'
      print

      # Create and clear the console log file
      tn = time.localtime() # Extract the time and date as strings
      date_str = str(tn[0])+str(tn[1]).zfill(2)+str(tn[2]).zfill(2)
      time_str = str(tn[3]).zfill(2)+str(tn[4]).zfill(2)+str(tn[5]).zfill(2)
      self.console_log_file = 'Base_Console_Log_' + date_str + '_' + time_str + '.txt'
      self.fp = open(self.console_log_file, 'wb') # Create / clear the file
      self.fp.close()
      print 'Logging console messages to:',self.console_log_file
      print

      # Set up Tkinter GUI
      self.window = tk.Tk() # Create main window
      self.window.wm_title("Iridium Beacon Base") # Add a title
      self.window.config(background="#FFFFFF") # Set background colour to white

      # Set up Frames
      self.toolFrame = tk.Frame(self.window, height=self.frame_height) # Frame for buttons and entries
      self.toolFrame.pack(side=tk.LEFT)

      self.imageFrame = tk.Frame(self.window, width=self.frame_width, height=self.frame_height) # Frame for map image
      self.imageFrame.pack(side=tk.RIGHT)

      # Load default blank image into imageFrame
      # Image must be self.frame_width x self.frame_height pixels
      filename = "map_image_blank.png"
      image = Image.open(filename)
      photo = ImageTk.PhotoImage(image)
      self.label = tk.Label(self.imageFrame,image=photo)
      self.label.pack(fill=tk.BOTH) # Make the image fill the frame
      self.image = photo # Store the image to avoid garbage collection
      self.label.bind("<Button-1>",self.left_click) # Left mouse button click event
      self.label.bind("<Button-3>",self.right_click) # Right mouse button click event

      row = 0

      # Update interval
      self.interval = tk.Entry(self.toolFrame) # Create an entry
      self.interval.grid(row=row, column=1) # Assign its position
      self.interval.delete(0, tk.END) # Delete any existing text (redundant?)
      self.interval.insert(0, str(self.default_interval)) # Insert default value
      self.interval.config(justify=tk.CENTER,width=22) # Configure
      self.interval_txt = tk.Label(self.toolFrame, text = 'Update interval (s)',width=20) # Create text label
      self.interval_txt.grid(row=row, column=0) # Assign its position
      row += 1

      # Time since last update
      self.time_since_last_update = tk.Entry(self.toolFrame)
      self.time_since_last_update.grid(row=row, column=1)
      self.time_since_last_update.delete(0, tk.END)
      self.time_since_last_update.insert(0, str(0))
      self.time_since_last_update.config(justify=tk.CENTER,width=22,state='readonly')
      self.time_since_last_update_txt = tk.Label(self.toolFrame, text = 'Time since last update (s)',width=20)
      self.time_since_last_update_txt.grid(row=row, column=0)
      row += 1

      # Separator
      self.sep_1 = tk.Frame(self.toolFrame,height=1,bg='#808080',width=self.sep_width)
      self.sep_1.grid(row=row, columnspan=2)
      row += 1

      # Base time
      self.base_time = tk.Entry(self.toolFrame)
      self.base_time.grid(row=row, column=1)
      self.base_time.delete(0, tk.END)
      self.base_time.config(justify=tk.CENTER,width=22,state='readonly')
      self.base_time_txt = tk.Label(self.toolFrame, text = 'Base time',width=20)
      self.base_time_txt.grid(row=row, column=0)
      row += 1

      # Base location
      self.base_location = tk.Entry(self.toolFrame)
      self.base_location.grid(row=row, column=1)
      self.base_location.delete(0, tk.END)
      self.base_location.config(justify=tk.CENTER,width=22,state='readonly')
      self.base_location_txt = tk.Label(self.toolFrame, text = 'Base location',width=20)
      self.base_location_txt.grid(row=row, column=0)
      row += 1

      # Base altitude
      self.base_altitude = tk.Entry(self.toolFrame)
      self.base_altitude.grid(row=row, column=1)
      self.base_altitude.delete(0, tk.END)
      self.base_altitude.config(justify=tk.CENTER,width=22,state='readonly')
      self.base_altitude_txt = tk.Label(self.toolFrame, text = 'Base altitude (m)',width=20)
      self.base_altitude_txt.grid(row=row, column=0)
      row += 1
      
      # Separator
      self.sep_2 = tk.Frame(self.toolFrame,height=1,bg='#808080',width=self.sep_width)
      self.sep_2.grid(row=row, columnspan=2)
      row += 1

      # Beacon time
      self.beacon_time = tk.Entry(self.toolFrame)
      self.beacon_time.grid(row=row, column=1)
      self.beacon_time.delete(0, tk.END)
      self.beacon_time.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_time_txt = tk.Label(self.toolFrame, text = 'Beacon time',width=20)
      self.beacon_time_txt.grid(row=row, column=0)
      row += 1

      # Beacon location
      self.beacon_location = tk.Entry(self.toolFrame)
      self.beacon_location.grid(row=row, column=1)
      self.beacon_location.delete(0, tk.END)
      self.beacon_location.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_location_txt = tk.Label(self.toolFrame, text = 'Beacon location',width=20)
      self.beacon_location_txt.grid(row=row, column=0)
      row += 1

      # Beacon altitude
      self.beacon_altitude = tk.Entry(self.toolFrame)
      self.beacon_altitude.grid(row=row, column=1)
      self.beacon_altitude.delete(0, tk.END)
      self.beacon_altitude.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_altitude_txt = tk.Label(self.toolFrame, text = 'Beacon altitude (m)',width=20)
      self.beacon_altitude_txt.grid(row=row, column=0)
      row += 1

      # Beacon speed
      self.beacon_speed = tk.Entry(self.toolFrame)
      self.beacon_speed.grid(row=row, column=1)
      self.beacon_speed.delete(0, tk.END)
      self.beacon_speed.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_speed_txt = tk.Label(self.toolFrame, text = 'Beacon speed (m/s)',width=20)
      self.beacon_speed_txt.grid(row=row, column=0)
      row += 1

      # Beacon heading
      self.beacon_heading = tk.Entry(self.toolFrame)
      self.beacon_heading.grid(row=row, column=1)
      self.beacon_heading.delete(0, tk.END)
      self.beacon_heading.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_heading_txt = tk.Label(self.toolFrame, text = ("Beacon track ("+u"\u00b0"+")"),width=20)
      self.beacon_heading_txt.grid(row=row, column=0)
      row += 1

      # Beacon pressure
      self.beacon_pressure = tk.Entry(self.toolFrame)
      self.beacon_pressure.grid(row=row, column=1)
      self.beacon_pressure.delete(0, tk.END)
      self.beacon_pressure.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_pressure_txt = tk.Label(self.toolFrame, text = 'Beacon pressure (Pa)',width=20)
      self.beacon_pressure_txt.grid(row=row, column=0)
      row += 1

      # Beacon temperature
      self.beacon_temperature = tk.Entry(self.toolFrame)
      self.beacon_temperature.grid(row=row, column=1)
      self.beacon_temperature.delete(0, tk.END)
      self.beacon_temperature.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_temperature_txt = tk.Label(self.toolFrame, text = ("Beacon temperature ("+u"\u2103"+")"),width=20)
      self.beacon_temperature_txt.grid(row=row, column=0)
      row += 1

      # Beacon voltage
      self.beacon_voltage = tk.Entry(self.toolFrame)
      self.beacon_voltage.grid(row=row, column=1)
      self.beacon_voltage.delete(0, tk.END)
      self.beacon_voltage.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_voltage_txt = tk.Label(self.toolFrame, text = 'Beacon voltage (V)',width=20)
      self.beacon_voltage_txt.grid(row=row, column=0)
      row += 1

      # Beacon Mobile Terminated Queue length (normally zero; higher values indicate a backlog of data)
      self.beacon_MTQ = tk.Entry(self.toolFrame)
      self.beacon_MTQ.grid(row=row, column=1)
      self.beacon_MTQ.delete(0, tk.END)
      self.beacon_MTQ.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_MTQ_txt = tk.Label(self.toolFrame, text = 'Beacon MT queue',width=20)
      self.beacon_MTQ_txt.grid(row=row, column=0)
      row += 1

      # Beacon serial number
      self.beacon_serial_no = tk.Entry(self.toolFrame)
      self.beacon_serial_no.grid(row=row, column=1)
      self.beacon_serial_no.delete(0, tk.END)
      self.beacon_serial_no.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_serial_no_txt = tk.Label(self.toolFrame, text = 'Beacon serial no.',width=20)
      self.beacon_serial_no_txt.grid(row=row, column=0)
      row += 1

      # Separator
      self.sep_3 = tk.Frame(self.toolFrame,height=1,bg='#808080',width=self.sep_width)
      self.sep_3.grid(row=row, columnspan=2)
      row += 1

      # Distance to beacon
      self.distance_to_beacon = tk.Entry(self.toolFrame)
      self.distance_to_beacon.grid(row=row, column=1)
      self.distance_to_beacon.delete(0, tk.END)
      self.distance_to_beacon.config(justify=tk.CENTER,width=22,state='readonly')
      self.distance_to_beacon_txt = tk.Label(self.toolFrame, text = 'Distance to Beacon (m)',width=20)
      self.distance_to_beacon_txt.grid(row=row, column=0)
      row += 1

      # Course to beacon
      self.course_to_beacon = tk.Entry(self.toolFrame)
      self.course_to_beacon.grid(row=row, column=1)
      self.course_to_beacon.delete(0, tk.END)
      self.course_to_beacon.config(justify=tk.CENTER,width=22,state='readonly')
      self.course_to_beacon_txt = tk.Label(self.toolFrame, text = ("Course to Beacon ("+u"\u00b0"+")"),width=20)
      self.course_to_beacon_txt.grid(row=row, column=0)
      row += 1

      # Separator
      self.sep_4 = tk.Frame(self.toolFrame,height=1,bg='#808080',width=self.sep_width)
      self.sep_4.grid(row=row, columnspan=2)
      row += 1

      # Message console - used to display status updates
      self.console_1 = tk.Text(self.toolFrame)
      self.console_1.grid(row=row,columnspan=2)
      self.console_1.config(width=42,height=self.console_height,wrap='none')
      row += 1

      # Serial console - used to display serial data from Base
      self.console_2 = tk.Text(self.toolFrame)
      self.console_2.grid(row=row,columnspan=2)
      self.console_2.config(width=42,height=self.console_height,wrap='none')
      row += 1

      # Separator
      self.sep_5 = tk.Frame(self.toolFrame,height=1,bg='#808080',width=self.sep_width)
      self.sep_5.grid(row=row, columnspan=2)
      row += 1

      # Buttons
      self.boldFont = tkFont.Font(size=9,weight='bold')
      self.zoom_in_button = tk.Button(self.toolFrame, text="Zoom +", font=self.boldFont, width=20, command=self.zoom_map_in, state='disabled')
      self.zoom_in_button.grid(row=row,column=0)
      self.flush_mt_button = tk.Button(self.toolFrame, text="Flush MT Queue", font=self.boldFont, width=20, command=self.flush_mt)
      self.flush_mt_button.grid(row=row,column=1)
      row += 1
      self.zoom_out_button = tk.Button(self.toolFrame, text="Zoom -", font=self.boldFont, width=20, command=self.zoom_map_out, state='disabled')
      self.zoom_out_button.grid(row=row,column=0)
      self.quit_button = tk.Button(self.toolFrame, text="Quit", font=self.boldFont, width=20, command=self.QUIT)
      self.quit_button.grid(row=row,column=1)

      # Menu to list current beacon locations
      self.menubar = tk.Menu(self.window)
      self.beacon_menu = tk.Menu(self.menubar, tearoff=0)
      self.menubar.add_cascade(label="Beacon Locations", menu=self.beacon_menu)
      self.window.config(menu=self.menubar)

      # Menu to list base location
      self.base_menu = tk.Menu(self.menubar, tearoff=0)
      self.menubar.add_cascade(label="Base Location", menu=self.base_menu)
      self.window.config(menu=self.menubar)

      # Set up next update
      self.last_update_at = time.time() # Last time an update was requested
      self.next_update_at = self.last_update_at #+ self.default_interval # Do first update after this many seconds

      # Timer
      self.window.after(2000,self.timer) # First timer event after 2 secs

      # Start GUI
      self.window.mainloop()

   def timer(self):
      ''' Timer function - calls itself repeatedly to schedule data collection and map updates '''
      do_update = False # Initialise is it time to do an update?
      now = time.time() # Get the current time
      self.time_since_last_update.configure(state='normal') # Unlock entry box
      time_since_last_update = now - self.last_update_at # Calculate interval since last update
      self.time_since_last_update.delete(0, tk.END) # Delete existing value
      if (now < self.next_update_at): # Is it time for the next update?
         # If it isn't yet time for an update, update the indicated time since last update
         self.time_since_last_update.insert(0, str(int(time_since_last_update)))
      else:
         # If it is time for an update: reset time since last update; set time for next update
         try: # Try and read the update interval
            interval = float(self.interval.get())
         except:
            #self.interval.configure(state='normal') # Unlock entry box
            self.interval.delete(0, tk.END) # Delete any existing text
            self.interval.insert(0, str(self.default_interval)) # Insert default value
            interval = self.default_interval
            #self.interval.configure(state='readonly') # Lock entry box
            #raise ValueError('Invalid Interval!')
         self.time_since_last_update.insert(0, '0') # Reset time since last update
         self.last_update_at = self.next_update_at # Update time of last update
         self.next_update_at = self.next_update_at + interval # Set time for next update
         do_update = True # Do update
      self.time_since_last_update.config(state='readonly') # Lock entry box

      if do_update: # If it is time to do an update
         self.writeToConsole(self.console_1,'Starting update') # Update message console
         self.get_base_location() # Read 'base_location' from Beacon Base GNSS
         self.get_beacon_data() # Contact Iridium and download a new message (if available)
         self.distance_between() # Update distance
         self.course_to() # Update heading
         if self.do_zoom: # Do we need to update the zoom?
            self.update_zoom() # Update zoom
            self.do_zoom = False
         if self.do_map_update: # Do we need to update the map?
            self.update_map() # Update the Google Static Maps image
            self.do_map_update = False

      self._job = self.window.after(250, self.timer) # Schedule another timer event in 0.25s

   def get_base_location(self):
      ''' Talk to Beacon Base using serial; get current base location '''
      # Base will respond with:
      # YYYYMMDDHHMMSS,lat,lon,alt,speed,heading,hdop,satellites
      # or an error message starting with "ERROR".
      console_message = 'Requesting base location (could take ' + str(self.gnss_timeout) + 's)'
      self.writeToConsole(self.console_1, console_message) # Update message console
      resp = self.writeWait(self.base_choice, self.gnss_timeout) # Send menu choice '1'; wait for response for gnss_timeout seconds
      if resp != '': # Did we get a response?
         try:
            self.writeToConsole(self.console_2,resp[:-2]) # If we did, copy it into the console
         except:
            pass
         if len(resp) >= 6: # Check length is non-trivial
            if (resp[0:5] != 'ERROR'): # Check if an error message was received
               # If the response wasn't an error:
               try:
                  parse = resp[:-2].split(',') # Try parsing the response
                  # If the parse was successful, check that the length of the first field (DateTime) is correct
                  if (len(parse) >= 8) and (len(parse[0]) == 14): # DateTime should always be 14 characters
                     # If DateTime is the correct length, assume the rest of the response contains valid data
                     # Construct 'base_time' in HH:MM:SS format
                     time_str = parse[0][8:10] + ':' + parse[0][10:12] + ':' + parse[0][12:]
                     self.base_time.config(state='normal') # Unlock base_time
                     self.base_time.delete(0, tk.END) # Delete old value
                     self.base_time.insert(0, time_str) # Insert new time
                     self.base_time.config(state='readonly') # Lock base_time
                     # Construct 'base_location' in lat,lon (float) format
                     base_location = parse[1] + ',' + parse[2]
                     if self.first_base: # Is this the first time we have seen the base location?
                        self.map_lat = float(parse[1]) # Center map on base location (could be overridden by beacon location if there is one)
                        self.map_lon = float(parse[2])
                        # Add it to the Base Location menu
                        self.base_menu.add_command(label=base_location,command=self.goto_base,background=self.base_colour)
                        self.first_base = False
                     self.base_location.config(state='normal') # Unlock base_location
                     self.base_location.delete(0, tk.END) # Delete old value
                     self.base_location.insert(0, base_location) # Insert new location
                     self.base_location.config(state='readonly') # Lock base_location
                     self.base_altitude.config(state='normal') # Unlock base_altitude
                     self.base_altitude.delete(0, tk.END) # Delete old value
                     self.base_altitude.insert(0, parse[3]) # Insert new altitude
                     self.base_altitude.config(state='readonly') # Lock base_altitude
                     self.base_menu.entryconfig(0, label=base_location) # Update base location menu
                     self.do_map_update = True # Update map with new beacon location
                     self.writeToConsole(self.console_1, 'Base location received') # Update message console
               except: # If parse failed, do nothing
                  self.writeToConsole(self.console_1, 'Serial parse failed!') # Update message console
            else:
               self.writeToConsole(self.console_1, 'ERROR received!') # Update message console
      else:
         self.writeToConsole(self.console_1, 'No serial data received!') # Update message console

   def get_beacon_data(self):
      ''' Talk to Beacon Base using serial; start Iridium session and download new data '''
      # Base will respond with:
      # beacon data followed by ',' and the MT queue length;
      # or (only) the MT queue length (if there was no data waiting to be downloaded);
      # or an error message starting with "ERROR".
      # Beacon data format will be:
      # YYYYMMDDHHMMSS,lat,lon,alt,speed,heading,hdop,satellites,pressure,temperature,vbat,count,rockblock_serial_no,mtq
      # provided the RockBLOCK option has been selected in the beacon Arduino code.
      # If the RockBLOCK option wasn't selected, the serial number will be missing and the parse will fail.
      console_message = 'Requesting beacon data (could take ' + str(self.beacon_timeout) + 's)'
      self.writeToConsole(self.console_1, console_message) # Update message console
      resp = self.writeWait(self.beacon_choice, self.beacon_timeout) # Send menu choice '3'; wait for response for beacon_timeout secs
      if resp != '': # Did we get a response?
         try:
            self.writeToConsole(self.console_2,resp[:-2]) # If we did, copy it into the console
         except:
            pass
         if len(resp) >= 8: # Check length is non-trivial
            if (resp[0:5] != 'ERROR') and (resp[0:5] != 'FLUSH'): # Check if an error message or an echo of FLUSH_MT was received
               # If the response wasn't an error or an echo of FLUSH_MT:
               try:
                  parse = resp[:-2].split(',') # Try parsing the response
                  # If the parse was successful:
                  # Check if the first field is "RBnnnnnnn"
                  if (len(parse[0]) == 9):
                     if (parse[0][0:2] == "RB"):
                        # If it is, remove it
                        parse = parse[1:]
                        # and remove it from resp too
                        resp = resp[10:]
                  # Now check that the length of the first field (DateTime) is correct
                  if (len(parse) >= 14) and (len(parse[0]) == 14): # DateTime should always be 14 characters
                     # If DateTime is the correct length, assume the rest of the response contains valid data
                     # Update beacon Mobile Terminated Queue length
                     self.beacon_MTQ.config(state='normal')
                     self.beacon_MTQ.delete(0, tk.END)
                     self.beacon_MTQ.insert(0, parse[13])
                     self.beacon_MTQ.config(state='readonly')
                     # Have we seen data from this beacon before?
                     if self.beacon_serials.has_key(parse[12]):
                        pass # We have seen this one before
                     else:
                        # This is a new beacon
                        # Check that we haven't reached the maximum number of beacons
                        if self.beacons < self.max_beacons:
                           # Maximum hasn't been reached so get things ready for this new beacon
                           self.beacon_serials[parse[12]] = self.beacons # Add this serial number and its beacon number
                           self.beacon_log_files.append('') # Append a NULL filename for this beacon
                           self.beacon_paths.append('&path=color:'+self.beacon_colours[self.beacons]+'|weight:5') # Append an empty path for this beacon
                           self.beacon_locations.append('') # Append a NULL location for this beacon
                           self.beacons += 1 # Increment the number of beacons being tracked
                           # This is a new beacon so center map on its location this time only
                           self.map_lat = float(parse[1])
                           self.map_lon = float(parse[2])
                           self.do_zoom = True
                           console_message = 'New beacon found (' + parse[12] + ')'
                           self.writeToConsole(self.console_1, console_message) # Update message console
                           # Add it to the Beacon Location menu
                           # https://stackoverflow.com/q/7542164
                           ser_no = parse[12]
                           self.beacon_menu.add_command(label=ser_no,command=lambda ser_no=ser_no: self.copy_location(ser_no))
                        else:
                           # Return now - maximum has been reached - don't process data from this beacon
                           self.writeToConsole(self.console_1, 'Beacon limit reached!') # Update message console
                           return
                     # Construct 'base_time' in HH:MM:SS format
                     time_str = parse[0][8:10] + ':' + parse[0][10:12] + ':' + parse[0][12:]
                     self.beacon_time.config(state='normal') # Unlock beacon_time
                     self.beacon_time.delete(0, tk.END) # Delete old value
                     self.beacon_time.insert(0, time_str) # Insert new time
                     self.beacon_time.config(state='readonly') # Lock beacon_time
                     # Construct 'beacon_location' in lat,lon (float) format
                     beacon_location = parse[1] + ',' + parse[2]
                     self.beacon_locations[self.beacon_serials[parse[12]]] = beacon_location # Update location for this beacon
                     self.beacon_location.config(state='normal')
                     self.beacon_location.delete(0, tk.END)
                     self.beacon_location.insert(0, beacon_location)
                     self.beacon_location.config(state='readonly')
                     self.beacon_location_txt.config(background=self.beacon_colours[self.beacon_serials[parse[12]]])
                     # Update beacon path (append this location to the path for this beacon)
                     self.beacon_paths[self.beacon_serials[parse[12]]] += '|' + beacon_location
                     # Check path length hasn't exceeded the maximum
                     def find_char(s, ch): # https://stackoverflow.com/a/11122355
                        return [i for i, ltr in enumerate(s) if ltr == ch]
                     while len(self.beacon_paths[self.beacon_serials[parse[12]]]) > self.max_path_lengths[self.beacons]:
                        # Delete path from second to third pipe character ('|') (first '|' preceeds the line weight)
                        pipes = find_char(self.beacon_paths[self.beacon_serials[parse[12]]],'|')
                        self.beacon_paths[self.beacon_serials[parse[12]]] = self.beacon_paths[self.beacon_serials[parse[12]]][:pipes[1]] + self.beacon_paths[self.beacon_serials[parse[12]]][pipes[2]:]
                     # Update beacon_altitude
                     self.beacon_altitude.config(state='normal')
                     self.beacon_altitude.delete(0, tk.END)
                     self.beacon_altitude.insert(0, parse[3])
                     self.beacon_altitude.config(state='readonly')
                     # Update beacon_speed
                     self.beacon_speed.config(state='normal')
                     self.beacon_speed.delete(0, tk.END)
                     self.beacon_speed.insert(0, parse[4])
                     self.beacon_speed.config(state='readonly')
                     # Update beacon_heading
                     self.beacon_heading.config(state='normal')
                     self.beacon_heading.delete(0, tk.END)
                     self.beacon_heading.insert(0, parse[5])
                     self.beacon_heading.config(state='readonly')
                     # Update beacon_pressure
                     self.beacon_pressure.config(state='normal')
                     self.beacon_pressure.delete(0, tk.END)
                     self.beacon_pressure.insert(0, parse[8])
                     self.beacon_pressure.config(state='readonly')
                     # Update beacon_temperature
                     self.beacon_temperature.config(state='normal')
                     self.beacon_temperature.delete(0, tk.END)
                     self.beacon_temperature.insert(0, parse[9])
                     self.beacon_temperature.config(state='readonly')
                     # Update beacon_voltage
                     self.beacon_voltage.config(state='normal')
                     self.beacon_voltage.delete(0, tk.END)
                     self.beacon_voltage.insert(0, parse[10])
                     self.beacon_voltage.config(state='readonly')
                     # Update beacon_serial_number
                     self.beacon_serial_no.config(state='normal')
                     self.beacon_serial_no.delete(0, tk.END)
                     self.beacon_serial_no.insert(0, parse[12])
                     self.beacon_serial_no.config(state='readonly')
                     # Update Beacon Location menu
                     label_str = parse[12] + ' : ' + beacon_location
                     self.beacon_menu.entryconfig(self.beacon_serials[parse[12]], label=label_str, background=self.beacon_colours[self.beacon_serials[parse[12]]])
                     # Check if the log file is empty (file name is NULL)
                     if self.beacon_log_files[self.beacon_serials[parse[12]]] == '':
                        # Create and clear the log file
                        # Construct the filename from the beacon GNSS datetime and the beacon serial number
                        self.beacon_log_files[self.beacon_serials[parse[12]]] = 'Beacon_Log_' + parse[0] + '_' + parse[12] + '.csv'
                        self.fp = open(self.beacon_log_files[self.beacon_serials[parse[12]]], 'wb') # Create / clear the file
                        self.fp.close()
                     # Now that the log file exists, append the new beacon data
                     self.fp = open(self.beacon_log_files[self.beacon_serials[parse[12]]], 'ab') # Open log file for append in binary mode
                     self.fp.write(resp) # Write the beacon response to the log file
                     self.fp.close() # Close the log file
                     self.do_map_update = True # Update map with new beacon data
                     self.writeToConsole(self.console_1, 'Beacon data received') # Update message console
               except:
                  self.writeToConsole(self.console_1, 'Serial parse failed!') # Update message console
            else:
               if (resp[0:5] == 'ERROR'):
                  self.writeToConsole(self.console_1, 'ERROR received!') # Update message console
               if (resp[0:5] == 'FLUSH'):
                  self.writeToConsole(self.console_1, 'FLUSH_MT and MTQ received') # Update message console
                  try:
                     parse = resp[:-2].split(',') # Try parsing the response
                     if (len(parse) >= 2):
                        # Update beacon Mobile Terminated Queue length
                        self.beacon_MTQ.config(state='normal')
                        self.beacon_MTQ.delete(0, tk.END)
                        self.beacon_MTQ.insert(0, parse[1])
                        self.beacon_MTQ.config(state='readonly')
                  except:
                     self.writeToConsole(self.console_1, 'Serial parse failed!') # Update message console
         else:
            # len(resp) is non-zero and less than 8 so it could contain (only) an mtq
            mtq = -1
            try:
               mtq = int(resp) # Try and extract MTQ value
            except:
               mtq = -1
            if mtq != -1:
               # MTQ should be zero (otherwise a full response should have been received)
               # but we'll give it the benefit of doubt and process it as if it could be non-zero:
               # Update beacon Mobile Terminated Queue length
               self.beacon_MTQ.config(state='normal')
               self.beacon_MTQ.delete(0, tk.END)
               self.beacon_MTQ.insert(0, str(mtq))
               self.beacon_MTQ.config(state='readonly')
               self.writeToConsole(self.console_1, 'No beacon data - only MTQ received') # Update message console
      else:
         self.writeToConsole(self.console_1, 'No serial data received!') # Update message console

   def distance_between(self):
      ''' Calculate distance. Gratefully plagiarised from Mikal Hart's TinyGPS. '''
      # https://github.com/mikalhart/TinyGPS/blob/master/TinyGPS.cpp
      # Calculate the great circle distance between 'base_location' and 'beacon_location'
      # See https://en.wikipedia.org/wiki/Great-circle_distance#Computational_formulas
      self.delta = 0.0 # Clear delta
      try: # Read base_location from entry box
         lat1,long1 = self.base_location.get().split(',')
         lat1 = math.radians(float(lat1))
         long1 = math.radians(float(long1))
      except:
         return # base_location must be empty so return now
         #raise ValueError('Invalid base_Location!')
      try: # Read beacon_location from entry box
         lat2,long2 = self.beacon_location.get().split(',')
         lat2 = math.radians(float(lat2))
         long2 = math.radians(float(long2))
      except:
         return # beacon location must be empty so return now
         #raise ValueError('Invalid Beacon_Location!')

      delta = self.calculate_delta(lat1,long1,lat2,long2) # Calculate delta
      self.distance_to_beacon.configure(state='normal') # Unlock entry box
      self.distance_to_beacon.delete(0,tk.END) # Delete old distance
      self.distance_to_beacon.insert(0,str(int(delta * 6378137.))) # Set distance
      self.distance_to_beacon.configure(state='readonly') # Lock entry box
      self.delta = math.degrees(delta) # Store the delta in degrees so update_zoom can use it

   def calculate_delta(self,lat1,long1,lat2,long2):
      ''' Calculate delta (angle) between lat1,long1 and lat2,long2. All values are in radians. '''
      delta = long1-long2
      sdlong = math.sin(delta)
      cdlong = math.cos(delta)
      slat1 = math.sin(lat1)
      clat1 = math.cos(lat1)
      slat2 = math.sin(lat2)
      clat2 = math.cos(lat2)
      delta = (clat1 * slat2) - (slat1 * clat2 * cdlong)
      delta = delta**2
      delta += (clat2 * sdlong)**2
      delta = delta**0.5
      denom = (slat1 * slat2) + (clat1 * clat2 * cdlong)
      delta = math.atan2(delta, denom)
      return delta
      
   def course_to(self):
      ''' Calculate heading. Gratefully plagiarised from Mikal Hart's TinyGPS. '''
      # https://github.com/mikalhart/TinyGPS/blob/master/TinyGPS.cpp
      try: # Read base_location from entry box
         lat1,long1 = self.base_location.get().split(',')
         lat1 = math.radians(float(lat1))
         long1 = math.radians(float(long1))
      except:
         return # base_location must be empty so return now
         #raise ValueError('Invalid base_Location!')
      try: # Read beacon_location from entry box
         lat2,long2 = self.beacon_location.get().split(',')
         lat2 = math.radians(float(lat2))
         long2 = math.radians(float(long2))
      except:
         return # beacon_location must be empty so return now
         #raise ValueError('Invalid Beacon_Location!')
      dlon = long2-long1
      a1 = math.sin(dlon) * math.cos(lat2)
      a2 = math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
      a2 = math.cos(lat1) * math.sin(lat2) - a2
      a2 = math.atan2(a1, a2)
      if (a2 < 0.): a2 += math.pi + math.pi
      self.course_to_beacon.configure(state='normal') # Unlock entry box
      self.course_to_beacon.delete(0, tk.END) # Delete old heading
      self.course_to_beacon.insert(0, str(int(math.degrees(a2)))) # Set heading
      self.course_to_beacon.configure(state='readonly') # Lock entry box

   def update_zoom(self):
      ''' Update Google StaticMap zoom based on angular separation of base_location and beacon_location '''
      # ** Run after distance_between() : requires updated self.delta **
      # delta is the angular separation of base_location and beacon_location

      adjusted_scales = np.array(self.scales) # Make a copy of the zoom vs pixel scale angle look-up table
      # Calculate latitude scale multiplier based on current latitude to correct for Mercator projection
      scale_multiplier_lat = math.cos(math.radians(self.map_lat))
      # Adjust the pixel scale angles in the zoom look up table to compensate for latitude
      # And convert them into angular limits for delta by also multiplying by delta_limit_pixels
      for entry in adjusted_scales:
         entry[1] = entry[1] * scale_multiplier_lat * self.delta_limit_pixels
      # Now set map zoom based on delta between base and beacon
      if (self.delta > adjusted_scales[0][1]): # Is delta greater than the useful radius for zoom 1?
         self.zoom = str('0') # If it is: set zoom 0
      else:
         # Else: set zoom to the lowest zoom level which will display this delta
         # Only zoom out, don't zoom in
         min_zoom = int(adjusted_scales[np.where(self.delta<=adjusted_scales[:,1])][-1][0])
         if min_zoom < int(self.zoom):
            self.zoom = str(min_zoom)

   def update_map(self):
      ''' Show base location, beacon locations and the beacon routes using Google Static Maps API '''

      self.writeToConsole(self.console_1, 'Updating map') # Update message console      

      # Assemble map center
      center = ("%.6f"%self.map_lat) + ',' + ("%.6f"%self.map_lon)

      # Update the Google Maps API StaticMap URL
      self.path_url = 'https://maps.googleapis.com/maps/api/staticmap?center=' # 54 chars
      self.path_url += center # 22 chars
      if self.base_location.get() != '': # Do we have a valid base location?
         self.path_url += '&markers=color:' + self.base_colour + '|' + self.base_location.get() # 15+6+3+22 chars
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
         urllib.urlretrieve(self.path_url, filename) # Attempt map image download
         # Enable zoom buttons and mouse clicks since valid map was downloaded
         self.zoom_in_button.config(state='normal') # Enable zoom+
         self.zoom_out_button.config(state='normal') # Enable zoom-
         self.enable_clicks = True # Enable mouse clicks
      except:
         self.writeToConsole(self.console_1, 'Map image download failed!') # Update message console
         # Check if we have any offline files
         if (self.tile_num > 0):
            # we have offline tiles so choose the one closest to the map center
            distances = []
            for tile in range(self.tile_num):
               distances.append(self.calculate_delta(math.radians(self.map_lat),math.radians(self.map_lon),math.radians(self.tile_lats[tile]),math.radians(self.tile_lons[tile])) * 6378137.)
            distances = np.array(distances) # convert to numpy array for argmin
            tile = distances.argmin()
            # copy chosen tile into map_image.png
            copyfile(self.tile_filenames[tile], 'map_image.png')
            # update map lat, lon and zoom
            self.map_lat = self.tile_lats[tile]
            self.map_lon = self.tile_lons[tile]
            self.zoom = self.tile_zooms[tile]
            # add markers to image
            # https://infohost.nmt.edu/tcc/help/pubs/pil/image-draw.html
            # open the image
            im = Image.open("map_image.png").convert("RGBA")
            draw = ImageDraw.Draw(im) # instantiate the Draw object
            if self.base_location.get() != '': # check if base location is known
               base_lat,base_lon = self.base_location.get().split(',') # get base lat and lon
               base_lat = float(base_lat) # convert lat to float
               base_lon = float(base_lon) # convert lon to float
               pixel_scale = self.scales[np.where(self.scales[:,0]==float(self.zoom))][0][1]
               x_dist = base_lon - self.map_lon # calculate x offset from tile centre in degrees
               x_dist = x_dist / pixel_scale # convert x offset into pixels
               pixel_scale = pixel_scale * math.cos(math.radians(self.map_lat)) # Adjust the pixel scale to compensate for latitude
               y_dist = base_lat - self.map_lat # calculate y offset from tile centre in degrees
               y_dist = y_dist / pixel_scale # convert y offset into pixels
               # check if the base can be shown on this tile
               if (abs(y_dist) < ((self.frame_height / 2) - (2 * self.offline_marker_radius))) and (abs(x_dist) < ((self.frame_width / 2) - (2 * self.offline_marker_radius))):
                  # calculate the bounding box top left
                  bby = int((self.frame_height / 2) - (y_dist + self.offline_marker_radius))
                  bbx = int((self.frame_width / 2) + x_dist - self.offline_marker_radius)
                  # add the marker (circle)
                  draw.ellipse([(bbx,bby),((bbx + (2 * self.offline_marker_radius)),(bby + (2 * self.offline_marker_radius)))],fill=self.base_colour,outline="black")
            if self.beacons > 0: # Do we have any valid beacons?
               for beacon in range(self.beacons):
                  beacon_lat,beacon_lon = self.beacon_locations[beacon].split(',') # get beacon lat and lon
                  beacon_lat = float(beacon_lat) # convert lat to float
                  beacon_lon = float(beacon_lon) # convert lon to float
                  pixel_scale = self.scales[np.where(self.scales[:,0]==float(self.zoom))][0][1]
                  x_dist = beacon_lon - self.map_lon # calculate x offset from tile centre in degrees
                  x_dist = x_dist / pixel_scale # convert x offset into pixels
                  pixel_scale = pixel_scale * math.cos(math.radians(self.map_lat)) # Adjust the pixel scale to compensate for latitude
                  y_dist = beacon_lat - self.map_lat # calculate y offset from tile centre in degrees
                  y_dist = y_dist / pixel_scale # convert y offset into pixels
                  # check if the beacon can be shown on this tile
                  if (abs(y_dist) < ((self.frame_height / 2) - (2 * self.offline_marker_radius))) and (abs(x_dist) < ((self.frame_width / 2) - (2 * self.offline_marker_radius))):
                     # calculate the bounding box top left
                     bby = int((self.frame_height / 2) - (y_dist + self.offline_marker_radius))
                     bbx = int((self.frame_width / 2) + x_dist - self.offline_marker_radius)
                     # add the marker (circle)
                     draw.ellipse([(bbx,bby),((bbx + (2 * self.offline_marker_radius)),(bby + (2 * self.offline_marker_radius)))],fill=self.beacon_colours[beacon],outline="black")
            del draw
            # save the image
            im.save("map_image.png")
            # Disable zoom buttons only as we are using offline maps
            self.zoom_in_button.config(state='disabled') # Disable zoom+
            self.zoom_out_button.config(state='disabled') # Disable zoom-
            self.enable_clicks = True # Enable mouse clicks
            self.writeToConsole(self.console_1, 'Using offline map tile') # Update message console
         else:
            # No offline files available so default to blank image
            filename = "map_image_blank.png"
            # Disable zoom buttons and mouse clicks as there is no map image to display
            self.zoom_in_button.config(state='disabled') # Disable zoom+
            self.zoom_out_button.config(state='disabled') # Disable zoom-
            self.enable_clicks = False # Disable mouse clicks

      # Update label using image
      image = Image.open(filename)
      photo = ImageTk.PhotoImage(image)
      self.label.configure(image=photo)
      self.image = photo
      
      # Update window
      self.window.update()

   def zoom_map_in(self):
      ''' Zoom in '''
      self.writeToConsole(self.console_1, 'Zooming in') # Update message console      
      # Increment zoom if zoom is less than 21
      if int(self.zoom) < 21:
         self.zoom = str(int(self.zoom) + 1)
         self.update_map()

   def zoom_map_out(self):
      ''' Zoom out '''
      self.writeToConsole(self.console_1, 'Zooming out') # Update message console      
      # Decrement zoom if zoom is greater than 0
      if int(self.zoom) > 0:
         self.zoom = str(int(self.zoom) - 1)
         self.update_map()

   def left_click(self, event):
      ''' Left mouse click - move map based on click position '''
      self.writeToConsole(self.console_1, 'Moving map') # Update message console      
      self.image_click(event, 'left')

   def right_click(self, event):
      ''' Right mouse click - copy map location to clipboard '''
      self.writeToConsole(self.console_1, 'Copying location to clipboard') # Update message console      
      self.image_click(event, 'right')

   def image_click(self, event, button):
      ''' Handle mouse click event '''
      if (self.enable_clicks) and (int(self.zoom) > 0) and (int(self.zoom) <= 21): # Are clicks enabled and is zoom 1-21?
         x_move = event.x - (self.frame_width / 2) # Required x move in pixels
         y_move = event.y - (self.frame_height / 2) # Required y move in pixels
         scale_x = self.scales[np.where(int(self.zoom)==self.scales[:,0])][0][1] # Select scale from scales using current zoom
         # Compensate y scale (Mercator projection) using current latitude
         scale_multiplier_lat = math.cos(math.radians(self.map_lat))
         scale_y = scale_x * scale_multiplier_lat # Calculate y scale
         new_lat = self.map_lat - (y_move * scale_y) # Calculate new latitude
         new_lon = self.map_lon + (x_move * scale_x) # Calculate new longitude
         if button == 'left':
            self.map_lat = new_lat # Update lat
            self.map_lon = new_lon # Update lon
            self.update_map() # Update map
         else:
            # Copy the location to the clipboard so it can be pasted into (e.g.) a browser
            self.window.clipboard_clear() # Clear clipboard
            loc = ("%.6f"%new_lat) + ',' + ("%.6f"%new_lon) # Construct location
            self.window.clipboard_append(loc) # Copy location to clipboard
            self.window.update() # Update window

   def copy_location(self, ser_no):
      ''' Copy the location of the beacon with this serial number to the clipboard '''
      self.writeToConsole(self.console_1, 'Copying beacon location to clipboard') # Update message console      
      self.window.clipboard_clear() # Clear clipboard
      loc = self.beacon_locations[self.beacon_serials[ser_no]] # Get location
      self.window.clipboard_append(loc) # Copy location to clipboard
      self.window.update() # Update window
      try:
         lat,lon = loc.split(',')
         self.map_lat = float(lat)
         self.map_lon = float(lon)
         self.update_map()
      except:
         pass

   def goto_base(self):
      ''' Copy the location of the base to the clipboard and center the map on its location '''
      self.writeToConsole(self.console_1, 'Copying base location to clipboard') # Update message console      
      try:
         self.window.clipboard_clear() # Clear clipboard
         loc = self.base_location.get() # Get location
         self.window.clipboard_append(loc) # Copy location to clipboard
         self.window.update() # Update window
         lat,lon = loc.split(',')
         self.map_lat = float(lat)
         self.map_lon = float(lon)
         self.update_map()
      except:
         pass

   def flush_mt(self):
      ''' Talk to Beacon Base using serial; send flush_mt command; process response '''
      # flush_mt returns: either (only) the MTQ; or an ERROR
      # This is RockBLOCK-specific!
      if tkMessageBox.askokcancel("Flush MT Queue", "Are you sure?\nAny messages in the MT queue will be deleted!"):
         self.writeToConsole(self.console_1, 'Requesting FLUSH_MT') # Update message console      
         resp = self.writeWait(self.flush_mt_choice, self.beacon_timeout) # Send menu choice '4'; wait for response for beacon_timeout seconds
         mtq = -1
         if resp != '': # Did we get a response?
            try:
               mtq = int(resp) # Try and extract MTQ value
            except:
               # ERROR received?
               mtq = -1
            if mtq != -1:
               # Update beacon Mobile Terminated Queue length
               self.beacon_MTQ.config(state='normal')
               self.beacon_MTQ.delete(0, tk.END)
               self.beacon_MTQ.insert(0, str(mtq))
               self.beacon_MTQ.config(state='readonly')
               self.writeToConsole(self.console_1, 'Request sent') # Update message console
         else:
            self.writeToConsole(self.console_1, 'No serial data received!') # Update message console

   def writeToConsole(self, console, msg):
      ''' Write msg to the console; check if console is full; delete oldest entry if it is '''
      console.configure(state = 'normal') # Unlock console
      numlines = int(console.index('end-1line').split('.')[0]) # How many lines are already in console?
      while numlines >= self.console_height: # If console is already full
         console.delete('1.0','2.0') # Delete the first line
         numlines = int(console.index('end-1line').split('.')[0])
      if console.index('end-1c')!='1.0': # If this isn't the first line
         console.insert('end', '\n') # Append a new line character
      console.insert('end', msg) # Append the message
      console.configure(state = 'disabled') # Lock the console
      self.window.update() # Update the window
      self.fp = open(self.console_log_file, 'ab') # Open log file for append in binary mode
      self.fp.write(msg+'\n') # Write the console message to the log file
      self.fp.close() # Close the log file
    
   def writeWait(self, data, delay):
      ''' Write data to serial; wait for up to delay seconds for a reply '''
      self.ser.flushInput() # Flush serial RX buffer (delete any old responses)
      self.ser.write(data) # Send data (command)
      for i in range(4*delay): # Wait for up to delay seconds (timeout is 0.25 secs)
         resp = self.ser.read(200) # Attempt to read a 200 character reply (forcing a timeout)
         if resp != '': # If the response was non-NULL, quit the loop
            break
      if resp != '': # If the response was non-NULL, return the response
         return resp
      else: # else return NULL
         return ''

   def QUIT(self):
      ''' Quit the program '''
      # "finally:" will close the serial port and log file - no need to do it here
      if tkMessageBox.askokcancel("Quit", "Are you sure?"):
         self.window.destroy() # Destroy the window

   def close(self):
      ''' Close the program: close the serial port; make sure the log file is closed '''
      try:
         print 'Closing port...'
         self.ser.close() # Close the serial port
      except:
         pass
      try:
         print 'Making sure log file is closed...'
         self.fp.close() # Close the log file
      except:
         pass
      if self.beacons > 0:
         print 'Beacon data was logged to:'
         for beacon in range(self.beacons):
            print self.beacon_log_files[beacon]
      print 'Console messages were logged to:',self.console_log_file

if __name__ == "__main__":
   try:
      base = BeaconBase()
   finally:
      try:
         base.close()
      except:
         pass

