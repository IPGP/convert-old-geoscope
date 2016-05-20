#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import glob
import os
import logging
import logging.handlers
import numpy as np
from obspy import read
from obspy.io.xseed import Parser
from obspy.signal.invsim import corn_freq_2_paz

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
# also log to the console at a level determined by the --verbose flag
console_handler = logging.StreamHandler()  # sys.stderr
# set later by set_log_level_from_verbose() in interactive sessions
console_handler.setLevel(logging.CRITICAL)
console_handler.setFormatter(logging.Formatter(
    '[%(levelname)s](%(name)s): %(message)s'))
logger.addHandler(console_handler)


class geoscope_to_steim2(object):

    def __init__(self, args):

        self.file_list = []
        self.file_streams = []
        if not args.output:
            self.output_dir = "./"
        else:
            self.output_dir = args.output + '/'
        self.dataless_dir = args.dataless

        if os.path.isfile(args.i):
            # One file
            self.file_list.append(args.i)
        elif os.path.isdir(args.i):
            # One directory
            self.file_list = glob.glob(args.i + '/*')

    def convert_and_save(self):
        """
        Convert streams in GEOSCOPE16_3 or GEOSCOPE16_4 format
        to STEIM 2 streams with locid OO.
        """
        print "Streams conversion"

        for input_file in self.file_list:
            stream_local = read(input_file, details=True)
            for trace_local in stream_local:
                print "#################################################################"
                print trace_local
                if u'GEOSCOPE16_' not in trace_local.stats.mseed.encoding:
                    print "No GEOSCOPE16 detected for this trace"
                    break
                elif trace_local.stats.mseed.encoding == u'GEOSCOPE16_3':
                    print "GEOSCOPE16_3 coding detected for this trace"
                    trace_local.data = trace_local.data * 2**7
                elif trace_local.stats.mseed.encoding == u'GEOSCOPE16_4':
                    print "GEOSCOPE16_4 coding detected for this trace"
                    trace_local.data = trace_local.data * 2**15

                # float to int
                tmp = trace_local.data.copy()
                trace_local.data = np.array(trace_local.data).astype(np.int32)
                dif_int_float = trace_local.data - tmp
                print "Maximum difference after float to int conversion: " + str(max(dif_int_float))

                # Compression format modification
                trace_local.stats.mseed.encoding = u'STEIM2'
                # on rajoute le location code
                trace_local.stats.location = u'00'
                print "Conversion ok"

               # G.AGD.00.MHZ.1987.123
                new_file_name = str(self.output_dir) + stream_local[0].get_id()\
                    + '.' + \
                    stream_local[0].stats.starttime.format_seed(
                        compact=True).replace(',', '.')[0:8]

                # AGD.G.00.MHZ.1987.123
                new_file_name = str(self.output_dir) + \
                    stream_local[0].stats.station + '.' +\
                    stream_local[0].stats.network + '.00.' + \
                    stream_local[0].stats.channel + '.' +\
                    stream_local[0].stats.starttime.format_seed(
                        compact=True).replace(',', '.')[0:8]

            logger.warn("le fichier sera sauvegarde ici: " + new_file_name)
            stream_local.write(
                new_file_name, format="MSEED", encoding="STEIM2")

    def verification(self):

        for input_file in self.file_list:
            st_ori = read(input_file, details=True)

            # G.AGD.00.MHZ.1987.123
            new_file_name = str(self.output_dir) + st_ori[0].stats.network + '.' + st_ori[0].stats.station + '.00.' + st_ori[0].stats.channel + '.' + st_ori[
                0].stats.starttime.format_seed(compact=True).replace(',', '.')[0:8]

            # AGD.G.00.MHZ.1987.123
            new_file_name = str(self.output_dir) + st_ori[0].stats.station + '.' + st_ori[0].stats.network + '.00.' + st_ori[0].stats.channel + '.' + st_ori[
                0].stats.starttime.format_seed(compact=True).replace(',', '.')[0:8]

            logger.warn(new_file_name)

            st_modif = read(new_file_name, details=True)
            dataless_file_name = 'dataless.' + \
                st_ori[0].stats.network + '.' + \
                st_ori[0].stats.station + '.seed'

            logger.warning('dataless file is: ' + dataless_file_name)
            dataless_parser = Parser(dataless_file_name)

            paz_ori = dataless_parser.get_paz(st_ori[0].get_id())
            paz_1hz_ori = corn_freq_2_paz(1.0, damp=0.707)
            st_ori.simulate(paz_remove=paz_ori, paz_simulate=paz_1hz_ori)

            paz_modif = dataless_parser.get_paz(st_modif[0].get_id())
            paz_1hz_modif = corn_freq_2_paz(1.0, damp=0.707)
            st_modif.simulate(paz_remove=paz_modif, paz_simulate=paz_1hz_modif)

            tr_orig = st_ori[0]
            tr_modif = st_modif[0]
            dif = tr_modif.data - tr_orig.data
            print "Maximum difference between original geoscope encoding data \
            and convert steim2 data after deconvolution: " + str(max(dif))


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

    parser.add_argument("-o", "--output", type=str, help='Name of the outputfile directory',
                        required=False)
    parser.add_argument("-d", "--dataless", type=str,
                        help='Name of the dataless or directory of dataless to\
                         use for verification', required=False)
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

    converter = geoscope_to_steim2(args)
    converter.convert_and_save()
    if args.dataless:
        converter.verification()

    logging.shutdown()

    #
if __name__ == '__main__':
    main()
