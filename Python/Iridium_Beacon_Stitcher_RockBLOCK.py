# Iridium Beacon Stitcher RockBLOCK

# Stitches Iridium Beacon .bin SBD files into .csv files

# Searches through the current directory and/or sub-directories, finds all
# .bin SBD files (downloaded by Iridium_Beacon_GMail_Downloader_RockBLOCK.py)
# and converts them into .csv files.
# Files from different beacons (with different IMEIs) are processed separately.

# Rock7 RockBLOCK SBD filenames have the format IMEI-MOMSN.bin where:
# IMEI is the International Mobile Equipment Identity number (15 digits)
# MOMSN is the Mobile Originated Message Sequence Number (1+ digits)
# Other Iridium service providers use different filename conventions.

# All files get processed. You will need to 'hide' files you don't
# want to process by moving them to (e.g.) a different directory.

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
import matplotlib.dates as mdates
import os

# list of imeis
imeis = []

# csv filenames
csv_filenames = []

print 'Iridium Beacon Stitcher RockBLOCK'
print

# Ask the user if they want to Overwrite or Append existing sbd files
try:
 overwrite_files = raw_input('Do you want to Overwrite or Append_To existing csv files? (O/A) (Default: O) : ')
except:
 overwrite_files = 'O'
if (overwrite_files != 'O') and (overwrite_files != 'o') and (overwrite_files != 'A') and (overwrite_files != 'a'):
 overwrite_files = 'O'
if (overwrite_files == 'o'): overwrite_files = 'O'

print

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

                print 'Found SBD file from beacon IMEI',imei,'with MOMSN',momsn
               
                # Check if this new file is from a beacon imei we haven't seen before
                if imei in imeis:
                    pass # We have seen this one before
                else:
                    imeis.append(imei) # New imei so add it to the list
                    csv_filenames.append('RockBLOCK_%s.csv'%imei) # Create the csv filename
                    if (overwrite_files == 'O'):
                        fp = open(csv_filenames[-1],'w') # Create the csv file (clear it if it already exists)
                        fp.close()

                index = imeis.index(imei) # Get the imei index

                fp = open(csv_filenames[index],'a') # Open the csv file for append
                fr = open(longfilename,'r') # Open the SBD file for read
                fp.write(fr.read()) # Copy the SBD data into the csv file
                fp.write('\n') # Add LF
                fr.close() # Close the SBD file
                fp.close() # Close the csv file




           
    
