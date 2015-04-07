# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from SimpleCV import Image
import soco
import json
import os
import subprocess
import time
import datetime

# <codecell>

import warnings
warnings.filterwarnings("ignore")

# <codecell>

file_location = r'/home/pi/sonart'
config_file = 'config.json'
covers_folder = 'covers'
sonos_ip = '192.168.1.82'
timer_duration = 0.5

# <codecell>

sonos = soco.SoCo(sonos_ip)
working_image = os.path.join(file_location,'working_image.jpg')

# <codecell>

# open the config file and read in the image keypoints

print('Loading Sonart')

print('  Loading Config...'),
with open(os.path.join(file_location, config_file), 'r+') as f:
    config = json.load(f) 
print('[Done]')

print('  Reading Keypoints')
for artist in config:
    try:
        print('    Record: {0}'.format(artist['title'])),
        image_location = os.path.join(file_location, covers_folder, artist['cover'])
        artist['keypoints'] = Image(str(image_location))._getRawKeypoints(500)
        print('[Done]')
    except:
        print('    Could not read image for record: {0}'.format(artist['title']))
        # want to reject this config item at this point
        
print('  Checking connectivity')

print('    Checking camera capture...'),
try:
    subprocess.call('raspistill -n -t 300 -w 640 -h 480 -o {0}'.format(working_image), shell=True)
except:
    raise Exception("Camera capture failed")
print('[Done]')

print('    Checking working image read...'),
try:
    img = Image(working_image)
except:
    raise Exception("Working image read failed")
print('[Done]')

print('Loading and checks complete. Running...')
print('Press ^C to exit.')

issue_count = 0

while (issue_count<10):
    
    try:
        subprocess.call('raspistill -n -t 300 -w 640 -h 480 -o {0}'.format(working_image), shell=True)
    except:
        print("Issue calling raspistill...retrying")
        issue_count += 1
        time.sleep(1)
        continue
    
    try:
        img = Image(working_image)
        source_kp = img._getRawKeypoints(500)
    except:
        time.sleep(1)
        continue

    # loop through matching each keypoint set and pull the highest matching set
    for idx, artist in enumerate(config):
        if img.matchKeypoints(source_kp, artist['keypoints'], minDist=0.15, minMatch=0.4):
        
            # write log that of which album recognised
            print('{1} Recognised {0}'.format(artist['title'], str(datetime.datetime.now())))
    
            try:
                # clear the queue
                sonos.clear_queue()
    
                # add and kick off the first track
                sonos.add_uri_to_queue(artist['tracks'][0]['uri'])
                sonos.play_from_queue(0)
    
                # add the rest of the tracks
                for item in artist['tracks'][1:]:
                    sonos.add_uri_to_queue(item['uri'])
                    
            except:
                print("Issue calling Sonos.")
                issue_count += 1
                sonos = soco.SoCo(sonos_ip)

    # sleep for a moment before looping again
    time.sleep(timer_duration)

