import os
import time
import uuid
os.environ['MPLBACKEND'] = 'Agg'

from flask import Flask, render_template, request, send_from_directory, flash
from brian2 import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

# Initialize Flask app and static folder for output files
app = Flask(__name__)
app.secret_key = 'd3c8e7f6b1a24e0c9f7a5b6c2e1d4f8a9b7c6e5d2f1a3b4c5d6e7f8a9b0c1d2e'  # Needed for flash messages
STATIC_FOLDER = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_FOLDER, exist_ok=True)

def validate_inputs(threshold, reset, sim_time, input_current, num_neurons, current_start, current_duration):
    """
    Check user inputs for validity and return a list of error messages if any.
    """
    errors = []
    if num_neurons < 1 or num_neurons > 100:
        errors.append("Number of neurons must be between 1 and 100.")
    if sim_time <= 0 or sim_time > 10000:
        errors.append("Simulation time must be positive and less than 10000 ms.")
    if current_start < 0 or current_duration < 0:
        errors.append("Current start and duration must be non-negative.")
    if current_start > sim_time:
        errors.append("Current start cannot be after simulation end.")
    if current_start + current_duration > sim_time:
        errors.append("Current injection interval exceeds simulation time.")
    if threshold <= reset:
        errors.append("Threshold should be greater than reset value.")
    return errors

def cleanup_static_folder(max_age_seconds=600):
    """
    Remove files older than max_age_seconds from the static folder to save disk space.
    """
    now = time.time()
    for fname in os.listdir(STATIC_FOLDER):
        fpath = os.path.join(STATIC_FOLDER, fname)
        if os.path.isfile(fpath):
            if now - os.path.getmtime(fpath) > max_age_seconds:
                try:
                    os.remove(fpath)
                except Exception:
                    pass

@app.route('/', methods=['GET'])
def index():
    """
    Render the main simulation form page.
    """
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    """
    Handle simulation requests: validate input, run Brian2 simulation, generate plots and data files.
    """
    cleanup_static_folder()
    # === Get form inputs with defaults ===
    try:
        threshold = float(request.form.get('threshold', 1.0))
        reset = float(request.form.get('reset', 0.0))
        sim_time = float(request.form.get('sim_time', 100))
        input_current = float(request.form.get('input_current', 1.2))
        num_neurons = int(request.form.get('num_neurons', 5))
        current_start = float(request.form.get('current_start', 0))
        current_duration = float(request.form.get('current_duration', sim_time))
        noise_enabled = 'noise' in request.form
        noise_intensity = float(request.form.get('noise_intensity', 0.2))
        noise_method = request.form.get('noise_method', 'additive')
        synapse_enabled = 'synapse' in request.form
        syn_weight = float(request.form.get('syn_weight', 0.2))
        syn_prob = float(request.form.get('syn_prob', 0.2))
        output_type = request.form.get('output_type', 'both')
    except Exception as e:
        flash(f"Invalid input: {e}")
        return render_template('index.html')

    # === Validate inputs ===
    errors = validate_inputs(threshold, reset, sim_time, input_current, num_neurons, current_start, current_duration)
    if errors:
        for err in errors:
            flash(err)
        return render_template('index.html',
                               threshold=threshold, reset=reset, sim_time=sim_time,
                               input_current=input_current, num_neurons=num_neurons,
                               current_start=current_start, current_duration=current_duration,
                               noise=noise_enabled, noise_intensity=noise_intensity, noise_method=noise_method,
                               synapse=synapse_enabled, syn_weight=syn_weight, syn_prob=syn_prob,
                               output_type=output_type)

    # === Unique filenames for this simulation ===
    unique_id = str(uuid.uuid4())
    img_filename = f'membrane_plot_{unique_id}.png'
    raster_filename = f'raster_plot_{unique_id}.png'
    csv_filename = f'sim_data_{unique_id}.csv'
    json_filename = f'sim_data_{unique_id}.json'
    
    sim_time_seconds = None  # For performance monitoring

    # === Start Brian2 Simulation ===
    try:
        start_time = time.time()
        start_scope()
        # Define neuron model equations
        eqs = '''
        dv/dt = (I - v) / (10*ms) : 1
        I : 1
        '''
        # Create neuron group
        G = NeuronGroup(num_neurons, eqs, threshold='v > {}'.format(threshold), reset='v = {}'.format(reset), method='euler')
        G.v = 0
        G.I = 0

        # Time array for current injection
        dt = float(defaultclock.dt/ms)
        time_array = np.arange(0, sim_time, dt)
        I_array = np.zeros((num_neurons, len(time_array)))

        # Set current for selected interval, safely
        start_idx = max(0, int(current_start / dt))
        end_idx = min(len(time_array), int((current_start + current_duration) / dt))
        if end_idx > start_idx:
            # Break input symmetry: each neuron gets a slightly different current
            for n in range(num_neurons):
                I_array[n, start_idx:end_idx] = input_current + 0.05 * n

        # Add noise if selected
        if noise_enabled:
            noise = noise_intensity * np.random.randn(num_neurons, len(time_array))
            if noise_method == 'additive':
                I_array += noise
            elif noise_method == 'multiplicative':
                I_array *= (1 + noise)

        # Create a TimedArray for time-varying input
        I_timed = TimedArray(I_array.T, dt=defaultclock.dt)
        G.run_regularly('I = I_timed(t, i)', dt=defaultclock.dt)

        # Add synapses if enabled
        if synapse_enabled and num_neurons > 1:
            # Add synaptic delay for realism and visible effect
            S = Synapses(G, G, on_pre='v_post += {}'.format(syn_weight), delay=1*ms)
            S.connect(p=syn_prob)

        # Set up monitors to record data
        M = StateMonitor(G, 'v', record=True)
        spike_mon = SpikeMonitor(G)
        run(sim_time * ms)
        sim_time_seconds = time.time() - start_time
    except Exception as e:
        flash(f"Simulation error: {e}")
        return render_template('index.html')

    # === Prepare plot and data file URLs ===
    img_url = None
    raster_url = None
    data_url = None
    json_url = None

    # Plot membrane potentials
    if output_type in ['voltage', 'both']:
        plt.figure(figsize=(10, 4))
        for i in range(num_neurons):
            plt.plot(M.t/ms, M.v[i], label=f'Neuron {i}')
        plt.xlabel('Time (ms)')
        plt.ylabel('Membrane potential (v)')
        plt.title('Membrane Potential Over Time')
        plt.legend()
        plt.tight_layout()
        img_path = os.path.join(STATIC_FOLDER, img_filename)
        plt.savefig(img_path)
        img_url = f'/static/{img_filename}'
        plt.close()

    # Plot spike raster
    if output_type in ['raster', 'both']:
        plt.figure(figsize=(10, 4))
        plt.plot(spike_mon.t/ms, spike_mon.i, '.k')
        plt.xlabel('Time (ms)')
        plt.ylabel('Neuron index')
        plt.title('Spike Raster Plot')
        plt.tight_layout()
        raster_path = os.path.join(STATIC_FOLDER, raster_filename)
        plt.savefig(raster_path)
        raster_url = f'/static/{raster_filename}'
        plt.close()

    # CSV Export: Save membrane potential traces
    df = pd.DataFrame({f"Neuron_{i}": M.v[i] for i in range(num_neurons)})
    df.insert(0, "Time(ms)", M.t/ms)
    csv_path = os.path.join(STATIC_FOLDER, csv_filename)
    df.to_csv(csv_path, index=False)
    data_url = f'/static/{csv_filename}'

    # JSON Export: Save data in JSON format
    json_data = {
        'time_ms': (M.t/ms).tolist(),
        'neurons': {f'Neuron_{i}': M.v[i].tolist() for i in range(num_neurons)}
    }
    json_path = os.path.join(STATIC_FOLDER, json_filename)
    with open(json_path, 'w') as jf:
        json.dump(json_data, jf)
    json_url = f'/static/{json_filename}'

    # Render the results page with plots and download links
    return render_template('index.html',
                           threshold=threshold, reset=reset, sim_time=sim_time,
                           input_current=input_current, num_neurons=num_neurons,
                           current_start=current_start, current_duration=current_duration,
                           noise=noise_enabled, noise_intensity=noise_intensity, noise_method=noise_method,
                           synapse=synapse_enabled, syn_weight=syn_weight, syn_prob=syn_prob,
                           output_type=output_type,
                           img_url=img_url, raster_url=raster_url,
                           data_url=data_url, json_url=json_url,
                           sim_time_seconds=sim_time_seconds)

@app.route('/static/<path:path>')
def static_file(path):
    """
    Serve static files (plots, data) from the static folder.
    """
    return send_from_directory(STATIC_FOLDER, path)

if __name__ == '__main__':
    # Start the Flask development server
    app.run(debug=True)
