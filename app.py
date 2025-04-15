import os
os.environ['MPLBACKEND'] = 'Agg'

from flask import Flask, render_template, request, send_file
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import csv
import numpy as np
from brian2 import *

app = Flask(__name__)

def run_simulation(threshold, reset, sim_time, input_current, noise, output_type, mode):
    defaultclock.dt = 0.1*ms
    duration = sim_time * ms
    N = 5

    eqs = '''
    dv/dt = (I - v) / (10*ms) : 1
    I : 1
    '''

    if noise:
        eqs = '''
        dv/dt = (I - v) / (10*ms) + 0.2*sqrt(1/ms)*xi : 1
        I : 1
        '''

    G = NeuronGroup(N, eqs, threshold='v>' + str(threshold),
                    reset='v=' + str(reset), method='euler')

    G.v = 0
    G.I = input_current

    M = StateMonitor(G, 'v', record=True)
    S = SpikeMonitor(G)

    run(duration)

    return G, M, S

def plot_graphs(M, S, output_type):
    fig, ax = plt.subplots(figsize=(10, 6))

    if output_type == 'voltage' or output_type == 'both':
        for i in range(len(M.v)):
            ax.plot(M.t/ms, M.v[i], label=f'Neuron {i}')
        ax.set_title("Membrane Potential Over Time")
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Membrane Potential (v)")
        ax.legend()

    if output_type == 'raster' or output_type == 'both':
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(S.t/ms, S.i, '.k')
        ax2.set_xlabel('Time (ms)')
        ax2.set_ylabel('Neuron index')
        ax2.set_title("Spike Raster Plot")
        fig2.tight_layout()
        buf2 = io.BytesIO()
        fig2.savefig('static/spike_raster.png')
        plt.close(fig2)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig('static/sim_result.png')
    plt.close(fig)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    threshold = float(request.form.get('threshold', 1.0))
    reset = float(request.form.get('reset', 0.0))
    sim_time = float(request.form.get('sim_time', 100.0))
    input_current = float(request.form.get('input_current', 1.2))
    noise = request.form.get('noise') == 'on'
    output_type = request.form.get('output_type', 'voltage')
    mode = request.form.get('mode', 'custom')

    G, M, S = run_simulation(threshold, reset, sim_time, input_current, noise, output_type, mode)
    plot_graphs(M, S, output_type)

    with open('static/sim_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time(ms)"] + [f"Neuron {i}" for i in range(len(M.v))])
        for j in range(len(M.t)):
            row = [M.t[j]/ms] + [M.v[i][j] for i in range(len(M.v))]
            writer.writerow(row)

    return render_template('index.html', 
                           img_url='/static/sim_result.png',
                           raster_url='/static/spike_raster.png' if output_type in ['raster', 'both'] else None,
                           data_url='/static/sim_data.csv',
                           threshold=threshold, reset=reset, sim_time=sim_time,
                           input_current=input_current, noise=noise,
                           output_type=output_type)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f'static/{filename}', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
