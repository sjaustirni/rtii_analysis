import numpy as np

from dsp import estimate_fs, highpass, compute_differences
from scipy import signal


def median_filter_if_outlier(window, min_value, max_value):
    """
    :param window: Window with the value in question in the middle
    :param min_value: Lower range of accepted values
    :param max_value: Upper range of accepted values
    :return: The middle window value if it is in the range of accepted values. Otherwise median value of the window
    """
    middle_index = int(len(window) / 2 + 1)
    current = window[middle_index]

    if current < min_value or current > max_value:
        return signal.medfilt(window, len(window))[middle_index]

    return current


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
        self.pulse_peaks, self.pulse_peaks_heights = ConditionData.__compute_peaks(self.pulse_filtered, self.seconds, 0,
                                                                                   50)
        self.ibi = ConditionData.__compute_ibi(self.pulse_peaks)
        self.heart_rate = [round(60 / el) for el in self.ibi]

    @staticmethod
    def __compute_ibi(pulse_peaks):
        ibi = compute_differences(pulse_peaks)
        ibi_without_outliers = ConditionData.__remove_ibi_artifacts(ibi, min_value=60 / 80)

        return ibi_without_outliers

    @staticmethod
    def __remove_ibi_artifacts(ibi_signal, max_value=60 / 50, min_value=60 / 100, median_window_length=7):
        """
        Applies median filter at outliers. This effectively removes artifacts from the IBI signal.
        We are median filtering instead of just removing the outliers in order to keep the length of the IBI signal.
        This method is naive, but it works well if max_value and min_value are properly set.

        :param ibi_signal: List of IBI readings
        :param max_value:   Maximum value of any expected true IBI reading. Readings greater than that are outliers.
                            Default is 60/50, that is IBI at 50bpm
        :param min_value:   Minimum value of any expected true IBI reading. Readings lower than that are outliers.
                            Default value is 60/100, that is IBI at 100bpm. This is suitable for most sitting tasks.
        :param median_window_length:    How big the rolling window should be. Must be an odd number.
                                        Choose something relatively small. If this window gets too big, you are no
                                        longer removing noise
            Default value is 60/100, that is IBI at 100bpm. This is suitable for most sitting tasks.
        :return: IBI signal without artifacts
        """

        # We need to pad the signal to be able to median filter at and near the edges
        padding = int(median_window_length / 2)
        padded_ibi = [ibi_signal[0]] * padding + ibi_signal + [ibi_signal[len(ibi_signal) - 1]] * padding

        return [median_filter_if_outlier(padded_ibi[idx - padding:idx + padding + 1], min_value, max_value)
                for idx in range(padding, len(padded_ibi) - padding)]

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
