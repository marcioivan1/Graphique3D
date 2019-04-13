from keyframe import *
from transform import quaternion_from_axis_angle
from transform import get_scale_matrix1D
from mesh import load_textured
import numpy as np

class Projectile(KeyFrameControlNode):

    def __init__(self, objet, position_init, rotate_keys,
                 scale, vitesse):
        translate = {0: position_init, 0.8: position_init}
        scale2 = {0: scale, 1: scale}
        self.vitesse = vitesse;
        super().__init__(translate, rotate_keys, scale2)
        self.add(*load_textured(objet))
        
    def draw(self, projection, view, model, **param):
        taille = self.get_Taille_trans()
        if(glfw.get_time()> taille):
            self.add_value_trans(taille + 1,
                self.get_last_value_trans() + self.vitesse)
        super().draw(projection, view, model, **param)


class ProjectileGuide(Projectile):

    def __init__(self, objet, planete_depart, planete_arrive,
                 vrot, periode, scale, vitesse):
        if(not planete_depart.is_Planete() or
           not planete_depart.is_Planete()):
            print("planete_depart or planete_arrive is not a Planete in ProjectileGuide")
        '''trajet = (planete_arrive.get_position()
            - planete_depart.get_position())
        if(np.linalg.norm(trajet ==0)):
            print(planete_depart.get_position())
        trajet = trajet / np.linalg.norm(trajet)
        position_init = (planete_depart.get_position()
            + planete_depart.get_rayon()*trajet)'''
        self.depart = planete_depart
        self.destination = planete_arrive
        rotate_keys = {0: quaternion(), periode/4:
                       quaternion_from_axis_angle(vrot,90),
                       periode/2:
                       quaternion_from_axis_angle(vrot,180),
                       3*periode/4:
                       quaternion_from_axis_angle(vrot,270),
                       periode: quaternion()}
        super().__init__(objet,vec(0,0,0), rotate_keys,
                         scale, vitesse)

    def draw(self, projection, view, model, **param):
        if(np.linalg.norm(self.position)==0):

            time =glfw.get_time() +1
            self.add_value_trans(time,
                                 self.depart.get_position()/
                                 get_scale_matrix1D(model))
            print(self.depart.get_position())
        self.update_speed()
        super().draw(projection, view, model, **param)

    def update_speed(self):
        speed = self.vitesse
        self.vitesse = self.destination.get_position() - self.get_position() 
        norm_v = np.linalg.norm(self.vitesse)
        if(norm_v == 0):
            self.vitesse = speed
        self.vitesse = self.vitesse / np.linalg.norm(self.vitesse)
        self.vitesse = self.vitesse * np.linalg.norm(speed)
