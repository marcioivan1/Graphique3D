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
                              color_shader=self.color_shader, win=self.win)

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


# -------------- main program and scene setup --------------------------------
def main():
    """ create a window, add scene objects, then run rendering loop """
    viewer = Viewer()

    # place instances of our basic objects
    #viewer.add(*[mesh for file in sys.argv[1:] for mesh in load(file)])
    #if len(sys.argv) < 2:
    #    print('Usage:\n\t%s [3dfile]*\n\n3dfile\t\t the filename of a model in'
    #          ' format supported by pyassimp.' % (sys.argv[0],))
    '''cylinder = Cylinder()
    base_shape = Node(transform=scale(0.3))     # make a thin cylinder

    base_shape.add(cylinder)

    # make a thin cylinder
    arm_shape = Node(transform=translate(0,0,0.8)@scale(0.2))
    arm_shape.add(cylinder)                     # shape of arm

    # make a thin cylinder
    forearm_shape = Node(transform=translate(0,0,0.9)@scale(0.1))
    forearm_shape.add(cylinder)                 # shape of forearm

    theta = 45.0        # base horizontal rotation angle
    phi1 = 45.0         # arm angle
    phi2 = 20.0         # forearm angle

    transform_forearm = Node(transform=translate(0,0,0) @ rotate((1,0,0), phi2))
    transform_forearm.add(forearm_shape)

    transform_arm = Node(transform=rotate((1,0,0), phi1))
    transform_arm.add(arm_shape, transform_forearm)

    transform_base = Node(transform=rotate((1,0,0), theta))
    transform_base.add(base_shape, transform_arm)
    viewer.add(transform_base)'''
    '''a = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
    b = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
    vector_keyframes = KeyFrames({0: a, 3: b, 6: b})
    #vector_keyframes = KeyFrames({0: vec(1, 0, 0), 3: vec(0, 1, 0), 6: vec(0, 0, 1)})
    print(vector_keyframes.value(1.5))'''


    '''translate_keys = {0: vec(0, 0, 0), 2: vec(1, 1, 0), 4: vec(0, 0, 0)}
    rotate_keys = {0: quaternion(), 2: quaternion_from_euler(180, 45, 90),
                   3: quaternion_from_euler(180, 0, 180), 4: quaternion()}
    scale_keys = {0: 1, 2: 0.5, 4: 1}
    keynode = KeyFrameControlNode(translate_keys, rotate_keys, scale_keys)
    keynode.add(Cylinder())
    viewer.add(keynode)'''

    system = SystemeSolaire()
    viewer.add(system)
    '''fusee = Projectile('objet3D/rocket_v1_L2.123c433550fa-0038-410c-a891-3367406a58a6/12216_rocket_v1_l2.obj',
                 vec(0,0,0),vec(0,0,0),0,
                    vec(-1,0,0),90,0.001,vec(0,00,0))

    #viewer.add(transform_base)'''
    '''viewer.add(*[mesh for file in sys.argv[1:] for mesh in
                 load_textured(file)])
    if len(sys.argv) < 2:
        print('Usage:\n\t%s [3dfile]*\n\n3dfile\t\t the filename of a model in'
              ' format supported by pyassimp.' % (sys.argv[0],))
    # start rendering loop'''
    # texture = TexturedPlane('grass.png')
    #viewer.add(texture)
    viewer.run()


if __name__ == '__main__':
    glfw.init()                # initialize window system glfw
    main()                     # main function keeps variables locally scoped
    glfw.terminate()           # destroy all glfw windows and GL contexts


