import json
import numpy as np

from condition_data import ConditionData
from supabase_utils import download_data_for
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# CONFIG
cache_file = '.cache/pokus.json'
current_user = ["pokus", "pokus2"]

# The signals are usually botched in the very beginning due to
# strong movement artifacts, amplified by running all kinds of
# filters, that don't do too well on the edges.
botched_data_skip = 25


def get_length_removed_sparse_elements(sparse_timestamps, seconds_to_remove):
    clean_sparse_timestamps = [el for el in sparse_timestamps if el > (sparse_timestamps[0] + seconds_to_remove)]
    return len(sparse_timestamps) - len(clean_sparse_timestamps)


def quick_summary(condition: ConditionData, title: str):
    mean_ibi = np.mean(condition.ibi[10:])

    print(title)
    print('Mean IBI: {:.0f}ms'.format(mean_ibi*1000))
    print('RMSSD: {:.1f}ms'.format(condition.rmssd_total))
    print('pNN50: {:.1f}ms'.format(condition.pnni_50_total))
    print()

def quick_plot(condition: ConditionData, title: str):
    stack_plots(title, condition.seconds, condition.pulse_peaks,
                [
                    (condition.eda_filtered, "EDA filtered", "blue", True),
                ],
                [
                    (condition.heart_rate, "Heart Rate", "red", True),
                    (condition.rmssd, "RMSSD", "orange", True)

                ],
                (condition.obstacle_hits_time, "Obstacle hits")
                )


def add_events_trace(fig, sig, event_data, row, col):
    for event in event_data:
        fig.add_trace(go.Scatter(x=[event, event],
                                 y=[0, np.max(sig)],
                                 mode='lines',
                                 line=dict(color='gray', width=2, dash='dash'),
                                 name="obstacle hit",
                                 showlegend=False
                                 ),
                      row=row,
                      col=col
                      )

    fig.add_trace(go.Scatter(x=[event_data], y=[0] * len(event_data), mode='markers', showlegend=False),
                  row=row,
                  col=col)


def plot_pulse(condition: ConditionData):
    fig = go.Figure(go.Scatter(x=condition.seconds, y=condition.pulse_filtered))
    fig.add_trace(go.Scatter(x=condition.pulse_peaks, y=condition.pulse_peaks_heights))
    fig.show()


def stack_plots(title, timestamps, sparse_timestamps, signals, sparse_signals, events):
    sparse_botched_data_skip = get_length_removed_sparse_elements(sparse_timestamps, 20)

    (event_data, event_name) = events
    fig = make_subplots(rows=len(sparse_signals) + len(signals), cols=1, shared_xaxes=True, y_title=title)

    for idx, (sig, name, color, show_events) in enumerate(sparse_signals):
        fig.add_trace(
            go.Scatter(x=sparse_timestamps[sparse_botched_data_skip:], y=sig[sparse_botched_data_skip:], line=dict(color=color), name=name),
            row=idx + 1,
            col=1
        )

        if show_events:
            add_events_trace(fig, sig, event_data, idx + 1, 1)

    for idx, (sig, name, color, show_events) in enumerate(signals):
        row = len(sparse_signals) + idx + 1
        fig.add_trace(
            go.Scatter(x=timestamps[botched_data_skip*10:], y=sig[botched_data_skip*10:], line=dict(color=color), name=name),
            row=row,
            col=1
        )

        if show_events:
            add_events_trace(fig, sig, event_data, row, 1)
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

    quick_plot(keyboard, "Keyboard")
    quick_summary(keyboard, "Keyboard")
    quick_plot(joystick, "Joystick")
    quick_summary(joystick, "Joystick")

