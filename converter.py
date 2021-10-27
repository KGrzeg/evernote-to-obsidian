#!/usr/bin/python3

import sys, getopt, os

from notepad import Notepad


def print_and_exit(status=None):
    print("converter.py -i <inputfile> [-o <outputdir>] [-s <htmldir>] [-p]")
    print("arguments:")
    print(" -h prints help and exit")
    print(" -i input file ex. notes.enex")
    print(" -o output directory for notes")
    print("  The -o argument is required only if -p is not set")
    print(" -s output directory for html files")
    print('  default value is "html" relative to -o')
    print(" -p prints notes list and exit")

    sys.exit(status)


def print_notes(inputfile):
    notepad = Notepad(inputfile)
    notepad.print_notes()


def parse(inputfile, outputdir):
    notepad = Notepad(inputfile)


def main(argv):
    inputfile = ""
    outputdir = ""
    sources = ""
    only_print = False

    try:
        opts, args = getopt.getopt(
            argv, "hpi:o:s:", ["printlist", "ifile=", "odir=", "sources="]
        )

    except getopt.GetoptError:
        print_and_exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print_and_exit()

        if opt in ("-p", "--printlist"):
            only_print = True

        elif opt in ("-i", "--ifile"):
            inputfile = arg

        elif opt in ("-o", "--odir"):
            outputdir = arg

        elif opt in ("-s", "--sources"):
            sources = arg

    if inputfile == "":
        print("inputfile is required")
        print_and_exit(2)

    if outputdir == "" and not only_print:
        print("outputdir is required")
        print_and_exit(2)

    if sources == "":
        sources = os.path.join(outputdir, "html")

    print("Input file is ", inputfile)
    print("Output file is ", outputdir)

    if only_print:
        print_notes(inputfile)
    else:
        parse(inputfile, outputdir)


if __name__ == "__main__":
    main(sys.argv[1:])
