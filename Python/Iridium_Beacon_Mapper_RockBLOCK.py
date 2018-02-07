# -*- coding: cp1252 -*-

## Iridium 9603N Beacon Mapper for RockBLOCK .bin attachments

## Written by Paul Clark: Jan-Feb 2018.

## Builds a list of all existing SBD .bin files.
## Once per minute, checks for the appearance of a new SBD .bin file.
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

# Converters
# 0:mdates.strpdate2num('%Y%m%d%H%M%S')

import Tkinter as tk
import tkMessageBox
import tkFont
import serial
import time
import urllib
from PIL import Image, ImageTk
import math
import numpy as np
from sys import platform
import os
import matplotlib.dates as mdates

class BeaconMapper(object):

   def __init__(self):
      ''' Init BeaconMapper: check for existing SBD .bin files; read API key; set up the Tkinter window '''
      print 'Iridium Beacon Mapper for RockBLOCK'
      print

      # Default values
      self._job = None # Keep track of timer calls
      self.zoom = '15' # Default Google Maps zoom (text)
      self.default_interval = 60 # Default update interval (secs)
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
         ignore_old_files = raw_input('Do you want to ignore any existing bin files? (Y/n) : ')
      except:
         ignore_old_files = 'Y'
      if (ignore_old_files != 'Y') and (ignore_old_files != 'y') and (ignore_old_files != 'N') and (ignore_old_files != 'n'):
         ignore_old_files = 'Y'
      if (ignore_old_files == 'y'): ignore_old_files = 'Y'

      # Build a list of all existing sbd files
      for root, dirs, files in os.walk("."):
         if len(files) > 0:
            #if root != ".": # Ignore files in this directory - only process subdirectories
            #if root == ".": # Ignore subdirectories - only process this directory
               for filename in files:
                  if filename[-4:] == '.bin': # check for bin file suffix
                     longfilename = os.path.join(root, filename)
                     if (ignore_old_files == 'Y'): self.sbd.append(longfilename) # add the filename to the list
      print 'Ignoring',len(self.sbd),'existing bin files'
      print

      # Read the Google Static Maps API key
      # Create one using: https://developers.google.com/maps/documentation/static-maps/get-api-key
      try:
         with open('Google_Static_Maps_API_Key.txt', 'r') as myfile:
            self.key = myfile.read().replace('\n', '')
            myfile.close()
      except:
         print 'Could not read the Google Static Maps API key!'
         print 'Create one here: https://developers.google.com/maps/documentation/static-maps/get-api-key'
         print 'then copy and paste it into a file called Google_Static_Maps_API_Key.txt'
         raise ValueError('Could not read API Key!')

      # Set up Tkinter GUI
      self.window = tk.Tk() # Create main window
      self.window.wm_title("Iridium Beacon Mapper") # Add a title
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

      # Beacon imei
      self.beacon_imei = tk.Entry(self.toolFrame)
      self.beacon_imei.grid(row=row, column=1)
      self.beacon_imei.delete(0, tk.END)
      self.beacon_imei.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_imei_txt = tk.Label(self.toolFrame, text = 'Beacon IMEI',width=20)
      self.beacon_imei_txt.grid(row=row, column=0)
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

      # Beacon MSN
      self.beacon_msn = tk.Entry(self.toolFrame)
      self.beacon_msn.grid(row=row, column=1)
      self.beacon_msn.delete(0, tk.END)
      self.beacon_msn.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_msn_txt = tk.Label(self.toolFrame, text = 'Beacon MOMSN',width=20)
      self.beacon_msn_txt.grid(row=row, column=0)
      row += 1

      # Separator
      self.sep_2 = tk.Frame(self.toolFrame,height=1,bg='#808080',width=self.sep_width)
      self.sep_2.grid(row=row, columnspan=2)
      row += 1

      # Buttons
      self.boldFont = tkFont.Font(size=9,weight='bold')
      self.zoom_in_button = tk.Button(self.toolFrame, text="Zoom +", font=self.boldFont, width=20, height=1, command=self.zoom_map_in, state='disabled')
      self.zoom_in_button.grid(row=row,column=0)
      self.zoom_out_button = tk.Button(self.toolFrame, text="Zoom -", font=self.boldFont, width=20, height=1, command=self.zoom_map_out, state='disabled')
      self.zoom_out_button.grid(row=row+1,column=0)
      self.quit_button = tk.Button(self.toolFrame, text="Quit", font=self.boldFont, width=20, height=2, command=self.QUIT)
      self.quit_button.grid(row=row,column=1,rowspan=2)

      # Menu to list current beacon locations
      self.menubar = tk.Menu(self.window)
      self.beacon_menu = tk.Menu(self.menubar, tearoff=0)
      self.menubar.add_cascade(label="Beacon Locations", menu=self.beacon_menu)
      self.window.config(menu=self.menubar)

      # Set up next update
      self.last_update_at = time.time() # Last time an update was requested
      self.next_update_at = self.last_update_at #+ self.default_interval # Do first update after this many seconds

      # Timer
      self.window.after(2000,self.timer) # First timer event after 2 secs

      # Start GUI
      self.window.mainloop()

   def timer(self):
      ''' Timer function - calls itself repeatedly to schedule map updates '''
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
         if self.check_for_files(): # Check for new SBD files
            self.update_map() # Update the Google Static Maps image

      self._job = self.window.after(250, self.timer) # Schedule another timer event in 0.25s

   def check_for_files(self):
      ''' Check for the appearance of any new SBD .bin files and parse them '''
      new_files = False # Found any new files?
      # Identify all the sbd files again 
      for root, dirs, files in os.walk("."):
         if len(files) > 0:
            #if root != ".": # Ignore files in this directory - only process subdirectories
            #if root == ".": # Ignore subdirectories - only process this directory
               for filename in files:
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
                               usecols=(0,1,2,3,4,5,8,9,10), converters={0:mdates.strpdate2num('%Y%m%d%H%M%S')})
                        except: # Messages with RockBLOCK destination
                           try:
                              gpstime,latitude,longitude,altitude,speed,heading,pressure,temperature,battery = \
                                  np.loadtxt(longfilename, delimiter=',', unpack=True, \
                                  usecols=(1,2,3,4,5,6,9,10,11), converters={1:mdates.strpdate2num('%Y%m%d%H%M%S')})
                           except:
                              print 'Ignoring',filename
                              ignore_me = True

                        if (ignore_me == False):
                           print 'Found new SBD file from beacon IMEI',imei,'with MOMSN',msnum
                           
                           pressure = int(round(pressure)) # Convert pressure to integer
                           altitude = int(round(altitude)) # Convert altitude to integer
                           time_str = mdates.num2date(gpstime).strftime('%H:%M:%S') # Construct time
                           position_str = "{:.6f},{:.6f}".format(latitude, longitude) # Construct position

                           # Check if this new file is from a beacon imei we haven't seen before
                           if self.beacon_imeis.has_key(imei):
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
                                 self.beacon_menu.add_command(label=imei,command=lambda imei=imei: self.copy_location(imei))
                              else:
                                 # Maximum has been reached - don't process data from this beacon
                                 print 'Unable to process file: maximum number of beacons reached!'
                                 ignore_me = True # Limit reached so ignore this file

                           if (ignore_me == False):
                              # Update beacon location
                              self.beacon_locations[self.beacon_imeis[imei]] = position_str # Update location for this beacon

                              # Change beacon location background colour
                              self.beacon_location_txt.config(background=self.beacon_colours[self.beacon_imeis[imei]])
                              
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
                              self.beacon_imei.config(state='normal') # Unlock beacon_imei
                              self.beacon_imei.delete(0, tk.END) # Delete old value
                              self.beacon_imei.insert(0, imei) # Insert new imei
                              self.beacon_imei.config(state='readonly') # Lock beacon_imei
                              # Update beacon time
                              self.beacon_time.config(state='normal') # Unlock beacon_time
                              self.beacon_time.delete(0, tk.END) # Delete old value
                              self.beacon_time.insert(0, time_str) # Insert new time
                              self.beacon_time.config(state='readonly') # Lock beacon_time
                              # Update beacon location
                              self.beacon_location.config(state='normal')
                              self.beacon_location.delete(0, tk.END)
                              self.beacon_location.insert(0, position_str)
                              self.beacon_location.config(state='readonly')
                              # Update beacon_altitude
                              self.beacon_altitude.config(state='normal')
                              self.beacon_altitude.delete(0, tk.END)
                              self.beacon_altitude.insert(0, str(altitude))
                              self.beacon_altitude.config(state='readonly')
                              # Update beacon_speed
                              self.beacon_speed.config(state='normal')
                              self.beacon_speed.delete(0, tk.END)
                              self.beacon_speed.insert(0, str(speed))
                              self.beacon_speed.config(state='readonly')
                              # Update beacon_heading
                              self.beacon_heading.config(state='normal')
                              self.beacon_heading.delete(0, tk.END)
                              self.beacon_heading.insert(0, str(heading))
                              self.beacon_heading.config(state='readonly')
                              # Update beacon_pressure
                              self.beacon_pressure.config(state='normal')
                              self.beacon_pressure.delete(0, tk.END)
                              self.beacon_pressure.insert(0, str(pressure))
                              self.beacon_pressure.config(state='readonly')
                              # Update beacon_temperature
                              self.beacon_temperature.config(state='normal')
                              self.beacon_temperature.delete(0, tk.END)
                              self.beacon_temperature.insert(0, str(temperature))
                              self.beacon_temperature.config(state='readonly')
                              # Update beacon_voltage
                              self.beacon_voltage.config(state='normal')
                              self.beacon_voltage.delete(0, tk.END)
                              self.beacon_voltage.insert(0, str(battery))
                              self.beacon_voltage.config(state='readonly')
                              # Update beacon_msn
                              self.beacon_msn.config(state='normal')
                              self.beacon_msn.delete(0, tk.END)
                              self.beacon_msn.insert(0, msnum)
                              self.beacon_msn.config(state='readonly')
                              # Update Beacon Location menu
                              label_str = imei + ' : ' + position_str
                              self.beacon_menu.entryconfig(self.beacon_imeis[imei], label=label_str, background=self.beacon_colours[self.beacon_imeis[imei]])

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
         urllib.urlretrieve(self.path_url, filename) # Attempt map image download
      except:
         filename = "map_image_blank.png" # If download failed, default to blank image

      # Update label using image
      image = Image.open(filename)
      photo = ImageTk.PhotoImage(image)
      self.label.configure(image=photo)
      self.image = photo
      
      # Enable zoom buttons and mouse clicks if a map image was displayed
      if filename == "map_image.png":
         self.zoom_in_button.config(state='normal') # Enable zoom+
         self.zoom_out_button.config(state='normal') # Enable zoom-
         self.enable_clicks = True # Enable mouse clicks
      else: # Else disable them again
         self.zoom_in_button.config(state='disabled') # Disable zoom+
         self.zoom_out_button.config(state='disabled') # Disable zoom-
         self.enable_clicks = False # Disable mouse clicks

      # Update window
      self.window.update()

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

   def left_click(self, event):
      ''' Left mouse click - move map based on click position '''
      self.image_click(event, 'left')

   def right_click(self, event):
      ''' Right mouse click - copy map location to clipboard '''
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

   def copy_location(self, imei):
      ''' Copy the location of this imei to the clipboard '''
      self.window.clipboard_clear() # Clear clipboard
      loc = self.beacon_locations[self.beacon_imeis[imei]] # Get location
      self.window.clipboard_append(loc) # Copy location to clipboard
      self.window.update() # Update window
      try:
         lat,lon = loc.split(',')
         self.map_lat = float(lat)
         self.map_lon = float(lon)
         self.update_map()
      except:
         pass

   def QUIT(self):
      ''' Quit the program '''
      if tkMessageBox.askokcancel("Quit", "Are you sure?"):
         self.window.destroy() # Destroy the window

if __name__ == "__main__":
   mapper = BeaconMapper()

