'''
Created on Feb 6, 2015

@author: u0490822
'''

from pyre.ui import glpanel
import nornir_imageregistration.spatial as spatial
import pyre.ui.camera

class ImageTransformPanelBase(glpanel.GLPanel):
    '''
    classdocs
    ''' 
    
    @property
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, value):

        if not self._camera is None:
            self._camera.RemoveOnChangeEventListener(self.OnCameraChanged)

        self._camera = value

        if not value is None:
            assert(isinstance(value, pyre.ui.camera.Camera))
            value.AddOnChangeEventListener(self.OnCameraChanged)

    def __init__(self, parent, id=-1, **kwargs):
        '''
        Constructor
        '''
        self._camera = None
        
        super(ImageTransformPanelBase, self).__init__(parent, id, **kwargs)
        pass
    
    
    def __str__(self, *args, **kwargs):
        return self.TopLevelParent.Label
    
    
    def update(self, dt):
        pass

    
    def on_resize(self, e):
        (self.width, self.height) = self.canvas.GetSizeTuple()
        if not self.camera is None:
            #try:
            self.camera.focus(self.width, self.height)
            #except:
            #pass

    def VisibleImageBoundingBox(self):

        (left, bottom) = self.ImageCoordsForMouse(0, 0)
        (right, top) = self.ImageCoordsForMouse(self.width, self.height)

        return spatial.Rectangle.CreateFromBounds((bottom, left, top, right))
    
    def GetCorrectedMousePosition(self, e):
        '''wxPython inverts the mouse position, flip it back'''
        (x, y) = e.GetPositionTuple()
        return (x, self.height - y)
    
    def OnTransformChanged(self):
        self.canvas.Refresh()

    def OnCameraChanged(self):
        self.canvas.Refresh()
        
    def lookatfixedpoint(self, point, scale):
        '''specify a point to look at in fixed space'''

        self.camera.x = point[0]
        self.camera.y = point[1]
        self.camera.scale = scale
        
    
    def draw_objects(self):
        raise NotImplemented("draw object is not implemented")        
        