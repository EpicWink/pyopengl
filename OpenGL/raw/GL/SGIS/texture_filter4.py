'''OpenGL extension SGIS.texture_filter4

Overview (from the spec)
	
	This extension allows 1D and 2D textures to be filtered using an
	application-defined, four sample per dimension filter.  (In addition to
	the NEAREST and LINEAR filters defined in the original GL Specification.)
	Such filtering results in higher image quality.  It is defined only
	for non-mipmapped filters.  The filter that is specified must be
	symmetric and separable (in the 2D case).

The official definition of this extension is available here:
http://oss.sgi.com/projects/ogl-sample/registry/SGIS/texture_filter4.txt

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_SGIS_texture_filter4'
_DEPRECATED = False
GL_FILTER4_SGIS = constant.Constant( 'GL_FILTER4_SGIS', 0x8146 )
GL_TEXTURE_FILTER4_SIZE_SGIS = constant.Constant( 'GL_TEXTURE_FILTER4_SIZE_SGIS', 0x8147 )
glGetTexFilterFuncSGIS = platform.createExtensionFunction( 
'glGetTexFilterFuncSGIS',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLenum,arrays.GLfloatArray,),
doc='glGetTexFilterFuncSGIS(GLenum(target), GLenum(filter), GLfloatArray(weights)) -> None',
argNames=('target','filter','weights',),
deprecated=_DEPRECATED,
)

glTexFilterFuncSGIS = platform.createExtensionFunction( 
'glTexFilterFuncSGIS',dll=platform.GL,
extension=EXTENSION_NAME,
resultType=None, 
argTypes=(constants.GLenum,constants.GLenum,constants.GLsizei,arrays.GLfloatArray,),
doc='glTexFilterFuncSGIS(GLenum(target), GLenum(filter), GLsizei(n), GLfloatArray(weights)) -> None',
argNames=('target','filter','n','weights',),
deprecated=_DEPRECATED,
)


def glInitTextureFilter4SGIS():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )
