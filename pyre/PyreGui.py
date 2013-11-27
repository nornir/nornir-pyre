import sys
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.select('2.8')
import wx

import os
from nornir_imageregistration.files.stosfile import StosFile
import nornir_imageregistration.transforms.factory
import pygletwx
import imagetransformpanel
import pyre
import common
import nornir_pools as Pools
from transformviewmodel import TransformViewModel
from imagetransformview import ImageTransformView
from compositetransformview import CompositeTransformView
import resources

import state

class MyFrame(wx.Frame):

    stosfilename = ''
    stosdirname = ''
    imagedirname = ''

    @property
    def ID(self):
        return self._ID


    def __init__(self, parent, windowID, title, showFixed=False, composite=False):
        wx.Frame.__init__(self, parent, title=title, size=(800, 400))

        print "Parent:" + str(self.Parent)

        self._ID = windowID
        # self.imagepanel = wx.Panel(self, -1)

        self.showFixed = showFixed
        self.Composite = composite

        self.FixedImageFullPath = None
        self.WarpedImageFullPath = None

        ###FOR DEBUGGING####
        # DataFullPath = os.path.join(os.getcwd(), "..", "Test","Data","Images")
        # FixedImageFullPath = os.path.join(DataFullPath, "0225_mosaic_64.png")
        # WarpedImageFullPath = os.path.join(DataFullPath, "0226_mosaic_64.png")
        # pyre.IrTweakInit(FixedImageFullPath, WarpedImageFullPath)
        ####################

        self.imagepanel = imagetransformpanel.ImageTransformViewPanel(parent=self,
                                              TransformViewModel=None,
                                              ImageTransformView=None,
                                              FixedSpace=self.showFixed,
                                              composite=self.Composite)

        # pyre.Config.TransformViewModel,
        # pyre.Config.FixedTransformView

        # self.control = wx.StaticText(panel, -1, README_Import(self), size=(800,-1))

        # Populate menu options into a File Dropdown menu.
        menuBar = wx.MenuBar()

        filemenu = self.__CreateFileMenu()
        menuBar.Append(filemenu, "&File")

        opsmenu = self.__CreateOpsMenu()
        menuBar.Append(opsmenu, "&Operations")

        self.windmenu = self.__CreateWindowsMenu()
        menuBar.Append(self.windmenu, "&Windows")

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Allows Drag and Drop
        dt = FileDrop(self)
        self.SetDropTarget(dt)

        # self.imagepanel.SetDropTarget(FileDrop(self.imagepanel))

        # self.SetDropTarget(TextDrop(self))
        # self.DragAcceptFiles(True)

        # print "Drop target set"

        # print str(self.GetDropTarget())

        self.Show(True)
        self.setPosition()

        # Make sure we have a GL context before initializing view window
        wx.CallAfter(self.UpdateRawImageWindow)


    def __CreateWindowsMenu(self):
        menu = wx.Menu()
        windowSubMenu = wx.Menu()

        displayCount = wx.Display_GetCount()

        if displayCount == 1:
            pass
        elif displayCount == 2:
            submenuWindow1 = windowSubMenu.Append(wx.ID_ANY, "Left 1 Window View")
            submenuWindow2 = windowSubMenu.Append(wx.ID_ANY, "Right 1 Window View")
            windowSubMenu.AppendSeparator()
            submenuWindow3 = windowSubMenu.Append(wx.ID_ANY, "2 Window View")

            self.Bind(wx.EVT_MENU, self.OnLeft1WindowView, submenuWindow1)
            self.Bind(wx.EVT_MENU, self.OnRight1WindowView, submenuWindow2)
            self.Bind(wx.EVT_MENU, self.On2WindowView, submenuWindow3)

            menu.AppendMenu(wx.ID_ANY, "&Window Options", windowSubMenu)

        elif displayCount >= 3:
            submenuWindow1 = windowSubMenu.Append(wx.ID_ANY, "Left 1 Window View")
            submenuWindow2 = windowSubMenu.Append(wx.ID_ANY, "Center 1 Window View")
            submenuWindow3 = windowSubMenu.Append(wx.ID_ANY, "Right 1 Window View")
            windowSubMenu.AppendSeparator()
            submenuWindow4 = windowSubMenu.Append(wx.ID_ANY, "Left 2 Window View")
            submenuWindow5 = windowSubMenu.Append(wx.ID_ANY, "Right 2 Window View")
            windowSubMenu.AppendSeparator()
            submenuWindow6 = windowSubMenu.Append(wx.ID_ANY, "3 Window View")

            self.Bind(wx.EVT_MENU, self.OnLeft1WindowView, submenuWindow1)
            self.Bind(wx.EVT_MENU, self.OnCenter1WindowView, submenuWindow2)
            self.Bind(wx.EVT_MENU, self.OnRight1WindowView, submenuWindow3)
            self.Bind(wx.EVT_MENU, self.On2WindowView, submenuWindow4)
            self.Bind(wx.EVT_MENU, self.OnRight2WindowView, submenuWindow5)
            self.Bind(wx.EVT_MENU, self.On3WindowView, submenuWindow6)

            menu.AppendMenu(wx.ID_ANY, "&Two Window Options", windowSubMenu)

        self.menuShowFixedImage = menu.Append(wx.ID_ANY, "&Fixed Image", kind=wx.ITEM_CHECK)
        menu.Check(self.menuShowFixedImage.GetId(), True)
        self.Bind(wx.EVT_MENU, self.OnShowFixedWindow, self.menuShowFixedImage)

        self.menuShowWarpedImage = menu.Append(wx.ID_ANY, "&Warped Image", kind=wx.ITEM_CHECK)
        menu.Check(self.menuShowWarpedImage.GetId(), True)
        self.Bind(wx.EVT_MENU, self.OnShowWarpedWindow, self.menuShowWarpedImage)

        self.menuShowCompositeImage = menu.Append(wx.ID_ANY, "&Composite Image", kind=wx.ITEM_CHECK)
        menu.Check(self.menuShowCompositeImage.GetId(), True)
        self.Bind(wx.EVT_MENU, self.OnShowCompositeWindow, self.menuShowCompositeImage)

        menu.AppendSeparator()

        menuRestoreOrientation = menu.Append(wx.ID_ANY, "&Restore Orientation")
        self.Bind(wx.EVT_MENU, self.OnRestoreOrientation, menuRestoreOrientation)

        return menu


    def __CreateOpsMenu(self):
        menu = wx.Menu()

        menuRotationTranslation = menu.Append(wx.ID_ANY, "&Rotate translate estimate")
        self.Bind(wx.EVT_MENU, self.OnRotateTranslate, menuRotationTranslation)

        menu.AppendSeparator()

        menuInstructions = menu.Append(wx.ID_ABOUT, "&Keyboard Instructions")
        self.Bind(wx.EVT_MENU, self.OnInstructions, menuInstructions)

        menuClear = menu.Append(wx.ID_ANY, "&Clear All Points")
        self.Bind(wx.EVT_MENU, self.OnClearAllPoints, menuClear)

        return menu


    def __CreateFileMenu(self):

        filemenu = wx.Menu()

        # Menu options
        menuOpenPyre = filemenu.Append(wx.ID_ANY, "&Open stos file")
        self.Bind(wx.EVT_MENU, self.OnOpenStos, menuOpenPyre)

        menuOpenFixedImage = filemenu.Append(wx.ID_ANY, "&Open Fixed Image")
        self.Bind(wx.EVT_MENU, self.OnOpenFixedImage, menuOpenFixedImage)

        menuOpenWarpedImage = filemenu.Append(wx.ID_ANY, "&Open Warped Image")
        self.Bind(wx.EVT_MENU, self.OnOpenWarpedImage, menuOpenWarpedImage)

        filemenu.AppendSeparator()

        menuSaveStos = filemenu.Append(wx.ID_ANY, "&Save Stos File")
        self.Bind(wx.EVT_MENU, self.OnSaveStos, menuSaveStos)

        menuSaveWarpedImage = filemenu.Append(wx.ID_ANY, "&Save Warped Image")
        self.Bind(wx.EVT_MENU, self.OnSaveWarpedImage, menuSaveWarpedImage)

        filemenu.AppendSeparator()

        menuExit = filemenu.Append(wx.ID_EXIT, "&Exit")
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        return filemenu


    def UpdateRawImageWindow(self):

        # if hasattr(self, 'imagepanel'):
        #    del self.imagepanel

        imageTransformView = None
        if self.Composite:
            imageTransformView = CompositeTransformView(state.currentConfig.FixedImageViewModel,
                                                    state.currentConfig.WarpedImageViewModel,
                                                    state.currentConfig.TransformViewModel)
        else:
            imageViewModel = state.currentConfig.FixedImageViewModel
            if not self.showFixed:
                imageViewModel = state.currentConfig.WarpedImageViewModel

            imageTransformView = ImageTransformView(imageViewModel,
                                                    state.currentConfig.TransformViewModel)

        self.imagepanel.TransformViewModel = state.currentConfig.TransformViewModel
        self.imagepanel.ImageTransformView = imageTransformView


    def ToggleWindowShown(self):
        if self.IsShown():
            self.Hide()
        else:
            self.Show()


    def OnShowFixedWindow(self, e):
        pyre.ToggleWindow('Fixed')


    def OnShowWarpedWindow(self, e):
        pyre.ToggleWindow('Warped')


    def OnShowCompositeWindow(self, e):
        pyre.ToggleWindow('Composite')


    def OnRestoreOrientation(self, e):
        pyre.Windows['Composite'].setPosition()
        pyre.Windows['Warped'].setPosition()
        pyre.Windows['Fixed'].setPosition()


    def OnClose(self, e):
        self.Shown = not self.Shown
        if not pyre.AnyVisibleWindows():
            self.OnExit()


    def OnExit(self, e=None):
        pyre.Exit()


    def OnInstructions(self, e):

        readme = resources.README()
        dlg = wx.MessageDialog(self, readme, "Keyboard Instructions", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnClearAllPoints(self, e):
        state.currentConfig.TransformViewModel = TransformViewModel.CreateDefault(state.currentConfig.FixedImageViewModel.RawImageSize,
                                                                 state.currentConfig.WarpedImageViewModel.RawImageSize)

#
#    def UpdateFromConfig(self):
#
#        if Config.CurrentTransform is None:
#            return
#
#        self.imagepanel.TransformViewModel = Config.TransformViewModel
#
#        if self.imagepanel.composite:
#            self.imagepanel.ImageTransformView = Config.CompositeView
#        elif self.showFixed:
#            self.imagepanel.ImageTransformView = Config.FixedTransformView
#        else:
#            self.imagepanel.ImageTransformView = Config.WarpedTransformView


    def OnRotateTranslate(self, e):
        common.RotateTranslateWarpedImage()


    def OnOpenFixedImage(self, e):
        dlg = wx.FileDialog(self, "Choose a file", MyFrame.imagedirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.GetFilename())
            MyFrame.imagedirname = str(dlg.GetDirectory())

            state.currentConfig.LoadFixedImage(os.path.join(MyFrame.imagedirname, filename))

        dlg.Destroy()
        # if Config.FixedImageFullPath is not None and Config.WarpedImageFullPath is not None:
        #    pyre.IrTweakInit(Config.FixedImageFullPath, Config.WarpedImageFullPath)


    def OnOpenWarpedImage(self, e):
        dlg = wx.FileDialog(self, "Choose a file", MyFrame.imagedirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.GetFilename())
            MyFrame.imagedirname = str(dlg.GetDirectory())

            state.currentConfig.LoadWarpedImage(os.path.join(MyFrame.imagedirname, filename))

        dlg.Destroy()

        # if Config.FixedImageFullPath is not None and Config.WarpedImageFullPath is not None:
        #    pyre.IrTweakInit(Config.FixedImageFullPath, Config.WarpedImageFullPath)


    def OnOpenStos(self, e):
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.stos", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = str(dlg.GetFilename())
            dirname = str(dlg.GetDirectory())
            MyFrame.stosfilename = filename

            state.currentConfig.LoadStos(os.path.join(dirname, filename))

        dlg.Destroy()


    def OnSaveWarpedImage(self, e):
        # Set the path for the output directory.
        if not (state.currentConfig.FixedImageViewModel is None or state.currentConfig.WarpedImageViewModel is None):
            dlg = wx.FileDialog(self, "Choose a Directory", MyFrame.imagedirname, "", "*.png", wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                MyFrame.imagedirname = dlg.GetDirectory()
                self.filename = dlg.GetFilename()
                state.currentConfig.OutputImageFullPath = os.path.join(MyFrame.imagedirname, self.filename)

                pool = Pools.GetGlobalThreadPool()
                pool.add_task("Save " + state.currentConfig.OutputImageFullPath,
                               common.SaveRegisteredWarpedImage,
                               state.currentConfig.OutputImageFullPath,
                               state.currentConfig.TransformViewModel.TransformModel,
                               state.currentConfig.WarpedImageViewModel.Image)


    def OnSaveStos(self, e):
        if not (state.currentConfig.TransformViewModel is None):
            self.dirname = ''
            dlg = wx.FileDialog(self, "Choose a Directory", MyFrame.stosdirname, MyFrame.stosfilename, "*.stos", wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                MyFrame.stosdirname = dlg.GetDirectory()
                MyFrame.stosfilename = dlg.GetFilename()
                saveFileFullPath = os.path.join(MyFrame.stosdirname, MyFrame.stosfilename)

                stosObj = StosFile.Create(state.currentConfig.FixedImageViewModel.ImageFilename,
                                          state.currentConfig.WarpedImageViewModel.ImageFilename,
                                          state.currentConfig.TransformViewModel.TransformModel)
                stosObj.Save(saveFileFullPath)
            dlg.Destroy()


    def OnLeft1WindowView(self, e):
        pyre.Windows['Fixed'].setPosition(position=0, desiredDisplays=1)
        pyre.Windows['Warped'].setPosition(position=0, desiredDisplays=1)
        pyre.Windows['Composite'].setPosition(position=0, desiredDisplays=1)


    def OnCenter1WindowView(self, e):
        pyre.Windows['Fixed'].setPosition(position=1, desiredDisplays=1)
        pyre.Windows['Warped'].setPosition(position=1, desiredDisplays=1)
        pyre.Windows['Composite'].setPosition(position=1, desiredDisplays=1)


    def OnRight1WindowView(self, e):

        count = wx.Display_GetCount()

        if count == 2:
            pyre.Windows['Fixed'].setPosition(position=1, desiredDisplays=1)
            pyre.Windows['Warped'].setPosition(position=1, desiredDisplays=1)
            pyre.Windows['Composite'].setPosition(position=1, desiredDisplays=1)
        else:
            pyre.Windows['Fixed'].setPosition(position=2, desiredDisplays=1)
            pyre.Windows['Warped'].setPosition(position=2, desiredDisplays=1)
            pyre.Windows['Composite'].setPosition(position=2, desiredDisplays=1)


    def On2WindowView(self, e):
        locations = 0, 1
        pyre.Windows['Fixed'].setPosition(position=locations, desiredDisplays=2)
        pyre.Windows['Warped'].setPosition(position=locations, desiredDisplays=2)
        pyre.Windows['Composite'].setPosition(position=locations, desiredDisplays=2)


    def OnRight2WindowView(self, e):
        locations = 1, 2
        pyre.Windows['Fixed'].setPosition(position=locations, desiredDisplays=2)
        pyre.Windows['Warped'].setPosition(position=locations, desiredDisplays=2)
        pyre.Windows['Composite'].setPosition(position=locations, desiredDisplays=2)


    def On3WindowView(self, e):
        locations = 0, 1, 2
        pyre.Windows['Fixed'].setPosition(position=locations, desiredDisplays=2)
        pyre.Windows['Warped'].setPosition(position=locations, desiredDisplays=2)
        pyre.Windows['Composite'].setPosition(position=locations, desiredDisplays=2)


    def findDisplayOrder(self, position=None):

        displays = (wx.Display(i) for i in range(wx.Display_GetCount()))
        sizes = [display.GetClientArea() for display in displays]

        orderedSizeList = []
        while len(sizes) > 0:
            smallestX = None
            for i in range(len(sizes)):
                if smallestX is None:
                    smallestX = sizes[i][0], i
                if sizes[i][0] < smallestX[0]:
                    smallestX = sizes[i][0], i
            orderedSizeList.append(sizes.pop(smallestX[1]))

        return orderedSizeList


    def setPosition(self, desiredDisplays=None, count=None, position=None):

        if count is None:
            count = wx.Display.GetCount()
        if desiredDisplays is None:
            desiredDisplays = count
        if position is None:
            if count == 1:
                position = 0
            elif count == 2:
                position = 0, 1
            else:
                position = 0, 1, 2

        sizes = self.findDisplayOrder(position)

        if not 'Fixed' in pyre.Windows:
            return

        if not 'Warped' in pyre.Windows:
            return

        ######
        # Use these for debug
        # count = 2
        # sizes = sizes[1]
        # desiredDisplays = 2
        # position = 0, 1
        ######
        if desiredDisplays == 1:
            halfY = sizes[position][3] / 2
            halfX = sizes[position][2] / 2
            if self.Title == "Fixed Image" or self.Title == pyre.Windows['Fixed'].Title:
                self.MoveXY(sizes[position][0], sizes[position][1])
                self.SetSizeWH(halfX, halfY)
            elif self.Title == "Warped Image" or self.Title == pyre.Windows['Warped'].Title:
                self.MoveXY(sizes[position][0] + halfX, sizes[position][1])
                self.SetSizeWH(halfX, halfY)
            else:
                self.MoveXY(sizes[position][0], halfY)
                self.SetSizeWH(sizes[position][2], halfY)

        elif desiredDisplays == 2 and count >= 2:
            halfX = (sizes[position[1]][2] - sizes[position[1]][0]) / 2
            halfY = (sizes[position[1]][3] - sizes[position[1]][1]) / 2
            if self.Title == "Fixed Image" or self.Title == pyre.Windows['Fixed'].Title:
                self.MoveXY(sizes[position[1]][0], sizes[position[1]][1])
                self.SetSizeWH(sizes[position[1]][2], halfY)
            elif self.Title == "Warped Image" or self.Title == pyre.Windows['Warped'].Title:
                self.MoveXY(sizes[position[1]][0], halfY)
                self.SetSizeWH(sizes[position[1]][2], halfY)
            else:
                self.MoveXY(sizes[position[0]][0], sizes[position[0]][1])
                self.SetSizeWH(sizes[position[0]][2], sizes[position[0]][3])

        elif desiredDisplays >= 3 and count >= 3:
            if self.Title == "Fixed Image" or self.Title == pyre.Windows['Fixed'].Title:
                self.MoveXY(sizes[position[0]][0], sizes[position[0]][1])
                self.SetSizeWH(sizes[0][2], sizes[0][3])
            elif self.Title == "Warped Image" or self.Title == pyre.Windows['Warped'].Title:
                self.MoveXY(sizes[position[2]][0], sizes[position[2]][1])
                self.SetSizeWH(sizes[position[2]][2], sizes[position[2]][3])
            else:
                self.MoveXY(sizes[position[1]][0], sizes[position[1]][1])
                self.SetSizeWH(sizes[position[1]][2], sizes[position[1]][3])
        self.Update()


class TextDrop (wx.TextDropTarget):
    def __init__(self, window):

        super(TextDrop, self).__init__()
        self.window = window

    def OnDragOver(self, *args, **kwargs):
        print "DragOver Text"
        return wx.TextDropTarget.OnDragOver(self, *args, **kwargs)

    def OnDropText(self, x, y, data):
        print str(data)

class FileDrop (wx.FileDropTarget):
    def __init__(self, window):

        super(FileDrop, self).__init__()
        self.window = window

    def OnDragOver(self, *args, **kwargs):
        print "DragOver"
        return wx.FileDropTarget.OnDragOver(self, *args, **kwargs)

    def OnDropFiles(self, x, y, filenames):
        for name in filenames:
            try:
                fullpath = name.encode('ascii')
                dirname, filename = os.path.split(name)
                root, extension = os.path.splitext(name)

                if extension == ".stos":
                    MyFrame.stosdirname = dirname
                    MyFrame.stosfilename = filename
                    state.currentConfig.LoadStos(fullpath)
                else:
                    if self.window.ID == "Fixed":
                        state.currentConfig.LoadFixedImage(fullpath)
                    elif self.window.ID == "Warped":
                        state.currentConfig.LoadWarpedImage(fullpath)
                    else:
                        pass

            except IOError, error:
                dlg = wx.MessageDialog(None, "Error opening file\n" + str(error))
                dlg.ShowModal()


if __name__ == '__main__':
   pass
