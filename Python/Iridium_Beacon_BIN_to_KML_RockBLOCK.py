# Converts Iridium Beacon .bin files into .kml files for GoogleEarth

# With thanks to Kyle Lancaster for simplekml:
# http://simplekml.readthedocs.io/en/latest/index.html
# https://pypi.python.org/pypi/simplekml

# Searches through the current directory and/or sub-directories, finds all
# .bin SBD files (downloaded by Iridium_Beacon_GMail_Downloader_RockBLOCK.py)
# and converts them into .kml files showing the combined route in point,
# linestring and arrow format.
# Files from different beacons (with different IMEIs) are processed separately.

# Rock7 RockBLOCK SBD filenames have the format IMEI-MOMSN.bin where:
# IMEI is the International Mobile Equipment Identity number (15 digits)
# MOMSN is the Mobile Originated Message Sequence Number (1+ digits)
# Other Iridium service providers use different filename conventions.

# All files get processed. You will need to 'hide' files you don't
# want to process by moving them to (e.g.) a different directory.

# (Iridium_Beacon_CSV_to_KML_RockBLOCK.py does the same thing but on a .csv file
# exported from RockBLOCK Operations, allowing you to easily select which messages you
# want to process.)

# The .bin SBD files contain the following in csv format:
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

import numpy as np
import simplekml
import matplotlib.dates as mdates
import os

# list of imeis
imeis = []

# kml filenames
point_filenames = []
linestring_filenames = []
arrow_filenames = []
course_filenames= []

# kmls
point_kmls = []
linestring_kmls = []
arrow_kmls = []
course_kmls = []

# point style
style = simplekml.Style()
style.labelstyle.color = simplekml.Color.red  # Make the text red
#style.labelstyle.scale = 2  # Make the text twice as big
style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'

# arrow (heading) styles
heading_styles = []
for heading in range(361): # Create iconstyles for each heading 0:360
    heading_styles.append(simplekml.Style())
    heading_styles[-1].iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/arrow.png'
    heading_styles[-1].iconstyle.heading = (heading + 180.) % 360. # Fix arrow orientation

# coordinates for the linestring(s)
coords = []

# Identify all .bin SBD files
for root, dirs, files in os.walk("."):
    
    # Comment out the next two lines to process all files in this directory and its subdirectories
    # Uncomment one or the other to search only this directory or only subdirectories
    #if root != ".": # Ignore files in this directory - only process subdirectories
    if root == ".": # Ignore subdirectories - only process this directory

    # Uncomment and modify the next two lines to only process a single subdirectory
    #search_me = "Test_RockBLOCK_Messages" # Search this subdirectory
    #if root == os.path.join(".",search_me): # Only process files in this subdirectory
    
        if len(files) > 0:
            # Find filenames with the correct format (imei-momsn.bin)
            valid_files = [afile for afile in files if ((afile[-4:] == '.bin') and (afile[15:16] == '-'))]
        else:
            valid_files = []
        if len(valid_files) > 0:
        
            sort_by = lambda num: int(num[16:-4]) # sort numerically by momsn           
            for filename in sorted(valid_files, key=sort_by):

                longfilename = os.path.join(root, filename)
                momsn = filename[16:-4] # Get the momsn
                imei = filename[0:15] # Get the imei
                ignore_me = False # Should we ignore this file?

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
                    print 'Found SBD file from beacon IMEI',imei,'with MOMSN',momsn
                   
                    # Convert pressure into height
                    # Add height offset to compensate for local atmospheric pressure
                    # or to stop route going underground
                    height_offset = 0. 
                    height = (44330.77 * (1 - ((pressure / 101326.)**0.1902632))) + height_offset

                    # Comment the next line to use the height calculated from pressure instead of GNSS altitude
                    height = altitude

                    # Check heading is valid
                    if (heading < 0.) or (heading > 360.): heading = 0.

                    # Check if this new file is from a beacon imei we haven't seen before
                    if imei in imeis:
                        pass # We have seen this one before
                    else:
                        imeis.append(imei) # New imei so add it to the list
                        point_filenames.append('RockBLOCK_%s_points.kml'%imei) # Create the points filename
                        linestring_filenames.append('RockBLOCK_%s_flightpath.kml'%imei) # Create the linestring filename
                        course_filenames.append('RockBLOCK_%s_COG.kml'%imei) # Create the linestring filename
                        arrow_filenames.append('RockBLOCK_%s_arrows.kml'%imei) # Create the arrows filename
                        point_kmls.append(simplekml.Kml()) # Create an empty kml for the points
                        linestring_kmls.append(simplekml.Kml()) # Create an empty kml for the linestring
                        course_kmls.append(simplekml.Kml()) # Create an empty kml for the COG linestring
                        arrow_kmls.append(simplekml.Kml()) # Create an empty kml for the arrows
                        coords.append([]) # Add empty coordinates for this imei

                    index = imeis.index(imei) # Get the imei index

                    # Update point kml
                    pnt = point_kmls[index].newpoint(name=str(momsn))
                    pnt.coords=[(longitude,latitude,height)]
                    pnt.style = style
                    # Update arrow kml
                    pnt = arrow_kmls[index].newpoint(name=str(momsn))
                    pnt.coords=[(longitude,latitude,height)]
                    pnt.style = heading_styles[int(round(heading))]
                    # Add these coordinates to the linstring list
                    coords[index].append((longitude,latitude,height))

# We have finished processing the SBD files so now save the kml files for each imei
for imei in imeis:
    index = imeis.index(imei) # Get the imei index
    point_kmls[index].save(point_filenames[index]) # Save the points kml file
    arrow_kmls[index].save(arrow_filenames[index]) # Save the arrows kml file

    # Create and save the linestrings using coords
    ls = linestring_kmls[index].newlinestring()
    ls.altitudemode = simplekml.AltitudeMode.absolute # Comment this line to show route clamped to ground
    ls.coords = coords[index]
    ls.extrude = 1
    ls.tessellate = 1
    ls.style.linestyle.width = 5
    ls.style.linestyle.color = simplekml.Color.yellow
    ls.style.polystyle.color = simplekml.Color.yellow
    linestring_kmls[index].save(linestring_filenames[index])

    cls = course_kmls[index].newlinestring()
    cls.coords = coords[index]
    cls.style.linestyle.width = 5
    cls.style.linestyle.color = simplekml.Color.yellow
    cls.style.polystyle.color = simplekml.Color.yellow
    course_kmls[index].save(course_filenames[index])



           
    
