# Converts a stitched .csv file into .kml files for GoogleEarth

# The .csv file should have been processed by Iridium_Beacon_CSV_DateTime.py
# _before_ being processed by this code

# With thanks to Kyle Lancaster for simplekml:
# http://simplekml.readthedocs.io/en/latest/index.html
# https://pypi.python.org/pypi/simplekml

# Converts the processed .csv into .kml files showing the combined route in point,
# arrow and linestring (3D flightpath and course-over-ground) format.

# The .csv file contains:
# (Optional) Column 0 = The Base's RockBLOCK serial number (see Iridium9603NBeacon_V4.ino)
# Column 1 = GNSS Tx Date (DD/MM/YY)
# Column 2 = GNSS Tx Time (HH:MM:SS)
# Column 3 = GNSS Latitude (degrees) (float)
# Column 4 = GNSS Longitude (degrees) (float)
# Column 5 = GNSS Altitude (m) (int)
# Column 6 = GNSS Speed (m/s) (float)
# Column 7 = GNSS Heading (Degrees) (int)
# Column 8 = GNSS HDOP (m) (float)
# Column 9 = GNSS satellites (int)
# Coulmn 10 = Pressure (Pascals) (int)
# Column 11 = Temperature (C) (float)
# Column 12 = Battery (V) (float)
# Column 13 = Iteration Count (int)
# (Optional) Column 14 = The Beacon's RockBLOCK serial number (see Iridium9603NBeacon_V4.ino)

import csv
import simplekml
import matplotlib.dates as mdates
import os

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

longfilename = ''
resp = 'N'

# Find the csv file
for root, dirs, files in os.walk("."):
    if len(files) > 0:
        # Comment out the next two lines to process all files in this directory and its subdirectories
        # Uncomment one or the other to search only this directory or only subdirectories
        #if root != ".": # Only check sub directories
        if root == ".": # Only check this directory
            for filename in files:
                if filename[-4:] == '.csv':
                    longfilename = os.path.join(root, filename)
                    question =  'Open ' + filename + '? (Y/n) : '
                    resp = input(question)
                    if resp == '' or resp == 'Y' or resp == 'y': break
                    longfilename = ''
                if resp == '' or resp == 'Y' or resp == 'y': break
            if resp == '' or resp == 'Y' or resp == 'y': break
    if resp == '' or resp == 'Y' or resp == 'y': break
                    
if longfilename == '': raise Exception('No file to open!')

point_filename = longfilename[:-4] + '_points.kml' # Create the points filename
arrow_filename = longfilename[:-4] + '_arrows.kml'  # Create the arrows filename
linestring_filename = longfilename[:-4] + '_flightpath.kml' # Create the linestring filename
course_filename = longfilename[:-4] + '_COG.kml' # Create the linestring filename
point_kml = simplekml.Kml() # Create an empty kml for the points
arrow_kml = simplekml.Kml() # Create an empty kml for the arrows
linestring_kml = simplekml.Kml() # Create an empty kml for the flightpath linestring
course_kml = simplekml.Kml() # Create an empty kml for the COG linestring
coords = [] # Create coordinates

with open(longfilename, "r") as f:
    reader = csv.reader(f)
    for line in reader:
        if (line[0][:2] == 'RB') : # Does the message payload have an RB prefix?
            try:
                latitude = float(line[3]) # Extract the latitude
                longitude = float(line[4]) # Extract the longitude
                altitude = float(line[5]) # Extract the altitude
                heading = float(line[7]) # Extract the heading
                pressure = float(line[10]) # Extract the pressure
                count = line[13] # Extract the message count
            except:
                latitude = 0.
                longitude = 0.
        else:
            try:
                latitude = float(line[2]) # Extract the latitude
                longitude = float(line[3]) # Extract the longitude
                altitude = float(line[4]) # Extract the altitude
                heading = float(line[6]) # Extract the heading
                pressure = float(line[9]) # Extract the pressure
                count = line[12] # Extract the message count
            except:
                latitude = 0.
                longitude = 0.

        if (latitude == 0.) and (longitude == 0.): # Check lat and lon are valid
            pass
        else:
            # Convert pressure into height
            # Add height offset to compensate for local atmospheric pressure
            # or to stop route going underground
            height_offset = 0. 
            height = (44330.77 * (1 - ((pressure / 101326.)**0.1902632))) + height_offset

            # Comment the next line to use the height calculated from pressure instead of GNSS altitude
            height = altitude

            # Check heading is valid
            if (heading < 0.) or (heading > 360.): heading = 0.

            # Update point kml
            pnt = point_kml.newpoint(name=count)
            pnt.coords=[(longitude,latitude,height)]
            pnt.style = style
            # Update arrow kml
            pnt = arrow_kml.newpoint(name=count)
            pnt.coords=[(longitude,latitude,height)]
            pnt.style = heading_styles[int(round(heading))]
            # Add these coordinates to the list for the linestring
            coords.append((longitude,latitude,height))

    # We have finished processing the csv file so now save the kml files
    point_kml.save(point_filename) # Save the points kml file
    arrow_kml.save(arrow_filename) # Save the arrows kml file

    # Create and save the linestrings (flightpath and course-over-ground) using coords
    ls = linestring_kml.newlinestring()
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.coords = coords
    ls.extrude = 1
    ls.tessellate = 1
    ls.style.linestyle.width = 5
    ls.style.linestyle.color = simplekml.Color.yellow
    ls.style.polystyle.color = simplekml.Color.yellow
    linestring_kml.save(linestring_filename)

    cls = course_kml.newlinestring()
    cls.coords = coords
    cls.style.linestyle.width = 5
    cls.style.linestyle.color = simplekml.Color.yellow
    cls.style.polystyle.color = simplekml.Color.yellow
    course_kml.save(course_filename)

    f.close()




           
    
