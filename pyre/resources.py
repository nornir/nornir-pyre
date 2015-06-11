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

from pkg_resources import resource_filename

# def ConfigDataPath():
#    return resource_filename(__name__, 'config')
#     try:
#         path = os.path.dirname(__file__)
#     except:
#         path = os.getcwd()
#
#     return path

def ResourcePath():
    Logger = logging.getLogger("resources")
    rpath = resource_filename(__name__, "resources")
    # rpath = os.path.join(PackagePath(), 'resources')
    Logger.info('Resources path: ' + rpath)
    return rpath


def README():
    '''Returns README.txt file as a string'''

    readmePath = resource_filename(__name__, "README.txt")

    # readmePath = os.path.join(PackagePath(), "readme.txt")
    if not os.path.exists(readmePath):
        return "No readme.txt was found in " + readmePath

    with open(readmePath, 'r') as hReadme:
        Readme = hReadme.read()
        hReadme.close()
        return Readme


def TextureForNumpyImage(image):
    '''Create a GL texture for the scipy.ndimage array'''
    
    image = numpy.float32(image) / 255.0
    textureid = glGenTextures(1)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glBindTexture(GL_TEXTURE_2D, textureid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_LUMINANCE8, image.shape[1], image.shape[0],
                               GL_LUMINANCE, GL_FLOAT, image)

    return textureid

def LoadTexture(image):
    data = imread(image, flatten=True)
    return TextureForNumpyImage(data)

if __name__ == '__main__':
    pass