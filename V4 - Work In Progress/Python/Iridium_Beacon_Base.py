# -*- coding: cp1252 -*-

## Iridium Beacon Base

## Written by Paul Clark: Dec 2017 - Jan 2018.

## This project is distributed under a Creative Commons Attribution + Share-alike (BY-SA) licence.
## Please refer to section 5 of the licence for the “Disclaimer of Warranties and Limitation of Liability”.

## Talks to an Iridium_9603N_Beacon_V4_Base via Serial.
## Displays position updates etc. using the Google Static Maps API:
## https://developers.google.com/maps/documentation/static-maps/intro
## You will need a Key to access the API. You can create one by following this link:
## https://developers.google.com/maps/documentation/static-maps/get-api-key

## The beacon sends data packets to the base via Iridium, forwarded by Rock7's RockBLOCK network.
## The serial number of the destination base is set in Iridium9603NBeacon_V4.ino

## Every 'update' seconds the GUI talks to the base beacon and:
## requests its GNSS data including time, position and altitude;
## starts an IridiumSBD session and downloads a packet from the mobile terminated queue
## (if any are present).
## If the MT queue length is greater than zero, 'update' is halved to try and clear the backlog.
## 'Update' will return to its default setting once MTQ is zero again.

## The GUI and base provide access to the RockBLOCK FLUSH_MT function, so an excess of
## unread Mobile Terminated messages can be discarded (note that you are still charged from these messages!)

## The software logs all received packets to a csv log file

## The software makes extensive use of the Google Static Map API
## The displayed map is automatically centered on the beacon position, but the center position can be
## changed by clicking in the image.
## The zoom level is set automatically to ensure both beacon and base positions are shown.
## The zoom can be changed using the buttons (but is automatically reset at the next update).

## The beacon's path is displayed as a red line on the map.
## The oldest waypoints may not be shown as the map fetch URL is limited to 8192 characters.

## The GUI uses 640x480 pixel map images. Higher resolution images are available if you have a premium plan with Google.

## The code can currently only handle data from a single beacon. A future upgrade will add support for multiple beacons.

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

class BeaconBase(object):

   def __init__(self):
      ''' Init BeaconBase: read API key; open the serial port; set up the Tkinter window '''
      print 'Iridium 9603N Beacon Base'
      print

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
         defcom = '/dev/ttyAMA0'
      elif platform.startswith('darwin'):
         # OS X
         defcom = '/dev/tty.usbmodem'
      elif platform.startswith('win'):
         # Windows...
         defcom = 'COM4'
      else:
         defcom = 'COM1'
      
      com_port = raw_input('Which serial port do you want to use (default '+defcom+')? ')
      if com_port == '': com_port = defcom
      print

      # Open port
      try:
         self.ser = serial.Serial(com_port, 115200, timeout=0.25)
      except:
         raise NameError('COULD NOT OPEN SERIAL PORT!')
      self.ser.flushInput() # Flush RX buffer

      # Defaults
      self.zoom = '0' # Default Google Maps zoom (text)
      self.default_interval = 120 # Default update interval (secs)
      self.last_update_at = time.time() # Last time an update was requested
      self.next_update_at = self.last_update_at + 1 # Do first update after this many seconds
      self.beacon_timeout = 65 # Default timeout for Iridium comms (needs to be > IridiumSBD.adjustSendReceiveTimeout)
      self.gnss_timeout = 35 # Default timeout for GNSS update (needs to be > timeout in Iridium9603NBeacon_V4_Base)
      self.log_file = '' # Log file name
      self.path = '' # Beacon path for Static Map
      self.console_height = 2 # Serial console window height in lines
      self.sep_width = 304 # Separator width in pixels
      self.map_lat = 0.0 # Map latitude (degrees)
      self.map_lon = 0.0 # Map longitude (degrees)
      self.frame_height = 480
      self.frame_width = 640
      self.base_choice = '1\r' # Send this choice to the beacon base to request the base GNSS position etc.
      self.beacon_choice = '3\r' # Send this choice to the beacon base to request the beacon data via Iridium
      self.flush_mt_choice = '4\r' # Send this choice to the beacon base to request a flush of the mobile terminated queue

      # Ask the user to confirm the update interval
      new_interval = 0
      try:
         new_interval = int(raw_input('What update interval would you like to use (default '+str(self.default_interval)+')? '))
      except:
         new_interval = 0
      if new_interval > 0: self.default_interval = new_interval
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
      self.label.bind("<Button 1>",self.image_click) # Mouseclick event

      # Numpy array to hold useful radii vs Google Static Map zoom level
      self.zooms = np.array([   # Useful radius (at 55 degrees north) is approximately:
      [1,60],              # Zoom 1: 60 degrees
      [2,30],              # Zoom 2: 30 degrees
      [3,15],              # Zoom 3: 15 degrees
      [4,9.0],             # Zoom 4: 9.0 degrees
      [5,4.8],             # Zoom 5: 4.8 degrees
      [6,2.4],             # Zoom 6: 2.4 degrees
      [7,1.2],             # Zoom 7: 1.2 degrees
      [8,0.6],             # Zoom 8: 0.6 degrees
      [9,0.3],             # Zoom 9: 0.3 degrees
      [10,0.15],           # Zoom 10: 0.15 degrees
      [11,0.075],          # Zoom 11: 0.075 degrees
      [12,0.04],           # Zoom 12: 0.04 degrees
      [13,0.02],           # Zoom 13: 0.02 degrees
      [14,0.01],           # Zoom 14: 0.01 degrees
      [15,0.005],          # Zoom 15: 0.005 degrees
      [16,0.0025],         # Zoom 16: 0.0025 degrees
      [17,0.00125],        # Zoom 17: 0.00125 degrees
      [18,0.000625],       # Zoom 18: 0.000625 degrees
      [19,0.000312],       # Zoom 19: 0.000312 degrees
      [20,0.00015],        # Zoom 20: 0.00015 degrees
      [21,0.000075]])      # Zoom 21: 0.000075 degrees

      # Pixel scales to help with map moves
      # https://gis.stackexchange.com/questions/7430/what-ratio-scales-do-google-maps-zoom-levels-correspond-to
      self.scales = np.array([
         [21,564.24861],
         [20,1128.497220],
         [19,2256.994440],
         [18,4513.988880],
         [17,9027.977761],
         [16,18055.955520],
         [15,36111.911040],
         [14,72223.822090],
         [13,144447.644200],
         [12,288895.288400],
         [11,577790.576700],
         [10,1155581.153000],
         [9,2311162.307000],
         [8,4622324.614000],
         [7,9244649.227000],
         [6,18489298.450000],
         [5,36978596.910000],
         [4,73957193.820000],
         [3,147914387.600000],
         [2,295828775.300000],
         [1,591657550.500000]])
      self.scale_multiplier = 1.18358396586e-09 # By trial

      row = 0

      # Update interval
      self.interval = tk.Entry(self.toolFrame) # Create an entry
      self.interval.grid(row=row, column=1) # Assign its position
      self.interval.delete(0, tk.END) # Delete any existing text (redundant?)
      self.interval.insert(0, str(self.default_interval)) # Insert default value
      self.interval.config(justify=tk.CENTER,width=22,state='readonly') # Configure and make readonly
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
      self.base_time.insert(0, '00:00:00')
      self.base_time.config(justify=tk.CENTER,width=22,state='readonly')
      self.base_time_txt = tk.Label(self.toolFrame, text = 'Base time',width=20)
      self.base_time_txt.grid(row=row, column=0)
      row += 1

      # Base location
      self.base_location = tk.Entry(self.toolFrame)
      self.base_location.grid(row=row, column=1)
      self.base_location.delete(0, tk.END)
      self.base_location.insert(0, '0.0,0.0')
      self.base_location.config(justify=tk.CENTER,width=22,state='readonly')
      self.base_location_txt = tk.Label(self.toolFrame, text = 'Base location',width=20)
      self.base_location_txt.grid(row=row, column=0)
      self.base_location_txt.config(background='#99CCFF')
      row += 1

      # Base altitude
      self.base_altitude = tk.Entry(self.toolFrame)
      self.base_altitude.grid(row=row, column=1)
      self.base_altitude.delete(0, tk.END)
      self.base_altitude.insert(0, '0')
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
      self.beacon_time.insert(0, '00:00:00')
      self.beacon_time.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_time_txt = tk.Label(self.toolFrame, text = 'Beacon time',width=20)
      self.beacon_time_txt.grid(row=row, column=0)
      row += 1

      # Beacon location
      self.beacon_location = tk.Entry(self.toolFrame)
      self.beacon_location.grid(row=row, column=1)
      self.beacon_location.delete(0, tk.END)
      center = str(self.map_lat) + ',' + str(self.map_lon)
      self.beacon_location.insert(0, center)
      self.beacon_location.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_location_txt = tk.Label(self.toolFrame, text = 'Beacon location',width=20)
      self.beacon_location_txt.grid(row=row, column=0)
      self.beacon_location_txt.config(background='#FF6666')
      row += 1

      # Beacon altitude
      self.beacon_altitude = tk.Entry(self.toolFrame)
      self.beacon_altitude.grid(row=row, column=1)
      self.beacon_altitude.delete(0, tk.END)
      self.beacon_altitude.insert(0, '0')
      self.beacon_altitude.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_altitude_txt = tk.Label(self.toolFrame, text = 'Beacon altitude (m)',width=20)
      self.beacon_altitude_txt.grid(row=row, column=0)
      row += 1

      # Beacon speed
      self.beacon_speed = tk.Entry(self.toolFrame)
      self.beacon_speed.grid(row=row, column=1)
      self.beacon_speed.delete(0, tk.END)
      self.beacon_speed.insert(0, '0.0')
      self.beacon_speed.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_speed_txt = tk.Label(self.toolFrame, text = 'Beacon speed (m/s)',width=20)
      self.beacon_speed_txt.grid(row=row, column=0)
      row += 1

      # Beacon heading
      self.beacon_heading = tk.Entry(self.toolFrame)
      self.beacon_heading.grid(row=row, column=1)
      self.beacon_heading.delete(0, tk.END)
      self.beacon_heading.insert(0, '0')
      self.beacon_heading.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_heading_txt = tk.Label(self.toolFrame, text = ("Beacon track ("+u"\u00b0"+")"),width=20)
      self.beacon_heading_txt.grid(row=row, column=0)
      row += 1

      # Beacon pressure
      self.beacon_pressure = tk.Entry(self.toolFrame)
      self.beacon_pressure.grid(row=row, column=1)
      self.beacon_pressure.delete(0, tk.END)
      self.beacon_pressure.insert(0, '00000')
      self.beacon_pressure.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_pressure_txt = tk.Label(self.toolFrame, text = 'Beacon pressure (Pa)',width=20)
      self.beacon_pressure_txt.grid(row=row, column=0)
      row += 1

      # Beacon temperature
      self.beacon_temperature = tk.Entry(self.toolFrame)
      self.beacon_temperature.grid(row=row, column=1)
      self.beacon_temperature.delete(0, tk.END)
      self.beacon_temperature.insert(0, '0.0')
      self.beacon_temperature.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_temperature_txt = tk.Label(self.toolFrame, text = ("Beacon temperature ("+u"\u2103"+")"),width=20)
      self.beacon_temperature_txt.grid(row=row, column=0)
      row += 1

      # Beacon voltage
      self.beacon_voltage = tk.Entry(self.toolFrame)
      self.beacon_voltage.grid(row=row, column=1)
      self.beacon_voltage.delete(0, tk.END)
      self.beacon_voltage.insert(0, '0.0')
      self.beacon_voltage.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_voltage_txt = tk.Label(self.toolFrame, text = 'Beacon voltage (V)',width=20)
      self.beacon_voltage_txt.grid(row=row, column=0)
      row += 1

      # Beacon Mobile Terminated Queue length (normally zero; higher values indicate a backlog of data)
      self.beacon_MTQ = tk.Entry(self.toolFrame)
      self.beacon_MTQ.grid(row=row, column=1)
      self.beacon_MTQ.delete(0, tk.END)
      self.beacon_MTQ.insert(0, '0')
      self.beacon_MTQ.config(justify=tk.CENTER,width=22,state='readonly')
      self.beacon_MTQ_txt = tk.Label(self.toolFrame, text = 'Beacon MT queue',width=20)
      self.beacon_MTQ_txt.grid(row=row, column=0)
      row += 1

      # Beacon serial number
      self.beacon_serial_no = tk.Entry(self.toolFrame)
      self.beacon_serial_no.grid(row=row, column=1)
      self.beacon_serial_no.delete(0, tk.END)
      self.beacon_serial_no.insert(0, '0')
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
      self.distance_to_beacon.insert(0, '0.0')
      self.distance_to_beacon.config(justify=tk.CENTER,width=22,state='readonly')
      self.distance_to_beacon_txt = tk.Label(self.toolFrame, text = 'Distance to Beacon (m)',width=20)
      self.distance_to_beacon_txt.grid(row=row, column=0)
      row += 1

      # Heading to beacon
      self.heading_to_beacon = tk.Entry(self.toolFrame)
      self.heading_to_beacon.grid(row=row, column=1)
      self.heading_to_beacon.delete(0, tk.END)
      self.heading_to_beacon.insert(0, '0')
      self.heading_to_beacon.config(justify=tk.CENTER,width=22,state='readonly')
      self.heading_to_beacon_txt = tk.Label(self.toolFrame, text = ("Heading to Beacon ("+u"\u00b0"+")"),width=20)
      self.heading_to_beacon_txt.grid(row=row, column=0)
      row += 1

      # Serial console - used to display base_location serial data from Beacon
      self.console_1 = tk.Text(self.toolFrame)
      self.console_1.grid(row=row,columnspan=2)
      self.console_1.config(width=42,height=self.console_height,wrap='none',state='disabled')
      row += 1

      # Serial console - used to display beacon_location serial data from Beacon
      self.console_2 = tk.Text(self.toolFrame)
      self.console_2.grid(row=row,columnspan=2)
      self.console_2.config(width=42,height=self.console_height,wrap='none',state='disabled')
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

      # Timer
      self.window.after(0,self.timer)

      # Start GUI
      self.window.mainloop()

   def timer(self):
      ''' Timer function - calls itself repeatedly to schedule data collection and map updates '''
      do_update = False # Is it time to do an update?
      now = time.time() # Get the current time
      self.time_since_last_update.configure(state='normal') # Unlock entry box
      try: # Try and read the update interval
         interval = float(self.interval.get())
      except:
         raise ValueError('Invalid Interval!')
      time_since_last_update = now - self.last_update_at # Calculate interval since last update
      self.time_since_last_update.delete(0, tk.END) # Delete existing value
      if (now < self.next_update_at): # Is it time for the next update?
         # If it isn't yet time for an update, update the indicated time since last update
         self.time_since_last_update.insert(0, str(int(time_since_last_update)))
      else:
         # If it is time for an update: reset time since last update; set time for next update
         self.time_since_last_update.insert(0, '0') # Reset time since last update
         self.last_update_at = self.next_update_at # Update time of last update
         self.next_update_at = self.next_update_at + interval # Set time for next update
         do_update = True # Do update
      self.time_since_last_update.config(state='readonly') # Lock entry box

      if do_update: # If it is time to do an update
         self.get_base_location() # Read 'base_location' from Beacon Base GNSS
         self.get_beacon_data() # Contact Iridium and download a new message (if available)
         self.distance_to() # Update distance
         self.heading_to() # Update heading
         self.update_zoom() # Update zoom
         self.update_map() # Update the Google Static Maps image
         # Enable zoom buttons now that map has been displayed
         self.zoom_in_button.config(state='normal')
         self.zoom_out_button.config(state='normal')
      
      self.window.after(250, self.timer) # Schedule another timer event in 0.25s

   def distance_to(self):
      ''' Calculate distance. Gratefully plagiarised from Mikal Hart's TinyGPS. '''
      # Calculate the great circle distance between 'base_location' and 'beacon_location'
      # See https://en.wikipedia.org/wiki/Great-circle_distance#Computational_formulas
      try: # Read base_location from entry box
         lat1,long1 = self.base_location.get().split(',')
         lat1 = math.radians(float(lat1))
         long1 = math.radians(float(long1))
      except:
         raise ValueError('Invalid base_Location!')
      try: # Read beacon_location from entry box
         lat2,long2 = self.beacon_location.get().split(',')
         lat2 = math.radians(float(lat2))
         long2 = math.radians(float(long2))
      except:
         raise ValueError('Invalid Beacon_Location!')
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
      self.delta = math.degrees(delta)
      self.distance_to_beacon.configure(state='normal') # Unlock entry box
      self.distance_to_beacon.delete(0,tk.END) # Delete old distance
      self.distance_to_beacon.insert(0,str(int(delta * 6372795.))) # Set distance
      self.distance_to_beacon.configure(state='readonly') # Lock entry box

   def heading_to(self):
      ''' Calculate heading. Gratefully plagiarised from Mikal Hart's TinyGPS. '''
      try: # Read base_location from entry box
         lat1,long1 = self.base_location.get().split(',')
         lat1 = math.radians(float(lat1))
         long1 = math.radians(float(long1))
      except:
         raise ValueError('Invalid base_Location!')
      try: # Read beacon_location from entry box
         lat2,long2 = self.beacon_location.get().split(',')
         lat2 = math.radians(float(lat2))
         long2 = math.radians(float(long2))
      except:
         raise ValueError('Invalid Beacon_Location!')
      dlon = long2-long1
      a1 = math.sin(dlon) * math.cos(lat2)
      a2 = math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
      a2 = math.cos(lat1) * math.sin(lat2) - a2
      a2 = math.atan2(a1, a2)
      if (a2 < 0.): a2 += math.pi + math.pi
      self.heading_to_beacon.configure(state='normal') # Unlock entry box
      self.heading_to_beacon.delete(0, tk.END) # Delete old heading
      self.heading_to_beacon.insert(0, str(int(math.degrees(a2)))) # Set heading
      self.heading_to_beacon.configure(state='readonly') # Lock entry box

   def update_zoom(self):
      ''' Update Google StaticMap zoom based on angular separation of base_location and beacon_location '''
      # ** Run after distance_to() : requires updated self.delta **
      # Delta is the angular separation of base_location and beacon_location

      if (self.delta > self.zooms[0][1]): # Is delta greater than the useful radius for zoom 1?
         self.zoom = str('0') # If it is: set zoom 0
      else: # Else: set zoom to the lowest zoom level which will display this delta
         self.zoom = str(int(self.zooms[np.where(self.delta<=self.zooms[:,1])][-1][0]))

   def update_map(self):
      ''' Show base_location, beacon_location and the beacon route using Google Maps API StaticMap '''
      
      # Assemble map center
      center = str(self.map_lat) + ',' + str(self.map_lon)

      # Get marker locations
      try:
         red = str(self.beacon_location.get()) # Put a red marker at the beacon location
      except:
         raise ValueError('Incorrect Beacon_Location!')
      try:
         blue = str(self.base_location.get()) # Put a blue marker at base_location
      except:
         raise ValueError('Incorrect base_Location!')

      def assemble_url(self, center, red, blue):
         ''' Assemble the URL for the Google StaticMap API '''
         # Update the Google Maps API StaticMap URL
         # Centered on center position
         # Use red marker to show beacon position
         # Use blue marker to show base position
         # Show the beacon path in red
         # Include the calculate zoom
         self.path_url = "https://maps.googleapis.com/maps/api/staticmap?center="
         self.path_url += center
         self.path_url += "&markers=color:red|"
         self.path_url += red
         self.path_url += "&markers=color:blue|"
         self.path_url += blue
         if self.path != '':
            self.path_url += "&path=color:red|weight:5"
            self.path_url += self.path
         self.path_url += "&zoom="
         self.path_url += self.zoom
         self.path_url += "&size="
         self.path_url += str(self.frame_width)
         self.path_url += "x"
         self.path_url += str(self.frame_height)
         self.path_url += "&maptype=hybrid&format=png&key="
         self.path_url += self.key

      # Assemble URL - check it for length, truncate if necessary
      assemble_url(self,center,red,blue)
      while len(self.path_url) > 8192: # Google allows URLs of up to 8192 characters
         self.path = self.path[1:] # Truncate path: delete first '|'
         self.path = self.path[(self.path.find('|')):] # Delete up to next '|'
         assemble_url(self,center,red,blue)

      # Update the URL for Google Maps
      self.map_url = "https://www.google.com/maps/search/?api=1&map_action=map&query="
      self.map_url += red

      # Copy the Google Maps URL to the clipboard so it can be pasted into a browser
      self.window.clipboard_clear()
      self.window.clipboard_append(self.map_url)
      self.window.update()

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

   def image_click(self, event):
      ''' Move map based on where image was clicked '''
      if (int(self.zoom) > 0) and (int(self.zoom) <= 21): # Is zoom 1-21?
         x_move = event.x - (self.frame_width / 2) # Required x move in pixels
         y_move = event.y - (self.frame_height / 2) # Required y move in pixels
         scale = self.scales[np.where(int(self.zoom)==self.scales[:,0])][0][1] # Select scale from scales using current zoom
         scale_x = scale * self.scale_multiplier # Calculate x scale
         # Compensate y scale (Mercator projection) using current latitude
         scale_multiplier_lat = math.sin(abs(math.radians(self.map_lat))) / math.tan(abs(math.radians(self.map_lat)))
         scale_y = scale * self.scale_multiplier * scale_multiplier_lat # Calculate y scale
         self.map_lat = self.map_lat - (y_move * scale_y) # Calculate new latitude
         self.map_lon = self.map_lon + (x_move * scale_x) # Calculate new longitude
         self.update_map() # Update map

   def flush_mt(self):
      ''' Talk to Beacon Base using serial; send flush_mt command; process response '''
      # flush_mt returns: either (only) the MTQ; or an ERROR
      # This is RockBLOCK-specific!
      if tkMessageBox.askokcancel("Flush MT Queue", "Are you sure?\nAny messages in the MT queue will be deleted!"):
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
               # If MTQ is > zero (i.e. there is a backlog of messages to be downloaded)
               # halve the interval to the next update (to gradually reduce MTQ)
               # else use the default interval
               self.interval.config(state='normal')
               self.interval.delete(0, tk.END)
               if int(self.beacon_MTQ.get()) > 0:
                  self.interval.insert(0, str(self.default_interval / 2))
                  self.next_update_at = self.last_update_at + (self.default_interval / 2)
               else:
                  self.interval.insert(0, str(self.default_interval))
                  self.next_update_at = self.last_update_at + self.default_interval
               self.interval.config(state='readonly')
         

   def get_base_location(self):
      ''' Talk to Beacon Base using serial; get current location (base_location) '''
      resp = self.writeWait(self.base_choice, self.gnss_timeout) # Send menu choice '1'; wait for response for gnss_timeout seconds
      if resp != '': # Did we get a response?
         try:
            self.writeToConsole(self.console_1,resp[:-2],'#0000FF') # If we did, copy it into the console
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
                     self.base_location.config(state='normal') # Unlock base_location
                     self.base_location.delete(0, tk.END) # Delete old value
                     self.base_location.insert(0, base_location) # Insert new location
                     self.base_location.config(state='readonly') # Lock base_location
                     self.base_altitude.config(state='normal') # Unlock base_altitude
                     self.base_altitude.delete(0, tk.END) # Delete old value
                     self.base_altitude.insert(0, parse[3]) # Insert new altitude
                     self.base_altitude.config(state='readonly') # Lock base_altitude
               except: # If parse failed, do nothing
                  pass

   def get_beacon_data(self):
      ''' Talk to Beacon Base using serial; start Iridium session and download new data '''
      # Base will respond with:
      # beacon data followed by ',' and the MT queue length;
      # (only) the MT queue length (if there was no data waiting to be downloaded);
      # an error message starting with "ERROR".
      resp = self.writeWait(self.beacon_choice, self.beacon_timeout) # Send menu choice '3'; wait for response for beacon_timeout secs
      if resp != '': # Did we get a response?
         try:
            self.writeToConsole(self.console_2,resp[:-2],'#FF0000') # If we did, copy it into the console
         except:
            pass
         if len(resp) >= 8: # Check length is non-trivial
            if (resp[0:5] != 'ERROR'): # Check if an error message was received
               # If the response wasn't an error:
               try:
                  parse = resp[:-2].split(',') # Try parsing the response
                  # If the parse was successful, check that the length of the first field (DateTime) is correct
                  if (len(parse) >= 14) and (len(parse[0]) == 14): # DateTime should always be 14 characters
                     # If DateTime is the correct length, assume the rest of the response contains valid data
                     # Construct 'base_time' in HH:MM:SS format
                     time_str = parse[0][8:10] + ':' + parse[0][10:12] + ':' + parse[0][12:]
                     self.beacon_time.config(state='normal') # Unlock beacon_time
                     self.beacon_time.delete(0, tk.END) # Delete old value
                     self.beacon_time.insert(0, time_str) # Insert new time
                     self.beacon_time.config(state='readonly') # Lock beacon_time
                     # Construct 'beacon_location' in lat,lon (float) format
                     self.map_lat = float(parse[1])
                     self.map_lon = float(parse[2])
                     beacon_location = parse[1] + ',' + parse[2]
                     self.beacon_location.config(state='normal')
                     self.beacon_location.delete(0, tk.END)
                     self.beacon_location.insert(0, beacon_location)
                     self.beacon_location.config(state='readonly')
                     # Update beacon path (append this location to the path)
                     self.path += '|' + beacon_location
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
                     # Update beacon Mobile Terminated Queue length
                     self.beacon_MTQ.config(state='normal')
                     self.beacon_MTQ.delete(0, tk.END)
                     self.beacon_MTQ.insert(0, parse[13])
                     self.beacon_MTQ.config(state='readonly')
                     # If MTQ is > zero (i.e. there is a backlog of messages to be downloaded)
                     # halve the interval to the next update (to gradually reduce MTQ)
                     # else use the default interval
                     self.interval.config(state='normal')
                     self.interval.delete(0, tk.END)
                     if int(self.beacon_MTQ.get()) > 0:
                        self.interval.insert(0, str(self.default_interval / 2))
                        self.next_update_at = self.last_update_at + (self.default_interval / 2)
                     else:
                        self.interval.insert(0, str(self.default_interval))
                        self.next_update_at = self.last_update_at + self.default_interval
                     self.interval.config(state='readonly')
                     # Check if the log file is empty (file name is NULL)
                     if self.log_file == '':
                        # Create and clear the log file
                        # Construct the filename from the beacon GNSS datetime and the beacon serial number
                        self.log_file = 'Beacon_Log_' + parse[0][0:8] + '_' + parse[0][8:] + '_' + parse[12] + '.csv'
                        self.fp = open(self.log_file, 'wb') # Create / clear the file
                        self.fp.close()
                     # Now that the log file exists, append the new beacon data
                     self.fp = open(self.log_file, 'ab') # Open log file for append in binary mode
                     self.fp.write(resp) # Write the beacon response to the log file
                     self.fp.close() # Close the log file
               except:
                  pass
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
               # If MTQ is > zero (i.e. there is a backlog of messages to be downloaded)
               # halve the interval to the next update (to gradually reduce MTQ)
               # else use the default interval
               self.interval.config(state='normal')
               self.interval.delete(0, tk.END)
               if int(self.beacon_MTQ.get()) > 0:
                  self.interval.insert(0, str(self.default_interval / 2))
                  self.next_update_at = self.last_update_at + (self.default_interval / 2)
               else:
                  self.interval.insert(0, str(self.default_interval))
                  self.next_update_at = self.last_update_at + self.default_interval
               self.interval.config(state='readonly')

   def writeToConsole(self, console, msg, color='#FFFFFF'):
      ''' Write msg to the console; check if console is full; delete oldest entry if it is '''
      console.configure(state = 'normal') # Unlock console
      console.configure(foreground=color) # Set text color
      numlines = int(console.index('end-1line').split('.')[0]) # How many lines are already in console?
      while numlines >= self.console_height: # If console is already full
         console.delete('1.0','2.0') # Delete the first line
         numlines = int(console.index('end-1line').split('.')[0])
      if console.index('end-1c')!='1.0': # If this isn't the first line
         console.insert('end', '\n') # Append a new line character
      console.insert('end', msg) # Append the message
      console.configure(state = 'disabled') # Lock the console
    
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
      print 'Beacon data was logged to:',self.log_file

if __name__ == "__main__":
   try:
      base = BeaconBase()
   finally:
      try:
         base.close()
      except:
         pass

