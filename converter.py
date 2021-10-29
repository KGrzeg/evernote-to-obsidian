#!/usr/bin/python3

import sys, getopt, os

from notepad import Notepad


def print_and_exit(status=None):
    print("converter.py -i <inputfile> [-o <outputdir>] [-r <attachmentdir>] [-p] [-d]")
    print("arguments:")
    print(" -h prints help and exit")
    print(" -i input file ex. notes.enex")
    print(" -o output directory for notes")
    print("  The -o argument is required only if -p is not set")
    print(" -r output directory for resource files relative to -o")
    print('  default value is "res"')
    print(" -p prints note list and exit")
    print(" -d do not save resources")

    sys.exit(status)


def print_notes(inputfile):
    notepad = Notepad(inputfile)
    notepad.print_note_list()


def parse(inputfile, outputdir, attachmentdir, dumpres):
    notepad = Notepad(inputfile)
    notepad.write_notes(outputdir, attachmentdir, dumpres)


def main(argv):
    inputfile = ""
    outputdir = ""
    attachmentdir = "res"
    only_print = False
    dumpres = True

    try:
        opts, args = getopt.getopt(
            argv, "hdpi:o:r:", ["dump", "printlist", "ifile=", "odir=", "attachmentdir="]
        )

    except getopt.GetoptError:
        print_and_exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print_and_exit()

        if opt in ("-p", "--printlist"):
            only_print = True

        if opt in ("-d", "--dump"):
            dumpres = False

        elif opt in ("-i", "--ifile"):
            inputfile = arg

        elif opt in ("-o", "--odir"):
            outputdir = arg

        elif opt in ("-r", "--attachmentdir"):
            attachmentdir = arg

    if inputfile == "":
        print("inputfile is required")
        print_and_exit(2)

    if outputdir == "" and not only_print:
        print("outputdir is required")
        print_and_exit(2)

    attachmentdir = os.path.join(outputdir, attachmentdir)

    print("Input file is ", inputfile)
    print("Output file is ", outputdir)

    if only_print:
        print_notes(inputfile)
    else:
        parse(inputfile, outputdir, attachmentdir, dumpres)


if __name__ == "__main__":
    main(sys.argv[1:])
