#!/usr/bin/env python3
"""
Python OpenGL practical application.
"""
# Python built-in modules
import os                           # os function, i.e. checking file status
from itertools import cycle
import sys

# External, non built-in modules
import OpenGL.GL as GL      # standard Python OpenGL wrapper
import glfw                 # lean window system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
import pyassimp                     # 3D resource loader
import pyassimp.errors              # Assimp error management + exceptions

from mesh import *
from shader import *

from transform import Trackball, identity, translate, rotate, scale, lerp, vec
from transform import (quaternion_slerp, quaternion_matrix, quaternion,
                       quaternion_from_euler)
from bisect import bisect_left
from itertools import cycle

from space import SystemeSolaire
from node import Node
from projectile import *
from skybox import *

# ------------ low level OpenGL object wrappers ----------------------------


# -------------- OpenGL Texture Wrapper ---------------------------------------



# ------------  simple color fragment shader demonstrated in Practical 1 ------
COLOR_VERT = """#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;


uniform mat4 model; 
uniform mat4 view;
uniform mat4 projection;


uniform mat3 transinvmod;

out vec3 monde_normal;
out vec4 positionFrag;

void main() {
    gl_Position = projection * view * model * vec4(position, 1);
    monde_normal = transinvmod * normal;
    positionFrag = vec4(position, 1);
}"""

COLOR_FRAG = """#version 330 core

in vec3 monde_normal;
in vec4 positionFrag;
uniform mat4 invview;

uniform vec3 lightDirection;

uniform vec3 color;
uniform vec3 Ks;
uniform vec3 Ka;
uniform float s;

out vec4 outColor;

vec3 colorFinal;
vec3 v;

void main() {
    float scalarProduct=dot(normalize(monde_normal),
    normalize(lightDirection));
    if(scalarProduct < 0){
        scalarProduct = 0.;
    }
    v = -vec3(invview*positionFrag);
    float scalar_product2 = dot(reflect(normalize(lightDirection),
    normalize(monde_normal)),normalize(v));
    if(scalar_product2 < 0){
        scalar_product2 = 0;
    }
    colorFinal = Ka + color*scalarProduct +
        Ks*pow(scalar_product2,s);
    outColor = vec4(colorFinal,1);
}"""

# -------------- Skybox texture shaders ---------------------------------------
TEXTURE_SKYBOX_VERT = """#version 330 core
uniform mat4 viewprojection;
layout(location = 0) in vec3 position;
out vec3 fragTexCoord;

void main() {
    gl_Position = viewprojection * vec4(position, 1);
    // fragTexCoord = position.xy;
    fragTexCoord = position;
}"""

TEXTURE_SKYBOX_FRAG = """#version 330 core
uniform samplerCube skybox; // each such OpenGL sampler is meant to be associated to an active texture unit
in vec3 fragTexCoord;
out vec4 outColor;
void main() {
    // access the texture and retrieve an RGBA color from it
    // (automatically filtered/interpolated according to the parameters passed at initialization)
    // a set of texture coordinates is passed in [0,1]^2 (vec2 type) to address which texel is retrieved
    outColor = texture(skybox, fragTexCoord); 
}"""





# ------------  Scene object classes ------------------------------------------








class Cylinder(Node):
    """ Very simple cylinder based on practical 2 load function """
    def __init__(self):
        super().__init__()
        self.add(*load('cylinder.obj'))  # just load the cylinder from file










# ------------  Viewer class & window management ------------------------------
class GLFWTrackball(Trackball):
    """ Use in Viewer for interactive viewpoint control """

    def __init__(self, win):
        """ Init needs a GLFW window handler 'win' to register callbacks """
        super().__init__()
        self.mouse = (0, 0)
        glfw.set_cursor_pos_callback(win, self.on_mouse_move)
        glfw.set_scroll_callback(win, self.on_scroll)

    def on_mouse_move(self, win, xpos, ypos):
        """ Rotate on left-click & drag, pan on right-click & drag """
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.drag(old, self.mouse, glfw.get_window_size(win))
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.pan(old, self.mouse)

    def on_scroll(self, win, _deltax, deltay):
        """ Scroll controls the camera distance to trackball center """
        self.zoom(deltay, glfw.get_window_size(win)[1])


class Viewer:
    """ GLFW viewer window, with classic initialization & graphics loop """

    def __init__(self, width=640, height=480):

        # version hints: create GL window with >= OpenGL 3.3 and core profile
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)
        self.win = glfw.create_window(width, height, 'Viewer', None, None)

        # make win's OpenGL context current; no OpenGL calls can happen before
        glfw.make_context_current(self.win)

        # register event handlers
        glfw.set_key_callback(self.win, self.on_key)

        # useful message to check OpenGL renderer characteristics
        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        # initialize GL by setting viewport and default render characteristics
        GL.glClearColor(0.1, 0.1, 0.1, 0.1)
        GL.glEnable(GL.GL_DEPTH_TEST)         # depth test now enabled (TP2)
        GL.glEnable(GL.GL_CULL_FACE)          # backface culling enabled (TP2)

        # compile and initialize shader programs once globally
        self.color_shader = Shader(COLOR_VERT, COLOR_FRAG)
        self.texture_shader_skybox = Shader(TEXTURE_SKYBOX_VERT, TEXTURE_SKYBOX_FRAG)

        # initially empty list of object to draw
        self.drawables = []

        # initialize trackball
        self.trackball = GLFWTrackball(self.win)

        # cyclic iterator to easily toggle polygon rendering modes
        self.fill_modes = cycle([GL.GL_LINE, GL.GL_POINT, GL.GL_FILL])
        
    def run(self):
        """ Main render loop for this OpenGL window """
        while not glfw.window_should_close(self.win):
            # clear draw buffer and depth buffer (<-TP2)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            winsize = glfw.get_window_size(self.win)
            view = self.trackball.view_matrix()
            projection = self.trackball.projection_matrix(winsize)

            # draw our scene objects
            for drawable in self.drawables:
                drawable.draw(projection, view, identity(),
                              color_shader=self.color_shader,
                              win=self.win,
                              texture_shader_skybox=self.texture_shader_skybox)

            # flush render commands, and swap draw buffers
            glfw.swap_buffers(self.win)

            # Poll for and process events
            glfw.poll_events()

    def add(self, *drawables):
        """ add objects to draw in this window """
        self.drawables.extend(drawables)

    def on_key(self, _win, key, _scancode, action, _mods):
        """ 'Q' or 'Escape' quits """
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)
            if key == glfw.KEY_W:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))
            if key == glfw.KEY_SPACE: glfw.set_time(0)


# -------------- main program and scene setup --------------------------------
def main():
    """ create a window, add scene objects, then run rendering loop """
    viewer = Viewer()

    file = ["ame_nebula/right.tga", "ame_nebula/left.tga", "ame_nebula/top.tga", 
    "ame_nebula/bottom.tga", "ame_nebula/front.tga", "ame_nebula/back.tga"]
    viewer.add(Skybox(file=file))

    system = SystemeSolaire()
    viewer.add(system)
    viewer.run()


if __name__ == '__main__':
    glfw.init()                # initialize window system glfw
    main()                     # main function keeps variables locally scoped
    glfw.terminate()           # destroy all glfw windows and GL contexts


