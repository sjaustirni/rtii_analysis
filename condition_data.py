import numpy as np

class ConditionData:
    def __init__(self, elements):
        self.participant = elements[0]["participant"]
        self.milis = ConditionData.extract(elements, "milis")
        self.left_button = ConditionData.extract(elements, "left_button")
        self.right_button = ConditionData.extract(elements, "right_button")
        self.joystick = ConditionData.extract(elements, "joystick")
        self.pulse = ConditionData.extract(elements, "pulse")
        self.eda = ConditionData.extract(elements, "eda")
        self.pressure = ConditionData.extract(elements, "pressure")
        self.obstacle_hits_time = ConditionData.extract(elements, "obstacle_hits_time")

    @staticmethod
    def extract(elements, name):
        return np.concatenate(np.array([el[name] for el in elements], dtype="object"))

