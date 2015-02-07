__all__ = ['compositetransformview', 'imagetransformview']
 
import compositetransformview
import imagetransformview
import numpy
import gl
import pyglet


def LineIndiciesFromTri(T):
    '''
    :param ndarray T: numpy array of triangle indicies
    :rtype: list
    :returns: 1D list of triangle indicies 
    '''
    
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

def DrawTriangles(verts, Triangles):
    LineIndicies = LineIndiciesFromTri(Triangles)

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