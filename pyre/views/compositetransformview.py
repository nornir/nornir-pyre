'''
Created on Oct 19, 2012

@author: u0490822
'''


import numpy
import logging
import scipy.spatial

import pyglet.gl as gl
from nornir_imageregistration.transforms import *
 
import imagetransformview

import pyre.views

import pyglet

import os
import resources


class CompositeTransformView(  imagetransformview.ImageTransformView):
    '''
    Combines and image and a transform to render an image
    '''
    @property
    def width(self):
        if self.FixedImageArray is None:
            return None 
        return self.FixedImageArray.width

    @property
    def height(self):
        if self.FixedImageArray is None:
            return None  
        return self.FixedImageArray.height

    @property
    def fixedwidth(self):
        if self.FixedImageArray is None:
            return None 
        return self.FixedImageArray.width

    @property
    def fixedheight(self):
        if self.FixedImageArray is None:
            return None
        return self.FixedImageArray.height


    def __init__(self, FixedImageArray, WarpedImageArray, Transform):
        '''
        Constructor
        '''
        super(CompositeTransformView, self).__init__(ImageViewModel=FixedImageArray, TransformViewModel=Transform, ForwardTransform=True)
         
        self.FixedImageArray = FixedImageArray
        self.WarpedImageArray = WarpedImageArray
        self.TransformViewModel = Transform
        self.ForwardTransform = False

        # imageFullPath = os.path.join(resources.ResourcePath(), "Point.png")
        # self.PointImage = pyglet.image.load(imageFullPath)
        # self.SelectedPointImage = pyglet.image.load(os.path.join(resources.ResourcePath(), "SelectedPoint.png"))

        # Valid Values are 'Add' and 'Subtract'
        self.ImageMode = 'Add'


    def draw_points(self, ForwardTransform=True, SelectedIndex=None, FixedSpace=True, BoundingBox=None, ScaleFactor=1):
        # if(ForwardTransform):
        
        if self.TransformViewModel is None:
            return 

        verts = self.TransformViewModel.WarpedPoints
        verts = self.TransformViewModel.Transform(verts)

        self._draw_points(verts, SelectedIndex, BoundingBox=BoundingBox, ScaleFactor=ScaleFactor)


    def RemoveTrianglesOutsideConvexHull(self, T, convex_hull):
        Triangles = numpy.array(T)
        if Triangles.ndim == 1:
            Triangles = Triangles.reshape(len(Triangles) / 3, 3)

        convex_hull_flat = numpy.unique(convex_hull)

        iTri = len(Triangles) - 1
        while(iTri >= 0):
            tri = Triangles[iTri]
            if tri[0] in convex_hull_flat and tri[1] in convex_hull_flat and tri[2] in convex_hull_flat:
                # OK, find out if the midpoint of any lines are outside the convex hull
                Triangles = numpy.delete(Triangles, iTri, 0)

            iTri = iTri - 1

        return Triangles

    def draw_lines(self, ForwardTransform=True):
        if(self.TransformViewModel is None):
            return

        pyglet.gl.glColor4f(1.0, 0, 0, 1.0)
        ImageArray = self.WarpedImageArray
        for ix in range(0, ImageArray.NumCols):
            for iy in range(0, ImageArray.NumRows):
                x = ImageArray.TextureSize[1] * ix
                y = ImageArray.TextureSize[0] * iy
                h, w = ImageArray.TextureSize

                WarpedCorners = [[y, x],
                                [y, x + w],
                                [y + h, x],
                                [y + h, x + w]]

                FixedCorners = self.TransformViewModel.Transform(WarpedCorners)

                tri = scipy.spatial.Delaunay(FixedCorners)
                LineIndicies = pyre.views.LineIndiciesFromTri(tri.vertices)

                FlatPoints = numpy.fliplr(FixedCorners).ravel().tolist()

                vertarray = (gl.GLfloat * len(FlatPoints))(*FlatPoints)

                gl.glDisable(gl.GL_TEXTURE_2D)

                pyglet.graphics.draw_indexed(len(vertarray) / 2,
                                                         gl.GL_LINES,
                                                         LineIndicies,
                                                         ('v2f', vertarray))
        pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)


    def draw_textures(self, BoundingBox=None, glFunc=None):
        
        

        if not self.FixedImageArray is None:
            FixedColor = None
            if(glFunc == gl.GL_FUNC_ADD):
                FixedColor = (1.0, 0.0, 1.0, 1.0)
    
            self._draw_fixed_image(self.FixedImageArray, FixedColor, BoundingBox=BoundingBox)

        if not self.WarpedImageArray is None:
            WarpedColor = None
            if(glFunc == gl.GL_FUNC_ADD):
                gl.glBlendEquation(glFunc)
                WarpedColor = (0, 1.0, 0, 1.0)
    
            self._draw_warped_image(self.WarpedImageArray, color=WarpedColor, BoundingBox=BoundingBox, glFunc=glFunc)
        # self._draw_fixed_image(self.__WarpedImageArray)
        # self._draw_warped_image(self.__FixedImageArray)
