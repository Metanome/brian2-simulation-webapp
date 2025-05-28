"""
app.py - Main Flask application for Brian2 Web Simulation

This file contains the Flask app, routes, and simulation logic for the Brian2 web interface.
It handles form input, validation, running simulations, generating plots, and serving results.
"""

import os
import time
import uuid
import json
import logging
os.environ['MPLBACKEND'] = 'Agg'  # Use non-GUI backend for matplotlib

from flask import Flask, render_template, request, send_from_directory, flash, jsonify, redirect
from brian2 import *

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

if os.environ.get("BRIAN2_CODEGEN", "").lower() == "numpy":
    prefs.codegen.target = 'numpy'  # Use NumPy backend on Render or when specified
else:
    prefs.codegen.target = 'cython'  # Use Cython locally for best performance

import matplotlib
matplotlib.use('Agg')  # Ensure matplotlib does not require a display

# Import our custom modules
from simulator import run_simulation, save_simulation_data
from plotting import (generate_static_voltage_plot, generate_static_raster_plot,
                     generate_interactive_voltage_plot, generate_interactive_raster_plot,
                     generate_network_topology_plot, generate_interactive_topology_plot)
from code_generator import generate_complete_code

# Initialize Flask app and static folder for output files
app = Flask(__name__)
app.secret_key = 'd3c8e7f6b1a24e0c9f7a5b6c2e1d4f8a9b7c6e5d2f1a3b4c5d6e7f8a9b0c1d2e'  # Needed for flash messages
OUTPUT_FOLDER = os.path.join(app.root_path, 'output')
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def cleanup_output_folder(output_folder, max_age_seconds=180):
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

def validate_inputs(threshold, reset, sim_time, input_current, num_neurons, current_start, current_duration, 
                   topology_type=None, synapse_enabled=False, **topology_params):
    """
    Check user inputs for validity and return a list of error messages if any.
    """
    errors = []
    
    # Existing validations
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
    
    # Topology parameter validations
    if synapse_enabled and topology_type:
        syn_prob = topology_params.get('syn_prob', 0.2)
        syn_weight = topology_params.get('syn_weight', 0.2)
        
        # General synapse validations
        if syn_prob < 0 or syn_prob > 1:
            errors.append("Connection probability must be between 0 and 1.")
        if abs(syn_weight) > 10:
            errors.append("Synaptic weight should be reasonable (between -10 and 10).")
        
        # Topology-specific validations
        if topology_type == 'small_world':
            k = topology_params.get('topology_k', 2)
            p_rewire = topology_params.get('topology_p_rewire', 0.1)
            if k % 2 != 0 or k < 2:
                errors.append("Small world k parameter must be an even number >= 2.")
            if k >= num_neurons:
                errors.append(f"Small world k ({k}) must be less than number of neurons ({num_neurons}).")
            if p_rewire < 0 or p_rewire > 1:
                errors.append("Rewiring probability must be between 0 and 1.")
        
        elif topology_type == 'regular':
            k_reg = topology_params.get('topology_k_reg', 2)
            if k_reg % 2 != 0 or k_reg < 2:
                errors.append("Regular lattice k parameter must be an even number >= 2.")
            if k_reg >= num_neurons:
                errors.append(f"Regular lattice k ({k_reg}) must be less than number of neurons ({num_neurons}).")
        
        elif topology_type == 'scale_free':
            m = topology_params.get('topology_m', 2)
            if m < 1 or m >= num_neurons // 2:
                errors.append(f"Scale-free m parameter must be between 1 and {num_neurons // 2}.")
        
        elif topology_type == 'modular':
            n_modules = topology_params.get('topology_n_modules', 4)
            p_intra = topology_params.get('topology_p_intra', 0.2)
            p_inter = topology_params.get('topology_p_inter', 0.01)
            
            if n_modules < 2 or n_modules > num_neurons // 2:
                errors.append(f"Number of modules must be between 2 and {num_neurons // 2}.")
            if p_intra < 0 or p_intra > 1:
                errors.append("Intra-module probability must be between 0 and 1.")
            if p_inter < 0 or p_inter > 1:
                errors.append("Inter-module probability must be between 0 and 1.")
            if p_intra < p_inter:
                errors.append("Intra-module probability should typically be higher than inter-module probability.")
    
    return errors

def validate_config(config):
    """Validate a loaded configuration before applying it."""
    errors = []
    
    # Required fields
    required_fields = ['neuron_model', 'num_neurons', 'sim_time', 'threshold', 'reset']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate field types and ranges
    try:
        if 'num_neurons' in config:
            num_neurons = int(config['num_neurons'])
            if num_neurons < 1 or num_neurons > 100:
                errors.append("Number of neurons must be between 1 and 100.")
        
        if 'sim_time' in config:
            sim_time = float(config['sim_time'])
            if sim_time <= 0 or sim_time > 10000:
                errors.append("Simulation time must be positive and less than 10000 ms.")
        
        if 'neuron_model' in config:
            valid_models = ['lif', 'izhikevich', 'adex', 'custom']
            if config['neuron_model'] not in valid_models:
                errors.append(f"Invalid neuron model. Must be one of: {valid_models}")
        
        # Validate topology parameters if present
        if config.get('synapse_enabled') and config.get('topology_type'):
            topology_validation = validate_inputs(
                config.get('threshold', 1.0), config.get('reset', 0.0),
                config.get('sim_time', 100), config.get('input_current', 1.2),
                config.get('num_neurons', 5), config.get('current_start', 0),
                config.get('current_duration', 100), 
                topology_type=config.get('topology_type'),
                synapse_enabled=config.get('synapse_enabled', False),
                **{k: v for k, v in config.items() if k.startswith('topology_') or k in ['syn_prob', 'syn_weight']}
            )
            errors.extend(topology_validation)
            
    except (ValueError, TypeError) as e:
        errors.append(f"Invalid data type in configuration: {e}")
    
    return errors

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main route: renders the simulation form and handles simulation requests.
    GET: Show the form. POST: Run simulation and show results.
    """
    if request.method == 'POST':
        cleanup_output_folder(OUTPUT_FOLDER)  # Clean up old output files
        try:
            # Read all form parameters, using defaults if not provided
            neuron_model = request.form.get('neuron_model', 'lif')
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

            # Extract topology parameters
            topology_type = request.form.get('topology_type', 'random')
            topology_k = int(request.form.get('topology_k', 2))
            topology_k_reg = int(request.form.get('topology_k_reg', 2))

            # Only modify topology_k if it's actually going to be used for small world
            original_topology_k = topology_k  # Save original value
            if topology_type == 'small_world' and topology_k % 2 != 0:
                topology_k = topology_k + 1
                # We'll still display the corrected value in the UI
            else:
                # For other topologies, use the original input value
                topology_k = original_topology_k
            topology_p_rewire = float(request.form.get('topology_p_rewire', 0.1))
            topology_m = int(request.form.get('topology_m', 2))

            # Extract modular network parameters
            topology_n_modules = int(request.form.get('topology_n_modules', 4))
            topology_p_intra = float(request.form.get('topology_p_intra', 0.2))
            topology_p_inter = float(request.form.get('topology_p_inter', 0.01))

            # Add this validation here
            if topology_type == 'small_world':
                # Ensure k is even for small world networks
                if topology_k % 2 != 0:
                    topology_k += 1
        except Exception as e:
            logging.exception("Invalid input during form parsing")
            flash(f"Invalid input: {e}")
            return render_template('index.html')

        # Validate all user input
        errors = validate_inputs(threshold, reset, sim_time, input_current, num_neurons, current_start, current_duration,
                        topology_type=topology_type, synapse_enabled=synapse_enabled,
                        syn_prob=syn_prob, syn_weight=syn_weight, topology_k=topology_k,
                        topology_k_reg=topology_k_reg, topology_p_rewire=topology_p_rewire,
                        topology_m=topology_m, topology_n_modules=topology_n_modules,
                        topology_p_intra=topology_p_intra, topology_p_inter=topology_p_inter)
        if neuron_model == 'custom':
            if not custom_eqs.strip() or not custom_threshold.strip() or not custom_reset.strip():
                errors.append("Custom model: equations, threshold, and reset are required.")
        if errors:
            for err in errors:
                flash(err)
                logging.warning(f"Input validation error: {err}")
            # Re-render form with previous values and error messages
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
                                   custom_reset=custom_reset,
                                   topology_type=topology_type,
                                   topology_k=topology_k,  # Use the modified variable
                                   topology_k_reg=topology_k_reg,
                                   topology_p_rewire=topology_p_rewire,
                                   topology_m=topology_m,
                                   topology_n_modules=topology_n_modules,
                                   topology_p_intra=topology_p_intra,
                                   topology_p_inter=topology_p_inter)

        # Generate unique filenames for this simulation run
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
            # Prepare simulation parameters
            sim_params = {
                'neuron_model': neuron_model,
                'num_neurons': num_neurons,
                'sim_time': sim_time,
                'input_current': input_current,
                'threshold': threshold,
                'reset': reset,
                'current_start': current_start,
                'current_duration': current_duration,
                'noise_enabled': noise_enabled,
                'noise_intensity': noise_intensity,
                'noise_method': noise_method,
                'synapse_enabled': synapse_enabled,
                'syn_weight': syn_weight,
                'syn_prob': syn_prob,
                'izh_a': izh_a,
                'izh_b': izh_b,
                'izh_c': izh_c,
                'izh_d': izh_d,
                'adex_a': adex_a,
                'adex_b': adex_b,
                'adex_deltaT': adex_deltaT,
                'adex_tau_w': adex_tau_w,
                'custom_eqs': custom_eqs,
                'custom_threshold': custom_threshold,
                'custom_reset': custom_reset,
                # Add topology parameters
                'topology_type': topology_type,
                'topology_k': topology_k,
                'topology_k_reg': topology_k_reg,
                'topology_p_rewire': topology_p_rewire,
                'topology_m': topology_m,
                'topology_n_modules': topology_n_modules,
                'topology_p_intra': topology_p_intra,
                'topology_p_inter': topology_p_inter
            }
            
            # Run the simulation
            results = run_simulation(sim_params)
            logging.info("Simulation run successful")
            # Extract results
            M = results['state_monitor']
            spike_mon = results['spike_monitor']
            sim_time_seconds = results['sim_time_seconds']
        except Exception as e:
            logging.exception("Simulation error")
            flash(f"Simulation error: {e}")
            return render_template('index.html')
        finally:
            # Clean up Brian2 cache after simulation
            cleanup_brian2_cache()

        # Prepare plot and data file URLs
        img_url = None
        raster_url = None
        data_url = None
        json_url = None

        # Generate static plots if requested
        if plot_type == 'static':
            # Always generate these if output_type is 'all', 'both' or their specific type
            if output_type in ['voltage', 'both', 'all']:
                img_filename = f'voltage_plot_{unique_id}.png'
                img_url = generate_static_voltage_plot(results['state_monitor'], num_neurons, OUTPUT_FOLDER, img_filename)
            else:
                img_url = None
                
            if output_type in ['raster', 'both', 'all']:
                raster_filename = f'raster_plot_{unique_id}.png'
                raster_url = generate_static_raster_plot(results['spike_monitor'], OUTPUT_FOLDER, raster_filename)
            else:
                raster_url = None
                
            # Only generate topology plot if 'all' and network graph exists
            if output_type == 'all' and synapse_enabled and results['network_graph'] is not None:
                topology_filename = f'topology_plot_{unique_id}.png'
                topology_url = generate_network_topology_plot(results['network_graph'], OUTPUT_FOLDER, topology_filename)
            else:
                topology_url = None

        # Generate interactive plots if requested
        if plot_type == 'interactive':
            # For voltage plots - add 'all' to check
            if output_type in ['voltage', 'both', 'all']:  # FIXED: added 'all'
                plotly_voltage_html = generate_interactive_voltage_plot(M, num_neurons)
            else:
                plotly_voltage_html = None
                
            # For raster plots - add 'all' to check  
            if output_type in ['raster', 'both', 'all']:  # FIXED: added 'all'
                plotly_raster_html = generate_interactive_raster_plot(spike_mon)
            else:
                plotly_raster_html = None
                
            # For topology plots - add output_type check
            if output_type == 'all' and synapse_enabled and results['network_graph'] is not None:  # FIXED: added output_type check
                plotly_topology_html = generate_interactive_topology_plot(results['network_graph'])
            else:
                plotly_topology_html = None

        # Save simulation data
        data_url, json_url = save_simulation_data(results, OUTPUT_FOLDER, unique_id)

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
                               custom_reset=custom_reset,
                               # Add these explicit topology parameter returns
                               topology_type=topology_type,
                               topology_k=topology_k,  # Use the modified variable
                               topology_k_reg=topology_k_reg,
                               topology_p_rewire=topology_p_rewire,
                               topology_m=topology_m,
                               topology_n_modules=topology_n_modules,
                               topology_p_intra=topology_p_intra,
                               topology_p_inter=topology_p_inter,
                               topology_url=topology_url if plot_type == 'static' else None,
                               plotly_topology_html=plotly_topology_html if plot_type == 'interactive' else None,
                               )
    else:
        return render_template('index.html')

@app.route('/output/<path:path>')
def output_file(path):
    """
    Serve output files (plots, data) from the output folder.
    """
    return send_from_directory(OUTPUT_FOLDER, path)

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save a configuration to the server."""
    if request.content_type != 'application/json':
        return jsonify({'error': 'Content type must be application/json'}), 415
    
    try:
        config = request.json
        config_id = str(uuid.uuid4())
        config_filename = f'config_{config_id}.json'
        with open(os.path.join(OUTPUT_FOLDER, config_filename), 'w') as f:
            json.dump(config, f, indent=2)
        logging.info(f"Configuration saved: {config_filename}")
        return jsonify({
            'success': True, 
            'message': 'Configuration saved',
            'config_id': config_id,
            'download_url': f'/output/{config_filename}'
        })
    except Exception as e:
        logging.exception("Error saving configuration")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/<config_id>', methods=['GET'])
def get_config(config_id):
    """Retrieve a saved configuration by ID."""
    config_filename = f'config_{config_id}.json'
    config_path = os.path.join(OUTPUT_FOLDER, config_filename)
    
    if not os.path.exists(config_path):
        logging.warning(f"Configuration not found: {config_filename}")
        return jsonify({'error': 'Configuration not found'}), 404
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate the configuration
        validation_errors = validate_config(config)
        if validation_errors:
            logging.warning(f"Invalid configuration loaded: {validation_errors}")
            return jsonify({
                'error': 'Invalid configuration',
                'validation_errors': validation_errors
            }), 400
        
        # Add metadata about when it was loaded
        config['_loaded_at'] = time.time()
        config['_validation_status'] = 'valid'
        
        return jsonify(config)
        
    except Exception as e:
        logging.exception("Error loading configuration")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_code', methods=['POST'])
def generate_code():
    """Generate Python code for the simulation with current parameters."""
    try:
        # Extract parameters from form
        sim_params = {
            'neuron_model': request.form.get('neuron_model', 'lif'),
            'izh_a': float(request.form.get('izh_a', 0.02)),
            'izh_b': float(request.form.get('izh_b', 0.2)),
            'izh_c': float(request.form.get('izh_c', -65)),
            'izh_d': float(request.form.get('izh_d', 2)),
            'adex_a': float(request.form.get('adex_a', 0.02)),
            'adex_b': float(request.form.get('adex_b', 0.2)),
            'adex_deltaT': float(request.form.get('adex_deltaT', 2)),
            'adex_tau_w': float(request.form.get('adex_tau_w', 30)),
            'custom_eqs': request.form.get('custom_eqs', ''),
            'custom_threshold': request.form.get('custom_threshold', ''),
            'custom_reset': request.form.get('custom_reset', ''),
            'threshold': float(request.form.get('threshold', 1.0)),
            'reset': float(request.form.get('reset', 0.0)),
            'sim_time': float(request.form.get('sim_time', 100)),
            'input_current': float(request.form.get('input_current', 1.2)),
            'num_neurons': int(request.form.get('num_neurons', 5)),
            'current_start': float(request.form.get('current_start', 0)),
            'current_duration': float(request.form.get('current_duration', 100)),
            'noise_enabled': 'noise' in request.form,
            'noise_intensity': float(request.form.get('noise_intensity', 0.2)),
            'noise_method': request.form.get('noise_method', 'additive'),
            'synapse_enabled': 'synapse' in request.form,
            'syn_weight': float(request.form.get('syn_weight', 0.2)),
            'syn_prob': float(request.form.get('syn_prob', 0.2)),
            'output_type': request.form.get('output_type', 'both'),
            'plot_type': request.form.get('plot_type', 'interactive'),
            'topology_type': request.form.get('topology_type', 'random'),
            'topology_k': int(request.form.get('topology_k', 2)),
            'topology_k_reg': int(request.form.get('topology_k_reg', 2)),
            'topology_p_rewire': float(request.form.get('topology_p_rewire', 0.1)),
            'topology_m': int(request.form.get('topology_m', 2)),
            'topology_n_modules': int(request.form.get('topology_n_modules', 4)),
            'topology_p_intra': float(request.form.get('topology_p_intra', 0.2)),
            'topology_p_inter': float(request.form.get('topology_p_inter', 0.01))
            # Add other topology parameters as needed
        }
        
        # Generate the code
        code = generate_complete_code(sim_params)
        
        # Write to file
        unique_id = str(uuid.uuid4())
        code_filename = f'brian2_sim_{unique_id}.py'
        code_path = os.path.join(OUTPUT_FOLDER, code_filename)
        
        with open(code_path, 'w') as f:
            f.write(code)
        logging.info(f"Generated code file: {code_filename}")
        return send_from_directory(OUTPUT_FOLDER, code_filename, 
                                  as_attachment=True, 
                                  download_name='brian2_simulation.py')
    except Exception as e:
        logging.exception("Error generating code")
        flash(f"Error generating code: {e}")
        return redirect('/')

def cleanup_brian2_cache():
    """Clean up Brian2 compilation cache to prevent memory buildup."""
    try:
        if prefs.codegen.target == 'cython':
            from brian2.codegen.runtime.cython_rt import CythonCodeObject
            if hasattr(CythonCodeObject, '_cache'):
                CythonCodeObject._cache.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Clear Brian2's device cache
        from brian2.devices.device import get_device
        device = get_device()
        if hasattr(device, 'reinit'):
            device.reinit()
            
    except Exception as e:
        logging.warning(f"Cache cleanup warning: {e}")
        
if __name__ == '__main__':
    app.run(port=5000)