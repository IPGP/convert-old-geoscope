#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri May 13 14:56:35 2016

@author: leroy
"""
import argparse
from obspy.io.xseed import Parser
import copy
import sys
import os
import fnmatch
from IPython import embed
import cPickle

gain_geoscope_3 = 2**7
gain_geoscope_4 = 2**7


class channel_period(object):
    def __init__(self, network, station, locid, channel, start_time, end_time, encoding):
        self.network = network
        self.station = station
        self.locid = locid
        self.channel = channel
        self.start_time = start_time
        self.end_time = end_time
        self.encoding = encoding
        self.gain=None
    
    def __str__(self):
        string=self.network,self.station,self.locid,self.channel,self.start_time,self.end_time
        return str(string)
    
class modify_dataless(object):

    def __init__(self, args):

        self.args = args
        self.file_list = []
        self.file_streams = []
        if len(args.i) == 1:
            args.i = args.i[0]
            if os.path.isfile(args.i):
                # One file
                self.file_list.append(args.i)
            elif os.path.isdir(args.i):
                # One directory
                for root, dirs, files in os.walk(args.i):
                    for filename in fnmatch.filter(files, '*'):
                        #print( os.path.join(root, filename))
                        self.file_list.append(os.path.join(root, filename))
        else:
            for file in args.i:
                self.file_list.append(file)

    def modify(self):

        for filename in self.file_list:
            print filename
            # Load Dataless to modify, assume only one station
            p = Parser(filename)

            # Get Data Format Identifier Codes
            lookup_steim2 = -1
            lookup_geoscope_3bit = -1
            lookup_geoscope_4bit = -1

            format_lookup_list = []
            print "---- Get data format identifier codes ----"
            for local_blockette in p.abbreviations:
                if local_blockette.blockette_type == 30:
                    # Increment number of format
                    # Get Data Format Identifier Code for Steim2
                    if "Steim2 Integer Compression Format" in local_blockette.short_descriptive_name:
                        lookup_steim2 = local_blockette.data_format_identifier_code
                        print "lookup_steim2 = ", lookup_steim2
                        format_lookup_list.append(lookup_steim2)
                    # Get Data Format Identifier Code for Geoscope 3 bits
                    if "Geoscope gain-range on 3 bits" in local_blockette.short_descriptive_name:
                        lookup_geoscope_3bit = local_blockette.data_format_identifier_code
                        print "lookup_3bit = ", lookup_geoscope_3bit
                        format_lookup_list.append(lookup_geoscope_3bit)
                    # Get Data Format Identifier Code for Geoscope 4 bits
                    if "Geoscope gain range on 4 bits" in local_blockette.short_descriptive_name:
                        lookup_geoscope_4bit = local_blockette.data_format_identifier_code
                        print "lookup_4bit = ", lookup_geoscope_4bit
                        format_lookup_list.append(lookup_geoscope_4bit)

            print format_lookup_list

            # Create Steim2 Data Format blockette if it does not exist
            print "---- Create Steim2 Data Format blockette if it does not exist ----"
            if lookup_steim2 == -1:
                # Get a blockette 30 with Steim2 encoding
                psteim2 = Parser("./test/dataless.G.CLF.seed")
                # Copy it on current dataless
                p.abbreviations.insert(0, psteim2.abbreviations[0])
                # create new lookup code (make sure it is not already used otherwise
                # increment)
                lookup_steim2 = 1
                while lookup_steim2 in format_lookup_list:
                    lookup_steim2 += 1
                print lookup_steim2
                # Set new lookup code
                p.abbreviations[0].data_format_identifier_code = lookup_steim2

            # Get Station = first station
            print "---- Get Station = first station ----"
            blksta = p.stations[0]

            # Remove Comment Blockettes because it is IPGP datacenter that insert them
            # and problems with PDCC

            print "---- Remove Comment Blockettes ----"

            i = 1
            while i < len(blksta):
                if blksta[i].blockette_type == 51:
                    blksta.pop(i)
                else:
                    i += 1

            # Remove Comment Blockettes
            i = 1
            while i < len(blksta):
                if blksta[i].blockette_type == 59:
                    blksta.pop(i)
                else:
                    i += 1

            # Look for all blockettes 52 that reference to one of Geoscope Data Format
            # Identifier Code
            print "---- Look for all blockettes 52 that reference Geoscope Data Format 3 bit ----"
            i = 1
            clone = -1
            if lookup_geoscope_3bit != -1:
                while i < len(blksta):
                    if blksta[i].blockette_type == 52:
                        if blksta[i].data_format_identifier_code == lookup_geoscope_3bit:
                            print ""
                            print blksta[i].channel_identifier, blksta[i].start_date, blksta[i].location_identifier
                            # Clone blockette 52
                            blksta.insert(i, copy.deepcopy(blksta[i]))
                            blksta[i].location_identifier = "00"
                            blksta[i].data_format_identifier_code = lookup_steim2
                            i += 1
                            clone = i
                        else:
                            clone = -1
                    else:
                        if clone != -1:  # Blockette is concerned
                            print blksta[i].stage_sequence_number, blksta[i].blockette_type,
                            # Clone blockette
                            b = copy.deepcopy(blksta[i])
                            # Detect stage 0
                            if b.stage_sequence_number == 0:
                                # If stage 0, add gain blockette before
                                newb = copy.deepcopy(blksta[i])
                                newb.sensitivity_gain = gain_geoscope_3
                                newb.stage_sequence_number = blksta[
                                    i - 1].stage_sequence_number + 1
                                print "new stage =", newb.stage_sequence_number
                                blksta.insert(clone, newb)
                                clone += 1
                                b.sensitivity_gain *= gain_geoscope_3
                                i += 1
                            blksta.insert(clone, b)
                            clone += 1
                            i += 1
                    i += 1

            # Verify
            print ""
            print ""
            print "---- Verify ----"
            display = -1
            if lookup_geoscope_3bit != -1:
                for blksta_local in blksta:
                    if blksta_local.blockette_type == 52:
                        if blksta_local.data_format_identifier_code == lookup_geoscope_3bit:
                            print ""
                            print blksta_local.channel_identifier, blksta_local.start_date,  blksta_local.location_identifier
                            display = 1
                        else:
                            display = -1
                    else:
                        if display == 1:
                            if blksta_local.stage_sequence_number == 0:
                                print blksta_local.stage_sequence_number, blksta_local.blockette_type, blksta_local.sensitivity_gain
                            else:
                                print blksta_local.stage_sequence_number, blksta_local.blockette_type

            # Look for all blockettes 52 that reference to one of Geoscope Data Format
            # Identifier Code
            print ""
            print ""
            print "---- Look for all blockettes 52 that reference Geoscope Data Format 4 bit ----"
            i = 1
            clone = -1
            if lookup_geoscope_4bit != -1:
                while i < len(blksta):
                    if blksta[i].blockette_type == 52:
                        if blksta[i].data_format_identifier_code == lookup_geoscope_4bit:
                            print ""
                            print blksta[i].channel_identifier, blksta[i].start_date, blksta[i].location_identifier
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
                        if clone != -1:  # Blockette is concerned
                            print blksta[i].stage_sequence_number, blksta[i].blockette_type,
                            # Clone blockette
                            b = copy.deepcopy(blksta[i])
                            # Detect stage 0
                            if b.stage_sequence_number == 0:
                                # If stage 0, add gain blockette before
                                newb = copy.deepcopy(blksta[i])
                                newb.sensitivity_gain = gain_geoscope_4
                                newb.stage_sequence_number = blksta[
                                    i - 1].stage_sequence_number + 1
                                print "new stage =", newb.stage_sequence_number
                                blksta.insert(clone, newb)
                                clone += 1
                                b.sensitivity_gain *= gain_geoscope_4
                                i += 1
                            blksta.insert(clone, b)
                            clone += 1
                            i += 1
                    i += 1

            # Verify
            print ""
            print ""
            print "---- Verify ----"
            display = -1
            if lookup_geoscope_4bit != -1:
                for blksta_local in blksta:
                    if blksta_local.blockette_type == 52:
                        if blksta_local.data_format_identifier_code == lookup_geoscope_4bit:
                            print ""
                            print blksta_local.channel_identifier, blksta_local.start_date,  blksta_local.location_identifier
                            display = 1
                        else:
                            display = -1
                    else:
                        if display == 1:
                            if blksta_local.stage_sequence_number == 0:
                                print blksta_local.stage_sequence_number, blksta_local.blockette_type, blksta_local.sensitivity_gain,
                            else:
                                print blksta_local.stage_sequence_number, blksta_local.blockette_type,

            # Write new dataless
            print ""
            print "---- Write new dataless ----"
            p.write_seed(self.args.output + '/' + os.path.basename(filename))

    def scan(self):
        self.channel_array=[] 
        for filename in self.file_list:
            # print filename
            # Load Dataless to modify, assume only one station
            p = Parser(filename)

            # Get station name and network code
            net, sta = p.get_inventory()['stations'][0]['station_id'].split('.')
            

            # Get Data Format Identifier Codes
            lookup_steim2 = -1
            lookup_geoscope_3bit = -1
            lookup_geoscope_4bit = -1

            format_lookup_list = []
            for local_blockette in p.abbreviations:
                if local_blockette.blockette_type == 30:
                    # Increment number of format
                    # Get Data Format Identifier Code for Steim2
                    if "Steim2 Integer Compression Format" in local_blockette.short_descriptive_name:
                        lookup_steim2 = local_blockette.data_format_identifier_code
                        # print "lookup_steim2 = ", lookup_steim2
                        format_lookup_list.append(lookup_steim2)
                    # Get Data Format Identifier Code for Geoscope 3 bits
                    if "Geoscope gain-range on 3 bits" in local_blockette.short_descriptive_name:
                        lookup_geoscope_3bit = local_blockette.data_format_identifier_code
                        # print "lookup_3bit = ", lookup_geoscope_3bit
                        format_lookup_list.append(lookup_geoscope_3bit)
                    # Get Data Format Identifier Code for Geoscope 4 bits
                    if "Geoscope gain range on 4 bits" in local_blockette.short_descriptive_name:
                        lookup_geoscope_4bit = local_blockette.data_format_identifier_code
                        # print "lookup_4bit = ", lookup_geoscope_4bit
                        format_lookup_list.append(lookup_geoscope_4bit)

            # print format_lookup_list

            # Get Station = first station
            blksta = p.stations[0]

            # Look for all blockettes 52 that reference to one of Geoscope Data Format
            # Identifier Code
            # print "---- Look for all blockettes 52 that reference Geoscope
            # Data Format 3 bit ----"

            if lookup_geoscope_3bit != -1:
                for blockette in blksta:
                    if (blockette.blockette_type == 52) and (blockette.data_format_identifier_code == lookup_geoscope_3bit):
                        print "3",  net,sta, blockette.channel_identifier,  blockette.location_identifier, blockette.start_date, blockette.end_date
                        self.channel_array.append(channel_period(net, sta, '', blockette.channel_identifier, blockette.start_date, blockette.end_date, '3'))
    
                        # embed()
            # print "---- Look for all blockettes 52 that reference Geoscope
            # Data Format 4 bit ----"
            if lookup_geoscope_4bit != -1:
                for blockette in blksta:
                    if (blockette.blockette_type == 52) and (blockette.data_format_identifier_code == lookup_geoscope_4bit):
                        print "4",  net,sta, blockette.channel_identifier,  blockette.location_identifier, blockette.start_date, blockette.end_date
                        self.channel_array.append(channel_period(net, sta, '', blockette.channel_identifier, blockette.start_date, blockette.end_date, '3'))
            
            cPickle.dump( self.channel_array, open( "dataless.p", "wb" ) )
#            cPickle.dump({ "lion": "yellow", "kitty": "red" }, open( "dataless.p", "wb" ) )
            
            
            for cha in self.channel_array:
                print cha
def main():

    # Parametres
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description='Convert Geoscope dataless into Steim dataless',
        formatter_class=formatter_class)
    # Station
    parser.add_argument(
        "-i", type=str, help="Name of the input file or directory", required=False, nargs='*')
    parser.add_argument("-s", "--scan", dest='scan',
                        help="Scan the dataless for Geoscope periods", required=False, action='store_true')

    parser.add_argument("-o", "--output", type=str,
                        help="Name of the output directory", default='./modified/', required=False)

    # parse arguments
    args = parser.parse_args()

    if args.i is None:
        print "geoscope_to_steim2 needs a filename or a directory"
        print parser.print_help()
        sys.exit()

    m = modify_dataless(args)
    if args.scan:
        m.scan()
    else:
        m.modify()

    #
if __name__ == '__main__':
    main()
