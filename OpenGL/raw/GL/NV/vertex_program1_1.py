'''OpenGL extension NV.vertex_program1_1

Overview (from the spec)
	
	This extension adds four new vertex program instructions (DPH,
	RCC, SUB, and ABS).
	
	This extension also supports a position-invariant vertex program
	option.  A vertex program is position-invariant when it generates
	the _exact_ same homogenuous position and window space position
	for a vertex as conventional OpenGL transformation (ignoring vertex
	blending and weighting).
	
	By default, vertex programs are _not_ guaranteed to be
	position-invariant because there is no guarantee made that the way
	a vertex program might compute its homogenous position is exactly
	identical to the way conventional OpenGL transformation computes
	its homogenous positions.  In a position-invariant vertex program,
	the homogeneous position (HPOS) is not output by the program.
	Instead, the OpenGL implementation is expected to compute the HPOS
	for position-invariant vertex programs in a manner exactly identical
	to how the homogenous position and window position are computed
	for a vertex by conventional OpenGL transformation.  In this way
	position-invariant vertex programs guarantee correct multi-pass
	rendering semantics in cases where multiple passes are rendered and
	the second and subsequent passes use a GL_EQUAL depth test.

The official definition of this extension is available here:
http://oss.sgi.com/projects/ogl-sample/registry/NV/vertex_program1_1.txt

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_NV_vertex_program1_1'
_DEPRECATED = False



def glInitVertexProgram11NV():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )
