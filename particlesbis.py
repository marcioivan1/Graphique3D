import random

# External, non built-in modules
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
import pyassimp                     # 3D ressource loader
import pyassimp.errors              # assimp error management + exceptions
from PIL import Image               # load images for textures

from vertex import *
from transform import *


# -----------------------------------------------------------------------------
class Particle:
    """ particle object """

    def __init__(self, position=np.array((0,0,0), 'f'),
                 velocity=np.array((0,1,0), 'f'),
                 color=np.array((1,1,1,1), 'f'), life=1.0):

        self.position = position
        self.velocity = velocity
        self.color = color
        self.life = life


# -----------------------------------------------------------------------------
class ParticleGenerator:
    """ particle object """

    def __init__(self, file, amount=500):

        # setup mesh and attribute properties
        position = np.array(((0,1),(1,0),(0,0),(0,1),(1,1),(1,0)), 'f')
        texCoords = np.array(((0,1),(1,0),(0,0),(0,1),(1,1),(1,0)), 'f')

        # setup texture and upload it to GPU
        self.texture = Texture(file)

        self.vertex_array = VertexArray([position, texCoords])

        self.particles = [Particle()] * amount
        self.amount = amount
        self.lastUsedParticle = 0


    def draw(self, projection, view, model, **param):
        for p in self.particles:
            if (p.life > 0.0):
       
                self.shader = param['texture_shader_particle']

                GL.glUseProgram(self.shader.glid)

                GL.glEnable(GL.GL_BLEND)

                # Use additive blending to give it a 'glow' effect
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)

                # draw code in the rendering loop
                self.vertex_array.execute(GL.GL_TRIANGLES)

                # only used for uniform
                color = p.color
                my_color_location = GL.glGetUniformLocation(self.shader.glid, 'color')
                GL.glUniform4fv(my_color_location, 1, color)

                position = p.position
                my_position_location = GL.glGetUniformLocation(self.shader.glid, 'offset')
                GL.glUniform2fv(my_position_location, 1, position)

                matrix_location = GL.glGetUniformLocation(self.shader.glid, 'projection')
                GL.glUniformMatrix4fv(matrix_location, 1, True, projection)

                # texture access setups
                loc = GL.glGetUniformLocation(self.shader.glid, 'sprite')
                GL.glActiveTexture(GL.GL_TEXTURE0) # activate the 0th texture unit ; ith unit to generalize
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture.glid) # associates an existing OpenGL texture to the corresponding texture unit
                GL.glUniform1i(loc, 0) # sampler is treated as a uniform integer variable, to which we pass the number of the texture unit
                self.vertex_array.execute(GL.GL_TRIANGLES)

                # Don't forget to reset to default blending mode
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)


    def update(self, dt, obj=0, newParticles=2, offset=np.array((0,0,0), 'f')):

        '''for i in range(0, newParticles):
            unusedParticle = self.firstUnusedParticle()
            self.respawnParticle(self.particles[unusedParticle],
            obj, offset)'''

        for p in self.particles:

            p.life -= dt
            if p.life > 0.0:
                p.position -= p.velocity * dt
                #p.color = p.color * dt * 2.5
            else:
                self.respawnParticle(p)


    def firstUnusedParticle(self):
        
        for i in range(self.lastUsedParticle, self.amount):
            if self.particles[i].life <= 0.0:
                self.lastUsedParticle = i
                return i

        for i in range(0, self.lastUsedParticle):
            if self.particles[i].life <= 0.0:
                self.lastUsedParticle = i
                return i

        self.lastUsedParticle = 0
        return 0

    def respawnParticle(self, particle, obj=0, offset=np.array((0,0,0), 'f')):
        
        rdm = ((random.randint(0, 32767) % 100) - 50) / 50.0
        rColor = 0.5 + ((random.randint(0, 32767) % 100) / 200.0)
        p = np.array((0,0,0), 'f')
        particle.position = p + vec(rdm, rdm, rdm) + offset # obj.position
        particle.color = np.array((rColor, rColor, rColor, 1.0), 'f')
        particle.life = 1.0
        v = np.array((0,1,0), 'f')
        particle.velocity = v * 0.1 # obj.velocity

