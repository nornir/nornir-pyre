'''
Created on Feb 10, 2015

@author: u0490822
'''

import nornir_imageregistration.spatial
import numpy
import pyre.views

class RectangleCommand(object):
    '''
    The user interface to draw and size a rectangle
    '''
    
    @property
    def Origin(self):
        return self._origin
    
    @Origin.setter
    def Origin(self, value):
        self._origin = numpy.array(value)
    
    @property
    def Area(self):
        return self.rect.Area
        
    @property
    def LastMousePosition(self):
        return self._lastMousePosition
    
    @LastMousePosition.setter
    def LastMousePosition(self, value):
        self._lastMousePosition = numpy.array(value)
    
    @property
    def rect(self):
        stacked = numpy.vstack((self.Origin, self.LastMousePosition))
        min_val = numpy.min(stacked,0)
        max_val = numpy.max(stacked,0)
        
        return nornir_imageregistration.spatial.Rectangle.CreateFromBounds((min_val[nornir_imageregistration.spatial.iPoint.Y],
                                                                                  min_val[nornir_imageregistration.spatial.iPoint.X],
                                                                                  max_val[nornir_imageregistration.spatial.iPoint.Y],
                                                                                  max_val[nornir_imageregistration.spatial.iPoint.X]))

    def __init__(self, origin, screen_to_volume_coord_func):
        '''
        Constructor
        :param tuple origin: Origin of rectangle
        :param func mouse_coord_func: Function to call to obtain mouse position in volume coordinates
        :param func mouse_to_volume_coord_func: Function to call to obtain volume position from screen coordinates
        '''
        
        self.Origin = origin 
        self.LastMousePosition = origin
        
        print("Start Rect: %d x %d" % (self.Origin[nornir_imageregistration.spatial.iPoint.X], self.Origin[nornir_imageregistration.spatial.iPoint.Y]))
         
        self.screen_to_volume_coord_func = screen_to_volume_coord_func

        
    def on_mouse_drag(self, e, mouse_position):
        '''
        :param obj e: wx mouse move object
        :param tuple mouse_position: Position of the mouse on the screen, corrected for inverted Y coordinates in GL        
        '''
        
        self.LastMousePosition = self.screen_to_volume_coord_func(mouse_position[nornir_imageregistration.spatial.iPoint.Y],
                                                                  mouse_position[nornir_imageregistration.spatial.iPoint.X])
        
        
        
        print("X: %g x Y: %g" % (self.LastMousePosition[nornir_imageregistration.spatial.iPoint.X], self.LastMousePosition[nornir_imageregistration.spatial.iPoint.Y]))
        pass
        
    def draw(self):
        
        pyre.views.DrawRectangle(self.rect, (0.5, 1.0, 1.0, 0.5))
        
        pass
    
        