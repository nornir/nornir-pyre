'''
Created on Oct 17, 2012

@author: u0490822
'''

import math
import numpy
import logging
import os
import scipy.ndimage
import nornir_shared.images as images
import sys
from pylab import *
import resources
import nornir_imageregistration.core as core
import common

from OpenGL.GL import *
from OpenGL.GLU import *
import nornir_imageregistration

Logger = logging.getLogger("ImageArray")


class ImageViewModel(object):
    '''
    Represents a numpy image as an array of textures.  Read-only.
    '''
    
    #The largest dimension we allow a texture to have
    MaxTextureDimension = int(4096)

    @property
    def Image(self):
        return self._Image

    @property
    def width(self):
        '''Size of the full image'''
        return self._Image.shape[1]

    @property
    def height(self):
        '''Size of the full image'''
        return self._Image.shape[0]

    @property
    def NumRows(self):
        '''Number of texture rows for the whole image'''
        return self._NumRows

    @property
    def NumCols(self):
        '''Number of texture columns for the whole image'''
        return self._NumCols

    @property
    def size(self):
        '''Size of the full image'''
        return (self._height, self._width)

    @property
    def shape(self):
        '''Size of the full image'''
        return (self._height, self._width)   

    @property
    def ImageArray(self):
        '''Array of textures for the full image'''
        if self._ImageArray is None:
            self._ImageArray = self.CreateImageArray()
        return self._ImageArray
    
    @property
    def TextureSize(self):
        '''Size of a texture'''
        return self._TextureSize


    @property
    def ImageFilename(self):
        '''Filename we loaded'''
        return self._ImageFilename
    
    @classmethod
    def FindTextureSize(cls, shape):
        _TextureSize = [int(core.NearestPowerOfTwo(shape[0])), int(core.NearestPowerOfTwo(shape[1]))]
        
        if _TextureSize[0] > cls.MaxTextureDimension:
            _TextureSize[0] = cls.MaxTextureDimension
            
        if _TextureSize[1] > cls.MaxTextureDimension:
            _TextureSize[1] = cls.MaxTextureDimension
            
        return _TextureSize
        

    def __init__(self, ImageInput):
        '''
        Constructor, _Image is either path to file or a numpy array
        '''
        # self._TileSize = (int(1024), int(1024))
        # self.TextureHeight = int(math.pow(2, math.ceil(math.log(self.height, 2))))
        # self.TextureWidth = int(math.pow(2, math.ceil(math.log(self.width, 2))))
        self._ImageFilename = None 

        # self.ViewTransform = transform

        # self.RawImageSize = Utils.Images.GetImageSize(ImageInput)

        Image = None

        '''Convert the passed _Image to a Luminance Texture, cutting the image into smaller images as necessary'''
        if isinstance(ImageInput, str) or isinstance(ImageInput, unicode):

            Logger.info("Loading image: " + ImageInput)
            self._ImageFilename = ImageInput

            self._Image = scipy.ndimage.imread(ImageInput, flatten=True)

           # self._Image = numpy.flipud(self._Image)
            # self.RawImageSize = self._Image.shape[1], self._Image.shape[0]

            Logger.info("Done")
        else:
            Image = ImageInput

        # Images are read only, create a memory mapped file for the image for use with multithreading
        # self._Image = core.npArrayToReadOnlySharedArray(self._Image)

        self.RawImageSize = self._Image.shape
        
        self._TextureSize = ImageViewModel.FindTextureSize(self.RawImageSize)
        self._NumCols = int(math.ceil(self._Image.shape[1] / float(self.TextureSize[1])))
        self._NumRows = int(math.ceil(self._Image.shape[0] / float(self.TextureSize[0])))

        self._height, self._width = self.NumRows * self.TextureSize[nornir_imageregistration.iPoint.Y], self.NumCols * self.TextureSize[nornir_imageregistration.iPoint.X]

        self._ImageArray = None


    def ResizeToPowerOfTwo(self, InputImage, Tilesize=None):

        if Tilesize is None:
            Tilesize = self._TileSize

        Resize = scipy.ndimage.imread(InputImage, flatten=True)

        height = Resize.shape[0]
        width = Resize.shape[1]

        NumCols = math.ceil(width / float(Tilesize[0]))
        NumRows = math.ceil(height / float(Tilesize[1]))

        newwidth = NumCols * Tilesize[0]
        newheight = NumRows * Tilesize[1]

        newImage = numpy.zeros((newheight, newwidth), dtype=Resize.dtype)

        newImage[0:Resize.shape[0], 0:Resize.shape[1]] = Resize

        return newImage

    def CreateArrayTile(self, ix, iy):
        '''Create a texture for the tile at given coordinates'''
        return


    def CreateImageArray(self):
        '''
        Generate an array of textures when images are larger than the max texture size
        '''
        # from Pools import Threadpool

        Logger.info("CreateImageArray")
        # Round up size to nearest power of 2
 
        TextureGrid = list()

        print_output = self.NumCols > 1 and self.NumRows > 1
        
        if print_output:
            print('\nConverting image to ' + str(self.NumCols) + "x" + str(self.NumRows) + ' grid of OpenGL textures')
            
        for iX in range(0, self.width, self.TextureSize[nornir_imageregistration.iPoint.X]):
            columnTextures = list()
            lastCol = iX + self.TextureSize[nornir_imageregistration.iPoint.X] > self.width

            end_iX = iX + self.TextureSize[nornir_imageregistration.iPoint.X]
            pad_image = end_iX > self.Image.shape[1]
            if pad_image:
                end_iX = self.Image.shape[1]

            if print_output:
                sys.stdout.write('\n')
                
            # print "ix " + str(iX)
            for iY in range(0, self.height, self.TextureSize[nornir_imageregistration.iPoint.Y]):

                if print_output:
                    sys.stdout.write('.')
                lastRow = iY + self.TextureSize[nornir_imageregistration.iPoint.Y] > self.height

                end_iY = iY + self.TextureSize[nornir_imageregistration.iPoint.Y]
                if end_iY > self.Image.shape[0]:
                    end_iY = self.Image.shape[0]
                    pad_image = True

                # temp = _Image[iX:iX + self.TextureSize[0], iY:iY + self.TextureSize[1]]

                # if not lastRow:

                temp = None
                if pad_image:
                    paddedImage = numpy.zeros(self.TextureSize)
                    paddedImage[0:end_iY - iY, 0:end_iX - iX] = self.Image[iY:end_iY, iX:end_iX]
                    temp = paddedImage
                else:
                    temp = self.Image[iY:end_iY, iX:end_iX]

                texture = resources.TextureForNumpyImage(temp)
                del temp
                columnTextures.append(texture)

            TextureGrid.append(columnTextures)

        if print_output:
            print('\nTexture creation complete\n')
            
        Logger.info("Completed CreateImageArray")
        return TextureGrid



