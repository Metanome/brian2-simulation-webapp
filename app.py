import os
os.environ['MPLBACKEND'] = 'Agg'

from flask import Flask, render_template, request, send_file, jsonify
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import csv
import json
import numpy as np
from brian2 import *

app = Flask(__name__)

def run_simulation(threshold, reset, sim_time, input_current, noise, noise_intensity, num_neurons, injection_start, injection_duration, output_type):
    defaultclock.dt = 0.1*ms
    duration = sim_time * ms
    N = num_neurons

    eqs = '''
    dv/dt = (I - v) / (10*ms) : 1
    I : 1
    '''

    if noise:
        eqs = '''
        dv/dt = (I - v) / (10*ms) + {}*sqrt(1/ms)*xi : 1
        I : 1
        '''.format(noise_intensity)

    G = NeuronGroup(N, eqs, threshold='v > {}'.format(threshold),
                    reset='v = {}'.format(reset), method='euler')
    G.v = 0

    I_vals = TimedArray(np.where((np.arange(int(sim_time/0.1)) * 0.1 >= injection_start) & 
                                 (np.arange(int(sim_time/0.1)) * 0.1 < injection_start + injection_duration),
                                 input_current, 0), dt=0.1*ms)
    G.run_regularly('I = I_vals(t)', dt=0.1*ms)

    M = StateMonitor(G, 'v', record=True)
    S = SpikeMonitor(G)

    run(duration)

    return G, M, S

def plot_graphs(M, S, output_type):
    if output_type in ['voltage', 'both']:
        fig, ax = plt.subplots(figsize=(10, 6))
        for i in range(len(M.v)):
            ax.plot(M.t/ms, M.v[i], label=f'Neuron {i}')
        ax.set_title("Membrane Potential Over Time")
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Membrane Potential (v)")
        ax.legend()
        fig.tight_layout()
        fig.savefig('static/sim_result.png')
        plt.close(fig)

    if output_type in ['raster', 'both']:
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(S.t/ms, S.i, '.k')
        ax2.set_xlabel('Time (ms)')
        ax2.set_ylabel('Neuron index')
        ax2.set_title("Spike Raster Plot")
        fig2.tight_layout()
        fig2.savefig('static/spike_raster.png')
        plt.close(fig2)

def export_data(M):
    csv_path = 'static/sim_data.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time(ms)"] + [f"Neuron {i}" for i in range(len(M.v))])
        for j in range(len(M.t)):
            row = [M.t[j]/ms] + [M.v[i][j] for i in range(len(M.v))]
            writer.writerow(row)

    json_path = 'static/sim_data.json'
    data = {
        "time_ms": [float(t/ms) for t in M.t],
        "voltages": {f"Neuron {i}": [float(v) for v in M.v[i]] for i in range(len(M.v))}
    }
    with open(json_path, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    threshold = float(request.form.get('threshold', 1.0))
    reset = float(request.form.get('reset', 0.0))
    sim_time = float(request.form.get('sim_time', 100.0))
    input_current = float(request.form.get('input_current', 1.2))
    noise = request.form.get('noise') == 'on'
    noise_intensity = float(request.form.get('noise_intensity', 0.2)) if noise else 0.0
    num_neurons = int(request.form.get('num_neurons', 5))
    injection_start = float(request.form.get('injection_start', 0.0))
    injection_duration = float(request.form.get('injection_duration', sim_time))
    output_type = request.form.get('output_type', 'voltage')

    G, M, S = run_simulation(threshold, reset, sim_time, input_current, noise, noise_intensity,
                             num_neurons, injection_start, injection_duration, output_type)
    
    plot_graphs(M, S, output_type)
    export_data(M)

    return render_template('index.html',
                           img_url='/static/sim_result.png' if output_type in ['voltage', 'both'] else None,
                           raster_url='/static/spike_raster.png' if output_type in ['raster', 'both'] else None,
                           csv_url='/download/sim_data.csv',
                           json_url='/download/sim_data.json',
                           threshold=threshold, reset=reset, sim_time=sim_time,
                           input_current=input_current, noise=noise,
                           noise_intensity=noise_intensity,
                           num_neurons=num_neurons,
                           injection_start=injection_start,
                           injection_duration=injection_duration,
                           output_type=output_type)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f'static/{filename}', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
