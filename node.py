from transform import Trackball, identity, translate, rotate
from transform import scale, lerp, vec

class Node:
    """ Scene graph transform and parameter broadcast node """
    def __init__(self, name='', children=(), transform=identity(), **param):
        self.transform, self.param, self.name = transform, param, name
        self.children = list(iter(children))
        pos = self.transform[:4,:4]@vec(0,0,0,1)
        self.position = pos[:3]

    def add(self, *drawables):
        """ Add drawables to this node, simply updating children list """
        self.children.extend(drawables)

    def draw(self, projection, view, model, **param):
        """ Recursive draw, passing down named parameters & model matrix. """
        # merge named parameters given at initialization with those given here
        param = dict(param, **self.param)
        model2 = model @ self.transform 
        pos = model2@vec(0,0,0,1)
        self.position = pos[:3]
        for child in self.children:
            child.draw(projection, view, model2, **param)

    def is_Planete(self):
        return False

    def get_position(self):
        return self.position


