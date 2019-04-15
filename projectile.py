from keyframe import *
from transform import quaternion_from_axis_angle
from transform import get_scale_matrix1D
from transform import quaternion_mul
from mesh import load_textured
import numpy as np

class Projectile(KeyFrameControlNode):
    
    #Begin at position_init with a constant speed: vitesse
    #vrot is the axis of the rotation during time, with periode
    #period
    #vrot_init and angle_init are for the initial rotation
    def __init__(self, objet, position_init, vrot, periode,
                 vrot_init, angle_init, scale, vitesse):
        translate = {0: position_init, 1: position_init}
        scale2 = {0: scale, 1: scale}
        self.vitesse = vitesse;
        self.rot_init = quaternion_from_axis_angle(vrot_init,
                                                   angle_init)
        if(periode > 0):
            rotate_keys = {0: quaternion(), periode/4:
                           quaternion_from_axis_angle(vrot,90),
                           periode/2:
                           quaternion_from_axis_angle(vrot,180),
                           3*periode/4:
                           quaternion_from_axis_angle(vrot,270),
                           periode: quaternion()}
        if(periode == 0):
            rotate_keys = {0: self.rot_init, 1: self.rot_init}
        super().__init__(translate, rotate_keys, scale2)
        self.add(*load_textured(objet))
        
    #Update position with the speed
    def draw(self, projection, view, model, **param):
        taille = self.get_Taille_trans()
        if(glfw.get_time()> taille):
            self.add_value_trans(taille + 1,
                self.get_last_value_trans() + self.vitesse)
        super().draw(projection, view, model, **param)


class ProjectileGuide(Projectile):
    #begin at planete_depart and go to planete_arrive
    def __init__(self, objet, planete_depart, planete_arrive,
                 vrot, periode, vrot_init, angle_init,
                 scale, vitesse):
        if(not planete_depart.is_Planete() or
           not planete_depart.is_Planete()):
            print("planete_depart or planete_arrive is not a Planete in ProjectileGuide")
        self.depart = planete_depart
        self.destination = planete_arrive
        super().__init__(objet,vec(0,0,0), vrot, periode,
                         vrot_init,angle_init,scale, vitesse)

    def draw(self, projection, view, model, **param):
        if(np.linalg.norm(self.position)==0):

            time =glfw.get_time() +1
            self.add_value_trans(time,
                                 self.depart.get_position()/
                                 get_scale_matrix1D(model))
        self.update_speed()
        taille = self.get_Taille_rota()
        if(glfw.get_time()> taille):
            self.add_value_rota(taille + 1,
                self.compute_quaternion())
        super().draw(projection, view, model, **param)

    def update_speed(self):
        speed = self.vitesse
        self.vitesse = self.destination.get_position() - self.get_position() 
        norm_v = np.linalg.norm(self.vitesse)
        if(norm_v == 0):
            self.vitesse = speed
        self.vitesse = self.vitesse / np.linalg.norm(self.vitesse)
        self.vitesse = self.vitesse * np.linalg.norm(speed)

    def compute_quaternion(self):
        direct = self.destination.get_position() - self.get_position()
        if(np.linalg.norm(direct)==0):
            return self.rot_init
        v_rota = np.cross(vec(0,1,0), direct) 
        cos_angle = np.dot(vec(0,1,0),
                           direct)/np.linalg.norm(direct)
        angle = np.arccos(cos_angle)
        angle = angle * 180 / np.pi
        return quaternion_mul(quaternion_from_axis_angle(v_rota,
                                                         angle),
                              self.rot_init)

