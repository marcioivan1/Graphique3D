# External, non built-in modules
import OpenGL.GL as GL      # standard Python OpenGL wrapper
import glfw                 # lean window system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
import pyassimp                     # 3D resource loader
import pyassimp.errors              # Assimp error management + exceptions

from vertex import *

# -------------- OpenGL Cubemap Texture Wrapper --------------------------------
class Cubemap:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, file, wrap_mode=GL.GL_CLAMP_TO_EDGE, min_filter=GL.GL_LINEAR,
                 mag_filter=GL.GL_LINEAR_MIPMAP_LINEAR):
        textureID = [GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_X, 
                            GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Y, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
                            GL.GL_TEXTURE_CUBE_MAP_POSITIVE_Z, GL.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z]
        self.glid = GL.glGenTextures(1, textureID) # creates an OpenGL id used to reference the GPU texture in subsequent calls
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, self.glid) # GPU texture bounded so it can be used or referenced
        # helper array stores texture format for every pixel size 1..4
        format = [GL.GL_LUMINANCE, GL.GL_LUMINANCE_ALPHA, GL.GL_RGB, GL.GL_RGBA]
        try:
            # imports images as a numpy array in exactly right format
            for i in range(0, 6):
                tex = np.array(Image.open(file[i]))
                GL.glTexImage2D(textureID[i], 0, GL.GL_RGBA, tex.shape[1],
                                tex.shape[0], 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, tex)

            # pass texture parameters that control how a texture wraps when addressed outside the 
            # standard range of [0,1]^2 and to control texel interpolation
            GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, min_filter);
            GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER, mag_filter);
            GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S, wrap_mode);
            GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T, wrap_mode);
            GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R, wrap_mode);  

            # generates a Gaussian image pyramid which is used for intelligent sampling at the appropriate scale to avoid aliasing
            GL.glGenerateMipmap(GL.GL_TEXTURE_CUBE_MAP)

            message = 'Loaded texture %s\t(%s, %s, %s, %s)'
            print(message % (file, tex.shape, wrap_mode, min_filter, mag_filter))
        except FileNotFoundError:
            print("ERROR: unable to load texture file %s" % file)
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)

    def __del__(self):  # delete GL texture from GPU when object dies
        GL.glDeleteTextures(self.glid)

# -----------------------------------------------------------------------------
class Skybox:
    """ skybox object """

    def __init__(self, file):
        position = np.array(((-1.0,  1.0, -1.0), (-1.0, -1.0, -1.0), ( 1.0, -1.0, -1.0), ( 1.0, -1.0, -1.0), ( 1.0,  1.0, -1.0), (-1.0,  1.0, -1.0),
                (-1.0, -1.0,  1.0), (-1.0, -1.0, -1.0), (-1.0,  1.0, -1.0), (-1.0,  1.0, -1.0), (-1.0,  1.0,  1.0), (-1.0, -1.0,  1.0),
                (1.0, -1.0, -1.0), (1.0, -1.0,  1.0), (1.0,  1.0,  1.0), (1.0,  1.0,  1.0), (1.0,  1.0, -1.0), (1.0, -1.0, -1.0),
                (-1.0, -1.0,  1.0), (-1.0,  1.0,  1.0), ( 1.0,  1.0,  1.0), ( 1.0,  1.0,  1.0), ( 1.0, -1.0,  1.0), (-1.0, -1.0,  1.0),
                (-1.0,  1.0, -1.0), (1.0,  1.0, -1.0), ( 1.0,  1.0,  1.0), ( 1.0,  1.0,  1.0), (-1.0,  1.0,  1.0), (-1.0,  1.0, -1.0),
                (-1.0, -1.0, -1.0), (-1.0, -1.0,  1.0), ( 1.0, -1.0, -1.0), ( 1.0, -1.0, -1.0), (-1.0, -1.0,  1.0), ( 1.0, -1.0,  1.0)), 'f')

        position = position*100

        self.vertex_array = VertexArray([position])

        self.file = file

        # setup texture and upload it to GPU
        self.texture = Cubemap(file)


    def draw(self, projection, view, model, win=None, **_kwargs):

        self.shader = _kwargs['texture_shader_skybox']

        GL.glUseProgram(self.shader.glid)

        # projection geometry
        loc = GL.glGetUniformLocation(self.shader.glid, 'viewprojection')
        GL.glUniformMatrix4fv(loc, 1, True, projection @ view)

        # texture access setups
        loc = GL.glGetUniformLocation(self.shader.glid, 'skybox')
        GL.glActiveTexture(GL.GL_TEXTURE0) # activate the 0th texture unit ; ith unit to generalize
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, self.texture.glid) # associates an existing OpenGL texture to the corresponding texture unit
        GL.glUniform1i(loc, 0) # sampler is treated as a uniform integer variable, to which we pass the number of the texture unit
        self.vertex_array.execute(GL.GL_TRIANGLES)

        # leave clean state for easier debugging
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)
        GL.glUseProgram(0)