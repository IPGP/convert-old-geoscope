#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import fnmatch
import glob
import os
import numpy
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

#./scan_float.py  -i /Volumes/82-89/donneesGEOSCOPE/1987/G/


gain = 2**8
#gain = 1


class scan_float(object):

    def __init__(self, args):

        self.file_list = []
        self.file_streams = []

        if os.path.isfile(args.i):
            # One file
            self.file_list.append(args.i)
        elif os.path.isdir(args.i):
            # One directory
            for root, dirs, files in os.walk(args.i):
                for filename in fnmatch.filter(files, '*'):
                    #print( os.path.join(root, filename))
                    self.file_list.append(os.path.join(root, filename))

        #    self.file_list = glob.glob(args.i + '/*')

    def convert_and_save(self):
        """
        Convert streams in GEOSCOPE16_3 or GEOSCOPE16_4 format
        to STEIM 2 streams with locid OO.
        """
        # print "Streams conversion"

        for input_file in self.file_list:
            stream_local = read(input_file, details=True)
            # print "**************************************************************************************************************"
            # print input_file
            network, station, locid, channel, data_type, year, day = input_file.split(
                '/')[-1].split('.')

            file_only_int = False
            file_mul27 = False
            file_mul215 = False
            file_flat=False

            for trace_local in stream_local:
                converted = False
                # print "#########################################################################################"
                #print trace_local
                if u'GEOSCOPE16_' not in trace_local.stats.mseed.encoding:
                    # print "No GEOSCOPE16 detected for this trace"
                    break
                elif 'GEOSCOPE' in trace_local.stats.mseed.encoding:
                    # print str(trace_local.stats.mseed.encoding)+" coding
                    # detected for this trace"

                    only_int = True
                    mul27 = False
                    mul215 = False
                    flat = True
                    last_sample = trace_local.data[0]

                    # test to find floats and int
                    for sample in trace_local.data:
                        # si sample est un float
                        if (int(sample) - sample) != 0:
                            trace_local.data = trace_local.data * 2**7
                            only_int = False
                            break
                        #le sample n'est pas un float
                        else:
                            if sample != last_sample:
                                flat = False
                                break
                       

                    if not only_int:
                        for sample_27 in trace_local.data:
                            # si sample * 2**7 est un float
                            if (int(sample_27) - sample_27) != 0:
                                trace_local.data = trace_local.data * 2**8
                                mul27 = False
                                break
                            mul27= True


                    if not mul27 and not only_int:
                        for sample_215 in trace_local.data:
                            # si sample * 2**15 est un float
                            if (int(sample_215) - sample_215) != 0:
                                print str(input_file) + ' 2**15 is not enough !'
                                break
                            mul215 = True

                    if only_int:
                        file_only_int = True
                    if mul27:
                        file_mul27 = True
                    if mul215:
                        file_mul215 = True
                    file_flat = flat and file_flat
                        
            
            file_status = str(input_file)
            if file_only_int: file_status += ' int'
            if file_flat: file_status += ' flat'
            if file_mul27 : file_status += ' 2_7'
            if file_mul215 : file_status += ' 2_15'
            print  file_status
            
                    
                    
def main():

    # Parametres
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description='Convert miniseed files with geoscope 13 or 14 encoding to\
        miniseed file with  Steim 2 encoding. With a dataless a verification\
        is done with deconvolution of the data \r\n\
        Test Geoscope 16_3\n\
        ./geoscope_to_steim2.py -i AGD.G..MHZ.1987.218 \r\n Test Geoscope 16_4\r\n\
        ./geoscope_to_steim2.py -i G.PCR.00.VH1.1982.229 ', formatter_class=formatter_class)
    # Station
    parser.add_argument(
        "-i", type=str, help="Name of the input file or directory", required=False)

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
        print "geoscope_to_steim2 needs a filename or a directory"
        print parser.print_help()
        sys.exit()

    converter = scan_float(args)
    converter.convert_and_save()
    # print converter.file_list
    # exit()

    logging.shutdown()

    #
if __name__ == '__main__':
    main()
