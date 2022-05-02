import json

from condition_data import ConditionData
from dsp import highpass
from supabase_utils import download_data_for
import plotly.graph_objects as go
from scipy import signal

# CONFIG
cache_file = '.cache/sjau.json'
current_user = ["sjau-desktop", "sjau-desktop2"]

data = None
if __name__ == "__main__":
    try:
        with open(cache_file, 'r') as f:
            print("Found cached data, loading them")
            data = json.load(f)
    except FileNotFoundError:
        print("No cache found, downloading")
        usernames_sql = "(" + ",".join(["\"{}\"".format(el) for el in current_user]) + ")"
        with open(cache_file, 'w') as f:
            data = download_data_for(usernames_sql).data
            json.dump(data, f)

    keyboard_elements = [el for el in data if el["condition"] == "keyboard"]
    joystick_elements = [el for el in data if el["condition"] == "joystick"]

    keyboard = ConditionData(keyboard_elements)
    joystick = ConditionData(joystick_elements)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=keyboard.seconds, y=keyboard.pulse_filtered, mode='lines', name='raw'))
    fig.add_trace(go.Scatter(x=keyboard.pulse_peaks, y=keyboard.pulse_peaks_heights, mode='markers', name='IBI'))

    fig.update_layout(
        title='Pulse'
    )

    fig.show()
