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
from obspy import read,Stream
from obspy.io.xseed import Parser
from obspy.signal.invsim import corn_freq_2_paz
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm 


class pyql(object):

    def __init__(self, args):

        self.args=args
        self.file_list = []
        self.file_streams = []
        if len(args.i) == 1:
            args.i=args.i[0]
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
    
    def plot(self):
        if self.args.overlay:
            st=Stream()
            color=iter(cm.rainbow(np.linspace(0,1,len(self.file_list))))  
            for input_file in self.file_list:
                for tr in read(input_file):
                    c=next(color)
                    times = [(tr.stats.starttime + t).datetime for t in tr.times()]
                    plt.plot(times, tr.data, linestyle="-", marker=None,
                                  color=c, label=tr.id)
            plt.grid()
            plt.legend()
            plt.show()
        else:
            st=Stream()
            for input_file in self.file_list:
                 st +=read(input_file)
            st.plot()
                 
                    
                    
def main():

    # Parametres
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description='plot files with obspy, formatter_class=formatter_class'    )
    # Station
    parser.add_argument(
        "-i", type=str, help="Name of the input file, files or directory",
         required=False,nargs='*')

    parser.add_argument("-o", "--overlay", dest="overlay",
                        action="count", default=None,
                        help="plot data on the same figure")


    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="count", default=0,
                        help="increases log verbosity for each occurence.")

    # parse arguments
    args = parser.parse_args()


    if args.i is None:
        print "Pyql needs at least a filename "
        print parser.print_help()
        sys.exit()

    p=pyql(args)
    p.plot()

    #
if __name__ == '__main__':
    main()
