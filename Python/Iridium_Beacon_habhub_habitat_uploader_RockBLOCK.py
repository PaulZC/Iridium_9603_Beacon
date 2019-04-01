# Iridium 9603N Beacon HabHub Habitat Uploader for RockBLOCK

# Builds a list of all existing SBD .bin files
# Once per minute, checks for the appearance of a new SBD .bin file
# When one is found, parses the file and uploads the data to the habhub habitat

# The uploader will only upload data from the specified IMEI or the first new IMEI
# This is to avoid uploading data from multiple beacons
# (The GMail_Downloader will download all messages from all beacons)
# (The code could be updated to include a list of 'approved' IMEIs and
# associated flight callsigns)

# Rock7 RockBLOCK SBD filenames have the format IMEI-MOMSN.bin where:
# IMEI is the International Mobile Equipment Identity number (15 digits)
# MOMSN is the Mobile Originated Message Sequence Number (1+ digits)
# Other Iridium service providers use different filename conventions.

# All files get processed. You will need to 'hide' files you don't
# want to process by moving them to (e.g.) a different directory.

# The .bin SBD files contain the following in csv format:
# (Optional) Column 0 = The Base's RockBLOCK serial number (see Iridium9603NBeacon_V5.ino)
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
# (Optional) Column 13 = The Beacon's RockBLOCK serial number (see Iridium9603NBeacon_V5.ino)

# Converters
# 0:mdates.strpdate2num('%Y%m%d%H%M%S')

# To install crcmod, you may need to:
# Go to https://pypi.org/project/crcmod/#files
# Download the source tar.gz
# Extract it and cd into the folder
# sudo python setup.py install

# To install couchdb, you may need to:
# Go to https://pypi.org/project/CouchDB/#files
# Download the source tar.gz
# Extract it and cd into the folder
# sudo python setup.py install

import os
import numpy as np
import time
import matplotlib.dates as mdates
import crcmod
import base64
import hashlib
import couchdb
from datetime import datetime
import re

# https://stackoverflow.com/a/2669120
def sorted_nicely(l): 
    """ Sort the given iterable in the way that humans expect.""" 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

if __name__ == '__main__':
    try:

        print 'Iridium Beacon to habhub habitat uploader for RockBLOCK'

        # Ask the user if they want to use a particular IMEI
        try:
            upload_this_IMEI = raw_input('If you want to track a particular IMEI, enter it now: ')
        except:
            upload_this_IMEI = ""

        # Ask the user for the flight callsign
        try:
            callsign = raw_input('Enter the flight callsign: ')
        except:
            raise ValueError('Invalid callsign!')
        if callsign == "":
            raise ValueError('Invalid callsign!')

        couch = couchdb.Server('http://habitat.habhub.org/')
        db = couch['habitat']

        # Build a list of all existing SBD .bin files
        sbd = []
        print 'Searching for existing SBD .bin files...'
        num_files = 0
        last_num_files = 0
        for root, dirs, files in os.walk(".", followlinks=False):
            #if root != ".": # Ignore files in this directory - only process subdirectories
            #if root == ".": # Ignore subdirectories - only process this directory
                if num_files > last_num_files:
                    print 'Found',num_files,'SBD .bin files so far...'
                    last_num_files = num_files
                if len(files) > 0:
                    # Find filenames with the correct format (imei-momsn.bin)
                    valid_files = [afile for afile in files if ((afile[-4:] == '.bin') and (afile[15:16] == '-'))]
                else:
                    valid_files = []
                if len(valid_files) > 0:
                    for filename in sorted_nicely(valid_files):
                        num_files += 1
                        longfilename = os.path.join(root, filename)
                        sbd.append(longfilename) # add the filename to the list
        print 'Found',len(sbd),'existing sbd files'
        print 'Checking once per minute for new ones...'

        # Once per minute, check for the appearance of a new sbd file
        while (True):
            for l in range(60): # Sleep for 60x1 seconds (to allow KeyboardInterrupt to be detected quickly)
                time.sleep(1)

            # Identify all the sbd files again 
            for root, dirs, files in os.walk("."):
                #if root != ".": # Ignore files in this directory - only process subdirectories
                #if root == ".": # Ignore subdirectories - only process this directory
                    if len(files) > 0:
                        # Find filenames with the correct format (imei-momsn.bin)
                        valid_files = [afile for afile in files if ((afile[-4:] == '.bin') and (afile[15:16] == '-'))]
                    else:
                        valid_files = []
                    if len(valid_files) > 0:
                        for filename in sorted_nicely(valid_files):
                            longfilename = os.path.join(root, filename)
                            msnum = filename[16:-4] # Get the momsn
                            imei = filename[0:15] # Get the imei

                            ignore_me = False # Should we ignore this file?

                            # Check if this file is in the list
                            # If it isn't then this must be a new SBD file so try and process it
                            try:
                                index = sbd.index(longfilename)
                            except:
                                index = -1
                            if index == -1:
                                sbd.append(longfilename) # Add new filename to list so even if invalid we don't process it again

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
                                    if upload_this_IMEI == "":
                                        upload_this_IMEI = imei
                                        print 'Uploading messages from IMEI',imei

                                    if (imei == upload_this_IMEI):
                                        print 'Found new SBD file from beacon IMEI',imei,'with MOMSN',msnum
                                        pressure = int(round(pressure)) # Convert pressure to integer
                                        time_str = mdates.num2date(gpstime).strftime('%H:%M:%S,%y%m%d') # Time string (HH:MM:SS,YYMMDD)
                                        location_str = "{:.6f},{:.6f},{}".format(latitude, longitude, int(round(altitude))) # Location

                                        # Assemble the UKHAS format string
                                        ukhas_str = "{},{},{},{:.2f},{:.1f},{},{},{},{}".format( \
                                            callsign, time_str, location_str, speed, heading, pressure, temperature, battery, msnum);

                                        # Calculate checksum
                                        crc16 = crcmod.mkCrcFun(0x11021, 0xFFFF, False, 0x0000)
                                        checksum =  "{:04X}".format(crc16(ukhas_str))

                                        # Append the checksum
                                        ukhas_str = "$${}*{}".format(ukhas_str, checksum)
                                        print 'Uploading:',ukhas_str

                                        # Packet ID
                                        packet_base64 = base64.standard_b64encode(ukhas_str+"\n")
                                        packet_sha256 = hashlib.sha256(packet_base64).hexdigest()

                                        # Time Created = backlog time
                                        time_created = mdates.num2date(gpstime).strftime('%Y-%m-%dT%H:%M:%S+00:00')

                                        # Time Uploaded = now
                                        now = datetime.utcnow()
                                        time_uploaded = now.replace(microsecond=0).isoformat()+"+00:00"

## >>>>> Comment from here
##                                        # Upload to the habhub habitat database
##                                        doc_id, doc_rev = db.save({
##                                            "type":"payload_telemetry",
##                                            "_id": packet_sha256,
##                                            "data":{
##                                                "_raw": packet_base64
##                                            },
##                                            "receivers": {
##                                                "BACKLOG": {
##                                                    "time_created": time_created,
##                                                    "time_uploaded": time_uploaded,
##                                                }
##                                            }
##                                        })
##                                        print 'Doc ID:',doc_id
##                                        print 'Doc Rev:',doc_rev
## >>>>> to here to disable habitat upload

    except KeyboardInterrupt:
        print 'CTRL+C received...'

    finally:
        print 'Bye!'
     
    
