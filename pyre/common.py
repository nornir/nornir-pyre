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
from nornir_imageregistration.transforms import *
import nornir_imageregistration.stos_brute as stos
import numpy

from scipy.misc import imsave
from scipy.ndimage import imread

from OpenGL.GL import *
from OpenGL.GLU import *


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
    pyre.Windows['Composite'].imagepanel.camera.x = LookAt[0]
    pyre.Windows['Composite'].imagepanel.camera.y = LookAt[1]
    pyre.Windows['Composite'].imagepanel.camera.scale = scale

#    Config.FixedWindow.camera.x = LookAt[0]
#    Config.FixedWindow.camera.y = LookAt[1]
#    Config.FixedWindow.camera.scale = scale
    pyre.Windows['Fixed'].imagepanel.camera.x = LookAt[0]
    pyre.Windows['Fixed'].imagepanel.camera.y = LookAt[1]
    pyre.Windows['Fixed'].imagepanel.camera.scale = scale

#    warpedLookAt = LookAt
#    if(not Config.WarpedWindow.ShowWarped):
#        warpedLookAt = Config.CurrentTransform.InverseTransform([LookAt])
#        warpedLookAt = warpedLookAt[0]

    warpedLookAt = LookAt
    if(pyre.Windows['Warped'].IsShown()):
        warpedLookAt = pyre.currentConfig._TransformViewModel.InverseTransform([LookAt])
        warpedLookAt = warpedLookAt[0]



#    Config.WarpedWindow.camera.x = warpedLookAt[0]
#    Config.WarpedWindow.camera.y = warpedLookAt[1]
#    Config.WarpedWindow.camera.scale = scale
    pyre.Windows['Warped'].imagepanel.camera.x = LookAt[0]
    pyre.Windows['Warped'].imagepanel.camera.y = LookAt[1]
    pyre.Windows['Warped'].imagepanel.camera.scale = scale


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

        pyre.history.SaveState(pyre.currentConfig.TransformViewModel.SetPoints, pyre.currentConfig.TransformViewModel.TransformModel.points)
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


if __name__ == "__main__":
    nornir_shared.misc.SetupLogging(os.curdir, Level=logging.WARNING)

    # If we get a single argument which is a stos file, load it
    if len(sys.argv) == 2:
        singleArg = sys.argv[1]

        (root, ext) = os.path.splitext(singleArg)
        if ext.lower() == ".stos":
            pyre.currentConfig.LoadStos(singleArg)
    else:
        parser = pyre.ProcessArgs()
        args = parser.parse_args()

        if not args.WarpedImageFullPath is None:
            pyre.currentConfig.LoadWarpedImage(args.WarpedImageFullPath)

        if not args.FixedImageFullPath is None:
            pyre.currentConfig.LoadFixedImage(args.FixedImageFullPath)

    pyre.Run()


