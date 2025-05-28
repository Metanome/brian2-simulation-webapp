"""
simulator.py - Brian2 simulation functions for Brian2 Web Simulation

This file contains functions for configuring and running Brian2 simulations.
"""

import time
import numpy as np
import pandas as pd
import json
import os
from brian2 import *
import topology


def run_simulation(params):
    """
    Run a Brian2 simulation with the given parameters
    
    Parameters
    ----------
    params : dict
        Dictionary with simulation parameters
        
    Returns
    -------
    dict
        Dictionary with simulation results
    """
    
    # At the start of the function:
    print("\n=== SIMULATION PARAMETERS ===")
    print(f"Neuron model: {params.get('neuron_model')}")
    print(f"Number of neurons: {params.get('num_neurons')}")
    
    # Topology-specific debugging:
    if params.get('synapse_enabled'):
        print("\n=== TOPOLOGY PARAMETERS ===")
        print(f"Topology type: {params.get('topology_type')}")
        print(f"Synaptic weight: {params.get('syn_weight')}")
        print(f"Connection probability: {params.get('syn_prob')}")
        
        if params.get('topology_type') == 'small_world':
            print(f"Small world k: {params.get('topology_k')}")
            print(f"Small world p_rewire: {params.get('topology_p_rewire')}")
        elif params.get('topology_type') == 'scale_free':
            print(f"Scale free m: {params.get('topology_m')}")
        elif params.get('topology_type') == 'regular':
            print(f"Regular lattice k_reg from params: {params.get('topology_k_reg')}")
            print(f"Regular lattice k from params: {params.get('topology_k')}")
            print(f"All topology params: {[k for k in params.keys() if k.startswith('topology_')]}")
        elif params.get('topology_type') == 'modular':
            print(f"Modules: {params.get('topology_n_modules')}")
            print(f"Intra-module prob: {params.get('topology_p_intra')}")
            print(f"Inter-module prob: {params.get('topology_p_inter')}")
    
    # Extract parameters
    neuron_model = params['neuron_model']
    num_neurons = params['num_neurons']
    sim_time = params['sim_time']
    input_current = params['input_current']
    current_start = params['current_start']
    current_duration = params['current_duration']
    noise_enabled = params['noise_enabled']
    noise_intensity = params.get('noise_intensity', 0.2)
    noise_method = params.get('noise_method', 'additive')
    synapse_enabled = params['synapse_enabled']
    syn_weight = params.get('syn_weight', 0.2)
    syn_prob = params.get('syn_prob', 0.2)
    
    # Record simulation start time
    start_time = time.time()
    
    # Reset Brian2 state
    start_scope()
    
    # Set up the neuron group based on model type
    if neuron_model == 'lif':
        from models import LIFModel
        model = LIFModel()
        threshold = params['threshold']
        reset = params['reset']
        
        eqs = model.get_equations()
        threshold_expr = model.get_threshold(threshold)
        reset_expr = model.get_reset(reset)
        
        G = NeuronGroup(num_neurons, eqs, threshold=threshold_expr, reset=reset_expr, method='euler')
        if 'v' in G.namespace:
            G.v = 0
        G.I = 0
        
    elif neuron_model == 'izhikevich':
        from models import IzhikevichModel
        model = IzhikevichModel()
        izh_a = params.get('izh_a', 0.02)
        izh_b = params.get('izh_b', 0.2)
        izh_c = params.get('izh_c', -65)
        izh_d = params.get('izh_d', 2)
        
        eqs = model.get_equations(izh_a, izh_b)
        threshold_expr = model.get_threshold()
        reset_expr = model.get_reset(izh_c, izh_d)
        
        G = NeuronGroup(num_neurons, eqs, threshold=threshold_expr, reset=reset_expr, method='euler')
        if 'v' in G.namespace:
            G.v = 0
        if 'u' in G.namespace:
            G.u = 0
        G.I = 0
        
    elif neuron_model == 'adex':
        from models import AdExModel
        model = AdExModel()
        adex_a = params.get('adex_a', 0.02)
        adex_b = params.get('adex_b', 0.2)
        adex_deltaT = params.get('adex_deltaT', 2)
        adex_tau_w = params.get('adex_tau_w', 30)
        
        eqs = model.get_equations()
        threshold_expr = model.get_threshold()
        reset_expr = model.get_reset(adex_b)
        
        G = NeuronGroup(num_neurons, eqs, threshold=threshold_expr, reset=reset_expr, method='euler')
        G = model.configure_group(G, input_current, adex_deltaT, adex_a, adex_tau_w)
        
    elif neuron_model == 'custom':
        from models import CustomModel
        model = CustomModel()
        custom_eqs = params.get('custom_eqs', '')
        custom_threshold = params.get('custom_threshold', '')
        custom_reset = params.get('custom_reset', '')
        
        eqs = model.get_equations(custom_eqs)
        threshold_expr = model.get_threshold(custom_threshold)
        reset_expr = model.get_reset(custom_reset)
        
        G = NeuronGroup(num_neurons, eqs, threshold=threshold_expr, reset=reset_expr, method='euler')
        if 'v' in G.namespace:
            G.v = 0
        if 'u' in G.namespace:
            G.u = 0
        if 'w' in G.namespace:
            G.w = 0
        G.I = 0
    
    # Create time array for current injection
    dt = float(defaultclock.dt/ms)
    time_array = np.arange(0, sim_time, dt)
    I_array = np.zeros((num_neurons, len(time_array)))
    
    # Set current for selected interval
    start_idx = max(0, int(current_start / dt))
    end_idx = min(len(time_array), int((current_start + current_duration) / dt))
    if end_idx > start_idx:
        # Each neuron gets a slightly different current to break symmetry
        for n in range(num_neurons):
            I_array[n, start_idx:end_idx] = input_current + 0.05 * n
    
    # Add noise if enabled
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
    
    S = None
    # Add synapses if enabled and more than one neuron
    if synapse_enabled and num_neurons > 1:
        # Get topology-related parameters
        topology_type = params.get('topology_type', 'random')
        
        topology_params = {
            'weight': syn_weight,
            'probability': syn_prob,
            'k': params.get('topology_k', 2),        # For small-world
            'k_reg': params.get('topology_k_reg', 2), # For regular lattice
            'p_rewire': params.get('topology_p_rewire', 0.1),
            'm': params.get('topology_m', 2),
            'n_modules': params.get('topology_n_modules', 4),
            'p_intra': params.get('topology_p_intra', 0.2),
            'p_inter': params.get('topology_p_inter', 0.01)
        }
        
        # Create connections based on chosen topology
        if topology_type == 'random':
            S, G_net = topology.create_random_connections(G, syn_weight, syn_prob)
        elif topology_type == 'small_world':
            S, G_net = topology.create_small_world_connections(G, syn_weight, topology_params['k'], topology_params['p_rewire'])
        elif topology_type == 'scale_free':
            S, G_net = topology.create_scale_free_connections(G, syn_weight, topology_params['m'])
        elif topology_type == 'regular':
            k_val = int(topology_params['k_reg'])
            S, G_net = topology.create_regular_lattice(G, syn_weight, k_val)
        elif topology_type == 'modular':
            S, G_net = topology.create_modular_connections(G, syn_weight, topology_params['n_modules'], 
                                topology_params['p_intra'], topology_params['p_inter'])
        else:
            # Default to random
            S, G_net = topology.create_random_connections(G, syn_weight, syn_prob)
        

    # Set up monitors to record data
    M = StateMonitor(G, 'v', record=True)
    spike_mon = SpikeMonitor(G)
    
    # Create a fresh Network explicitly listing all components
    net = Network()
    net.add(G)  # Add neuron group
    if S is not None:
        net.add(S)  # Add synapses if they exist
    net.add(M, spike_mon)  # Add monitors

    # Run the simulation
    net.run(sim_time * ms)
    
    # Calculate simulation time
    sim_time_seconds = time.time() - start_time
    
    # Return simulation results
    return {
        'state_monitor': M,
        'spike_monitor': spike_mon,
        'sim_time_seconds': sim_time_seconds,
        'network_graph': G_net if synapse_enabled and num_neurons > 1 else None
    }


def save_simulation_data(results, output_folder, unique_id):
    """
    Save simulation data to CSV and JSON files
    
    Parameters
    ----------
    results : dict
        Dictionary with simulation results
    output_folder : str
        Path to the output folder
    unique_id : str
        Unique identifier for this simulation run
        
    Returns
    -------
    tuple
        URLs for the saved data files
    """
    M = results['state_monitor']
    num_neurons = len(M.v)
    
    # Generate filenames
    csv_filename = f'sim_data_{unique_id}.csv'
    json_filename = f'sim_data_{unique_id}.json'
    
    # Save to CSV
    df = pd.DataFrame({f"Neuron_{i}": M.v[i] for i in range(num_neurons)})
    df.insert(0, "Time(ms)", M.t/ms)
    csv_path = os.path.join(output_folder, csv_filename)
    df.to_csv(csv_path, index=False)
    data_url = f'/output/{csv_filename}'
    
    # Save to JSON
    neurons_json = {}
    for i in range(num_neurons):
        v = M.v[i]
        v_data = [float(val / mV) if hasattr(val, 'unit') else float(val) for val in v]
        neurons_json[f'Neuron_{i}'] = v_data
    
    json_data = {
        'time_ms': (M.t/ms).tolist(),
        'neurons': neurons_json,
        'unit': 'mV'
    }
    json_path = os.path.join(output_folder, json_filename)
    with open(json_path, 'w') as jf:
        json.dump(json_data, jf)
    json_url = f'/output/{json_filename}'
    
    return data_url, json_url