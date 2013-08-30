'''
Created on Oct 16, 2012

@author: u0490822
'''
import os
import pyre
import logging
import nornir_shared.misc
import argparse
import nornir_imageregistration.assemble as assemble
import sys
import PyreGui
from nornir_imageregistration.alignment_record import AlignmentRecord
from nornir_imageregistration.transforms import *
import nornir_imageregistration.stos_brute as stos
import state
from transformviewmodel import TransformViewModel
import numpy

from scipy.misc import imsave
from scipy.ndimage import imread

from OpenGL.GL import *
from OpenGL.GLU import *

if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.select('2.8')
import wx

from commandhistory import CommandHistory
history = CommandHistory()

OutputWindow = None
app = None

__Transform = None

currentConfig = state.Configuration()

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


def LoadTexture(image):
    data = imread(image, flatten=True)
    return TextureForNumpyImage(data)

def TextureForNumpyImage(image):
    '''Create a GL texture for the scipy.ndimage array'''

    image = image / 255.0
    image = numpy.float32(image)
    textureid = glGenTextures(1)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glBindTexture(GL_TEXTURE_2D, textureid)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_LUMINANCE, image.shape[1], image.shape[0],
                               GL_LUMINANCE, GL_FLOAT, image)

    return textureid


def SaveRegisteredWarpedImage(fileFullPath, transform, warpedImage):

    # registeredImage = assemble.WarpedImageToFixedSpace(transform, Config.FixedImageArray.Image.shape, Config.WarpedImageArray.Image)
    registeredImage = AssembleHugeRegisteredWarpedImage(transform,
                                                        pyre.currentConfig.FixedImageViewModel.Image.shape,
                                                        pyre.currentConfig.WarpedImageViewModel.Image)

    imsave(fileFullPath, registeredImage)


def AssembleHugeRegisteredWarpedImage(transform, fixedImageShape, warpedImage):
    '''Cut image into tiles, assemble small chunks'''

    return assemble.TransformImage(transform, fixedImageShape, warpedImage)


def SyncWindows(LookAt, scale):
    '''Make all windows look at the same spot with the same magnification, LookAt point should be in fixed space'''
#    Config.CompositeWin.camera.x = LookAt[0]
#    Config.CompositeWin.camera.y = LookAt[1]
#    Config.CompositeWin.camera.scale = scale
    Windows['Composite'].imagepanel.camera.x = LookAt[0]
    Windows['Composite'].imagepanel.camera.y = LookAt[1]
    Windows['Composite'].imagepanel.camera.scale = scale

#    Config.FixedWindow.camera.x = LookAt[0]
#    Config.FixedWindow.camera.y = LookAt[1]
#    Config.FixedWindow.camera.scale = scale
    Windows['Fixed'].imagepanel.camera.x = LookAt[0]
    Windows['Fixed'].imagepanel.camera.y = LookAt[1]
    Windows['Fixed'].imagepanel.camera.scale = scale

#    warpedLookAt = LookAt
#    if(not Config.WarpedWindow.ShowWarped):
#        warpedLookAt = Config.CurrentTransform.InverseTransform([LookAt])
#        warpedLookAt = warpedLookAt[0]

    warpedLookAt = LookAt
    if(Windows['Warped'].IsShown()):
        warpedLookAt = currentConfig._TransformViewModel.InverseTransform([LookAt])
        warpedLookAt = warpedLookAt[0]



#    Config.WarpedWindow.camera.x = warpedLookAt[0]
#    Config.WarpedWindow.camera.y = warpedLookAt[1]
#    Config.WarpedWindow.camera.scale = scale
    Windows['Warped'].imagepanel.camera.x = LookAt[0]
    Windows['Warped'].imagepanel.camera.y = LookAt[1]
    Windows['Warped'].imagepanel.camera.scale = scale


def RotateTranslateWarpedImage():
    if not (pyre.currentConfig.FixedImageViewModel is None or pyre.currentConfig.WarpedImageViewModel is None):
        alignRecord = stos.SliceToSliceBruteForce(pyre.currentConfig.FixedImageViewModel.Image,
                                                                 pyre.currentConfig.WarpedImageViewModel.Image,
                                                                  LargestDimension=818)
        # alignRecord = IrTools.alignment_record.AlignmentRecord((22.67, -4), 100, -132.5)
        print "Alignment found: " + str(alignRecord)
        transform = alignRecord.ToTransform(pyre.currentConfig.FixedImageViewModel.RawImageSize,
                                             pyre.currentConfig.WarpedImageViewModel.RawImageSize)
        pyre.currentConfig.TransformViewModel.SetPoints(transform.points)

        history.SaveState(pyre.currentConfig.TransformViewModel.SetPoints, pyre.currentConfig.TransformViewModel.TransformModel.points)
        # Config.TransformViewModel = TransformViewModel(Config.CurrentTransform)

def AttemptAlignPoint(transform, fixedImage, warpedImage, controlpoint, warpedpoint, alignmentArea=None):
    '''Try to use the Composite view to render the two tiles we need for alignment'''

    if alignmentArea is None:
        alignmentArea = pyre.currentConfig.AlignmentTileSize

    FixedBotLeft = [controlpoint[0] - (alignmentArea[0] / 2.0),
                    controlpoint[1] - (alignmentArea[1] / 2.0)]


    # Pull image subregions
    warpedImageROI = assemble.WarpedImageToFixedSpace(transform,
                            fixedImage.shape, warpedImage, botleft=FixedBotLeft, area=alignmentArea)

    fixedImageROI = assemble.FixedImage(pyre.currentConfig.FixedImageViewModel.Image, FixedBotLeft, alignmentArea)

    # core.ShowGrayscale([fixedImageROI, warpedImageROI])

    # pool = Pools.GetGlobalMultithreadingPool()

    # task = pool.add_task("AttemptAlignPoint", core.FindOffset, fixedImageROI, warpedImageROI, MinOverlap = 0.2)
    # apoint = task.wait_return()
    # apoint = core.FindOffset(fixedImageROI, warpedImageROI, MinOverlap=0.2)

    anglesToSearch = pyre.currentConfig.AnglesToSearch
    apoint = stos.SliceToSliceBruteForce(fixedImageROI, warpedImageROI, AngleSearchRange=anglesToSearch, MinOverlap=0.25)

    print("Auto-translate result: " + str(apoint))
    return apoint

def DefaultTransform(FixedShape=None, WarpedShape=None):
    # FixedSize = Utils.Images.GetImageS ize(FixedImageFullPath)
    # WarpedSize = Utils.Images.GetImageSize(WarpedImageFullPath)


    if FixedShape is None:
        FixedShape = (512, 512)

    if WarpedShape is None:
        WarpedShape = (512, 512)

    alignRecord = AlignmentRecord(peak=(0, 0), weight=0, angle=0)
    return alignRecord.ToTransform(FixedShape,
                                        WarpedShape)


def DefaultTransformViewModel(FixedShape=None, WarpedShape=None):

    T = DefaultTransform(FixedShape, WarpedShape)

    return TransformViewModel(T)


def AnyVisibleWindows():
        AnyVisibleWindows = False
        for w in pyre.Windows.values():
            AnyVisibleWindows = AnyVisibleWindows or w.IsShown()

        return AnyVisibleWindows

def Exit():
    '''Destroy all windows and exit the application'''
    for w in pyre.Windows.values():
        w.Destroy()

def README_Import():
    readmePath = os.path.join(os.path.dirname(sys.argv[0]), "readme.txt")
    hReadme = open(readmePath, 'r')

    Readme = hReadme.read()
    hReadme.close()
    return Readme


def Run():

    readmetxt = README_Import()
    print readmetxt

    pyre.app = wx.App(False)

    pyre.Windows["Fixed"] = PyreGui.MyFrame(None, "Fixed", 'Fixed Image', showFixed=True)
    pyre.Windows["Warped"] = PyreGui.MyFrame(None, "Warped", 'Warped Image')
    pyre.Windows["Composite"] = PyreGui.MyFrame(None, "Composite", 'Composite', showFixed=True, composite=True)

    pyre.app.MainLoop()

if __name__ == '__main__':

    nornir_shared.misc.SetupLogging(os.curdir, Level=logging.WARNING)

    # If we get a single argument which is a stos file, load it
    if len(sys.argv) == 2:
        singleArg = sys.argv[1]

        (root, ext) = os.path.splitext(singleArg)
        if ext.lower() == ".stos":
            pyre.currentConfig.LoadStos(singleArg)
    else:
        parser = ProcessArgs()
        args = parser.parse_args()

        if not args.WarpedImageFullPath is None:
            pyre.currentConfig.LoadWarpedImage(args.WarpedImageFullPath)

        if not args.FixedImageFullPath is None:
            pyre.currentConfig.LoadFixedImage(args.FixedImageFullPath)

    # Run()

#    functionStr = 'IrTweakInit("' + str(FixedImageFullPath) + '", "' + str(WarpedImageFullPath) + '")'
#    functionStr = functionStr.replace('\\', '\\\\')
    nornir_shared.misc.RunWithProfiler("Run()")
   # IrTweakInit(Config.FixedImageFullPath, Config.WarpedImageFullPath)

