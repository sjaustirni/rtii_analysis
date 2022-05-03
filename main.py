import json

from condition_data import ConditionData
from supabase_utils import download_data_for
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# CONFIG
cache_file = '.cache/sjau.json'
current_user = ["sjau-desktop", "sjau-desktop2"]


def plot_hr_ibi(timestamps, hr, ibi):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True)

    fig.add_trace(
        go.Scatter(x=timestamps, y=hr, name="HR", ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(x=timestamps, y=ibi, name="IBI"),
        row=2,
        col=1
    )

    fig.show()


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

    plot_hr_ibi(keyboard.seconds, keyboard.heart_rate, keyboard.ibi)