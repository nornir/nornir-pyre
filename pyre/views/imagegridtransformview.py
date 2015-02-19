
'''
Created on Oct 19, 2012

@author: u0490822
'''


import numpy
import logging
import scipy.spatial
import os
import math

import pyglet

import pyglet.gl as gl
import nornir_imageregistration.transforms.base
import nornir_imageregistration.transforms.triangulation
import nornir_imageregistration.spatial

import scipy.spatial.distance

import pyre.views

from pyre.viewmodels.transformcontroller import TransformController

import time

import resources
from imageop import scale


class RenderCache(object):
    '''This object stores variables that must be calculated every time the transform changes'''
    
        
    pass

class PointTextures(object):
    '''
    Provides graphics for transform points
    '''
    
    __pointImage = None
    __selectedPointImage = None
    __pointGroup = None
    __selectedPointSpriteOn = None
    __selectedPointSpriteOff = None
     
    @property
    def PointImage(self):
        if PointTextures.__pointImage is None:
            PointTextures.LoadTextures()

        return PointTextures.__pointImage

    @property
    def SelectedPointImage(self):
        if PointTextures.__selectedPointImage is None:
            PointTextures.LoadTextures()

        return PointTextures.__selectedPointImage

    @property
    def PointGroup(self):
        if PointTextures.__pointGroup is None:
            PointTextures.LoadTextures()

        return PointTextures.__pointGroup

    @property
    def SelectedPointSpriteOn(self):
        if PointTextures.__selectedPointSpriteOn is None:
            PointTextures.LoadTextures()

        return PointTextures.__selectedPointSpriteOn

    @property
    def SelectedPointSpriteOff(self):
        if PointTextures.__selectedPointSpriteOff is None:
            PointTextures.LoadTextures()

        return PointTextures.__selectedPointSpriteOff
     
    @classmethod
    def LoadTextures(cls):
        if cls.__pointImage is None:
            cls.__pointImage = pyglet.image.load(os.path.join(resources.ResourcePath(), "Point.png"))
            cls.__pointImage.anchor_x = cls.__pointImage.width / 2
            cls.__pointImage.anchor_y = cls.__pointImage.height / 2
            
        if cls.__selectedPointImage is None:
            cls.__selectedPointImage = pyglet.image.load(os.path.join(resources.ResourcePath(), "SelectedPoint.png"));
            cls.__selectedPointImage.anchor_x = cls.__selectedPointImage.width / 2
            cls.__selectedPointImage.anchor_y = cls.__selectedPointImage.height / 2
 
        if cls.__pointGroup is None:
            cls.__pointGroup = pyglet.sprite.SpriteGroup(texture=cls.__pointImage.get_texture(), blend_src=pyglet.gl.GL_SRC_ALPHA, blend_dest=pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
            cls.__selectedPointSpriteOn = pyglet.sprite.Sprite(cls.__selectedPointImage, 0, 0)
            cls.__selectedPointSpriteOff = pyglet.sprite.Sprite(cls.__pointImage, 0, 0)
    

class ImageTransformViewBase(object):
    '''
    Base class for ImageTransformView objects
    '''
      
    @property
    def width(self):
        raise NotImplementedError()

    @property
    def height(self):
        raise NotImplementedError()
    
    @property
    def Transform(self):
        raise NotImplementedError()
    
    def draw_textures(self, ShowWarped=True, BoundingBox=None, glFunc=None):
        raise NotImplementedError()
    

class ImageGridTransformView(ImageTransformViewBase,PointTextures):
    '''
    Combines and image and a transform to render an image.  Read-only operations used for rendering the graphics.
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
    def Transform(self):
        return self._Transform

    @Transform.setter
    def Transform(self, value):
        if not self._Transform is None:
            self._Transform.RemoveOnChangeEventListener(self.OnTransformChanged)

        self._Transform = value

        if not value is None:
            assert(isinstance(value, nornir_imageregistration.transforms.base.Base))
            self._Transform.AddOnChangeEventListener(self.OnTransformChanged)
            
        self.OnTransformChanged()
 
    @property
    def z(self):
        return self._z
    
    @z.setter
    def z(self, value):
        self._z = value 
        

    def __init__(self, ImageViewModel, Transform=None, ForwardTransform=True):
        '''
        Constructor
        :param imageviewmodel ImageViewModel: Textures for image
        :param transform Transform: nornir_imageregistration transform
        :param bool ForwardTransform: Set to true if points are mapped using Transform, False if points are mapped with InverseTransform
        '''
        self._Transform = None

        self.rendercache = RenderCache()
        self.ForwardTransform = ForwardTransform
        self._ImageViewModel = ImageViewModel
        self.Transform = Transform
        self._z = 0.5
        self._buffers = None
        
        self.Debug = False


    def OnTransformChanged(self):

        self._buffers = None
        # Keep the points if we can
        SavedPointCache = RenderCache()
        if hasattr(self.rendercache, 'PointCache'):
            PointCache = self.rendercache.PointCache
            if hasattr(PointCache, 'Sprites'):
                if len(PointCache.Sprites) == len(self.Transform.FixedPoints):
                    SavedPointCache = PointCache

        self.rendercache = None
        self.rendercache = RenderCache()
        

        if not SavedPointCache is None:
            self.rendercache.PointCache = SavedPointCache
             
    
    @classmethod
    def _update_sprite_position(cls, sprite, point, scale):
        sprite.x = point[nornir_imageregistration.iPoint.X]
        sprite.y = point[nornir_imageregistration.iPoint.Y]
        sprite.scale = scale
        
    
    def _update_sprite_flash(self, sprite, is_selected, time_for_selected_to_flash=False):
        
        if not is_selected:
            if sprite.image != self.PointImage:
                sprite.image = self.PointImage
                return
            
        else: 
            if time_for_selected_to_flash:
                sprite.image = self.SelectedPointImage
            else:
                sprite.image = self.PointImage
        
        

    def _draw_points(self, verts, SelectedIndex=None, BoundingBox=None, ScaleFactor=1.0):

        PointBaseScale = 8.0
        
        current_time = time.time()
        time_for_selected_to_flash = current_time % 1 > 0.5

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
                    ImageGridTransformView._update_sprite_position(sprites[i], verts[i], scale)
                    is_selected = i == SelectedIndex
                    self._update_sprite_flash(sprites[i], is_selected, time_for_selected_to_flash) 
                
                gl.glDisable(gl.GL_DEPTH_TEST)
                PointBatch.draw()
                gl.glEnable(gl.GL_DEPTH_TEST)
            except:
                self.rendercache.PointCache = None
                l = logging.getLogger('ImageGridTransformView')
                l.error("Cached Point sprite error, resetting cache")

        else:
            PointBatch = pyglet.graphics.Batch()
            spriteList = list()
            for i in range(0, len(verts)):
                point = verts[i]
                
                #if math.isnan(point[0]) or math.isnan(point[1]):
                #    continue

                Image = self.PointImage
                if math.isnan(point[0]) or math.isnan(point[1]):
                    continue  

                if SelectedIndex is not None:
                    if(i == SelectedIndex and  time.time() % 1 > .5):
                        Image = self.SelectedPointImage

                s = pyglet.sprite.Sprite(Image, x=point[1], y=point[0], group=self.PointGroup, batch=PointBatch)
                s.scale = scale
                spriteList.append(s)


            PointCache.Sprites = spriteList
            PointCache.PointBatch = PointBatch

            gl.glDisable(gl.GL_DEPTH_TEST)
            PointBatch.draw()
            gl.glEnable(gl.GL_DEPTH_TEST)

            self.rendercache.PointCache = PointCache
            # print str(s.x) + ", " + str(s.y)

        # PointBatch.draw()

    def draw_points(self, SelectedIndex=None, FixedSpace=True, BoundingBox=None, ScaleFactor=1):

        if(not FixedSpace):
            verts = self.Transform.WarpedPoints
        else:
            verts = self.Transform.FixedPoints

        self._draw_points(verts, SelectedIndex, BoundingBox, ScaleFactor)


    def draw_lines(self):
        if(self.Transform is None):
            return

        Triangles = []
        if(self.ForwardTransform):
            # Triangles = self.__Transform.WarpedTriangles
            verts = numpy.fliplr(self.Transform.WarpedPoints)
            Triangles = self.Transform.WarpedTriangles
        else:
            verts = numpy.fliplr(self.Transform.FixedPoints)
            Triangles = self.Transform.FixedTriangles
            
        pyre.views.DrawTriangles(verts, Triangles)
        
    @classmethod 
    def _fixed_texture_coords(cls):
        t = (0.0, 0.0, 0,
             1.0, 0.0, 0,
             1.0, 1.0, 0,
             0.0, 1.0, 0,
             0.5, 0.5, 1.0)

    def DrawFixedImage(self, ImageViewModel, color, BoundingBox=None, z=None):
        '''Draw a fixed image, bounding box indicates the visible area.  Everything is drawn if BoundingBox is None'''
        
        if z is None:
            z = self.z
        
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
                t = (0.0, 0.0, self.z,
                     1.0, 0.0, self.z,
                     1.0, 1.0, self.z,
                     0.0, 1.0, self.z) 
                w, h = ImageViewModel.TextureSize
                x = ImageViewModel.TextureSize[1] * ix
                y = ImageViewModel.TextureSize[0] * iy

                # Check bounding box if it exists
                if not BoundingBox is None:
                    if not nornir_imageregistration.spatial.Rectangle.contains(BoundingBox, [y, x, y + h, x + w]):
                        continue

                array = None
                if cacheColumn[iy] is None: 
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
                
                 
    def WarpedImageDataGrid(self, grid_size):
        '''Grab the cached image data for a warped image
        ''' 
        
        WarpedImageDataGrid = None
        if hasattr(self.rendercache, 'WarpedImageDataGrid'):
            WarpedImageDataGrid = self.rendercache.WarpedImageDataGrid
        else:
            WarpedImageDataGrid = []
            for i in range(0, grid_size[1]):
                WarpedImageDataGrid.append([None] * grid_size[0])

            self.rendercache.WarpedImageDataGrid = WarpedImageDataGrid
            
        return WarpedImageDataGrid
     
    
    @classmethod
    def _tile_grid_point_pairs(cls, Transform, tile_bounding_rect,  ForwardTransform=True, grid_size = (8.0, 8.0)):
        '''
        :return: Fills the tile area with a (MxN) grid of points.  Maps the points through the transform.  Then adds the known transform points to the results
        '''
         
        (y, x) = tile_bounding_rect.BottomLeft
        h = tile_bounding_rect.Height
        w = tile_bounding_rect.Width
     
        WarpedCorners = [[y, x],
                        [ y, x + w, ],
                        [y + h, x],
                        [ y + h, x + w]]
        
        xstep = int(w / grid_size[1])
        ystep = int(h / grid_size[0]) 
        for xtemp in range(0, w + 1, xstep):
            for ytemp in range(0, h + 1, ystep):
                WarpedCorners.append([ytemp + y, xtemp + x])
                
        WarpedCorners = numpy.array(WarpedCorners, dtype=numpy.float32)
        
        # Figure out where the corners of the texture belong
        FixedCorners = None
        if(ForwardTransform):
            FixedCorners = Transform.Transform(WarpedCorners)
        else:
            FixedCorners = Transform.InverseTransform(WarpedCorners)
            
        TilePointPairs = numpy.concatenate([WarpedCorners, FixedCorners], 1)
        
        #Add the known points from the transform to the grid
        AllPointPairs = TilePointPairs
        FixedP, WarpedP = Transform.GetWarpedPointsInRect(tile_bounding_rect.ToArray())
        TransformPointPairs = numpy.concatenate((WarpedP, FixedP), 2).squeeze()
        if(len(TransformPointPairs) > 0):
            AllPointPairs = numpy.vstack([TilePointPairs, TransformPointPairs])
        
        return AllPointPairs
    
    
    @classmethod
    def _tile_bounding_rect(cls, Transform, tile_bounding_rect, ForwardTransform=True,  grid_size = (3.0, 3.0)):
        '''
        :return: Returns a bounding rectangle built from points placed around the edge of the tile
        '''
         
        (y, x) = tile_bounding_rect.BottomLeft
        h = tile_bounding_rect.Height
        w = tile_bounding_rect.Width
     
        WarpedCorners = [[y, x],
                        [ y, x + w, ],
                        [y + h, x],
                        [ y + h, x + w]]
        
        xstep = int(w / grid_size[1])
        ystep = int(h / grid_size[0]) 
        for xtemp in range(0, w + 1, xstep):
            WarpedCorners.append([0 + y, xtemp + x])
            WarpedCorners.append([h + y, xtemp + x])
                
        for ytemp in range(0, h + 1, ystep):
            WarpedCorners.append([ytemp + y, 0 + x])
            WarpedCorners.append([ytemp + y, w + x])

        WarpedCorners = numpy.array(WarpedCorners, dtype=numpy.float32)
        
        # Figure out where the corners of the texture belong
        FixedCorners = None
        if(ForwardTransform):
            FixedCorners = Transform.Transform(WarpedCorners)
        else:
            FixedCorners = Transform.InverseTransform(WarpedCorners)
            
        return nornir_imageregistration.spatial.Rectangle.CreateFromBounds(nornir_imageregistration.spatial.BoundsArrayFromPoints(FixedCorners))
     
    
    @classmethod
    def _build_tile_render_data(cls, Transform, z, rect, ForwardTransform=True,):
               
        TilePointPairs = cls._tile_grid_point_pairs(Transform, rect, ForwardTransform)
        
        (vertarray, texarray, verts) = cls._render_data_for_transform_point_pairs(TilePointPairs, rect, z)
  
        #LabelBatch = self.CreateLabelVertexNumberBatch(FixedPoints)
        LabelBatch = None

        return (vertarray, texarray, verts, LabelBatch)
    
    
    @classmethod
    def _z_values_for_points(cls, FixedPointsYX):
        center = numpy.mean(FixedPointsYX,0)
        Z = scipy.spatial.distance.cdist(numpy.resize(center, (1,2)), FixedPointsYX, 'euclidean')
        Z = numpy.transpose(Z)
        Z /= numpy.max(Z)
        Z = 1 - Z
        return Z
         
    
    @classmethod
    def _render_data_for_transform_point_pairs(cls, PointPairs, tile_bounding_rect, z=None):
        '''Generate verticies and texture coordinates for a set of transform points'''
         
        WarpedPointsYX, FixedPointsYX = numpy.hsplit(PointPairs, 2)
        
        #tile_bounding_rect = nornir_imageregistration.spatial.BoundingPrimitiveFromPoints(WarpedPoints)
        (y, x) = tile_bounding_rect.BottomLeft
        h = tile_bounding_rect.Height
        w = tile_bounding_rect.Width

        # Need to convert from Y,x to X,Y coordinates
        FixedPointsXY = numpy.fliplr(FixedPointsYX)
        WarpedPointsXY = numpy.fliplr(WarpedPointsYX)
        # Do triangulation before we transform the points to prevent concave edges having a texture mapped over them.
        tri = scipy.spatial.Delaunay(WarpedPointsXY)

        texturePoints = numpy.array([[(u - x) / float(w), (v - y) / float(h)] for u, v in FixedPointsXY], dtype=numpy.float32)

        #Set vertex z according to distance from center
        if not z is None: 
            z_array = numpy.ones( (WarpedPointsXY.shape[0],1) ) * z
        else:
            z_array = cls._z_values_for_points(FixedPointsYX)
        
        Verts3D = numpy.hstack((WarpedPointsXY, z_array ))
        vertarray = list(Verts3D.flat)
        texarray = list(texturePoints.flat)
          
        vertarray = (gl.GLfloat * len(vertarray))(*vertarray)
        texarray = (gl.GLfloat * len(texarray))(*texarray)

        verts = tri.vertices 

        verts = verts.flatten()
        
        return (vertarray, texarray, verts)

    
    def DrawWarpedImage(self, ImageViewModel, ForwardTransform=True, color=None, BoundingBox=None, z=None, glFunc=gl.GL_FUNC_ADD):
        
            
        if ImageViewModel.NumCols > 1 or ImageViewModel.NumRows > 1:
            return self._draw_warped_imagegridviewmodel(ImageViewModel, ForwardTransform=True, color=None, BoundingBox=BoundingBox, z=z, glFunc=glFunc)
        
        WarpedImageDataGrid = self.WarpedImageDataGrid( (ImageViewModel.NumRows, ImageViewModel.NumRows) )
        
        if WarpedImageDataGrid[0][0] is None:
            tile_bounding_rect = nornir_imageregistration.spatial.Rectangle.CreateFromPointAndArea((0,0), ImageViewModel.TextureSize)
            (vertarray, texarray, verts) = ImageGridTransformView._render_data_for_transform_point_pairs(self.Transform.points,  tile_bounding_rect, z)
            WarpedImageDataGrid[0][0] = (vertarray, texarray, verts)
        else:
            (vertarray, texarray, verts) = WarpedImageDataGrid[0][0]
        
        texture = ImageViewModel.ImageArray[0][0]
        
        if self._buffers is None:
            self._buffers = pyre.views.GetOrCreateBuffers(len(vertarray) / 3,
                                                  ('v3f', vertarray),
                                                  ('t2f', texarray)) 
        
        pyre.views.DrawTextureWithBuffers(texture, vertarray, self._buffers, verts, color, glFunc=glFunc) 
        return 
        
    def _draw_warped_imagegridviewmodel(self, ImageViewModel, ForwardTransform=True, color=None, BoundingBox=None, z=None, glFunc=gl.GL_FUNC_ADD):
        
        if z is None:
            z = self.z
            
        if color is None:
            color = (1.0, 1.0, 1.0, 1.0)
            
        WarpedImageDataGrid = self.WarpedImageDataGrid( (ImageViewModel.NumRows, ImageViewModel.NumRows) )
  
        for ix in range(0, ImageViewModel.NumCols):
            column = ImageViewModel.ImageArray[ix]
            for iy in range(0, ImageViewModel.NumRows):
                texture = column[iy]
                x = ImageViewModel.TextureSize[1] * ix
                y = ImageViewModel.TextureSize[0] * iy 
                
                tile_bounding_rect = nornir_imageregistration.spatial.Rectangle.CreateFromPointAndArea((y,x), ImageViewModel.TextureSize)

                vertarray = None
                texarray = None
                verts = None
                tilecolor = None

                if WarpedImageDataGrid[ix][iy] is None:
                    
                    warped_bounding_rect = ImageGridTransformView._tile_bounding_rect(self.Transform, tile_bounding_rect, ForwardTransform)
                    if not nornir_imageregistration.spatial.Rectangle.contains(BoundingBox, warped_bounding_rect):
                        continue
                    
                    vertarray, texarray, verts, LabelBatch = ImageGridTransformView._build_tile_render_data(self.Transform, z, tile_bounding_rect, ForwardTransform=ForwardTransform)

                    WarpedImageDataGrid[ix][iy] = (vertarray, texarray, verts, LabelBatch)
                else:
                    vertarray, texarray, verts, LabelBatch = WarpedImageDataGrid[ix][iy]

                pyre.views.DrawTexture(texture, vertarray, texarray, verts, color, glFunc=glFunc)

#                 if self.Debug:
#                     tilecolor = numpy.random.rand(4).tolist()
#                     LabelBatch.draw()
# 
#                     LineIndicies = pyre.views.LineIndiciesFromTri(verts)
# 
#                     gl.glDisable(gl.GL_TEXTURE_2D)
#                     pyglet.gl.glColor3f(tilecolor[0], tilecolor[1], tilecolor[2])
#                     pyglet.graphics.draw_indexed(len(vertarray) / 3,
#                                                              gl.GL_LINES,
#                                                              LineIndicies,
#                                                              ('v3f', vertarray))
# 
#                     pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)
#                     NumTestPoints = 16
#                     p = numpy.zeros([NumTestPoints, 2])
#                     p[:, 1] = [512] * NumTestPoints
#                     p[:, 0] = range(0, 1024, 1024 / NumTestPoints)
#                     tp = self.Transform.ForwardRBFInstance.Transform(p)
# 
#                     self._draw_points(tp)
# 
#                     p = numpy.zeros([NumTestPoints, 2])
#                     p[:, 0] = [512] * NumTestPoints
#                     p[:, 1] = range(0, 1024, 1024 / NumTestPoints)
#                     tp = self.Transform.ForwardRBFInstance.Transform(p)
# 
#                     self._draw_points(tp)
# 
#                 pyglet.gl.glColor4f(1.0, 1.0, 1.0, 1.0)
#                 gl.glDisable(gl.GL_BLEND)


    def CreateLabelVertexNumberBatch(self, verts):
        LabelBatch = pyglet.graphics.Batch()

        for i in range(0, verts.shape[0]):
            p = verts[i]
   #         l = pyglet.text.Label(text = str(i), font_name = 'Times New Roman', font_size = 36, x = p[0], y = p[1], color = (255, 255, 255, 255), width = 128, height = 128, anchor_x = 'center', anchor_y = 'center', batch = LabelBatch)

        return LabelBatch


    def draw_textures(self, ShowWarped=True, BoundingBox=None, z=None, glFunc=None):
        if self.ImageViewModel is None:
            return

        if ShowWarped:
            self.DrawWarpedImage(self.ImageViewModel, color=None, BoundingBox=BoundingBox, z=z )
        else:
            self.DrawFixedImage(self.ImageViewModel, color=None, BoundingBox=BoundingBox, z=z)
