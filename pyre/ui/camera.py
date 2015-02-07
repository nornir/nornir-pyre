'''
Created on Oct 17, 2012

@author: u0490822
'''

from pyglet.gl import *
import math

class Camera(object):
    '''
    classdocs
    '''

    @property
    def x(self):
        return self._x


    @x.setter
    def x(self, value):
        self._x = value
        self._FireChangeEvent()


    @property
    def y(self):
        return self._y


    @y.setter
    def y(self, value):
        self._y = value
        self._FireChangeEvent()


    @property
    def ViewWidth(self):
        return self._viewwidth;


    @property
    def ViewHeight(self):
        return self._viewheight;
    
#    @ViewHeight.setter
#    def ViewHeight(self, value):
#        self._viewheight = value
#        
#    @ViewWidth.setter
#    def ViewWidth(self, value):
#        self._viewwidth = value

    @property
    def angle(self):
        return float(self._angle);


    @angle.setter
    def angle(self, value):
        self._angle = float(value);
        self._FireChangeEvent()


    @property
    def scale(self):
        return float(self._scale);


    @scale.setter
    def scale(self, value):
        self._scale = float(value);
        self._FireChangeEvent()


    def __init__(self, position, scale=1, angle=0, size=None):
        self._x, self._y = position  # centered on
        self._angle = 0  # tilt
        self._scale = scale  # zoom
        self.__OnChangeEventListeners = []
        

        if size is None:
            self._viewwidth = 640 * scale
            self._viewheight = 480 * scale 
        else:
            self.focus(size[1]* scale, size[0] * scale)
            
    def AddOnChangeEventListener(self, func):
        self.__OnChangeEventListeners.append(func)


    def RemoveOnChangeEventListener(self, func):
        if func in self.__OnChangeEventListeners:
            self.__OnChangeEventListeners.remove(func)
            
            
    def _FireChangeEvent(self):
        for func in self.__OnChangeEventListeners:
            func()


    def focus(self, win_width, win_height):
        glViewport(0, 0, win_width, win_height);
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = float(win_width) / float(win_height)

        self._viewwidth = self.scale * aspect;
        self._viewheight = self.scale;

        scale = self.scale / 2.0
        gluOrtho2D(-scale * aspect,  # left
                   + scale * aspect,  # right
                   - scale,  # bottom
                   + scale)  # top

        # Set modelview matrix to move, scale & rotate
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.x, self.y, +1.0,  # camera  x,y,z
                  self.x, self.y, -1.0,  # look at x,y,z
                  math.sin(self.angle), math.cos(self.angle), 0.0)
