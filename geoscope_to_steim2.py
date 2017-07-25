#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import numpy as np
#from IPython import embed
from obspy.io.xseed import Parser as Dataless_Parser
#from modif_dataless import channel_period
from obspy import UTCDateTime
import os
import sys
from glob import glob
import fnmatch
from obspy import read


# ./modif_dataless.py -s -i ./dataless/dataless.G.BNG.seed

#./geoscope_to_steim2.py --sds ../donneesGEOSCOPE/ --dataless_resume ./dataless.p -o ./dataout/

class geoscope_to_steim2(object):

    def __init__(self, args):

        self.max_percentage_error = 0.001
        self.convert_start_time = UTCDateTime()
        self.file_list = []
        self.file_streams = []

        if not args.output:
            self.output_dir = "./"
        else:
            self.output_dir = args.output + '/'
        self.dataless = args.dataless

        inputs = glob(args.data_source_dir)

        for inp in inputs:
            if os.path.isfile(inp):
                # One file
                self.file_list.append(inp)
            elif os.path.isdir(inp):
                # One directory
                for root, dirs, files in os.walk(inp):
                    for filename in fnmatch.filter(files, '*'):
                        #print( os.path.join(root, filename))
                        self.file_list.append(os.path.join(root, filename))
        # print self.file_list

    def convert_and_save(self):
        """
        Convert streams in GEOSCOPE16_3 or GEOSCOPE16_4 format
        to STEIM 2 streams with locid OO.
        """
        # print "Streams conversion"
        pb = False
        self.new_dataless_periods = []
        station = ''
        network = ''
        channel = ''
        starttime = False

        for input_file in self.file_list:
            stream_local = read(input_file, details=True)
            stream_encoding = None

            for trace_local in stream_local:

                network = trace_local.stats.network
                station = trace_local.stats.station
                channel = trace_local.stats.channel
                starttime = trace_local.stats.starttime

                # Check multiple encodings in one file
                if not stream_encoding:
                    stream_encoding = trace_local.stats.mseed.encoding
                if stream_encoding != trace_local.stats.mseed.encoding:
                    print "Double encodage dans le fichier!!!!!!"
                    print input_file
                    exit()

                if u'GEOSCOPE16_' not in trace_local.stats.mseed.encoding:
                    pass
                    print "No GEOSCOPE16 detected for this trace"
                    print trace_local

                elif u'GEOSCOPE16_' in trace_local.stats.mseed.encoding:
                    print trace_local.stats.mseed.encoding + " detected for this trace"
                    print trace_local

                    coef = 2**7

                    trace_local.data = coef * trace_local.data
                    trace_local.data = np.array(
                        trace_local.data, dtype='int32')
                    # print trace_local.data

                    trace_local_data = trace_local.data
                    trace_local_data_int = trace_local_data.astype(int)

                    #  test after mutiplication
                    if np.all((trace_local_data - trace_local_data_int) == 0):
                        pass
                        print "After multiplication trace only contains int"
                    else:
                        print "##########################################################################################################################"
                        print "After multiplication trace still contains floats"
                        pb = True
                        exit()
                    new_id = "%(network)s.%(station)s.00.%(channel)s" % trace_local.stats
                    self.new_dataless_periods.append(
                        [new_id, trace_local.stats.starttime, trace_local.stats.endtime])

            if pb:
                print "Conversion problem for file : " + input_file
            else:
                self.print_results()

                # new locid and mseed.encoding
                for trace in stream_local:
                    trace.stats.mseed.encoding = u'STEIM2'
                    trace.stats.location = u'00'

                file_dir = self.output_dir + '/' + str(starttime.year) + '/' + \
                    network + '/' + station + '/' + channel + '.D'
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)

                nameout = "%s/%s.%s.%s.%s.D.%04i.%03i" % (
                    file_dir, network, station, '00', channel, starttime.year, starttime.julday)

                #new_file_name = str(self.output_dir) + '/'+network + '.'+station + '.00.' +channel+'.D.'+starttime
                #stream_local.write(new_file_name, format="MSEED", encoding="STEIM2")
                stream_local.write(nameout, format="MSEED", encoding="STEIM2")
#
         # bar.finish()

        print "Total time: ", (UTCDateTime() - self.convert_start_time)
        # cPickle.dump(self.dataless_resume_data, open(
        #    self.dataless_resume_filename + "_processed", "wb"))

    def print_results(self):
        # Sort periods by start time
        self.new_dataless_periods.sort(key=lambda date: date[1])
        # Sort periods by channels
        self.new_dataless_periods.sort(key=lambda canal: canal[0])

        # embed()
        for period in self.new_dataless_periods:
            print period[0] + '\t' + period[1].format_seed() + '\t' + period[2].format_seed()

    def check_dataless(self):

        print "Dataless and data check"

        try:
           dataless_parser = Dataless_Parser(self.dataless)
        except:
            print('Dataless file does not exist or has a problem')
            sys.exit(0)

        self.check_error = False

        for input_file in self.file_list:

            stream_initiale = read(input_file)

            trace_local = stream_initiale[0]
            network = trace_local.stats.network
            station = trace_local.stats.station
            channel = trace_local.stats.channel
            starttime = trace_local.stats.starttime

            file_dir = self.output_dir + '/' + str(starttime.year) + '/' + \
                network + '/' + station + '/' + channel + '.D'

            nameout = "%s/%s.%s.%s.%s.D.%04i.%03i" % (
                file_dir, network, station, '00', channel, starttime.year, starttime.julday)

#            print input_file
#            print new_file_name
            stream_modifie = read(nameout)

            for double_trace in zip(stream_initiale, stream_modifie):
                trace_local_init = double_trace[0]
                type(trace_local_init)
                s_ori = dataless_parser.get_paz(
                    trace_local_init.id, trace_local_init.stats.starttime)['sensitivity']
                trace_local_init.data = trace_local_init.data / s_ori

                trace_local_modif = double_trace[1]

                try:
                    s = dataless_parser.get_paz(
                        trace_local_modif.id, trace_local_modif.stats.starttime)['sensitivity']
                except:
                    print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    print trace_local_modif.id
                    print input_file
                    exit()
                trace_local_modif.data = trace_local_modif.data / s
                max_diff = max(trace_local_init.data - trace_local_modif.data)
                indice_max = np.argmax(trace_local_init.data - trace_local_modif.data)
                error_percentage = max_diff*100/trace_local_modif.data[indice_max]
      
                
                if error_percentage > self.max_percentage_error:
                    print "##########################################################################################################################"
                    print 'Maximum difference of ' + str(max_diff) + ' in physical units for ' + input_file
                    print "valeur initiale\t" + str(trace_local_init.data[indice_max])
                    print "valeur finale\t" + str(trace_local_modif.data[indice_max])
                    print "pourcentage erreur\t" + str(error_percentage)
                
                
                    self.check_error = True
        if self.check_error:
            print "##########################################################################################################################"
            print "##########################################################################################################################"
            print "##########################################################################################################################"
            print "##########################################################################################################################"
            print "\t\t\tProblem in at least one file or dataless period"
            print "##########################################################################################################################"
            print "##########################################################################################################################"
            print "##########################################################################################################################"
            print "##########################################################################################################################"
        else:
            print "No conversion and dataless problem"


def main():

    # Parametres
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description='Convert miniseed files with geoscope 13 or 14 encoding to\
        miniseed file with  Steim 2 encoding.  ', formatter_class=formatter_class)

    parser.add_argument('data_source_dir', action='store', type=str,
                        help='path of directories containing data to convert or files')


    parser.add_argument('-o', '--output', type=str, help='Name of the outputfile directory',
                        required=False)

    parser.add_argument('-d', '--dataless', type=str,
                        help='Name of the dataless or directory of dataless to\
                         use for verification', required=False)

    parser.add_argument('-c','--check_dataless_only', action='store_true')


    # parse arguments
    try:
       args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)
    
    converter = geoscope_to_steim2(args)
    
    if not args.check_dataless_only:
        converter.convert_and_save()
    
    converter.check_dataless()

    #
if __name__ == '__main__':
    np.seterr(divide='ignore', invalid='ignore')
    main()
