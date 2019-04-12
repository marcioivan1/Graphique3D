from transform import translate, rotate, scale, lerp, vec, lerpCircle
from transform import (quaternion_slerp, quaternion_matrix, quaternion,
                       quaternion_from_euler)
from node import Node
import glfw
from bisect import bisect_left


class KeyFrames:
    """ Stores keyframe pairs for any value type with interpolation_function"""
    def __init__(self, time_value_pairs, interpolation_function=lerp):
        if isinstance(time_value_pairs, dict):  # convert to list of pairs
            time_value_pairs = time_value_pairs.items()
        keyframes = sorted(((key[0], key[1]) for key in time_value_pairs))
        self.times, self.values = zip(*keyframes)  # pairs list -> 2 lists
        self.interpolate = interpolation_function

    def value(self, time):
        """ Computes interpolated value from keyframes, for a given time """

        # 1. ensure time is within bounds else return boundary keyframe
        if time < self.times[0] or time > self.times[len(self.times)-1]:
            print("Mauvaise utilisation interpolation")
            exit(0)

        # 2. search for closest index entry in self.times, using bisect_left function
        position = bisect_left(self.times, time)
        # 3. using the retrieved index, interpolate between the two neighboring values
        # in self.values, using the initially stored self.interpolate function
        fraction = (time - self.times[position - 1])/(self.times[position] - self.times[position-1])
        return self.interpolate(self.values[position -1], self.values[position], fraction)

    def valueCycle(self, time):
        """ Computes interpolated value from keyframes, for a given time """

        # 1. ensure time is within bounds else return boundary keyframe
        taille = self.times[len(self.times)-1]
        time2 = time % taille
        # 2. search for closest index entry in self.times, using bisect_left function
        position = bisect_left(self.times, time2)
        # 3. using the retrieved index, interpolate between the two neighboring values
        # in self.values, using the initially stored self.interpolate function
        fraction = (time2 - self.times[position - 1])/(self.times[position] - self.times[position-1])
        return self.interpolate(self.values[position -1], self.values[position], fraction)

    def add_value(self, time, value):
        self.times = self.times + (time,)
        self.values = self.values + (value,)

    def get_Taille_time(self):
        return self.times[len(self.times)-1]

    def get_last_value(self):
        return self.values[len(self.values)-1]


class TransformKeyFrames:
    """ KeyFrames-like object dedicated to 3D transforms """
    def __init__(self, translate_keys, rotate_keys, scale_keys, interpolation_translate=lerp):
        """ stores 3 keyframe sets for translation, rotation, scale """
        self.translation = KeyFrames(translate_keys, interpolation_translate)
        self.rotation = KeyFrames(rotate_keys, quaternion_slerp)
        self.scale = KeyFrames(scale_keys)

    def value(self, time):
        """ Compute each component's interpolation and compose TRS matrix """
        result_translation = translate(self.translation.value(time))
        result_rotation = quaternion_matrix(self.rotation.value(time))
        result_scale = scale(self.scale.value(time))

        return result_translation @ result_rotation @ result_scale

    def valueCycle(self, time):
        """ Compute each component's interpolation and compose TRS matrix """
        result_translation = translate(self.translation.valueCycle(time))
        result_rotation = quaternion_matrix(self.rotation.valueCycle(time))
        result_scale = scale(self.scale.valueCycle(time))

        return result_translation @ result_rotation @ result_scale

    def get_Taille_rota(self):
        return self.rotation.get_Taille_time()

    def get_Taille_trans(self):
        return self.translation.get_Taille_time()

    def get_Taille_scale(self):
        return self.scale.get_Taille_time()

    def add_value_rota(self, value, time):
        self.rotation.add_value(value,time)

    def add_value_trans(self, value, time):
        self.translation.add_value(value,time)

    def add_value_scale(self, value, time):
        self.scale.add_value(value,time)

    def get_last_value_trans(self):
        return self.translation.get_last_value()

class KeyFrameControlNode(Node):
    """ Place node with transform keys above a controlled subtree """
    def __init__(self, translate_keys, rotate_keys, scale_keys, interpolate_translate = lerp, **kwargs):
        super().__init__(**kwargs)
        self.keyframes = TransformKeyFrames(translate_keys,
                                            rotate_keys,
                                            scale_keys,
                                            interpolate_translate)

    def draw(self, projection, view, model, **param):
        """ When redraw requested, interpolate our node transform from keys """
        self.transform = self.keyframes.valueCycle(glfw.get_time())
        super().draw(projection, view, model, **param)

    def get_Taille_rota(self):
        return self.keyframes.get_Taille_rota()

    def get_Taille_trans(self):
        return self.keyframes.get_Taille_trans()

    def get_Taille_scale(self):
        return self.keyframes.get_Taille_scale()

    def add_value_rota(self, value, time):
        self.keyframes.add_value_rota(value,time)

    def add_value_trans(self, value, time):
        self.keyframes.add_value_trans(value,time)

    def add_value_scale(self, value, time):
        self.keyframes.add_value_scale(value,time)

    def get_last_value_trans(self):
        return self.keyframes.get_last_value_trans()
