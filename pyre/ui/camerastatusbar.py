

import wx
import nornir_imageregistration
 
class CameraStatusBar(wx.StatusBar):

    @property
    def camera(self):
        return self._camera
    
    @camera.setter
    def camera(self, value):
        self._camera = value
    
    def __init__(self, parent, camera, **kwargs):
        self._camera = camera
        super(CameraStatusBar, self).__init__(parent, **kwargs)
        self.SetFieldsCount(3)

    def update_status_bar(self, point):
        if self.camera is None:
            return
        
        if point is None:
            return 
        # mousePosTemplate = '%d x, %d y, %4.2f%%
        
        point = self.camera.ImageCoordsForMouse(point[nornir_imageregistration.iPoint.Y], point[nornir_imageregistration.iPoint.X])
  
        ZoomValue = (1.0 / (float(self.camera.scale) / float(self.camera.WindowHeight))) * 100.0
        # mousePosStr = mousePosTemplate % (x, y, ZoomValue)

        self.SetFields(['%dx, %dy' % (point[nornir_imageregistration.iPoint.X], point[nornir_imageregistration.iPoint.Y]),
                                  '%4.2f%%' % ZoomValue])

        self.Refresh()
        