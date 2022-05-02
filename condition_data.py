import numpy as np

from dsp import estimate_fs, highpass
from scipy import signal


class ConditionData:
    """
    A convenience wrapper around data for a condition. All raw data is saved here.
    Moreover, relevant characteristics are computed on init and cached.
    """

    def __init__(self, elements):
        self.participant = elements[0]["participant"]
        self.milis = ConditionData.__extract(elements, "milis")
        self.seconds = [el / 1000 for el in self.milis]
        self.left_button = ConditionData.__extract(elements, "left_button")
        self.right_button = ConditionData.__extract(elements, "right_button")
        self.joystick = ConditionData.__extract(elements, "joystick")
        self.pulse = ConditionData.__extract(elements, "pulse")
        self.eda = ConditionData.__extract(elements, "eda")
        self.pressure = ConditionData.__extract(elements, "pressure")
        self.obstacle_hits_time = ConditionData.__extract(elements, "obstacle_hits_time")

        self.fs = estimate_fs(self.milis)

        self.pulse_filtered = ConditionData.__filter(self.pulse, self.fs, 0.5)
        self.pulse_peaks, self.pulse_peaks_heights = ConditionData.__compute_peaks(self.pulse_filtered, self.seconds, 0, 50)

    @staticmethod
    def __compute_peaks(data, timestamps, threshold=0, height=100):
        """
        Finds peaks in the data

        :param data: Filtered signal data without movement artifacts or noise
        :param timestamps: Timestamps for each signal sample
        :return: X and Y position of each peak
        """
        peaks, _ = signal.find_peaks(data, threshold=threshold, height=height)
        peaks_x = [timestamps[idx] for idx in peaks]
        peaks_y = [data[idx] for idx in peaks]

        return peaks_x, peaks_y

    @staticmethod
    def __filter(data, fs, high_cutoff):
        """
        Filters data with a high-pass filter to remove movement artifacts
        and a median filter to remove noise

        :param data: Raw signal to filter
        :param fs: Sampling frequency
        :param high_cutoff: Frequency cutoff for highpass filter
                            (this frequency will get damped at most 3dB)
                            At most half of the sampling frequency
        :return: Filtered signal without movement and noise artifacts
        """
        highpass_filtered = highpass(data, fs, high_cutoff, 3)
        median_filtered = signal.medfilt(highpass_filtered, 5)

        return median_filtered

    @staticmethod
    def __extract(samples, name):
        """
        Extracts a signal from samples

        :param samples: An object list where each element is one sample
        :param name: Name of the signal to extract
        :return: A single signal consisting of values gathered across the samples
        """
        # The data for the first 1323 samples is botched in the keyboard condition, so we scrap those
        return np.concatenate(np.array([el[name] for el in samples], dtype="object"))[1323:]
