#!/usr/bin/python3

import sys, getopt

from notepad import Notepad


def print_and_exit(status=None):
    print("converter.py -i <inputfile> -o <outputdir>")
    sys.exit(status)


def parse(inputfile):
    notepad = Notepad(inputfile)


def main(argv):
    inputfile = ""
    outputdir = ""

    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])

    except getopt.GetoptError:
        print_and_exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print_and_exit()

        elif opt in ("-i", "--ifile"):
            inputfile = arg

        elif opt in ("-o", "--ofile"):
            outputdir = arg

    if inputfile == "":
        print("inputfile is required")
        print_and_exit(2)

    if outputdir == "":
        print("outputdir is required")
        print_and_exit(2)

    print("Input file is ", inputfile)
    print("Output file is ", outputdir)

    parse(inputfile)


if __name__ == "__main__":
    main(sys.argv[1:])
