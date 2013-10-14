'''
Created on Sep 12, 2013

@author: u0490822
'''

import os
import numpy
from scipy.misc import imread
import logging

from OpenGL.GL import *
from OpenGL.GLU import *


def PackagePath():
    try:
        path = os.path.dirname(__file__)
    except:
        path = os.getcwd()

    return path

def ResourcePath():
    Logger = logging.getLogger("resources")
    rpath = os.path.join(PackagePath(), 'resources')
    Logger.info('Resources path: ' + rpath)
    return rpath


def README():
    '''Returns README.txt file as a string'''

    readmePath = os.path.join(PackagePath(), "readme.txt")
    if not os.path.exists(readmePath):
        return "No readme.txt was found in " + readmePath

    with open(readmePath, 'r') as hReadme:
        Readme = hReadme.read()
        hReadme.close()
        return Readme


def TextureForNumpyImage(image):
    '''Create a GL texture for the scipy.ndimage array'''

    image = image / 255.0
    image = numpy.float32(image)
    textureid = glGenTextures(1)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glBindTexture(GL_TEXTURE_2D, textureid)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_LUMINANCE, image.shape[1], image.shape[0],
                               GL_LUMINANCE, GL_FLOAT, image)

    return textureid

def LoadTexture(image):
    data = imread(image, flatten=True)
    return TextureForNumpyImage(data)

if __name__ == '__main__':
    pass