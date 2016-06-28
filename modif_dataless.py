# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:56:35 2016

@author: leroy
"""

from obspy.io.xseed import Parser
import copy
import sys


def modify(filename) :

    print filename    
    
    # Load Dataless to modify, assume only one station
    p = Parser("./dataless/"+filename)
    
    # Get Data Format Identifier Codes
    lookup_steim2 = -1
    lookup_geoscope_3bit = -1
    lookup_geoscope_4bit = -1
    i=0
    format_lookup_list = []
    print "---- Get data format identifier codes ----"
    while i < len(p.abbreviations):
        if p.abbreviations[i].blockette_type == 30:
            # Increment number of format          
            # Get Data Format Identifier Code for Steim2
            if p.abbreviations[i].short_descriptive_name.rfind("2") != -1:
                lookup_steim2 = p.abbreviations[i].data_format_identifier_code
                print "lookup_steim2 = ", lookup_steim2
                format_lookup_list.append(lookup_steim2)
            # Get Data Format Identifier Code for Geoscope 3 bits
            if p.abbreviations[i].short_descriptive_name.rfind("3") != -1:
                lookup_geoscope_3bit = p.abbreviations[i].data_format_identifier_code
                print "lookup_3bit = ", lookup_geoscope_3bit
                format_lookup_list.append(lookup_geoscope_3bit)
            # Get Data Format Identifier Code for Geoscope 4 bits
            if p.abbreviations[i].short_descriptive_name.rfind("4") != -1:
                lookup_geoscope_4bit = p.abbreviations[i].data_format_identifier_code
                print "lookup_4bit = ", lookup_geoscope_4bit
                format_lookup_list.append(lookup_geoscope_4bit)
        i+=1
                    
    print format_lookup_list
    
    # Create Steim2 Data Format blockette if it does not exist
    print "---- Create Steim2 Data Format blockette if it does not exist ----"
    if lookup_steim2 == -1:
        # Get a blockette 30 with Steim2 encoding
        psteim2 = Parser("./test/dataless.G.CLF.seed")
        # Copy it on current dataless
        p.abbreviations.insert(0, psteim2.abbreviations[0])
        # create new lookup code (make sure it is not already used otherwise increment)
        lookup_steim2 = 1
        while lookup_steim2 in format_lookup_list :
            lookup_steim2 += 1     
        print lookup_steim2
        # Set new lookup code
        p.abbreviations[0].data_format_identifier_code = lookup_steim2
        
    
    # Get Station = first station
    print "---- Get Station = first station ----"
    blksta = p.stations[0]
    
    # Remove Comment Blockettes
    print "---- Remove Comment Blockettes ----"
    i=1
    while i < len(blksta):
        if blksta[i].blockette_type == 51:
            blksta.pop(i)
        else:
            i+=1
            
    # Remove Comment Blockettes
    i=1
    while i < len(blksta):
        if blksta[i].blockette_type == 59:
            blksta.pop(i)
        else:
            i+=1
        
    # Look for all blockettes 52 that reference to one of Geoscope Data Format Identifier Code
    print "---- Look for all blockettes 52 that reference Geoscope Data Format 3 bit ----"
    i=1
    clone = -1
    if lookup_geoscope_3bit != -1:
        while i < len(blksta) :
            if blksta[i].blockette_type == 52:
                if blksta[i].data_format_identifier_code == lookup_geoscope_3bit :                
                    print ""                
                    print blksta[i].channel_identifier , blksta[i].start_date, blksta[i].location_identifier
                    # Clone blockette 52
                    blksta.insert(i, copy.deepcopy(blksta[i]))
                    blksta[i].location_identifier = "00"
                    blksta[i].data_format_identifier_code = lookup_steim2
                    i += 1
                    clone = i
                else:
                    clone = -1
            else:
                if clone != -1: # Blockette is concerned
                    print blksta[i].stage_sequence_number, blksta[i].blockette_type,
                    # Clone blockette                 
                    b = copy.deepcopy(blksta[i])
                    # Detect stage 0
                    if b.stage_sequence_number == 0:
                        # If stage 0, add gain blockette before
                        newb = copy.deepcopy(blksta[i])
                        newb.sensitivity_gain = 128
                        newb.stage_sequence_number = blksta[i-1].stage_sequence_number + 1
                        print "new stage =", newb.stage_sequence_number
                        blksta.insert(clone, newb)
                        clone += 1
                        b.sensitivity_gain *= 128
                        i += 1
                    blksta.insert(clone, b)               
                    clone += 1
                    i += 1
            i+=1
            
            
    # Verify
    print ""
    print ""
    print "---- Verify ----"
    i=1
    display = -1
    if lookup_geoscope_3bit != -1:
        while i < len(blksta) :
            if blksta[i].blockette_type == 52:
                if blksta[i].data_format_identifier_code == lookup_geoscope_3bit :                
                    print ""                
                    print blksta[i].channel_identifier , blksta[i].start_date,  blksta[i].location_identifier
                    display = 1
                else:
                    display = -1
            else:
                if display == 1:
                    if blksta[i].stage_sequence_number == 0:
                        print blksta[i].stage_sequence_number, blksta[i].blockette_type, blksta[i].sensitivity_gain,
                    else:
                        print blksta[i].stage_sequence_number, blksta[i].blockette_type,
            i += 1
            
            
    # Look for all blockettes 52 that reference to one of Geoscope Data Format Identifier Code
    print ""
    print ""
    print "---- Look for all blockettes 52 that reference Geoscope Data Format 4 bit ----"
    i=1
    clone = -1
    if lookup_geoscope_4bit != -1:
        while i < len(blksta) :
            if blksta[i].blockette_type == 52:
                if blksta[i].data_format_identifier_code == lookup_geoscope_4bit :                
                    print ""                
                    print blksta[i].channel_identifier , blksta[i].start_date, blksta[i].location_identifier
                    # Clone blockette 52
                    blksta.insert(i, copy.deepcopy(blksta[i]))
                    blksta[i].location_identifier = "00"
                    print lookup_steim2, lookup_geoscope_4bit
                    blksta[i].data_format_identifier_code = lookup_steim2
                    i += 1
                    clone = i
                else:
                    clone = -1
            else:
                if clone != -1: # Blockette is concerned
                    print blksta[i].stage_sequence_number, blksta[i].blockette_type,
                    # Clone blockette                 
                    b = copy.deepcopy(blksta[i])
                    # Detect stage 0
                    if b.stage_sequence_number == 0:
                        # If stage 0, add gain blockette before
                        newb = copy.deepcopy(blksta[i])
                        newb.sensitivity_gain = 32768
                        newb.stage_sequence_number = blksta[i-1].stage_sequence_number + 1
                        print "new stage =", newb.stage_sequence_number
                        blksta.insert(clone, newb)
                        clone += 1
                        b.sensitivity_gain *= 32768
                        i += 1
                    blksta.insert(clone, b)               
                    clone += 1
                    i += 1
            i+=1
            
            
    # Verify
    print ""
    print ""
    print "---- Verify ----"
    i=1
    display = -1
    if lookup_geoscope_4bit != -1:
        while i < len(blksta) :
            if blksta[i].blockette_type == 52:
                if blksta[i].data_format_identifier_code == lookup_geoscope_4bit :                
                    print ""                
                    print blksta[i].channel_identifier , blksta[i].start_date,  blksta[i].location_identifier
                    display = 1
                else:
                    display = -1
            else:
                if display == 1:
                    if blksta[i].stage_sequence_number == 0:
                        print blksta[i].stage_sequence_number, blksta[i].blockette_type, blksta[i].sensitivity_gain,
                    else:
                        print blksta[i].stage_sequence_number, blksta[i].blockette_type,
            i += 1
        
     
    
    
    # Write new dataless
    print ""
    print "---- Write new dataless ----"
    p.write_seed("./modified/"+filename+".modified")





################################################

#directory = os.listdir("./dataless")

#for file in directory :   
#    if "dataless" in file:
#        print file        
#        modify(file)

file = "dataless.G.BNG.seed"
modify(file)
