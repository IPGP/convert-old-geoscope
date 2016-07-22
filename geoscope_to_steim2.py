#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import numpy
import cPickle
import numpy as np
from IPython import embed
from obspy import read
from obspy.io.xseed import Parser
from obspy.signal.invsim import corn_freq_2_paz
import matplotlib.pyplot as plt
from obspy.clients.filesystem import sds
from modif_dataless import channel_period
from progress.bar import Bar
from obspy import UTCDateTime


# ./geoscope_to_steim2.py --sds /Volumes/82-89/donneesGEOSCOPE/  --dataless_resume ./dataless.p

gain = 2**7
gain = 1


class geoscope_to_steim2(object):

    def __init__(self, args):

        self.file_list = []
        self.file_streams = []

        if not args.output:
            self.output_dir = "./"
        else:
            self.output_dir = args.output + '/'
        self.dataless_dir = args.dataless

        print "Reading SDS archive"
        self.sds_client = sds.Client(args.sds)
        self.dataless_resume = cPickle.load(open(args.dataless_resume, "rb"))

    def convert_and_save(self):
        """
        Convert streams in GEOSCOPE16_3 or GEOSCOPE16_4 format
        to STEIM 2 streams with locid OO.
        """
        #print "Streams conversion"


        bar = Bar('Processing dataless channels', max=len(self.dataless_resume))
        for item in self.dataless_resume:
            # print item
            st = self.sds_client.get_waveforms(
                item.network, item.station, item.locid, item.channel, item.start_time, item.end_time, details=True)
            stream_gain = 1
            
            bar_trace = Bar('Processing traces ', max=len(st))
            for trace_local in st:
                # print tr.stats
                if u'GEOSCOPE16_' not in trace_local.stats.mseed.encoding:
                    print "No GEOSCOPE16 detected for this trace"
                    print tr
                    exit()
                local_gain=1
                
               # test to find floats and int
                for sample in trace_local.data:
                    # if sample is a float
                    if (int(sample) - sample) != 0:
                        local_gain=2**7
                        trace_local.data = trace_local.data * local_gain
                        break



                if local_gain != 1:
                    for sample_27 in trace_local.data:
                        # si sample * 2**7 est un float
                        if (int(sample_27) - sample_27) != 0:
                            local_gain=local_gain*2
                            trace_local.data = trace_local.data * local_gain
                            break

                ### Last verification !
                for sample_final in trace_local.data:
                        # si sample * 2**15 est un float
                        if (int(sample_final) - sample_final) != 0:
                            print str(tr) +' '+ local_gain,' is not enough !'
                            exit()
                if local_gain > stream_gain:
                    stream_gain = local_gain
                    print "for ",item.station, item.channel,item.start_time, item.end_time,"gain is ",stream_gain
                bar_trace.next()
            bar_trace.finish()
            ### End of channel processing
            bar.next()
        bar.finish()
        

def main():

    # Parametres
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description='Convert miniseed files with geoscope 13 or 14 encoding to\
        miniseed file with  Steim 2 encoding.  ', formatter_class=formatter_class)
    # Station
    parser.add_argument(
        "--sds", type=str, help="path of the SDS archive", required=True)

    parser.add_argument(
        "--dataless_resume", type=str, help="dataless_resume file", required=True,
        default='dataless.p')

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

    converter = geoscope_to_steim2(args)
    converter.convert_and_save()

    #
if __name__ == '__main__':
    np.seterr(divide='ignore', invalid='ignore')
    main()
