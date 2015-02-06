'''
Created on Oct 24, 2012

@author: u0490822
'''
import numpy
from nornir_imageregistration.files.stosfile import StosFile
from nornir_imageregistration.mosaic import Mosaic
import nornir_imageregistration.transforms.factory as factory
from pyre.viewmodels.imageviewmodel import ImageViewModel
from pyre.viewmodels.transformviewmodel import TransformViewModel
import os

# app = wx.App(False)
currentConfig = None

class Configuration(object):

    # Global Variables
    ExportTileSize = [1024, 1024]

    AlignmentTileSize = [128, 128]
    AnglesToSearch = numpy.linspace(-7.5, 7.5, 21)

    @property
    def FixedImageFullPath(self):
        return self.fixedImageViewModel.ImageFilename

    @property
    def WarpedImageFullPath(self):
        return self.warpedImageViewModel.ImageFilename

    @property
    def FixedImageViewModel(self):
        return self._FixedImageViewModel

    @FixedImageViewModel.setter
    def FixedImageViewModel(self, val):
        self._FixedImageViewModel = val
        if not val is None:
            assert(isinstance(val, ImageViewModel))

        self.FireOnImageChanged(True)

    @property
    def WarpedImageViewModel(self):
        return self._WarpedImageViewModel

    @WarpedImageViewModel.setter
    def WarpedImageViewModel(self, val):
        self._WarpedImageViewModel = val
        if not val is None:
            assert(isinstance(val, ImageViewModel))

        self.FireOnImageChanged(False)

    @property
    def CompositeImageViewModel(self):
        return self._CompositeImageViewModel

    @CompositeImageViewModel.setter
    def CompositeImageViewModel(self, val):
        self._CompositeImageViewModel = val
        if not val is None:
            assert(isinstance(val, ImageViewModel))

        self.FireOnImageChanged(False)

    @property
    def TransformViewModel(self):
        if self._TransformViewModel is None:
            FixedShape = None
            WarpedShape = None

            if not self.WarpedImageViewModel is None:
                WarpedShape = [self.WarpedImageViewModel.height, self.WarpedImageViewModel.width]

            if not self.FixedImageViewModel is None:
                FixedShape = [self.FixedImageViewModel.height, self.FixedImageViewModel.width]

            self.TransformViewModel = TransformViewModel.CreateDefault(FixedShape, WarpedShape)

        return self._TransformViewModel

    @TransformViewModel.setter
    def TransformViewModel(self, val):
        self._TransformViewModel = val

        if not val is None:
            assert(isinstance(val, TransformViewModel))

        self.FireOnTransformViewModelChanged()

    def __init__(self):

        self._TransformViewModel = None
        self._WarpedImageViewModel = None
        self._FixedImageViewModel = None
        self._CompositeImageViewModel = None

        self._OnTransformViewModelChangeEventListeners = []
        self._OnImageChangeEventListeners = []

    def AddOnTransformViewModelChangeEventListener(self, func):
        self._OnTransformViewModelChangeEventListeners.append(func)

    def FireOnTransformViewModelChanged(self):
        for func in self._OnTransformViewModelChangeEventListeners:
            func()

    def AddOnImageViewModelChangeEventListener(self, func):
        self._OnImageChangeEventListeners.append(func)


    def FireOnImageChanged(self, FixedImage):
        for func in self._OnImageChangeEventListeners:
            func(FixedImage)


    def LoadTransform(self, StosData):
        ''':return: A Transform'''

        obj = None
        if isinstance(StosData, str):
            obj = StosFile.Load(StosData)
        elif isinstance(StosData, StosFile):
            obj = StosData

        if obj is None:
            return

        stostransform = factory.LoadTransform(obj.Transform)
        if not stostransform is None:
            self.TransformViewModel.SetPoints(stostransform.points)


    def LoadFixedImage(self, ImageFileFullPath):
        self.LoadImage(ImageFileFullPath, FixedImage=True)


    def LoadWarpedImage(self, ImageFileFullPath):
        self.LoadImage(ImageFileFullPath, FixedImage=False)


    def LoadImage(self, imageFullPath, FixedImage=True):

        if not os.path.exists(imageFullPath):
            print("Image passed to load image does not exist: " + imageFullPath)
            return

        ivm = ImageViewModel(imageFullPath)
        if FixedImage:
            self.FixedImageViewModel = ivm
        else:
            self.WarpedImageViewModel = ivm
        
            
    def LoadMosaic(self, mosaicFullPath):
        dirname = os.path.dirname(mosaicFullPath)
        filename = os.path.basename(mosaicFullPath)
        
        mosaic = Mosaic.LoadFromMosaicFile(mosaicFullPath)
        
        listImageViews = []
        
 #       for filename, transform in mosaic.ImageToTransform.items():
 
    def LoadStos(self, stosFullPath):

        dirname = os.path.dirname(stosFullPath)
        filename = os.path.basename(stosFullPath)

        obj = StosFile.Load(os.path.join(dirname, filename))
        self.LoadTransform(stosFullPath)

        if os.path.exists(obj.ControlImageFullPath):
            self.LoadFixedImage(obj.ControlImageFullPath)
        else:
            nextPath = os.path.join(dirname, obj.ControlImageName)
            if os.path.exists(nextPath):
                self.LoadFixedImage(nextPath)
            else:
                print("Could not find fixed image: " + obj.ControlImageFullPath)

        if os.path.exists(obj.MappedImageFullPath):
            self.LoadWarpedImage(obj.MappedImageFullPath)
        else:
            nextPath = os.path.join(dirname, obj.MappedImageName)
            if os.path.exists(nextPath):
                self.LoadWarpedImage(nextPath)
            else:
                print("Could not find fixed image: " + obj.MappedImageFullPath)

currentConfig = Configuration()

if __name__ == '__main__':
    pass
