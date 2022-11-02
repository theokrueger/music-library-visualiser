#!/usr/bin/python3
'''
music library visualiser
------------------------
a simple python3 script to
visualise various parts of
your music library.
'''

import sys, os, threading, time
import taglib # req pytaglib
from alive_progress import alive_bar # req alive-progress
from matplotlib import pyplot as plt # req matplotlib
import numpy as np # req numpy

HELPTEXT="""\
music library visualiser - a program to plot data about your music library

usage:
    main.py -d <directory> [options]

flags:
    -h, --help       show this help text

variables:
    -d, --directory  set your music library directory (default: prompt)
    -j, --jobs       change maximum number of threads (default: 4)

dependencies:
    [pip]
    pytaglib
    numpy
    matplotlib
    alive-progress

    [system]
    taglib

contact:
    don't.
"""

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
                                case '-h' | '--help':
                                        print(HELPTEXT)
                                        sys.exit(0)
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
                        print('unknown argument: ' + arg)
                        sys.exit(1)

        if opts['verbose']:
                print('options:' + str(opts))

        return opts

opts = parse_args()

## GET LIST OF ALL FILES ##
def walk_directory(input_dir):
        with alive_bar(0) as bar:
                track_files = walk_directory_helper(input_dir, bar)
                bar.text('')
                return track_files

def walk_directory_helper(input_dir, bar):
        bar.text('scanning ' + input_dir)

        if not os.path.exists(input_dir):
                print('directory does not exist:' + input_dir)
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
def get_tags(tracks, tag_list, bar):
        tags = {}
        for track in tracks:
                bar.text('seading tags of ' + track)
                tag_list[track] = taglib.File(track).tags
                bar()
        return tags

## THREADED TAG GETTING ##
def get_tags_threaded(tracks):
        length = len(tracks)
        num_threads = opts['jobs']
        threads = []

        with alive_bar(length) as bar:
                if opts['verbose']:
                        bar.text('awaiting ' + str(num_threads) + ' threads for tag processing')

                # create workers
                tag_list = {}
                min = 1
                for i in range(1, num_threads + 1):
                        max = int( (length / num_threads) * i )
                        if opts['verbose']: # (hack) avoid mess with the statusbar using \n\r
                                print("\n\rcreating worker #" + str(i) + ": items " + str(min) + " to " + str(max), end='')
                        thread = threading.Thread(
                                target=get_tags,
                                args=(tracks[min-1:max], tag_list, bar)
                        )
                        threads.append(thread)
                        min = max + 1

                 # start workers
                for thread in threads:
                        thread.start()

                # await workers
                for thread in threads:
                        thread.join()
                        num_threads -= 1

                return tag_list

## MAIN PROGRAM ##
def main():
        # directory scanning
        if opts['dir'] == None:
                opts['dir'] = input('input a directory to scan:')
        tracks = walk_directory( opts['dir'] )

        # threaded tagging operations
        tracks = get_tags_threaded(tracks)

        data = {} # tag : count
        for track in tracks:
                # get category name
                tag = tracks[track].get('GENRE')
                if tag == None:
                        tag = 'none'
                else:
                        tag = tag[0].lower();

                if data.get(tag) == None: # create category if empty
                        data[tag] = 0

                data[tag] = data[tag] + 1 # increment category

        fig = plt.figure(figsize =(10, 7))
        labels = []
        numbers = []
        for label in data:
                labels.append(label)
                numbers.append(data[label])
        plt.pie(numbers, labels = labels)
        plt.show()

## RUN THE PROGRAM ##
main()
