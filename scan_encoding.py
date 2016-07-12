#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import fnmatch
import glob
import os
import logging
import logging.handlers
import numpy as np
from IPython import embed
from obspy import read
from obspy.io.xseed import Parser
from obspy.signal.invsim import corn_freq_2_paz
import matplotlib.pyplot as plt

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
# also log to the console at a level determined by the --verbose flag
console_handler = logging.StreamHandler()  # sys.stderr
# set later by set_log_level_from_verbose() in interactive sessions
console_handler.setLevel(logging.CRITICAL)
console_handler.setFormatter(logging.Formatter(
    '[%(levelname)s](%(name)s): %(message)s'))
logger.addHandler(console_handler)


#            ../scan_encoding.py -i /Volumes/82-89/donneesGEOSCOPE/1987/G/NOC/VHZ.D/ -f




class scan_encoding(object):

    def __init__(self, args):

        self.file_list = []
        self.channels_coding = []
        self.channels_coding_start_time = {}
        self.channels_coding_end_time = {}
        
       
        if os.path.isfile(args.i):
            # One file
            self.file_list.append(args.i)
        elif os.path.isdir(args.i):
            # One directory
            for root, dirs, files in os.walk(args.i):
                for filename in fnmatch.filter(files, '*'):
                    #print( os.path.join(root, filename))
                    self.file_list.append( os.path.join(root, filename))

        if args.file:
            for input_file in self.file_list:
                stream_local = read(input_file ,headonly=True)
                for trace_local in stream_local:
                    tmp=trace_local.get_id()+'_'+trace_local.stats.mseed.encoding
                    print input_file+'\t'+tmp+'\t'+str(trace_local.stats.starttime)+'\t'+str(trace_local.stats.endtime)
        else:
            for input_file in reversed(self.file_list):
                stream_local = read(input_file ,headonly=True)
                for trace_local in stream_local:
                
                    tmp=trace_local.get_id()+'_'+trace_local.stats.mseed.encoding
                
                    #New channel + encoding
                    if tmp not in self.channels_coding:
                        self.channels_coding.append(tmp)
                        self.channels_coding_start_time[tmp]=trace_local.stats.starttime
                        self.channels_coding_end_time[tmp]=trace_local.stats.endtime
                    #Known channel but maybe with new dates 
                    else:
                        if trace_local.stats.starttime < self.channels_coding_start_time[tmp]:
                            self.channels_coding_start_time[tmp]=trace_local.stats.starttime
                        if trace_local.stats.endtime > self.channels_coding_end_time[tmp]:
                            self.channels_coding_end_time[tmp]=trace_local.stats.endtime
                        #print tmp+'\t'+ str(self.channels_coding_start_time[tmp])+ '\t'+str(self.channels_coding_end_time[tmp])

        
            for channel in self.channels_coding:
                print channel+'\t'+ str(self.channels_coding_start_time[channel])+ '\t'+str(self.channels_coding_end_time[channel])
                    


             
def main():

    # Parametres
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description='scan files or directory and print unique coding for each channel'
        , formatter_class=formatter_class)
    # Station
    parser.add_argument(
        "-i", type=str, help="Name of the input file or directory", required=False)

    parser.add_argument("-f", "--file", help="print coding for each file.",
                         required=False, action='store_true')
                    

    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="count", default=0,
                        help="increases log verbosity for each occurence.")

    # parse arguments
    args = parser.parse_args()

    if not args.verbose:
        console_handler.setLevel('ERROR')
    elif args.verbose == 1:
        console_handler.setLevel('WARNING')
    elif args.verbose == 2:
        console_handler.setLevel('INFO')
    elif args.verbose >= 3:
        console_handler.setLevel('DEBUG')
    else:
        logger.critical("UNEXPLAINED NEGATIVE COUNT!")

    if args.i is None:
        print "scan_encoding needs a filename or a directory"
        print parser.print_help()
        sys.exit()

    converter = scan_encoding(args)
    
  
    logging.shutdown()

    #
if __name__ == '__main__':
    main()
