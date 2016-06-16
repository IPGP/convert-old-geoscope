# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:56:35 2016

@author: leroy
"""

from obspy.io.xseed import Parser
import copy
import sys

# Load Dataless to modify, assume only one station
p = Parser("dataless.G.SSB.seed")

# Get Data Format Identifier Code
if p.abbreviations[0].blockette_type == 30:
    if p.abbreviations[0].data_family_type == 1:
        # Test if encoding is Geoscope 3 bits
        if p.abbreviations[0].short_descriptive_name.rfind("3") != -1:
            # Set gain to 2^7 = 128
            gain = 2**7
        # Or if encoding is Geoscope 4 bits
        elif p.abbreviations[0].short_descriptive_name.rfind("4") != -1:
            # Set gain to 2^15 = 32768
            gain = 2**15
        else :
            # Print warning and exit
            print("No Geoscope encoding")
            sys.exit()

    
# Clone current station
#p.stations.insert(0,copy.deepcopy(p.stations[0]))

# Get Station = first station
blksta = p.stations[0]

sys.exit()

# Remove Comment Blockettes
i=1
while i < len(blksta):
    if blksta[i].blockette_type == 51:
        blksta.pop(i)
    i+=1
    



## Change Location code
#i=1
#while i < len(blksta):
#    # Test if blockette is a channel blockette (52)
#    if blksta[i].blockette_type == 52:
#        blksta[i].location_identifier = '00'
#    i+=1
        

# Iterate to find all stages 0 and insert a new blockette 58 with gain
# before + update gain on stage 0
# --------------------------------------------------------------------

# Start from 1 to skip blockette 50
i=1
while i < len(blksta):
    # Test if blockette is a gain blockette
    if blksta[i].blockette_type == 58:   
        # Test if the blockette is the last of the channel = stage 0
        if blksta[i].stage_sequence_number == 0:
            # Update gain on stage 0
            blksta[i].sensitivity_gain *= gain
            # Insert a copy of gain of the last stage
            blksta.insert(i, copy.deepcopy(blksta[i-1]))
            # Update gain on new stage
            blksta[i].sensitivity_gain = gain
            # Increment stage number on new blockette
            blksta[i].stage_sequence_number = blksta[i].stage_sequence_number + 1
            # Skip next blockette (= stage 0 that has been shifted due to insert)            
            i+=1
    # Go to next blockette
    i+=1


# Update information for new encoding
# -----------------------------------

# Get a blockette 30 with Steim2 encoding
psteim2 = Parser("dataless.G.CLF.seed")
# Copy it on current dataless
p.abbreviations[0] = psteim2.abbreviations[0]

        
# Write Dataless    
p.write_seed("SSB.dataless.modif")

