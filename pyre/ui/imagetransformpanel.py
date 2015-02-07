'''
Created on Oct 16, 2012

@author: u0490822
'''


from pyre.ui import camera
import math

from pyglet import *

from pyre.ui import glpanel
import wx  

from pyre.state import currentConfig
from pyre import history

from pyre.viewmodels.transformviewmodel import TransformViewModel
from pyre.views.imagetransformview import ImageTransformView
from pyre.views.compositetransformview import CompositeTransformView

import imagetransformpanelbase

class ImageTransformViewPanel(imagetransformpanelbase.ImageTransformPanelBase):
    '''
    classdocs
    '''
    _CurrentDragPoint = None
    _HighlightedPointIndex = 0

    @property
    def SelectedPointIndex(self):
        return ImageTransformViewPanel._CurrentDragPoint

    @SelectedPointIndex.setter
    def SelectedPointIndex(self, value):

        ImageTransformViewPanel._CurrentDragPoint = value

        if not value is None:
            ImageTransformViewPanel._HighlightedPointIndex = value

    @property
    def HighlightedPointIndex(self):
        return ImageTransformViewPanel._HighlightedPointIndex

    @property
    def TransformViewModel(self):
        return self.ImageTransformView.TransformViewModel

    @property
    def ImageTransformView(self):
        return self._ImageTransformView
    
    @ImageTransformView.setter
    def ImageTransformView(self, value):

        self._ImageTransformView = value

        if value is None:
            self.camera = None
            return
        else:
            assert(isinstance(value, ImageTransformView))

        (self.width, self.height) = self.canvas.GetSizeTuple() 
        
        try:
            if not value is None:
                self.camera = camera.Camera((value.width / 2.0, value.height / 2.0), max([value.width / 2.0, value.height / 2.0]))
        except TypeError:
            print("Type error creating camera for ImageTransformView %s" % str(value))
            self.camera = None
            pass


    def __init__(self, parent, id=-1, TransformViewModel=None, ImageTransformView=None, FixedSpace=None, composite=False, **kwargs):
        '''
        Constructor
        '''

        self._camera = None 
        self._ImageTransformView = None
        self.SelectionMaxDistance = 1

        super(ImageTransformViewPanel, self).__init__(parent, id, **kwargs)
 
        self.ImageTransformView = ImageTransformView

        currentConfig.AddOnTransformViewModelChangeEventListener(self.OnTransformViewModelChanged)
        currentConfig.AddOnImageViewModelChangeEventListener(self.OnImageViewModelChanged)

        # self.schedule = clock.schedule_interval(func = self.update, interval = 1 / 2.)
        self.timer = wx.Timer(self)
        self.canvas.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        (self.width, self.height) = self.canvas.GetSizeTuple()

        wx.EVT_TIMER(self, -1, self.on_timer)

        self.ShowLines = False

        self.LastMousePosition = None

        self.FixedSpace = FixedSpace

        self.ShowWarped = False

        self.glFunc = gl.GL_FUNC_ADD

        self.composite = composite

        self.LastMousePosition = None

        self.LastDrawnBoundingBox = None

        self.canvas.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_scroll)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_press)
        self.canvas.Bind(wx.EVT_MIDDLE_DOWN, self.on_mouse_press)
        self.canvas.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_press)
        self.canvas.Bind(wx.EVT_MOTION, self.on_mouse_drag)
        self.canvas.Bind(wx.EVT_LEFT_UP, self.on_mouse_release)
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_press)

        self.canvas.Bind(wx.EVT_SIZE, self.on_resize)

        self.AddStatusBar()

        self.DebugTickCounter = 0
        self.timer.Start(500)

    def AddStatusBar(self):
        self.statusBar = wx.StatusBar(self)
        self.sizer.Add(self.statusBar, flag=wx.BOTTOM | wx.EXPAND)
        self.statusBar.SetFieldsCount(3)

    def update_status_bar(self):
        x, y = self.ImageCoordsForMouse(self.LastMousePosition[0], self.LastMousePosition[1])

        if self.camera is None:
            return
        # mousePosTemplate = '%d x, %d y, %4.2f%%

        if self.camera.scale == 0 or self.height == 0:
            return

        ZoomValue = (1.0 / (float(self.camera.scale) / float(self.height))) * 100.0
        # mousePosStr = mousePosTemplate % (x, y, ZoomValue)

        self.statusBar.SetFields(['%dx, %dy' % (x, y),
                                  '%4.2f%%' % ZoomValue])

        self.statusBar.Refresh()

    def on_timer(self, e):
#        DebugStr = '%d' % self.DebugTickCounter
#        DebugStr = DebugStr + '\b' * len(DebugStr)
#        print DebugStr
        self.DebugTickCounter += 1
        self.canvas.Refresh()
        return
 

    def OnTransformViewModelChanged(self):
        if not self.ImageTransformView is None:
            self.ImageTransformView.TransformViewModel = currentConfig.TransformViewModel

        self.canvas.Refresh()



    def _LabelPreamble(self):
        if self.FixedSpace:
            return "Fixed: "
        else:
            return "Warping: "

    def OnImageViewModelChanged(self, FixedImage):

        if self.composite:
            self.UpdateRawImageWindow()
        elif self.FixedSpace == FixedImage:
            self.UpdateRawImageWindow()
            self.TopLevelParent.Label = self._LabelPreamble() + os.path.basename(self.ImageTransformView.ImageViewModel.ImageFilename)

        self.canvas.Refresh()

    def UpdateRawImageWindow(self):
        if self.composite:
            if not (currentConfig.FixedImageViewModel is None or currentConfig.WarpedImageViewModel is None):
                self.ImageTransformView = CompositeTransformView(currentConfig.FixedImageViewModel,
                                                                 currentConfig.WarpedImageViewModel,
                                                                 currentConfig.TransformViewModel)
        elif not self.FixedSpace:
            self.ImageTransformView = ImageTransformView(currentConfig.WarpedImageViewModel, currentConfig.TransformViewModel, ForwardTransform=True)
        else:
            self.ImageTransformView = ImageTransformView(currentConfig.FixedImageViewModel, currentConfig.TransformViewModel, ForwardTransform=False)


    def NextGLFunction(self):
        if self.glFunc == gl.GL_FUNC_ADD:
            self.glFunc = gl.GL_FUNC_SUBTRACT
        else:
            self.glFunc = gl.GL_FUNC_ADD


    def on_key_press(self, e):
        keycode = e.GetKeyCode()

        symbol = ''
        try:
            KeyChar = '%c' % keycode
            symbol = KeyChar.lower()
        except:
            pass

        if keycode == wx.WXK_TAB:
            try:
                if(self.FixedSpace):
                    self.NextGLFunction()
                else:
                    self.ShowWarped = not self.ShowWarped
            except:
                pass

        elif (keycode == wx.WXK_LEFT or \
             keycode == wx.WXK_RIGHT or \
             keycode == wx.WXK_UP or \
             keycode == wx.WXK_DOWN) and not self.HighlightedPointIndex is None:

            # Users can nudge points with the arrow keys.  Holding shift steps five pixels, holding Ctrl shifts 25.  Holding both steps 125
            multiplier = 1
            print multiplier
            if(e.ShiftDown()):
                multiplier = multiplier * 5
                print multiplier
            if(e.ControlDown()):
                multiplier = multiplier * 25
                print multiplier

            if keycode == wx.WXK_LEFT:
                delta = [0, -1]
            elif keycode == wx.WXK_RIGHT:
                delta = [0, 1]
            elif keycode == wx.WXK_UP:
                delta = [1, 0]
            elif keycode == wx.WXK_DOWN:
                delta = [-1, 0]


            delta[0] = delta[0] * multiplier
            delta[1] = delta[1] * multiplier

            print multiplier
            self.TransformViewModel.MovePoint(self.HighlightedPointIndex, delta[1], delta[0], FixedSpace=self.FixedSpace)

        elif symbol == 'a':  # "A" Character
            ImageDX = 0.1 * self.camera.ViewWidth
            self.camera.x = self.camera.x + ImageDX
        elif symbol == 'd':  # "D" Character
            ImageDX = -0.1 * self.camera.ViewWidth
            self.camera.x = self.camera.x + ImageDX
        elif symbol == 'w':  # "W" Character
            ImageDY = -0.1 * self.camera.ViewHeight
            self.camera.y = self.camera.y + ImageDY
        elif symbol == 's':  # "S" Character
            ImageDY = 0.1 * self.camera.ViewHeight
            self.camera.y = self.camera.y + ImageDY

        elif keycode == wx.WXK_PAGEUP:
            self.camera.scale = self.scale * 0.9
        elif keycode == wx.WXK_PAGEDOWN:
            self.camera.scale = self.camera.scale * 1.1
        elif keycode == wx.WXK_SPACE:

            # If SHIFT is held down, align everything.  Otherwise align the selected point
            if not e.ShiftDown() and not self.HighlightedPointIndex is None:
                self.SelectedPointIndex = self.TransformViewModel.AutoAlignPoints(self.HighlightedPointIndex)

            elif e.ShiftDown():
                self.TransformViewModel.AutoAlignPoints(range(0, self.TransformViewModel.NumPoints))

            history.SaveState(self.TransformViewModel.SetPoints, self.TransformViewModel.points)
        elif symbol == 'l':
            self.ShowLines = not self.ShowLines
        elif keycode == wx.WXK_F1:
            self._ImageTransformView.Debug = not self._ImageTransformView.Debug
        elif symbol == 'm':
            LookAt = [self.camera.x, self.camera.y]

            if not self.FixedSpace and self.ShowWarped:
                LookAt = self.TransformViewModel.Transform([LookAt])
                LookAt = LookAt[0]

            # pyre.SyncWindows(LookAt, self.camera.scale)

        elif symbol == 'z' and e.CmdDown():
            history.Undo()
        elif symbol == 'x' and e.CmdDown():
            history.Redo()

    def lookatfixedpoint(self, point, scale):
        '''specify a point to look at in fixed space'''

        if not self.FixedSpace:
            point = self.TransformViewModel.Transform.InverseTransform([point])
            point = point[0]
            
        super(self, ImageTransformViewPanel).lookatfixedpoint(point, scale)
 

    def draw_objects(self):
        '''Region is [x,y,TextureWidth,TextureHeight] indicating where the image should be drawn on the window'''

        if self._ImageTransformView is None or self.camera is None:
            return

        BoundingBox = self.VisibleImageBoundingBox()

        # self.clear()
        self.camera.focus(self.width, self.height)


        # Draw an image if we can
        if not self.composite:
            self._ImageTransformView.draw_textures(BoundingBox=BoundingBox, ShowWarped=self.ShowWarped, glFunc=gl.GL_FUNC_ADD)
        else:
            self._ImageTransformView.draw_textures(BoundingBox=BoundingBox, glFunc=self.glFunc)

        if self.TransformViewModel is None:
            return

        if self.ShowLines:
            self._ImageTransformView.draw_lines()

        FixedSpacePoints = self.FixedSpace
        if self.composite:
            FixedSpacePoints = False
        elif not self.FixedSpace and self.ShowWarped:
            FixedSpacePoints = True

        # pointScale = (BoundingBox[3] * BoundingBox[2]) / (self.height * self.width)
        pointScale = self.camera.scale / self.height
        self._ImageTransformView.draw_points(SelectedIndex=self.HighlightedPointIndex, BoundingBox=BoundingBox, FixedSpace=FixedSpacePoints, ScaleFactor=pointScale)


        self.SelectionMaxDistance = (float(self.camera.ViewHeight) / float(self.height)) * 16.0
        if(self.SelectionMaxDistance < 16):
            self.SelectionMaxDistance = 16


 #       graphics.draw(2, gl.GL_LINES, ('v2i', (0, 0, 0, 10)))
 #       graphics.draw(2, gl.GL_LINES, ('v2i', (0, 0, 100, 0)))

        # if not self.LastMousePosition is None and len(self.LastMousePosition) > 0:


#            fontsize = 16 * (self.camera.scale / self.height)
#            labelx, labely = self.ImageCoordsForMouse(0, 0)
#            l = text.Label(text = mousePosStr, x = labelx, y = labely,
#                            width = fontsize * len(mousePosStr),
#                            anchor_y = 'bottom',
#                            font_size = fontsize,
#                            dpi = 300,
#                            font_name = 'Times New Roman')
#            l.draw()


    def on_mouse_motion(self, x, y, dx, dy):
        self.LastMousePosition = [x, y]

    def ImageCoordsForMouse(self, x, y):
        if self.camera is None:
            return (None, None)

        ImageX = ((float(x) / self.width) * self.camera.ViewWidth) + (self.camera.x - (self.camera.ViewWidth / 2.0))
        ImageY = ((float(y) / self.height) * self.camera.ViewHeight) + (self.camera.y - (self.camera.ViewHeight / 2.0))
        return (ImageX, ImageY)

    def on_mouse_scroll(self, e):

        if self.camera is None:
            return

        scroll_y = e.GetWheelRotation() / 120.0

        # We rotate when command is down
        if e.CmdDown():
            angle = float(abs(scroll_y) / 4.0) ** 2.0

            if angle > 15.0:
                angle = 15.0

            rangle = (angle / 180.0) * 3.14159
            if scroll_y < 0:
                rangle = -rangle

           # print "Angle: " + str(angle)
            self.TransformViewModel.RotateWarped(rangle, (currentConfig.WarpedImageViewModel.RawImageSize[0] / 2.0,
                                                          currentConfig.WarpedImageViewModel.RawImageSize[1] / 2.0))

        else:
            zdelta = (1 + (-scroll_y / 20))
            self.camera.scale = self.camera.scale * zdelta
            max_image_dimension_value = max([self.TransformViewModel.Width , self.TransformViewModel.Height ])
            if self.camera.scale > max_image_dimension_value * 2.0:
                self.camera.scale = max_image_dimension_value * 2.0

            if self.camera.scale < 0.5: 
                self.camera.scale = 0.5


    def on_mouse_release(self, e):
        self.SelectedPointIndex = None


    def on_mouse_press(self, e):
        (x, y) = self.GetCorrectedMousePosition(e)
        ImageX, ImageY = self.ImageCoordsForMouse(x, y)

        if ImageX is None or ImageY is None:
            return

        self.LastMousePosition = (x, y)

        if self.TransformViewModel is None:
            return

        if e.ShiftDown():
            if  e.LeftDown() and self.SelectedPointIndex is None:
                self.SelectedPointIndex = self.TransformViewModel.TryAddPoint(ImageX, ImageY, FixedSpace=self.FixedSpace)
                if e.AltDown():
                    self.TransformViewModel.AutoAlignPoints(self.SelectedPointIndex)

                history.SaveState(self.TransformViewModel.SetPoints, self.TransformViewModel.points)
            elif e.RightDown():
                self.TransformViewModel.TryDeletePoint(ImageX, ImageY, self.SelectionMaxDistance, FixedSpace=self.FixedSpace)
                if self.SelectedPointIndex > self.TransformViewModel.NumPoints:
                    self.SelectedPointIndex = self.TransformViewModel.NumPoints - 1

                history.SaveState(self.TransformViewModel.SetPoints, self.TransformViewModel.points)

        elif e.LeftDown():
            if e.AltDown() and not self.HighlightedPointIndex is None:
                self.TransformViewModel.SetPoint(self.HighlightedPointIndex, ImageX, ImageY, FixedSpace=self.FixedSpace)
                history.SaveState(self.TransformViewModel.SetPoints, self.TransformViewModel.points)
            else:
                distance, index = (None, None)
                if not self.composite:
                    distance, index = self.TransformViewModel.NearestPoint([ImageY, ImageX], FixedSpace=self.FixedSpace)
                else:
                    distance, index = self.TransformViewModel.NearestPoint([ImageY, ImageX], FixedSpace=True)

                print "d: " + str(distance) + " to p# " + str(index) + " max d: " + str(self.SelectionMaxDistance)
                if distance < self.SelectionMaxDistance:
                        self.SelectedPointIndex = index
                else:
                    self.SelectedPointIndex = None


    def on_mouse_drag(self, e):

        (x, y) = self.GetCorrectedMousePosition(e)

        if self.LastMousePosition is None:
            self.LastMousePosition = (x, y)
            return

        dx = x - self.LastMousePosition[0]
        dy = (y - self.LastMousePosition[1])

        self.LastMousePosition = (x, y)

        ImageX, ImageY = self.ImageCoordsForMouse(x, y)
        if ImageX is None:
            return

        ImageDX = (float(dx) / self.width) * self.camera.ViewWidth
        ImageDY = (float(dy) / self.height) * self.camera.ViewHeight

        if(e.RightIsDown()):
            self.camera.x = self.camera.x - ImageDX
            self.camera.y = self.camera.y - ImageDY

        if(e.LeftIsDown()):
            if e.CmdDown():
               # Translate all points
               self.TransformViewModel.TranslateFixed((ImageDY, ImageDX))
            else:
                # Create a point or drag a point
                if(not self.SelectedPointIndex is None):
                    self.SelectedPointIndex = self.TransformViewModel.MovePoint(self.SelectedPointIndex, ImageDX, ImageDY, FixedSpace=self.FixedSpace)
                elif(e.ShiftDown()):  # The shift key is selected and we do not have a last point dragged
                    return
                else:
                    # find nearest point
                    self.SelectedPointIndex = self.TransformViewModel.TryDrag(ImageX, ImageY, ImageDX, ImageDY, self.SelectionMaxDistance, FixedSpace=self.FixedSpace)

        self.update_status_bar()


