
import argparse 
import Utils.Misc
import sys
import os
import logging

def ProcessArgs():

    # conflict_handler = 'resolve' replaces old arguments with new if both use the same option flag
    parser = argparse.ArgumentParser('Pyre', conflict_handler = 'resolve');

    parser.add_argument('-Fixed',
                        action = 'store',
                        required = True,
                        type = str,
                        default = None,
                        help = 'Path to the fixed image',
                        dest = 'FixedImageFullPath'
                        );

    parser.add_argument('-Warped',
                        action = 'store',
                        required = True,
                        type = str,
                        default = None,
                        help = 'Path to the image to be warped',
                        dest = 'WarpedImageFullPath'
                        );

    parser.add_argument('-Output',
                        action = 'store',
                        required = True,
                        default = None,
                        type = str,
                        help = 'The path to the image file to write',
                        dest = 'OutputImageFullPath'
                        );

    return parser;

if __name__ == "__main__":
    parser = ProcessArgs();

    args = parser.parse_args();

    Config.WarpedImageFullPath = args.WarpedImageFullPath;
    Config.FixedImageFullPath = args.FixedImageFullPath;
    Config.OutputImageFullPath = args.OutputImageFullPath;
    Config.OutputDir = os.path.dirname(Config.OutputImageFullPath);

    Utils.Misc.SetupLogging(Config.OutputDir, Level = logging.WARNING);

    print sys.argv[0]
    try:
        readmePath = os.path.join(os.path.dirname(sys.argv[0]), "readme.txt");
        hReadme = open(readmePath, 'r');

        Readme = hReadme.read();
        hReadme.close();
    except:
        print "Could not display readme.txt";
        pass

    assert(os.path.exists(Config.WarpedImageFullPath));
    assert(os.path.exists(Config.FixedImageFullPath));

    print Readme;

