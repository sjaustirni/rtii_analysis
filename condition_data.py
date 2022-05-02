import numpy as np

from dsp import estimate_fs

class ConditionData:
    def __init__(self, elements):
        self.participant = elements[0]["participant"]
        self.milis = ConditionData.extract(elements, "milis")
        self.seconds = [el/1000 for el in self.milis]
        self.left_button = ConditionData.extract(elements, "left_button")
        self.right_button = ConditionData.extract(elements, "right_button")
        self.joystick = ConditionData.extract(elements, "joystick")
        self.pulse = ConditionData.extract(elements, "pulse")
        self.eda = ConditionData.extract(elements, "eda")
        self.pressure = ConditionData.extract(elements, "pressure")
        self.obstacle_hits_time = ConditionData.extract(elements, "obstacle_hits_time")

        self.fs = estimate_fs(self.milis)

    @staticmethod
    def extract(elements, name):
        # The data for the first 1323 samples is botched in the keyboard condition, so we scrap those
        return np.concatenate(np.array([el[name] for el in elements], dtype="object"))[1323:]

