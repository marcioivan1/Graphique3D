import math
from node import *
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
    #periode period
    def __init__(self, planete, vrot, periode, scale, name='', **kwargs):
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
        super().__init__(translate, rotate, scale, name, **kwargs)
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
                 vdirec, periode2, name='', lumineux=False, **kwargs):
        if (name=='' and lumineux == True):
            print("Un objet lumineux doit avoir un nom")
        vrot2 = np.cross(vecDeb, vdirec)
        if(np.linalg.norm(vecDeb)==0):
            translate ={0: vec(0,0,0), 1:vec(0,0,0)}
        else:
            translate = {0: vecDeb, (periode2/4):
                         rotate(vrot2,90)[:3,:3] @ vecDeb,
                         (periode2/2): rotate(vrot2,180)[:3,:3]@vecDeb,
                         (3*periode2/4): rotate(vrot2, 270)[:3,:3]@vecDeb,
                         (periode2): vecDeb}
        demi_grand_axe = math.pow(periode2*periode2*66740*math.pow(10,15)/(2*np.pi*np.pi),1/3)
        rotate2 = {0: quaternion(), 1:quaternion()}
        scale2 = {0: 1, 2: 1, 4: 1}
        self.lumineux = lumineux
        if(lumineux==True):
            kwargs['light'] = (0,0,0)
        super().__init__(translate, rotate2, scale2, name,
                         lerpCircle, **kwargs)
        planeteP = Planete(planete, vrot, periode1, scale)
        self.add(planeteP)

    def draw(self, projection, view, model, **param):
        if(self.lumineux):
            param['light'] = self.get_position()
            if('position' in param):
                del param['position']
        if(not self.lumineux):
            param['position'] = self.get_position()
        super().draw(projection, view, model, **param)

    def get_Planete(self):
        return self.children[0]

#Create a Solar System : we can add node below
class SystemeSolaire(KeyFrameControlNode):

    def __init__(self):


        translate_keys_solar_system = {0: vec(0, 0, 00), 2: vec(0, 0, 00),
                                4: vec(0, 0, 00)}
        rotate_keys_solar_system = {0: quaternion(), 2: quaternion()}
        scale_keys_solar_system = {1: 0.0001, 2: 0.0001}
        super().__init__(translate_keys_solar_system,
                         rotate_keys_solar_system,
                         scale_keys_solar_system)
        transform_base = PlaneteTransform('objet3D/Sun_v2_L3.123cbc92ee65-5f03-4298-b1e6-b236b6b8b4aa/13913_Sun_v2_l3.obj',
                  np.array([1, 1, 0]), 10,np.array([0, 0, 0]),
                                  2, np.array([0, 0.1, 0]), 10,
                                  'soleil',True)

        translate_keys_t_sun = {0: vec(0, 0, 00), 2: vec(0, 0, 00),
                                4: vec(0, 0, 00)}
        rotate_keys_t_sun = {0: quaternion(), 2: quaternion()}

        transform_terre = PlaneteTransform('objet3D/Earth_v1_L3.123cce489830-ca89-49f4-bb2a-c921cce7adb2/13902_Earth_v1_l3.obj',
                                   np.array([1,1,0]), 1,
                                   np.array([9500,0,0]),1,np.array([1,1,0]),36.5)




        transform_lune = PlaneteTransform('objet3D/Moon/Moon2K.obj',
                                   np.array([1,1,1]), 2,
                                   np.array([3500,0,0]),100,np.array([1,1,1]),5)
        transform_lune2 = PlaneteTransform('objet3D/Moon/Moon2K.obj',
                                   np.array([1,1,1]), 2,
                                   np.array([0,15000,0]),200,np.array([1,1,1]),60)
        transform_terre.add(transform_lune)

        fusee = ProjectileGuide('objet3D/rocket_v1_L2.123c433550fa-0038-410c-a891-3367406a58a6/12216_rocket_v1_l2.obj',
                        transform_terre.get_Planete(),
                        transform_lune2.get_Planete(),
                                vec(1,0,0),0,vec(-1,0,0),90,1,vec(0,2000,0))

        rot_fusee_vert = RotationControlNode(glfw.KEY_UP, glfw.KEY_DOWN, vec(1, 0, 0))
        rot_fusee_horiz = RotationControlNode(glfw.KEY_LEFT, glfw.KEY_RIGHT, vec(0, 1, 0))
        rot_fusee_vert.add(fusee)
        rot_fusee_horiz.add(rot_fusee_vert)



        scale_keys_t_sun2 = {0:1, 2:1}
        transform_base2 = KeyFrameControlNode(translate_keys_t_sun,
                                   rotate_keys_t_sun,
                                              scale_keys_t_sun2)
        transform_base.add(transform_terre)
        transform_base.add(transform_lune2)
        transform_base.add(rot_fusee_horiz)
        transform_base2.add(transform_base)
        transform_base2.add(rot_fusee_horiz)
        self.add(transform_base)
