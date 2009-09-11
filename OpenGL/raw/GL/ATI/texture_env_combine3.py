'''OpenGL extension ATI.texture_env_combine3

Overview (from the spec)
	
	Adds new set of operations to the texture combiner operations.
	
	MODULATE_ADD_ATI               Arg0 * Arg2 + Arg1
	MODULATE_SIGNED_ADD_ATI        Arg0 * Arg2 + Arg1 - 0.5
	MODULATE_SUBTRACT_ATI          Arg0 * Arg2 - Arg1
	
	where Arg0, Arg1 and Arg2 are derived from
	
	    PRIMARY_COLOR_ARB       primary color of incoming fragment
	    TEXTURE                 texture color of corresponding texture unit
	    CONSTANT_ARB            texture environment constant color
	    PREVIOUS_ARB            result of previous texture environment; on
	                            texture unit 0, this maps to PRIMARY_COLOR_ARB
	
	In addition, the result may be scaled by 1.0, 2.0 or 4.0.
	
	Note that in addition to providing more flexible equations new source 
	inputs have been added for zero and one.

The official definition of this extension is available here:
http://oss.sgi.com/projects/ogl-sample/registry/ATI/texture_env_combine3.txt

Automatically generated by the get_gl_extensions script, do not edit!
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_ATI_texture_env_combine3'
_DEPRECATED = False
GL_MODULATE_ADD_ATI = constant.Constant( 'GL_MODULATE_ADD_ATI', 0x8744 )
GL_MODULATE_SIGNED_ADD_ATI = constant.Constant( 'GL_MODULATE_SIGNED_ADD_ATI', 0x8745 )
GL_MODULATE_SUBTRACT_ATI = constant.Constant( 'GL_MODULATE_SUBTRACT_ATI', 0x8746 )


def glInitTextureEnvCombine3ATI():
    '''Return boolean indicating whether this extension is available'''
    return extensions.hasGLExtension( EXTENSION_NAME )
