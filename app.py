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
import plotly.graph_objs as go
import plotly.io as pio

# Initialize Flask app and static folder for output files
app = Flask(__name__)
app.secret_key = 'd3c8e7f6b1a24e0c9f7a5b6c2e1d4f8a9b7c6e5d2f1a3b4c5d6e7f8a9b0c1d2e'  # Needed for flash messages
OUTPUT_FOLDER = os.path.join(app.root_path, 'output')
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def cleanup_output_folder(output_folder, max_age_seconds=600):
    """
    Remove files older than max_age_seconds from the output folder to save disk space.
    """
    now = time.time()
    for fname in os.listdir(output_folder):
        fpath = os.path.join(output_folder, fname)
        if os.path.isfile(fpath):
            if now - os.path.getmtime(fpath) > max_age_seconds:
                try:
                    os.remove(fpath)
                except Exception:
                    pass

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
    cleanup_output_folder(OUTPUT_FOLDER)
    # === Get form inputs with defaults ===
    try:
        neuron_model = request.form.get('neuron_model', 'lif')
        # Model-specific params
        izh_a = float(request.form.get('izh_a', 0.02))
        izh_b = float(request.form.get('izh_b', 0.2))
        izh_c = float(request.form.get('izh_c', -65))
        izh_d = float(request.form.get('izh_d', 2))
        adex_a = float(request.form.get('adex_a', 0.02))
        adex_b = float(request.form.get('adex_b', 0.2))
        adex_deltaT = float(request.form.get('adex_deltaT', 2))
        adex_tau_w = float(request.form.get('adex_tau_w', 30))
        custom_eqs = request.form.get('custom_eqs', '')
        custom_threshold = request.form.get('custom_threshold', '')
        custom_reset = request.form.get('custom_reset', '')

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
        plot_type = request.form.get('plot_type', 'interactive')
    except Exception as e:
        flash(f"Invalid input: {e}")
        return render_template('index.html')

    # === Validate inputs ===
    errors = validate_inputs(threshold, reset, sim_time, input_current, num_neurons, current_start, current_duration)
    # Model-specific validation
    if neuron_model == 'custom':
        if not custom_eqs.strip() or not custom_threshold.strip() or not custom_reset.strip():
            errors.append("Custom model: equations, threshold, and reset are required.")
    if errors:
        for err in errors:
            flash(err)
        return render_template('index.html',
                               threshold=threshold, reset=reset, sim_time=sim_time,
                               input_current=input_current, num_neurons=num_neurons,
                               current_start=current_start, current_duration=current_duration,
                               noise=noise_enabled, noise_intensity=noise_intensity, noise_method=noise_method,
                               synapse=synapse_enabled, syn_weight=syn_weight, syn_prob=syn_prob,
                               output_type=output_type, plot_type=plot_type,
                               neuron_model=request.form.get('neuron_model'),
                               izh_a=request.form.get('izh_a', type=float),
                               izh_b=request.form.get('izh_b', type=float),
                               izh_c=request.form.get('izh_c', type=float),
                               izh_d=request.form.get('izh_d', type=float),
                               adex_a=request.form.get('adex_a', type=float),
                               adex_b=request.form.get('adex_b', type=float),
                               adex_deltaT=request.form.get('adex_deltaT', type=float),
                               adex_tau_w=request.form.get('adex_tau_w', type=float),
                               custom_eqs=custom_eqs,
                               custom_threshold=custom_threshold,
                               custom_reset=custom_reset)

    # === Unique filenames for this simulation ===
    unique_id = str(uuid.uuid4())
    img_filename = f'membrane_plot_{unique_id}.png'
    raster_filename = f'raster_plot_{unique_id}.png'
    csv_filename = f'sim_data_{unique_id}.csv'
    json_filename = f'sim_data_{unique_id}.json'
    
    sim_time_seconds = None  # For performance monitoring
    plotly_voltage_html = None
    plotly_raster_html = None

    # === Start Brian2 Simulation ===
    try:
        start_time = time.time()
        start_scope()
        # --- Model selection ---
        if neuron_model == 'lif':
            eqs = '''
            dv/dt = (I - v) / (10*ms) : 1
            I : 1
            '''
            threshold_expr = f'v > {threshold}'
            reset_expr = f'v = {reset}'
        elif neuron_model == 'izhikevich':
            eqs = '''
            dv/dt = (0.04*v**2 + 5*v + 140 - u + I)/ms : 1
            du/dt = {a}*( {b}*v - u )/ms : 1
            I : 1
            '''.format(a=izh_a, b=izh_b)
            threshold_expr = 'v >= 30'
            reset_expr = f'v = {izh_c}; u += {izh_d}'
        elif neuron_model == 'adex':
            eqs = '''
            dv/dt = ( -gL*(v-EL) + gL*deltaT*exp((v-VT)/deltaT) - w + I ) / C : volt
            dw/dt = ( a*(v-EL) - w ) / tau_w : amp
            I : amp
            gL : siemens
            EL : volt
            deltaT : volt
            VT : volt
            a : siemens
            tau_w : second
            C : farad
            '''
            threshold_expr = 'v > VT'
            reset_expr = f'v = EL; w += {adex_b}*pA'
            G = NeuronGroup(num_neurons, eqs, threshold=threshold_expr, reset=reset_expr, method='euler')
            G.v = -65*mV
            G.w = 0*pA
            G.I = input_current * pA
            G.gL = 10*nS
            G.EL = -65*mV
            G.deltaT = adex_deltaT * mV
            G.VT = -50*mV
            G.a = adex_a * nS
            G.tau_w = adex_tau_w * ms
            G.C = 200*pF
        elif neuron_model == 'custom':
            eqs = custom_eqs
            threshold_expr = custom_threshold
            reset_expr = custom_reset
        else:
            flash("Unknown neuron model selected.")
            return render_template('index.html')

        # --- Create neuron group ---
        if neuron_model != 'adex':
            G = NeuronGroup(num_neurons, eqs, threshold=threshold_expr, reset=reset_expr, method='euler')
            if 'v' in G.namespace:
                G.v = 0
            if 'u' in G.namespace:
                G.u = 0
            if 'w' in G.namespace:
                G.w = 0
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
        if neuron_model == 'adex':
            I_timed = TimedArray(I_array.T * pA, dt=defaultclock.dt)
            G.run_regularly('I = I_timed(t, i)', dt=defaultclock.dt)
        else:
            I_timed = TimedArray(I_array.T, dt=defaultclock.dt)
            G.run_regularly('I = I_timed(t, i)', dt=defaultclock.dt)

        # Add synapses if enabled
        if synapse_enabled and num_neurons > 1:
            if neuron_model == 'adex':
                syn_weight_str = f'{syn_weight}*pA'
                S = Synapses(G, G, on_pre=f'I_post += {syn_weight_str}', delay=1*ms)
            else:
                syn_weight_str = f'{syn_weight}'
                S = Synapses(G, G, on_pre=f'v_post += {syn_weight_str}', delay=1*ms)
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

    # Only generate static plots if requested
    if plot_type == 'static':
        if output_type in ['voltage', 'both']:
            plt.figure(figsize=(10, 4))
            for i in range(num_neurons):
                plt.plot(M.t/ms, M.v[i], label=f'Neuron {i}')
            plt.xlabel('Time (ms)')
            plt.ylabel('Membrane potential (v)')
            plt.title('Membrane Potential Over Time')
            plt.legend()
            plt.tight_layout()
            img_path = os.path.join(OUTPUT_FOLDER, img_filename)
            plt.savefig(img_path)
            img_url = f'/output/{img_filename}'
            plt.close()

        if output_type in ['raster', 'both']:
            plt.figure(figsize=(10, 4))
            plt.plot(spike_mon.t/ms, spike_mon.i, '.k')
            plt.xlabel('Time (ms)')
            plt.ylabel('Neuron index')
            plt.title('Spike Raster Plot')
            plt.tight_layout()
            raster_path = os.path.join(OUTPUT_FOLDER, raster_filename)
            plt.savefig(raster_path)
            raster_url = f'/output/{raster_filename}'
            plt.close()

    # Only generate interactive plots if requested (default)
    if plot_type == 'interactive':
        if output_type in ['voltage', 'both']:
            traces = []
            for i in range(num_neurons):
                traces.append(go.Scatter(
                    x=(M.t/ms),
                    y=M.v[i],
                    mode='lines',
                    name=f'Neuron {i}'
                ))
            layout = go.Layout(
                title='Membrane Potential Over Time',
                xaxis=dict(title='Time (ms)'),
                yaxis=dict(title='Membrane potential (v)'),
                legend=dict(
                    orientation='h',
                    yanchor='top',
                    y=-0.2,  # places legend below the x-axis label
                    xanchor='center',
                    x=0.5
                ),
                margin=dict(l=40, r=20, t=40, b=60),  # increase bottom margin for legend
                height=350
            )
            fig = go.Figure(data=traces, layout=layout)
            plotly_voltage_html = pio.to_html(fig, full_html=False)

        if output_type in ['raster', 'both']:
            trace = go.Scatter(
                x=(spike_mon.t/ms),
                y=spike_mon.i,
                mode='markers',
                marker=dict(color='black', size=6),
                showlegend=False
            )
            layout = go.Layout(
                title='Spike Raster Plot',
                xaxis=dict(title='Time (ms)'),
                yaxis=dict(title='Neuron index'),
                margin=dict(l=40, r=20, t=40, b=40),
                height=350
            )
            fig = go.Figure(data=[trace], layout=layout)
            plotly_raster_html = pio.to_html(fig, full_html=False)

    # CSV Export: Save membrane potential traces
    df = pd.DataFrame({f"Neuron_{i}": M.v[i] for i in range(num_neurons)})
    df.insert(0, "Time(ms)", M.t/ms)
    csv_path = os.path.join(OUTPUT_FOLDER, csv_filename)
    df.to_csv(csv_path, index=False)
    data_url = f'/output/{csv_filename}'

    # JSON Export: Save data in JSON format
    neurons_json = {}
    for i in range(num_neurons):
        v = M.v[i]
        # Convert each value to float in mV, regardless of type
        v_data = [float(val / mV) if hasattr(val, 'unit') else float(val) for val in v]
        neurons_json[f'Neuron_{i}'] = v_data

    json_data = {
        'time_ms': (M.t/ms).tolist(),
        'neurons': neurons_json,
        'unit': 'mV'
    }
    json_path = os.path.join(OUTPUT_FOLDER, json_filename)
    with open(json_path, 'w') as jf:
        json.dump(json_data, jf)
    json_url = f'/output/{json_filename}'

    # Render the results page with plots and download links
    return render_template('index.html',
                           threshold=threshold,
                           reset=reset,
                           sim_time=sim_time,
                           input_current=input_current,
                           num_neurons=num_neurons,
                           current_start=current_start,
                           current_duration=current_duration,
                           noise=noise_enabled,
                           noise_intensity=noise_intensity,
                           noise_method=noise_method,
                           synapse=synapse_enabled,
                           syn_weight=syn_weight,
                           syn_prob=syn_prob,
                           output_type=output_type,
                           plot_type=plot_type,
                           img_url=img_url,
                           raster_url=raster_url,
                           data_url=data_url,
                           json_url=json_url,
                           plotly_voltage_html=plotly_voltage_html,
                           plotly_raster_html=plotly_raster_html,
                           sim_time_seconds=sim_time_seconds,
                           neuron_model=neuron_model,
                           izh_a=request.form.get('izh_a', type=float),
                           izh_b=request.form.get('izh_b', type=float),
                           izh_c=request.form.get('izh_c', type=float),
                           izh_d=request.form.get('izh_d', type=float),
                           adex_a=request.form.get('adex_a', type=float),
                           adex_b=request.form.get('adex_b', type=float),
                           adex_deltaT=request.form.get('adex_deltaT', type=float),
                           adex_tau_w=request.form.get('adex_tau_w', type=float),
                           custom_eqs=custom_eqs,
                           custom_threshold=custom_threshold,
                           custom_reset=custom_reset)

@app.route('/output/<path:path>')
def output_file(path):
    """
    Serve output files (plots, data) from the output folder.
    """
    return send_from_directory(OUTPUT_FOLDER, path)

if __name__ == '__main__':
    # Start the Flask development server
    app.run(debug=True)