'''
Created on Sep 12, 2013

@author: u0490822
'''

import os
import resources
import sys

Windows = {}
app = None


def Run():
    if not hasattr(sys, 'frozen'):
        import wxversion
        wxversion.select('2.8')

    import wx

    import PyreGui as PyreGui

    readmetxt = resources.README()
    print readmetxt
    global app
    global Windows

    app = wx.App(False)

    Windows["Fixed"] = PyreGui.MyFrame(None, "Fixed", 'Fixed Image', showFixed=True)
    Windows["Warped"] = PyreGui.MyFrame(None, "Warped", 'Warped Image')
    Windows["Composite"] = PyreGui.MyFrame(None, "Composite", 'Composite', showFixed=True, composite=True)

    app.MainLoop()

    print "Exiting main loop"

if __name__ == '__main__':
    pass