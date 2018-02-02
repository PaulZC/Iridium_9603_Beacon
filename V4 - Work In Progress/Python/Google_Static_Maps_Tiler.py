# -*- coding: cp1252 -*-

## Google Static Maps Tiler
## Grabs the selected Google Static Map tiles

## Requires a Google Static Maps API key
## Create one using: https://developers.google.com/maps/documentation/static-maps/get-api-key
## Then copy and paste it into a file called Google_Static_Maps_API_Key.txt

import urllib
from PIL import Image, ImageTk
import math
import numpy as np

frame_height = 480 # Google Static Map window width
frame_width = 640 # Google Static Map window height
map_type = 'roadmap' # Maps can be: roadmap , satellite , terrain or hybrid

# Google static map API pixel scales
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
scales = np.array([
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
      key = myfile.read().replace('\n', '')
      myfile.close()
except:
   print 'Could not read the API key!'
   print 'Create one here: https://developers.google.com/maps/documentation/static-maps/get-api-key'
   print 'then copy and paste it into a file called Google_Static_Maps_API_Key.txt'
   raise ValueError('Could not read API Key!')

# Ask the user for the lat and lon extents and tile size
try:
   max_lat = float(raw_input('Enter the maximum (northern-most) latitude in degrees: '))
except:
   raise ValueError('Invalid value!')
if (max_lat < -90.) or (max_lat > 90.): raise ValueError('Invalid value!')
try:
   min_lat = float(raw_input('Enter the minimum (southern-most) latitude in degrees: '))
except:
   raise ValueError('Invalid value!')
if (min_lat < -90.) or (min_lat > 90.): raise ValueError('Invalid value!')
if (max_lat < min_lat): raise ValueError('Invalid value!')
try:
   min_lon = float(raw_input('Enter the minimum (western-most) longitude in degrees: '))
except:
   raise ValueError('Invalid value!')
if (min_lon < -180.) or (min_lon > 180.): raise ValueError('Invalid value!')
try:
   max_lon = float(raw_input('Enter the maximum (eastern-most) longitude in degrees: '))
except:
   raise ValueError('Invalid value!')
if (max_lon < -180.) or (max_lon > 180.): raise ValueError('Invalid value!')
if (max_lon < min_lon): raise ValueError('Invalid value!')
try:
   tile_size = float(raw_input('Enter the tile size in degrees: '))
except:
   raise ValueError('Invalid value!')

# Find the largest absolute latitude
abs_max_lat = abs(max_lat)
if abs(min_lat) > abs_max_lat: abs_max_lat = abs(min_lat)

adjusted_scales = np.array(scales) # Make a copy of the zoom vs pixel scale angle look-up table
# Calculate latitude scale multiplier based on current latitude to correct for Mercator projection
scale_multiplier_lat = math.cos(math.radians(abs_max_lat))
# Adjust the pixel scale angles in the zoom look up table to compensate for latitude
for entry in adjusted_scales:
   entry[1] = entry[1] * scale_multiplier_lat
# Calculate the maximum pixel scale required to display the full tile
min_pixel_scale = tile_size / frame_height
# Set zoom to the highest zoom level which will display the tile_size
zoom = int(adjusted_scales[np.where(min_pixel_scale<=adjusted_scales[:,1])][-1][0])

# Calculate loop limits
num_tiles_lat = int(math.ceil((max_lat - min_lat) / tile_size))
num_tiles_lon = int(math.ceil((max_lon - min_lon) / tile_size))

num_files = 0

# Loop though tiles
for lat in np.arange((min_lat + (tile_size / 2.)), ((min_lat + (tile_size / 2.)) + (num_tiles_lat * tile_size)), tile_size):
   for lon in np.arange((min_lon + (tile_size / 2.)), ((min_lon + (tile_size / 2.)) + (num_tiles_lon * tile_size)), tile_size):
   
      # Assemble map center
      center = ("%.6f"%lat) + ',' + ("%.6f"%lon)

      # Update the Google Maps API StaticMap URL
      path_url = 'https://maps.googleapis.com/maps/api/staticmap?center='
      path_url += center
      path_url += '&zoom='
      path_url += str(zoom)
      path_url += '&size='
      path_url += str(frame_width)
      path_url += 'x'
      path_url += str(frame_height)
      path_url += '&maptype=' + map_type + '&format=png&key='
      path_url += key

      # Download the API map image from Google
      filename = ("StaticMapTile_Zoom_%i"%zoom) + ("_Lat_%.2f"%lat) + ("_Lon_%.2f_.png"%lon) # Download map to this file
      try:
         urllib.urlretrieve(path_url, filename) # Attempt map image download
         print 'Downloaded: ',filename
         num_files += 1
      except:
         raise ValueError('Map tile download failed!')      

print 'Downloaded',num_files,'files'
print 'Finished!'

