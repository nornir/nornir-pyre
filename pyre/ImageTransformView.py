
'''
Created on Oct 19, 2012

@author: u0490822
'''


import numpy
import logging
import scipy.spatial
import os

import pyglet

import pyglet.gl as gl
from nornir_imageregistration.transforms import *

from nornir_imageregistration.geometry.rectangle import Rectangle

from transformviewmodel import TransformViewModel

import time

import pyre


class RenderCache(object):
    '''This object stores variables that must be calculated every time the transform changes'''
    pass

class ImageTransformView(object):
    '''
    Combines and image and a transform to render an image.  Read-only operations
    '''

    @property
    def width(self):
        if self._ImageViewModel is None:
            return 1

        return self._ImageViewModel.width

    @property
    def height(self):
        if self._ImageViewModel is None:
            return 1

        return self._ImageViewModel.height

    @property
    def ImageViewModel(self):
        return self._ImageViewModel;

    @property
    def TransformViewModel(self):
        return self._TransformViewModel

    @TransformViewModel.setter
    def TransformViewModel(self, value):
        if not self._TransformViewModel is None:
            self._TransformViewModel.RemoveOnChangeEventListener(self.OnTransformChanged)

        self._TransformViewModel = value

        if not value is None:
            assert(isinstance(value, TransformViewModel))
            self._TransformViewModel.AddOnChangeEventListener(self.OnTransformChanged)
        self.OnTransformChanged()

    def __init__(self, ImageViewModel, TransformViewModel=None, ForwardTransform=True):
        '''
        Constructor
        '''
        self._TransformViewModel = None

        self.rendercache = RenderCache()
        self.ForwardTransform = ForwardTransform
        self._ImageViewModel = ImageViewModel
        self.TransformViewModel = TransformViewModel

       # print "Pyre resource path: " + ResourcePath()

        self.PointImage = pyglet.image.load(os.path.join(pyre.ResourcePath(), "Point.png"))
        self.PointImage.anchor_x = self.PointImage.width / 2
        self.PointImage.anchor_y = self.PointImage.height / 2
        self.SelectedPointImage = pyglet.image.load(os.path.join(pyre.ResourcePath(), "SelectedPoint.png"));
        self.SelectedPointImage.anchor_x = self.SelectedPointImage.width / 2
        self.SelectedPointImage.anchor_y = self.SelectedPointImage.height / 2


        self.Debug = False

        self.PointGroup = pyglet.sprite.SpriteGroup(texture=self.PointImage.get_texture(), blend_src=pyglet.gl.GL_SRC_ALPHA, blend_dest=pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.SelectedPointSpriteOn = pyglet.sprite.Sprite(self.SelectedPointImage, 0, 0)
        self.SelectedPointSpriteOff = pyglet.sprite.Sprite(self.PointImage, 0, 0)

    def OnTransformChanged(self):

        # Keep the points if we can
        SavedPointCache = RenderCache()
        if hasattr(self.rendercache, 'PointCache'):
            PointCache = self.rendercache.PointCache
            if hasattr(PointCache, 'Sprites'):
                if len(PointCache.Sprites) == len(self.TransformViewModel.FixedPoints):
                    SavedPointCache = PointCache

        self.rendercache = None
        self.rendercache = RenderCache()

        if not SavedPointCache is None:
            self.rendercache.PointCache = SavedPointCache

    def _draw_points(self, verts, SelectedIndex=None, BoundingBox=None, ScaleFactor=1.0):

        PointBaseScale = 8.0

        PointCache = RenderCache()
        if hasattr(self.rendercache, 'PointCache'):
            if not self.rendercache.PointCache is None:
                PointCache = self.rendercache.PointCache

        self.PointImage.anchor_x = self.PointImage.width / 2
        self.PointImage.anchor_y = self.PointImage.height / 2

        self.SelectedPointImage.anchor_x = self.PointImage.width / 2
        self.SelectedPointImage.anchor_y = self.PointImage.height / 2

        scale = (PointBaseScale / float(self.PointImage.width)) * float(ScaleFactor)

        if(scale < PointBaseScale / float(self.PointImage.width)):
            scale = PointBaseScale / float(self.PointImage.width)

        if hasattr(PointCache, 'LastSelectedPointIndex'):
            if self.rendercache.LastSelectedPointIndex != SelectedIndex:
                if hasattr(PointCache, 'sprites'):
                    del PointCache.sprites
                    del PointCache.PointBatch

        self.rendercache.LastSelectedPointIndex = SelectedIndex

        if hasattr(PointCache, 'Sprites'):
            try:
                sprites = PointCache.Sprites
                PointBatch = PointCache.PointBatch

                for i in range(0, len(verts)):
                    point = verts[i]
                    s = sprites[i]
                    s.x = point[1]
                    s.y = point[0]
                    s.scale = scale

                    if SelectedIndex is not None:
                        if i == SelectedIndex:
                            if(time.time() % 1 > 0.5):
                                s.image = self.SelectedPointImage
                            else:
                                s.image = self.PointImage

                PointBatch.draw()
            except:
                self.rendercache.PointCache = None
                l = logging.getLogger('ImageTransformView')
                l.error("Cached Point sprite error, resetting cache")

        else:
            PointBatch = pyglet.graphics.Batch()
            spriteList = list()
            for i in range(0, len(verts)):
                point = verts[i]

                Image = self.PointImage
                if SelectedIndex is not None:
                    if(i == SelectedIndex and  time.time() % 1 > .5):
                        Image = self.SelectedPointImage

                s = pyglet.sprite.Sprite(Image, x=point[1], y=point[0], group=self.PointGroup, batch=PointBatch)
                s.scale = scale
                spriteList.append(s)


            PointCache.Sprites = spriteList
            PointCache.PointBatch = PointBatch

            PointBatch.draw()

            self.rendercache.PointCache = PointCache
            # print str(s.x) + ", " + str(s.y)

        # PointBatch.draw()

    def draw_points(self, SelectedIndex=None, FixedSpace=True, BoundingBox=None, ScaleFactor=1):

        if(not FixedSpace):
            verts = self.TransformViewModel.WarpedPoints
        else:
            verts = self.TransformViewModel.FixedPoints

        self._draw_points(verts, SelectedIndex, BoundingBox, ScaleFactor)

    def draw_lines(self,):
        if(self.TransformViewModel is None):
            return

        Triangles = []
        if(self.ForwardTransform):
            # Triangles = self.__Transform.WarpedTriangles
            verts = numpy.fliplr(self.TransformViewModel.WarpedPoints)
            Triangles = self.TransformViewModel.WarpedTriangles
        else:
            verts = numpy.fliplr(self.TransformViewModel.FixedPoints)
            Triangles = self.TransformViewModel.FixedTriangles

        LineIndicies = []
        for tri in Triangles:
            LineIndicies.append(tri[0])
            LineIndicies.append(tri[1])
            LineIndicies.append(tri[1])
            LineIndicies.append(tri[2])
            LineIndicies.append(tri[2])
            LineIndicies.append(tri[0])

        zCoords = numpy.zeros((len(verts), 1), dtype=verts.dtype)
        Points = numpy.hstack((verts, zCoords))

        FlatPoints = Points.ravel().tolist()
        vertarray = (gl.GLfloat * len(FlatPoints))(*FlatPoints)

        gl.glDisable(gl.GL_TEXTURE_2D)
        pyglet.gl.glColor4f(1.0, 0, 0, 1.0)
        pyglet.graphics.draw_indexed(len(vertarray) / 3,
                                                 gl.GL_LINES,
                                                 LineIndicies,
                                                 ('v3f', vertarray))
        pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)

    def _draw_fixed_image(self, ImageViewModel, color, BoundingBox=None):
        '''Draw a fixed image, bounding box indicates the visible area.  Everything is drawn if BoundingBox is None'''
        if hasattr(self.rendercache, 'FixedImageDataGrid'):
            FixedImageDataGrid = self.rendercache.FixedImageDataGrid
        else:
            FixedImageDataGrid = []
            for i in range(0, ImageViewModel.NumCols):
                FixedImageDataGrid.append([None] * ImageViewModel.NumRows)
                self.rendercache.FixedImageDataGrid = FixedImageDataGrid

        if color is None:
            color = (1.0, 1.0, 1.0, 1.0)

        for ix in range(0, ImageViewModel.NumCols):
            column = ImageViewModel.ImageArray[ix]
            cacheColumn = FixedImageDataGrid[ix]
            for iy in range(0, ImageViewModel.NumRows):

                texture = column[iy]
                t = (0.0, 0.0, 0.0,
                     1.0, 0.0, 0.0,
                     1.0, 1.0, 0.0,
                     0.0, 1.0, 0.0)
                w, h = ImageViewModel.TextureSize
                x = ImageViewModel.TextureSize[1] * ix
                y = ImageViewModel.TextureSize[0] * iy

                # Check bounding box if it exists
                if not BoundingBox is None:
                    if not Rectangle.contains(BoundingBox, [x, y, x + w, y + h]):
                        continue

                array = None
                if cacheColumn[iy] is None:
                    z = 0
                    array = (gl.GLfloat * 32)(
                         t[0], t[1], t[2], 1.,
                         x, y, z, 1.,
                         t[3], t[4], t[5], 1.,
                         x + w, y, z, 1.,
                         t[6], t[7], t[8], 1.,
                         x + w, y + h, z, 1.,
                         t[9], t[10], t[11], 1.,
                         x, y + h, z, 1.)

                    cacheColumn[iy] = array
                else:
                    array = cacheColumn[iy]

                gl.glEnable(gl.GL_TEXTURE_2D)
                gl.glDisable(gl.GL_CULL_FACE)

                pyglet.gl.glColor4f(color[0], color[1], color[2], color[3])

                gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
                gl.glPushClientAttrib(gl.GL_CLIENT_VERTEX_ARRAY_BIT)
                gl.glInterleavedArrays(gl.GL_T4F_V4F, 0, array)
                gl.glDrawArrays(gl.GL_QUADS, 0, 4)
                gl.glPopClientAttrib()

                pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)


    def _draw_warped_image(self, ImageViewModel, ForwardTransform=True, color=None, BoundingBox=None, glFunc=gl.GL_FUNC_ADD):

        if color is None:
            color = (1.0, 1.0, 1.0, 1.0)

        if hasattr(self.rendercache, 'WarpedImageDataGrid'):
            WarpedImageDataGrid = self.rendercache.WarpedImageDataGrid
        else:
            WarpedImageDataGrid = []
            for i in range(0, ImageViewModel.NumCols):
                WarpedImageDataGrid.append([None] * ImageViewModel.NumRows)

            self.rendercache.WarpedImageDataGrid = WarpedImageDataGrid

        for ix in range(0, ImageViewModel.NumCols):
            column = ImageViewModel.ImageArray[ix]
            for iy in range(0, ImageViewModel.NumRows):
                texture = column[iy]
                x = ImageViewModel.TextureSize[1] * ix
                y = ImageViewModel.TextureSize[0] * iy
                h, w = ImageViewModel.TextureSize

                vertarray = None
                texarray = None
                verts = None
                tilecolor = None

                if WarpedImageDataGrid[ix][iy] is None:
                    # Draw the warped image on the fixed image
                    FixedP, WarpedP = self.TransformViewModel.GetWarpedPointsInRect([y, x, y + h, x + w])

                    TransformPointPairs = numpy.concatenate((WarpedP, FixedP), 2).squeeze()


                    WarpedCorners = [[y, x],
                                    [ y, x + w, ],
                                    [y + h, x],
                                    [ y + h, x + w]]

                    xstep = int(w / 8.0)
                    ystep = int(h / 8.0)
                    for xtemp in range(0, w + 1, xstep):
                        for ytemp in range(0, h + 1, ystep):
                            WarpedCorners.append([ytemp + y, xtemp + x])

                    WarpedCorners = numpy.array(WarpedCorners, dtype=numpy.float32)

                    # Figure out where the corners of the texture belong
                    if(ForwardTransform):
                        FixedCorners = self.TransformViewModel.Transform(WarpedCorners)
                    else:
                        FixedCorners = self.TransformViewModel.InverseTransform(WarpedCorners)

                    # Check if the corners are outside the bounds
                    tileBorder = [numpy.min(FixedCorners[:, 1]), numpy.min(FixedCorners[:, 0]), numpy.max(FixedCorners[:, 1]), numpy.max(FixedCorners[:, 0])]
                    if not Rectangle.contains(BoundingBox, tileBorder):
                        continue

                    TilePointPairs = numpy.concatenate([WarpedCorners, FixedCorners], 1)

                    AllPointPairs = TilePointPairs
                    if(len(TransformPointPairs) > 0):
                        AllPointPairs = numpy.vstack([TilePointPairs, TransformPointPairs])

                    AllPointPairs = triangulation.Triangulation.RemoveDuplicates(AllPointPairs)

                    WarpedPoints, FixedPoints = numpy.hsplit(AllPointPairs, 2)

                    # Need to convert from Y,x to X,Y coordinates
                    FixedPoints = numpy.fliplr(FixedPoints)
                    WarpedPoints = numpy.fliplr(WarpedPoints)
                    # Do triangulation before we transform the points to prevent concave edges having a texture mapped over them.
                    tri = scipy.spatial.Delaunay(WarpedPoints)

                    texturePoints = numpy.array([[(u - x) / float(w), (v - y) / float(h)] for u, v in WarpedPoints], dtype=numpy.float32)

                    vertarray = []
                    texarray = []
                    for i in range(0, FixedPoints.shape[0]):

                        modelCoord = FixedPoints[i].tolist()

                        texCoord = texturePoints[i].tolist()
                        modelCoord.append(0.0)

                        [vertarray.append(vert) for vert in modelCoord]
                        [texarray.append(uv) for uv in texCoord]

                    vertarray = (gl.GLfloat * len(vertarray))(*vertarray)
                    texarray = (gl.GLfloat * len(texarray))(*texarray)

                    verts = tri.vertices

                    # verts = self.RemoveTrianglesOutsideConvexHull(verts, tri.convex_hull)

                    verts = verts.flatten()

                    tilecolor = numpy.random.rand(4).tolist()

                    LabelBatch = self.CreateLabelVertexNumberBatch(FixedPoints)

                    WarpedImageDataGrid[ix][iy] = (vertarray, texarray, verts, tilecolor, LabelBatch)
                else:
                    vertarray, texarray, verts, tilecolor, LabelBatch = WarpedImageDataGrid[ix][iy]

                gl.glEnable(gl.GL_TEXTURE_2D)
                gl.glDisable(gl.GL_CULL_FACE)
                gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE)

                gl.glBlendEquation(glFunc)

                pyglet.gl.glColor4f(color[0], color[1], color[2], color[3])


                pyglet.graphics.draw_indexed(len(vertarray) / 3,
                                             gl.GL_TRIANGLES,
                                             verts.tolist(),
                                             ('v3f', vertarray),
                                             ('t2f', texarray))

                gl.glBlendEquation(gl.GL_FUNC_ADD)

                if self.Debug:

                    LabelBatch.draw()

                    LineIndicies = self.LineIndiciesFromTri(verts)

                    gl.glDisable(gl.GL_TEXTURE_2D)
                    pyglet.gl.glColor3f(tilecolor[0], tilecolor[1], tilecolor[2])
                    pyglet.graphics.draw_indexed(len(vertarray) / 3,
                                                             gl.GL_LINES,
                                                             LineIndicies,
                                                             ('v3f', vertarray))

                    pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                    NumTestPoints = 16
                    p = numpy.zeros([NumTestPoints, 2])
                    p[:, 1] = [512] * NumTestPoints
                    p[:, 0] = range(0, 1024, 1024 / NumTestPoints)
                    tp = self.TransformViewModel.ForwardRBFInstance.TransformViewModel(p)

                    self._draw_points(tp)

                    p = numpy.zeros([NumTestPoints, 2])
                    p[:, 0] = [512] * NumTestPoints
                    p[:, 1] = range(0, 1024, 1024 / NumTestPoints)
                    tp = self.TransformViewModel.ForwardRBFInstance.TransformViewModel(p)

                    self._draw_points(tp)

                pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                gl.glDisable(gl.GL_BLEND)

    def CreateLabelVertexNumberBatch(self, verts):
        LabelBatch = pyglet.graphics.Batch()

        for i in range(0, verts.shape[0]):
            p = verts[i]
   #         l = pyglet.text.Label(text = str(i), font_name = 'Times New Roman', font_size = 36, x = p[0], y = p[1], color = (255, 255, 255, 255), width = 128, height = 128, anchor_x = 'center', anchor_y = 'center', batch = LabelBatch)

        return LabelBatch

    def LineIndiciesFromTri(self, T):
        LineIndicies = []

        Triangles = numpy.array(T)
        if Triangles.ndim == 1:
            Triangles = Triangles.reshape(len(Triangles) / 3, 3)

        for tri in Triangles:
            LineIndicies.append(tri[0])
            LineIndicies.append(tri[1])
            LineIndicies.append(tri[1])
            LineIndicies.append(tri[2])
            LineIndicies.append(tri[2])
            LineIndicies.append(tri[0])

        return LineIndicies

    def draw_textures(self, ShowWarped=True, BoundingBox=None, glFunc=None):
        if self.ImageViewModel is None:
            return

        if ShowWarped:
            self._draw_warped_image(self.ImageViewModel, color=None, BoundingBox=BoundingBox)
        else:
            self._draw_fixed_image(self.ImageViewModel, color=None, BoundingBox=BoundingBox)
