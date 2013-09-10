
import argparse
# import nornir_shared.misc as misc
# import nornir_shared
import sys
import os

if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.select('2.8')

import wx
from commandhistory import CommandHistory
import state as state
import PyreGui as PyreGui

app = wx.App(False)
history = CommandHistory()
OutputWindow = None
currentConfig = state.Configuration()
__Transform = None

'''Dictionary of all windows'''
Windows = {}

def ProcessArgs():

    # conflict_handler = 'resolve' replaces old arguments with new if both use the same option flag
    parser = argparse.ArgumentParser('pyre', conflict_handler='resolve')

    parser.add_argument('-Fixed',
                        action='store',
                        required=False,
                        type=str,
                        default=None,
                        help='Path to the fixed image',
                        dest='FixedImageFullPath'
                        )

    parser.add_argument('-Warped',
                        action='store',
                        required=False,
                        type=str,
                        default=None,
                        help='Path to the image to be warped',
                        dest='WarpedImageFullPath'
                        )

    return parser


def ResourcePath():

    try:
        path = os.path.dirname(__file__)
    except:
        path = os.getcwd()

    return os.path.join(path, 'resources')


def README_Import():
    readmePath = os.path.join(os.path.dirname(sys.argv[0]), "readme.txt")
    if not os.path.exists(readmePath):
        return "No readme.txt was found in " + readmePath

    hReadme = open(readmePath, 'r')

    Readme = hReadme.read()
    hReadme.close()
    return Readme


def Run():

    readmetxt = README_Import()
    print readmetxt

    # app = wx.App(False)

    Windows["Fixed"] = PyreGui.MyFrame(None, "Fixed", 'Fixed Image', showFixed=True)
    Windows["Warped"] = PyreGui.MyFrame(None, "Warped", 'Warped Image')
    Windows["Composite"] = PyreGui.MyFrame(None, "Composite", 'Composite', showFixed=True, composite=True)

    app.MainLoop()


def Exit():
    '''Destroy all windows and exit the application'''
    for w in Windows.values():
        w.Destroy()


#    functionStr = 'IrTweakInit("' + str(FixedImageFullPath) + '", "' + str(WarpedImageFullPath) + '")'
#    functionStr = functionStr.replace('\\', '\\\\')
    # nornir_shared.misc.RunWithProfiler("Run()")
   # IrTweakInit(Config.FixedImageFullPath, Config.WarpedImageFullPath)



def AnyVisibleWindows():
        AnyVisibleWindows = False
        for w in Windows.values():
            AnyVisibleWindows = AnyVisibleWindows or w.IsShown()

        return AnyVisibleWindows

   # assert(os.path.exists(Config.WarpedImageFullPath))
   # assert(os.path.exists(Config.FixedImageFullPath))

   # print Readme

