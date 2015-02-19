'''
Created on Sep 12, 2013

@author: u0490822
'''

import os
import resources
import sys
import pyre

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
    
    args = pyre.ProcessArgs()
    arg_values = args.parse_args()
     
    app = wx.App(False)
    
    Windows["Fixed"] = PyreGui.StosWindow(None, "Fixed", 'Fixed Image', showFixed=True)
    Windows["Warped"] = PyreGui.StosWindow(None, "Warped", 'Warped Image')
    Windows["Composite"] = PyreGui.StosWindow(None, "Composite", 'Composite', showFixed=True, composite=True)
    Windows["Mosaic"] = PyreGui.MosaicWindow(None, "Mosaic", 'Mosaic')
    
    LoadDataFromArgs(arg_values)

    app.MainLoop()

    print "Exiting main loop"
    
def LoadDataFromArgs(arg_values):
    
    if 'stosFullPath' in arg_values:
        pyre.state.currentStosConfig.LoadStos(arg_values.stosFullPath)
    else:
        if 'WarpedImageFullPath' in arg_values:
            pyre.state.currentStosConfig.LoadWarpedImage(arg_values.WarpedImageFullPath)
        if 'FixedImageFullPath' in arg_values:
            pyre.state.currentStosConfig.LoadFixedImage(arg_values.FixedImageFullPath)
            
    if 'mosaicFullPath' in arg_values:
        tiles_path = os.path.dirname(arg_values.mosaicFullPath)
        if 'mosaicTilesFullPath' in arg_values:
            tiles_path = arg_values.mosaicTilesFullPath
        pyre.state.currentMosaicConfig.LoadMosaic(arg_values.mosaicFullPath, tiles_path)    
    

if __name__ == '__main__':
    pass