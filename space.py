import math
from node import Node
from keyframe import *
from mesh import load_textured
from transform import Trackball, identity, translate, rotate, scale, lerp, vec
from transform import (quaternion_slerp, quaternion_matrix, quaternion,
                       quaternion_from_euler,
                       quaternion_from_axis_angle)
import numpy as np
from projectile import *


class Planete(KeyFrameControlNode):

    #load planete object, the planete turn around vrot axis with
    #periode periode
    def __init__(self, planete, vrot, periode, scale):
        translate = {0: vec(0,0,0), 1: vec(0,0,0)}
        rotate = {0: quaternion(), periode/4:
                  quaternion_from_axis_angle(
            vrot, degrees= 90), periode/2:
                  quaternion_from_axis_angle(
            vrot, degrees = 180), 3*periode/4:
                  quaternion_from_axis_angle(
            vrot, degrees = 270), periode: quaternion()}
        scale = {0: scale, 2: scale}
        self.rayon = 1.;
        super().__init__(translate, rotate, scale)
        self.add(*load_textured(planete))


    def is_Planete(self):
        return True

    def get_rayon(self):
        return self.rayon


class PlaneteTransform(KeyFrameControlNode):
    '''create a Planete(planete,vrot,periode1,scale) and turn it
    around the center of the node, with a periode2 period and the
    initial position is vecDeb'''
    def __init__(self, planete, vrot, periode1, vecDeb, scale,
                 vdirec, periode2):
        vrot2 = np.cross(vecDeb, vdirec)
        translate = {0: vecDeb, (periode2/4):
                     rotate(vrot2,90)[:3,:3] @ vecDeb,
                     (periode2/2): rotate(vrot2,180)[:3,:3]@vecDeb,
                     (3*periode2/4): rotate(vrot2, 270)[:3,:3]@vecDeb,
                     (periode2): vecDeb}
        demi_grand_axe = math.pow(periode2*periode2*66740*math.pow(10,15)/(2*np.pi*np.pi),1/3)
        exentricite = ((np.linalg.norm(vecDeb)-demi_grand_axe)
                       / demi_grand_axe)
        rotate2 = {0: quaternion(), 1:quaternion()}
        scale2 = {0: 1, 2: 1, 4: 1}
        super().__init__(translate, rotate2, scale2, lerpCircle)
        planeteP = Planete(planete, vrot, periode1, scale)
        self.add(planeteP)

        
#Create a Solar System : we can add node below
class SystemeSolaire(Node):

    def __init__(self):

        super().__init__()
        soleil = Planete('objet3D/Sun_v2_L3.123cbc92ee65-5f03-4298-b1e6-b236b6b8b4aa/13913_Sun_v2_l3.obj',
                  np.array([1, 1, 0]), 10, 2)

        translate_keys_sun = {0: vec(0, 0, 0), 2: vec(0, 0, 0), 4: vec(0, 0, 0)}
        rotate_keys_sun = {0: quaternion(), 1:
                           quaternion_from_euler(90, 0, 0),
                       2: quaternion_from_euler(180, 0, 0), 3:
                           quaternion_from_euler(270,0,0),
                           4: quaternion()}
        scale_keys_sun = {0: 2, 2: 2, 4: 2}
        base = KeyFrameControlNode(translate_keys_sun,
                                   rotate_keys_sun, scale_keys_sun)
        base.add(soleil)

        translate_keys_earth = {0: vec(0, 3500, 00), 2: vec(0, 2500, 00),
                                4: vec(0, 3500, 00)}
        rotate_keys_earth = {0: quaternion(), 1:
                             quaternion_from_euler(90, 0, 0),
                       2: quaternion_from_euler(180, 0, 0), 3:
                             quaternion_from_euler(270,0,0), 4:
                             quaternion()}
        #rotate_keys_earth = {0: quaternion(), 2: quaternion(),
         #              3: quaternion(), 4: quaternion()}
        scale_keys_earth = {0: 1, 2: 1, 4: 1}

        terre_shape = KeyFrameControlNode(translate_keys_earth,
                                   rotate_keys_earth, scale_keys_earth)
        #terre_shape.add(terre)                     


        rotate_keys_t_earth = {0: quaternion(), 2: quaternion(),
                       3: quaternion(), 4: quaternion()}
        rotate_keys_t_earth = {0: quaternion(), 2:
                             quaternion_from_euler(90, 0, 0),
                       4: quaternion_from_euler(180, 0, 0), 6:
                             quaternion_from_euler(270,0,0), 8:
                             quaternion()}
        translate_keys_t_earth = {0: vec(0, 0, 3500), 2: vec(0, 2475,
                                                           2475),
                                4: vec(0, 3500, 0),
                                6:vec(0,2475,-2475), 8: vec(0,
                                                            0,-3500),
                                10: vec(0, -2475, -2475), 12: vec(0,
                                                                  -3500,
                                                                  0),
                                14: vec(0, - 2475, 2475), 16: vec(0,
                                    0, 3500)}
        translate_keys_t_earth = {0: vec(0, 00, 00), 2: vec(0, 00, 00),
                                4: vec(0, 00, 00)}
        scale_keys_t_earth = {0: 1, 2: 1, 4: 1}

        transform_terre = KeyFrameControlNode(translate_keys_t_earth,
                                   rotate_keys_t_earth, scale_keys_t_earth)

        translate_keys_t_sun = {0: vec(0, 0, 00), 2: vec(0, 0, 00),
                                4: vec(0, 0, 00)}
        rotate_keys_t_sun = {0: quaternion(), 2: quaternion()}
        scale_keys_t_sun = {0: 1, 2: 1, 4: 1}

        fusee = Projectile('objet3D/rocket_v1_L2.123c433550fa-0038-410c-a891-3367406a58a6/12216_rocket_v1_l2.obj',
                     vec(0,0,0),rotate_keys_t_sun, 1,
                     vec(0,100,00))
        transform_terre = PlaneteTransform('objet3D/Earth_v1_L3.123cce489830-ca89-49f4-bb2a-c921cce7adb2/13902_Earth_v1_l3.obj',
                                   np.array([1,1,0]), 1,
                                   np.array([9500,0,0]),1,np.array([1,1,0]),36.5)

        transform_lune = PlaneteTransform('objet3D/Moon/Moon2K.obj',
                                   np.array([1,1,1]), 2,
                                   np.array([3500,0,0]),19.5,np.array([1,1,1]),5)
        transform_terre.add(transform_lune)


        transform_base = KeyFrameControlNode(translate_keys_t_sun,
                                   rotate_keys_t_sun,
                                              scale_keys_t_sun)
        transform_base.add(soleil)
        transform_base.add(fusee) 
        transform_base.add(transform_terre)
        self.add(transform_base)
