import numpy as np
from scipy import signal


def compute_differences(number_list):
    """
    :param number_list:
    :return: A list of differences between each pair of consecutive elements of the original list
    """
    return [t - s for s, t in zip(number_list, number_list[1:])]


def estimate_fs(milis):
    differences = compute_differences(milis)
    return int(np.median(differences))


def highpass(data, fs, cutoff, order=2):
    sos = signal.butter(order, cutoff, 'hp', fs=fs, output='sos')
    return signal.sosfilt(sos, data)

