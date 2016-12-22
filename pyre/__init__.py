'''

Pyre commands
=============

The blinking point is the currently selected point

Mouse
______

Left Button

   ``<Left Click>`` to select an existing point
   
   ``Shift + <Left Click>`` to add a new point
   
   ``Alt+Shift + <Left Click>`` to add a new point and auto-align
   
   ``<Left Click> + drag`` to move point under the cursor
   
   ``Ctrl + <Left Click> + drag`` to translate warped image
   
   ``Alt + <Left Click>`` to move currently selected point to mouse position

Right Button

   ``Shift + <Right Click>`` to delete point under the cursor
   
   ``<Right Click> + drag`` to move the view

Scroll wheel

   ``<Scroll wheel>`` zoom in or out
   
   ``Ctrl + <Scroll wheel>`` to rotate warped image

Keys
____

   ``A,W,S,D`` Move the view
   
   ``Page Up/Down`` Change the magnification

   ``M`` Match the view on all windows to look at the same point as the current window (Not Functional for Warped Image)
   
   ``L`` Show transform mesh lines
   
   ``Space`` Auto-align the selected point
   
   ``Shift + Space`` Auto-align all points

   ``Ctrl+Z`` to undo a step
   
   ``Ctrl+X`` to redo a step

   ``Tab`` Change properties of the view.  A warped image may be displayed as it appears registered.  The composite view will switch to a different view.

'''

import argparse
import sys
import os

import logging
import commandhistory

from launcher import Run, Windows
from commandhistory import history

__all__ = ['ui', 'viewmodels', 'views']

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
    
    parser.add_argument('-stos',
                        action='store',
                        required=False,
                        type=str,
                        default=None,
                        help='Path to the stos file to load',
                        dest='stosFullPath'
                        )
    
    parser.add_argument('-mosaic',
                        action='store',
                        required=False,
                        type=str,
                        default=None,
                        help='Path to the mosaic file to load',
                        dest='mosaicFullPath'
                        )
    
    parser.add_argument('-tiles',
                        action='store',
                        required=False,
                        type=str,
                        default=None,
                        help='Path to the tiles referred to in the mosaic file',
                        dest='mosaicTilesFullPath'
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
