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
from nornir_imageregistration.transforms import *
import nornir_imageregistration.stos_brute as stos
import numpy

from scipy.misc import imsave
from scipy.ndimage import imread
from commandhistory import history

from launcher import Windows
import nornir_imageregistration


def SaveRegisteredWarpedImage(fileFullPath, transform, warpedImage):
    from pyre.state import currentStosConfig

    # registeredImage = assemble.WarpedImageToFixedSpace(transform, Config.FixedImageArray.Image.shape, Config.WarpedImageArray.Image)
    registeredImage = AssembleHugeRegisteredWarpedImage(transform,
                                                        currentStosConfig.FixedImageViewModel.Image.shape,
                                                        currentStosConfig.WarpedImageViewModel.Image)

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
        warpedLookAt = currentStosConfig._TransformViewModel.InverseTransform([LookAt])
        warpedLookAt = warpedLookAt[0]



#    Config.WarpedWindow.camera.x = warpedLookAt[0]
#    Config.WarpedWindow.camera.y = warpedLookAt[1]
#    Config.WarpedWindow.camera.scale = scale
    Windows['Warped'].imagepanel.camera.x = LookAt[0]
    Windows['Warped'].imagepanel.camera.y = LookAt[1]
    Windows['Warped'].imagepanel.camera.scale = scale


def RotateTranslateWarpedImage(LimitImageSize=False):
    from pyre.state import currentStosConfig

    largestdimension = 2047
    if LimitImageSize:
        largestdimension = 818

    if not (currentStosConfig.FixedImageViewModel is None or currentStosConfig.WarpedImageViewModel is None):
        alignRecord = stos.SliceToSliceBruteForce(currentStosConfig.FixedImageViewModel.Image,
                                                                 currentStosConfig.WarpedImageViewModel.Image,
                                                                  LargestDimension=largestdimension,
                                                                  Cluster=False)
        # alignRecord = IrTools.alignment_record.AlignmentRecord((22.67, -4), 100, -132.5)
        print "Alignment found: " + str(alignRecord)
        transform = alignRecord.ToTransform(currentStosConfig.FixedImageViewModel.RawImageSize,
                                             currentStosConfig.WarpedImageViewModel.RawImageSize)
        currentStosConfig.TransformController.SetPoints(transform.points)

        history.SaveState(currentStosConfig.TransformController.SetPoints, currentStosConfig.TransformController.Transform.points)


def AttemptAlignPoint(transform, fixedImage, warpedImage, controlpoint, warpedpoint, alignmentArea=None):
    '''Try to use the Composite view to render the two tiles we need for alignment'''
    from pyre.state import currentStosConfig

    if alignmentArea is None:
        alignmentArea = currentStosConfig.AlignmentTileSize
        
    FixedRectangle = nornir_imageregistration.Rectangle.CreateFromPointAndArea(point=[controlpoint[0] - (alignmentArea[0] / 2.0),
                                                                                   controlpoint[1] - (alignmentArea[1] / 2.0)],
                                                                             area=alignmentArea)

    FixedRectangle = nornir_imageregistration.Rectangle.SafeRound(FixedRectangle)
    FixedRectangle = nornir_imageregistration.Rectangle.change_area(FixedRectangle, alignmentArea)
    
    # Pull image subregions
    warpedImageROI = assemble.WarpedImageToFixedSpace(transform,
                            fixedImage.shape, warpedImage, botleft=FixedBotLeft, area=alignmentArea, extrapolate=True)

    fixedImageROI = nornir_imageregistration.core.CropImage(currentStosConfig.FixedImageViewModel.Image, FixedRectangle.BottomLeft[1], FixedRectangle.BottomLeft[0], FixedRectangle.Area[1], FixedRectangle.Area[0])

    # nornir_imageregistration.core.ShowGrayscale([fixedImageROI, warpedImageROI])

    # pool = Pools.GetGlobalMultithreadingPool()

    # task = pool.add_task("AttemptAlignPoint", core.FindOffset, fixedImageROI, warpedImageROI, MinOverlap = 0.2)
    # apoint = task.wait_return()
    # apoint = core.FindOffset(fixedImageROI, warpedImageROI, MinOverlap=0.2)

    anglesToSearch = currentStosConfig.AnglesToSearch
    apoint = stos.SliceToSliceBruteForce(fixedImageROI, warpedImageROI, AngleSearchRange=anglesToSearch, MinOverlap=0.25, SingleThread=True, Cluster=False)

    print("Auto-translate result: " + str(apoint))
    return apoint

def Run():
    pyre.Run()


if __name__ == "__main__":
    from pyre.state import currentStosConfig

    nornir_shared.misc.SetupLogging(os.curdir, Level=logging.WARNING)

    # If we get a single argument which is a stos file, load it
    if len(sys.argv) == 2:
        singleArg = sys.argv[1]

        (root, ext) = os.path.splitext(singleArg)
        if ext.lower() == ".stos":
            currentStosConfig.LoadStos(singleArg)
    else:
        parser = pyre.ProcessArgs()
        args = parser.parse_args()

        if not args.WarpedImageFullPath is None:
            currentStosConfig.LoadWarpedImage(args.WarpedImageFullPath)

        if not args.FixedImageFullPath is None:
            currentStosConfig.LoadFixedImage(args.FixedImageFullPath)

    pyre.Run()


