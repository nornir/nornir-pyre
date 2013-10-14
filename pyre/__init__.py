import argparse
import sys
import os

import logging
import commandhistory

from launcher import Run, Windows
from commandhistory import history

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


def Exit():
    '''Destroy all windows and exit the application'''
    for w in Windows.values():
        w.Destroy()


def AnyVisibleWindows():
    AnyVisibleWindows = False
    for w in Windows.values():
        AnyVisibleWindows = AnyVisibleWindows or w.IsShown()

    return AnyVisibleWindows


def ToggleWindow(key):
    if key in Windows:
        w = Windows[key]
        if w.IsShown():
            w.Hide()
        else:
            w.Show()

    if not AnyVisibleWindows():
        Exit()
