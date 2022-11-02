#!/usr/bin/python3
'''
music library visualiser
------------------------
a simple python3 script to
visualise various parts of
your music library.

REQUIREMENTS
------------------------
system:
        taglib

pip:
        pytaglib
        matplotlib
        numpy
        alive-progress

'''

import sys, os, threading, time
import taglib # req pytaglib
from alive_progress import alive_bar # req alive-progress
from matplotlib import pyplot as plt # req matplotlib
import numpy as np # req numpy
## SUPPORTED FILETYPES ##
allowed_types = (
        '.mp3',
        '.ogg',
        '.flac',
        '.wav',
)

## PARSE ARGUMENTS ##
def parse_args():
        opts = {
                'dir' : None,
                'verbose' : False,
                'jobs' : 4,
        }
        skip = 1

        # iterate over all args
        for i, arg in enumerate(sys.argv):
                if skip > 0:
                        skip = skip - 1
                elif arg[:1] == '-':
                        # arg is switch
                        match arg:
                                case '-d' | '--directory':
                                        skip = 1 # next arg is directory
                                        opts['dir'] = sys.argv[i + 1]
                                case '-v' | '--verbose':
                                        opts['verbose'] = True
                                case '-j' | '--jobs':
                                        skip = 1 # next arg is n of jobs
                                        opts['jobs'] = int(sys.argv[i + 1])
                                case _:
                                        print('Unknown argument: ' + arg)
                                        sys.exit(1)
                else:
                        print('arg: ' + arg)
                        # arg is verb
                        print('Unknown argument: ' + arg)
                        sys.exit(1)

        if opts['verbose']:
                print('Options:' + str(opts))

        return opts

opts = parse_args()

## GET LIST OF ALL FILES ##
def walk_directory(input_dir):
        with alive_bar(0) as bar:
                track_files = walk_directory_helper(input_dir, bar)
                bar.text('')
                return track_files

def walk_directory_helper(input_dir, bar):
        bar.text('Scanning ' + input_dir)

        if not os.path.exists(input_dir):
                print('Directory does not exist:' + input_dir)
                sys.exit(1)

        # scan directory
        track_files = []
        for item in os.scandir(input_dir):
                if item.is_file():
                        _, file_extension = os.path.splitext(item)
                        if file_extension != '' and any(file_extension in t for t in allowed_types):
                                track_files.append( os.path.join(input_dir, item) )
                                bar()
                elif item.is_dir():
                        for file in walk_directory_helper( os.path.join(input_dir, item, ""), bar ): # recursive
                                track_files.append( file )

        return track_files

## GET TAGS OF FILES ##
def get_tags(tracks, bar):
        tags = {}
        for track in tracks:
                bar.text('Reading tags of ' + track)
                tags[track] = taglib.File(track).tags
                #print( tags[track].get("ALBUM") )
                bar()
        return tags

## THREADED TAG GETTING ##
def get_tags_threaded(tracks):
        length = len(tracks)
        num_threads = opts['jobs']
        threads = []

        with alive_bar(length) as bar:
                if opts['verbose']:
                        bar.text('Awaiting ' + str(num_threads) + ' threads for tag processing')

                # create workers
                min = 1
                for i in range(1, num_threads + 1):
                        max = int( (length / num_threads) * i )
                        if opts['verbose']:
                                print("\n\rCreating worker #" + str(i) + ": Items " + str(min) + " to " + str(max), end='')
                        thread = threading.Thread(
                                target=get_tags,
                                args=(tracks[min-1:max], bar)
                        )
                        threads.append(thread)
                        min = max + 1

                # start workers
                for thread in threads:
                        thread.start()

                tracks = {}
                # await workers
                for thread in threads:
                        thread.join()
                        num_threads -= 1
                return tracks

## MAIN PROGRAM ##
def main():
        # directory scanning
        if opts['dir'] == None:
                opts['dir'] = input('Input a directory to scan:')
        tracks = walk_directory( opts['dir'] )

        # threaded tagging operations
        tracks = get_tags_threaded(tracks)

## RUN THE PROGRAM ##
main()
