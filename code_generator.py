"""
Generate executable Python code from simulation parameters.
"""
import textwrap

def indent(text, amount=4):
    """Add indentation to lines."""
    padding = ' ' * amount
    return ''.join(padding + line if line.strip() else line for line in text.splitlines(True))

def generate_imports():
    """Generate import statements."""
    return textwrap.dedent("""
        from brian2 import *
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Set up Brian2
        prefs.codegen.target = 'cython'  # Use 'numpy' for better compatibility or 'cython' for speed
        defaultclock.dt = 0.01*ms  # Simulation time step
        
        """)

def generate_neuron_model(params):
    """Generate code for neuron model."""
    model = params['neuron_model']
    
    if model == 'lif':
        code = textwrap.dedent(f"""
            # Leaky Integrate-and-Fire model
            eqs = '''
            dv/dt = (I-v)/(10*ms) : 1
            I : 1
            '''
            threshold = '{params['threshold']}'
            reset = 'v = {params["reset"]}'
            
            """)
    elif model == 'izhikevich':
        code = textwrap.dedent(f"""
            # Izhikevich model
            a = {params['izh_a']}  # Time scale of recovery variable
            b = {params['izh_b']}  # Sensitivity of recovery variable
            c = {params['izh_c']}  # After-spike reset value of v
            d = {params['izh_d']}  # After-spike reset value of u
            
            eqs = '''
            dv/dt = (0.04*v**2 + 5*v + 140 - u + I)/ms : 1
            du/dt = (a*(b*v - u))/ms : 1
            I : 1
            '''
            threshold = 'v > 30'
            reset = '''
            v = c
            u += d
            '''
            
            """)
    elif model == 'adex':
        code = textwrap.dedent(f"""
            # Adaptive Exponential Integrate-and-Fire model
            a = {params['adex_a']}*nS
            b = {params['adex_b']}*nA
            deltaT = {params['adex_deltaT']}*mV
            tau_w = {params['adex_tau_w']}*ms
            
            eqs = '''
            dv/dt = (-(v-(-70*mV)) + deltaT*exp((v-(-50*mV))/deltaT) + (I*nA) - w)/ms : volt
            dw/dt = (a*(v-(-70*mV)) - w)/tau_w : amp
            I : 1
            '''
            threshold = 'v > -30*mV'
            reset = '''
            v = -70*mV
            w += b
            '''
            
            """)
    elif model == 'custom':
        code = textwrap.dedent(f"""
            # Custom model
            eqs = '''
            {params['custom_eqs']}
            '''
            threshold = '{params['custom_threshold']}'
            reset = '{params['custom_reset']}'
            
            """)
    else:
        code = "# Unknown model type\n"
    
    return code

def generate_noise_code(params):
    """Generate code for noise if enabled."""
    if not params['noise_enabled']:
        return ""
    
    intensity = params['noise_intensity']
    method = params['noise_method']
    
    if method == 'additive':
        return textwrap.dedent(f"""
            # Add noise to equations
            eqs = eqs[:-3] + '+({intensity}*xi*second**0.5) : 1'
            
            """)
    elif method == 'multiplicative':
        return textwrap.dedent(f"""
            # Add multiplicative noise to equations
            eqs = eqs[:-3] + '+(({intensity}*xi*second**0.5)*v) : 1'
            
            """)
    else:
        return "# Unknown noise method\n"

def generate_network_code(params):
    """Generate code for network connectivity"""
    code = []
    if params['synapse_enabled'] and params['num_neurons'] > 1:
        topology_type = params.get('topology_type', 'random')
        
        code.append("\n# Network connectivity")
        if topology_type == 'random':
            code.append(f"syn = Synapses(G, G, on_pre='v_post += {params['syn_weight']}')")
            code.append(f"syn.connect(p={params['syn_prob']})")
        elif topology_type == 'small_world':
            code.append("# Small world network (Watts-Strogatz model)")
            code.append(f"k = {params['topology_k']}  # Number of nearest neighbors")
            code.append(f"p_rewire = {params['topology_p_rewire']}  # Rewiring probability")
            # Add more code...
    return "\n".join(code)

def generate_simulation_code(params):
    """Generate code to run the simulation."""
    code = textwrap.dedent(f"""
        # Set up current injection
        I_stim = {params['input_current']}  # Input current strength
        current_start = {params['current_start']}*ms  # When to start the current
        current_duration = {params['current_duration']}*ms  # How long to inject current
        
        @network_operation(when='start')
        def update_current(t):
            if current_start <= t < (current_start + current_duration):
                neurons.I = I_stim
            else:
                neurons.I = 0
        
        # Run the simulation
        print("Starting simulation...")
        run({params['sim_time']}*ms)
        print(f"Simulation completed with {{len(spike_mon.i)}} spikes.")
        
        """)
    return code

def generate_plotting_code(params):
    """Generate code for plotting results."""
    output_type = params.get('output_type', 'both')
    
    if output_type == 'voltage' or output_type == 'both':
        voltage_plot = textwrap.dedent("""
            # Plot membrane potential traces
            plt.figure(figsize=(10, 6))
            for i in range(min(5, N)):  # Plot up to 5 neurons
                plt.plot(state_mon.t/ms, state_mon.v[i], label=f'Neuron {i}')
            plt.xlabel('Time (ms)')
            plt.ylabel('Membrane Potential')
            plt.title('Membrane Potential Traces')
            plt.legend()
            plt.tight_layout()
            plt.savefig('membrane_potential.png')
            plt.show()
            
            """)
    else:
        voltage_plot = ""
    
    if output_type == 'raster' or output_type == 'both':
        raster_plot = textwrap.dedent("""
            # Plot spike raster
            plt.figure(figsize=(10, 6))
            plt.plot(spike_mon.t/ms, spike_mon.i, '.k', markersize=5)
            plt.xlabel('Time (ms)')
            plt.ylabel('Neuron index')
            plt.title('Spike Raster Plot')
            plt.tight_layout()
            plt.savefig('spike_raster.png')
            plt.show()
            
            """)
    else:
        raster_plot = ""
    
    return voltage_plot + raster_plot

def generate_summary_code(params):
    """Generate code to print summary and save data."""
    return textwrap.dedent("""
        # Print some statistics
        if len(spike_mon.i) > 0:
            avg_rate = len(spike_mon.i) / (len(neurons) * (defaultclock.t/second))
            print(f"Average firing rate: {avg_rate:.2f} Hz")
        else:
            print("No spikes detected.")
        
        # Save the data
        spike_times = np.array(spike_mon.t/ms)
        spike_indices = np.array(spike_mon.i)
        
        np.savez('simulation_data.npz', 
                 spike_times=spike_times,
                 spike_indices=spike_indices,
                 membrane_potential=state_mon.v[:],
                 time=state_mon.t/ms)
        
        print("Data saved to 'simulation_data.npz'")
        """)

def generate_complete_code(params):
    """Generate the complete Python code for the simulation."""
    code_sections = [
        "#!/usr/bin/env python",
        "# Brian2 Simulation generated from web interface",
        "",
        generate_imports(),
        generate_neuron_model(params),
        generate_noise_code(params),
        generate_network_code(params),
        generate_simulation_code(params),
        generate_plotting_code(params),
        generate_summary_code(params)
    ]
    
    return "\n".join(code_sections)