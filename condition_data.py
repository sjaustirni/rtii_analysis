import hrvanalysis as hrv
import numpy as np

from dsp import estimate_fs, highpass, compute_differences
from scipy import signal
from scipy.ndimage.filters import uniform_filter1d
import pandas as pd


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
        # Sometimes the data from the database comes in unsorted for some reason
        elements.sort(key=lambda el: el["id"])
        self.participant = elements[0]["participant"]
        self.milis = ConditionData.__extract(elements, "milis")
        self.seconds = [el / 1000 for el in self.milis]
        self.left_button = ConditionData.__extract(elements, "left_button")
        self.right_button = ConditionData.__extract(elements, "right_button")
        self.joystick = ConditionData.__extract(elements, "joystick")
        self.pulse = ConditionData.__extract(elements, "pulse")
        self.eda = ConditionData.__extract(elements, "eda")
        self.pressure = ConditionData.__extract(elements, "pressure")
        self.obstacle_hits_time = [el / 1000 for el in
                                   ConditionData.__extract(elements, "obstacle_hits_time")]

        self.fs = estimate_fs(self.milis)

        self.pulse_filtered = ConditionData.__filter(self.pulse, self.fs, high_cutoff=0.07)
        self.pulse_peaks, self.pulse_peaks_heights = ConditionData.__compute_peaks(self.pulse_filtered, self.seconds, 0,
                                                                                   20)
        self.ibi = ConditionData.__compute_ibi(self.pulse_peaks)
        self.heart_rate = [round(60 / max(0.00001, el)) for el in self.ibi]

        self.eda_filtered = ConditionData.__filter(ConditionData.__remove_eda_artifacts(self.eda), self.fs,
                                                   moving_avg_kernel=8, median_kernel=None)
        self.pressure_filtered = ConditionData.__compute_pressure(
            ConditionData.__filter(self.pressure, self.fs, moving_avg_kernel=5))

        self.rmssd = ConditionData.__compute_time_hrv(self.ibi, 'rmssd').transpose().values.tolist()[0]
        self.rmssd_total = ConditionData.__compute_time_hrv(self.ibi, 'rmssd', None)

        self.pnni_50_total = ConditionData.__compute_time_hrv(self.ibi, 'pnni_50', None)


    @staticmethod
    def __compute_time_hrv(ibi, name, window_size=20):
        if window_size is None:
            return hrv.get_time_domain_features([el * 1000 for el in ibi[10:]])[name]

        ibi_frame = pd.DataFrame(data=[np.nan]*10+ibi[10:])
        return ibi_frame.rolling(window=window_size, min_periods=int(window_size/2)).apply(func=lambda window: hrv.get_time_domain_features(window)[name])


    @staticmethod
    def __compute_pressure(pressure_filtered):
        return [0 if el > 0.2 else 1 for el in pressure_filtered]

    @staticmethod
    def __compute_ibi(pulse_peaks):
        ibi = compute_differences(pulse_peaks)
        ibi_without_outliers = ConditionData.__remove_ibi_artifacts(ibi, min_value=60 / 80)

        return ibi_without_outliers

    @staticmethod
    def __remove_artifacts(readings, max_value=60 / 50, min_value=60 / 100, median_window_length=None):
        """
        Applies median filter at outliers. This effectively removes artifacts from the signal.
        We are median filtering instead of just removing the outliers in order to keep the length of the signal.
        This method is naive, but it works well if max_value and min_value are properly set.

        :param readings: List of readings
        :param max_value:   Maximum value of any expected true reading. Readings greater than that are outliers.
        :param min_value:   Minimum value of any expected true IBI reading. Readings lower than that are outliers.
        :param median_window_length:    How big the rolling window should be. Must be an odd number.
                                        Choose something relatively small. If this window gets too big, you are no
                                        longer removing noise
        :return: Signal without artifacts
        """

        # We need to pad the signal to be able to median filter at and near the edges
        padding = int(median_window_length / 2)
        padded_readings = np.concatenate(([readings[0]] * padding, readings, [readings[len(readings) - 1]] * padding))

        return [median_filter_if_outlier(padded_readings[idx - padding:idx + padding + 1], min_value, max_value)
                for idx in range(padding, len(padded_readings) - padding)]

    @staticmethod
    def __remove_ibi_artifacts(ibi_signal, max_value=60 / 50, min_value=60 / 100, median_window_length=7):
        return ConditionData.__remove_artifacts(ibi_signal, max_value, min_value, median_window_length)

    @staticmethod
    def __remove_eda_artifacts(eda_signal, max_value=350, min_value=200, median_window_length=51):
        return ConditionData.__remove_artifacts(eda_signal, max_value, min_value, median_window_length)

    @staticmethod
    def __compute_peaks(data, timestamps, threshold=0, height=50):
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
    def __filter(data, fs, high_cutoff=None, moving_avg_kernel=None, median_kernel=5):
        """
        Filters data with a high-pass filter to remove movement artifacts
        and a median filter to remove noise.
        Optionally, a low pass filter is applied too, if the `low_cuttoff` is provided

        :param data: Raw signal to filter
        :param fs: Sampling frequency
        :param high_cutoff: Frequency cutoff for highpass filter. Used to remove motion artifacts.
                            At most half of the sampling frequency. If None, no highpass filter is applied.
        :param moving_avg_kernel:   Size of the kernel to smooth data with. Used as a last-resort low-pass filter for
                                    removing high frequency artifacts in signals with low sampling frequency. The bigger
                                    the kernel, the more smooth the resulted will be.
                                    If None, no moving average filter is applied.
        :param median_kernel:   Size of the kernel to remove outliers. The bigger the kernel to longer-lasting outliers
                                can be removed. If None, no median kernel is applied.
        :return: Filtered signal without movement and noise artifacts
        """

        result = np.array(data).astype(np.float)

        if high_cutoff:
            result = highpass(data, fs, high_cutoff, 3)

        if median_kernel:
            result = signal.medfilt(result, median_kernel)

        if moving_avg_kernel:
            result = uniform_filter1d(result, size=moving_avg_kernel)

        return result

    @staticmethod
    def __extract(samples, name):
        """
        Extracts a signal from samples

        :param samples: An object list where each element is one sample
        :param name: Name of the signal to extract
        :param sparse_data: Whether the data to be extracted is sparse
        :return: A single signal consisting of values gathered across the samples
        """

        data = np.concatenate(np.array([el[name] for el in samples], dtype="object"))

        return data
