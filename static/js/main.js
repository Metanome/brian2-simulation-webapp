/*
main.js - Main JavaScript for Brian2 Web Simulation
Handles UI logic, form validation, preset management, spinner overlay, and local storage for the simulation web app.
*/

window.onload = function() {
    // Show spinner and disable options-panel on form submit
    document.getElementById('simForm').onsubmit = function() {
        setTimeout(function() {
            document.getElementById('spinner').style.display = 'flex';
            document.querySelector('.options-panel').classList.add('disabled-panel');
        }, 10);
        document.getElementById('output-placeholder').style.display = 'none';
    };

    // Set initial UI state based on selected model and options
    var model = document.getElementById('neuron_model').value;
    showModelFields(model);
    toggleNoiseOptions();
    toggleSynapseOptions();

    // Update preset description on load
    document.getElementById('preset-desc').innerText = presetDescriptions[document.getElementById('preset').value] || presetDescriptions['custom'];

    // Update model fields when neuron model changes
    document.getElementById('neuron_model').addEventListener('change', function() {
        showModelFields(this.value);
    });
    // Update preset description and sync model if preset changes
    document.getElementById('preset').addEventListener('change', function() {
        document.getElementById('preset-desc').innerText = presetDescriptions[this.value] || presetDescriptions['custom'];
        // If preset implies a model, update neuron model
        const presetToModel = {
            lif_quickstart: 'lif',
            balanced_random: 'lif',
            strongly_coupled: 'lif',
            sparse_excitatory: 'lif',
            inhibition_dominated: 'lif',
            noisy_single: 'lif',
            synchronous_bursting: 'lif',
            minimal: 'lif'
        };
        if (presetToModel[this.value]) {
            document.getElementById('neuron_model').value = presetToModel[this.value];
            showModelFields(presetToModel[this.value]);
        }
    });

    // Restore last used settings from localStorage if available
    if (window.localStorage) {
        const saved = localStorage.getItem('brian2sim-settings');
        if (saved) {
            try {
                setFields(JSON.parse(saved));
                showModelFields(document.getElementById('neuron_model').value);
                toggleNoiseOptions();
                toggleSynapseOptions();
            } catch (e) {
                console.error("Error loading saved settings:", e);
                localStorage.removeItem('brian2sim-settings');
            }
        }
        // Save settings on any form change
        document.getElementById('simForm').addEventListener('change', function() {
            localStorage.setItem('brian2sim-settings', JSON.stringify(getFields()));
        });
    }

    // Hide placeholder if results are present
    if (document.querySelector('.output img, .output .plotly-graph-div')) {
        document.getElementById('output-placeholder').style.display = 'none';
    }

    // Hide spinner and re-enable options-panel on page load (after simulation)
    document.getElementById('spinner').style.display = 'none';
    document.querySelector('.options-panel').classList.remove('disabled-panel');

    // Set up event listeners for synaptic connections
    document.getElementById('synapse').addEventListener('change', toggleSynapseOptions);
    document.getElementById('topology_type').addEventListener('change', updateTopologyParams);
    
    // Initialize visibility of options
    toggleSynapseOptions();
    updateTopologyParams();
};

// Default values for all simulation fields
const defaults = {
    threshold: 1.0,
    reset: 0.0,
    sim_time: 100,
    input_current: 1.2,
    num_neurons: 5,
    current_start: 0,
    current_duration: 100,
    noise: true,
    noise_intensity: 0.2,
    noise_method: "additive",
    synapse: true,
    syn_weight: 0.2,
    syn_prob: 0.2,
    output_type: "both",
    plot_type: "interactive",
    neuron_model: "lif",
    izh_a: 0.02, izh_b: 0.2, izh_c: -65, izh_d: 2,
    adex_a: 0.02, adex_b: 0.2, adex_deltaT: 2, adex_tau_w: 30,
    custom_eqs: "", custom_threshold: "", custom_reset: "",
    
    // Topology parameters
    topology_type: 'random',
    topology_k: 2,           // Used for small-world
    topology_p_rewire: 0.1,  // Used for small-world
    topology_m: 2,           // Used for scale-free
    topology_k_reg: 2,       // Used for regular lattice
    topology_n_modules: 4,   // Used for modular
    topology_p_intra: 0.2,   // Used for modular
    topology_p_inter: 0.01   // Used for modular
};

// Descriptions for each preset scenario
const presetDescriptions = {
    custom: "Set your own parameters or pick a preset to see a typical network scenario.",
    lif_quickstart: "A classic Leaky Integrate-and-Fire (LIF) network with 5 neurons, moderate input, and sparse synapses. Great for quick demos.",
    balanced_random: "A medium-sized network with 20 neurons, more noise, and sparse random connectivity. Useful for exploring asynchronous firing.",
    strongly_coupled: "A large, densely connected network with strong synapses and multiplicative noise. Shows rich, collective dynamics.",
    sparse_excitatory: "A small network with weak, sparse excitatory coupling and moderate noise. Good for observing isolated spikes.",
    inhibition_dominated: "A medium network dominated by strong inhibitory synapses. Demonstrates suppression and competition.",
    noisy_single: "A single neuron with high noise and no synapses. Useful for exploring stochastic firing and membrane fluctuations.",
    synchronous_bursting: "A medium network with high synaptic weight and probability, low noise. Promotes synchronous bursts.",
    minimal: "A minimal network of 2 neurons, no noise, weak synapses. Useful for debugging and basic connectivity tests."
};

// Apply a preset: set all fields to preset values
function applyPreset(preset) {
    let presetValues = {};
    if (preset === "lif_quickstart") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 100, input_current: 1.2, num_neurons: 5,
            current_start: 0, current_duration: 100, noise: true, noise_intensity: 0.2,
            noise_method: "additive", synapse: true, syn_weight: 0.2, syn_prob: 0.2, output_type: "both"
        };
    } else if (preset === "balanced_random") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 200, input_current: 1.0, num_neurons: 20,
            current_start: 0, current_duration: 200, noise: true, noise_intensity: 0.4,
            noise_method: "additive", synapse: true, syn_weight: 0.3, syn_prob: 0.1, output_type: "both"
        };
    } else if (preset === "strongly_coupled") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 300, input_current: 1.5, num_neurons: 50,
            current_start: 0, current_duration: 300, noise: true, noise_intensity: 0.5,
            noise_method: "multiplicative", synapse: true, syn_weight: 0.8, syn_prob: 0.5, output_type: "both"
        };
    } else if (preset === "sparse_excitatory") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 150, input_current: 1.1, num_neurons: 10,
            current_start: 0, current_duration: 150, noise: true, noise_intensity: 0.15,
            noise_method: "additive", synapse: true, syn_weight: 0.1, syn_prob: 0.05, output_type: "both"
        };
    } else if (preset === "inhibition_dominated") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 200, input_current: 1.3, num_neurons: 20,
            current_start: 0, current_duration: 200, noise: true, noise_intensity: 0.25,
            noise_method: "additive", synapse: true, syn_weight: -0.5, syn_prob: 0.2, output_type: "both"
        };
    } else if (preset === "noisy_single") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 100, input_current: 1.0, num_neurons: 1,
            current_start: 0, current_duration: 100, noise: true, noise_intensity: 0.5,
            noise_method: "additive", synapse: false, syn_weight: 0.0, syn_prob: 0.0, output_type: "both"
        };
    } else if (preset === "synchronous_bursting") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 120, input_current: 1.4, num_neurons: 15,
            current_start: 0, current_duration: 120, noise: true, noise_intensity: 0.1,
            noise_method: "additive", synapse: true, syn_weight: 1.0, syn_prob: 0.8, output_type: "both"
        };
    } else if (preset === "minimal") {
        presetValues = {
            neuron_model: 'lif', threshold: 1.0, reset: 0.0, sim_time: 50, input_current: 1.0, num_neurons: 2,
            current_start: 0, current_duration: 50, noise: false, noise_intensity: 0.0,
            noise_method: "additive", synapse: true, syn_weight: 0.05, syn_prob: 1.0, output_type: "both"
        };
    }
    // Merge preset values with defaults to ensure all fields are covered
    setFields({...defaults, ...presetValues});
    document.getElementById('preset-desc').innerText = presetDescriptions[preset] || presetDescriptions['custom'];
    // Update UI based on new values
    showModelFields(document.getElementById('neuron_model').value);
    toggleNoiseOptions();
    toggleSynapseOptions();
}

// Set all form fields from a values object
function setFields(values) {
    const setValue = (name, value) => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            if (el.type === 'checkbox') el.checked = value;
            else el.value = value;
        }
    };
    Object.keys(values).forEach(key => setValue(key, values[key]));
}

// Get all form field values as an object
function getFields() {
    const formData = new FormData(document.getElementById('simForm'));
    const data = {};
    for (let [key, value] of formData.entries()) {
        const el = document.querySelector(`[name="${key}"]`);
        if (el && el.type === 'number') {
            data[key] = parseFloat(value);
        } else if (el && el.type === 'checkbox') {
            data[key] = el.checked;
        } else {
            data[key] = value;
        }
    }
    // Ensure checkboxes that might be missing are included as false
    if (!data.noise) data.noise = false;
    if (!data.synapse) data.synapse = false;
    // Add model params not in form directly
    data.izh_a = parseFloat(document.querySelector('[name="izh_a"]').value);
    data.izh_b = parseFloat(document.querySelector('[name="izh_b"]').value);
    data.izh_c = parseFloat(document.querySelector('[name="izh_c"]').value);
    data.izh_d = parseFloat(document.querySelector('[name="izh_d"]').value);
    data.adex_a = parseFloat(document.querySelector('[name="adex_a"]').value);
    data.adex_b = parseFloat(document.querySelector('[name="adex_b"]').value);
    data.adex_deltaT = parseFloat(document.querySelector('[name="adex_deltaT"]').value);
    data.adex_tau_w = parseFloat(document.querySelector('[name="adex_tau_w"]').value);
    data.custom_eqs = document.querySelector('[name="custom_eqs"]').value;
    data.custom_threshold = document.querySelector('[name="custom_threshold"]').value;
    data.custom_reset = document.querySelector('[name="custom_reset"]').value;
    data.neuron_model = document.getElementById('neuron_model').value;
    
    // Add topology parameters
    data.topology_type = document.getElementById('topology_type').value;
    
    // Always get these values if elements exist
    if (document.getElementById('topology_k')) {
        data.topology_k = parseInt(document.getElementById('topology_k').value);
    }
    if (document.getElementById('topology_p_rewire')) {
        data.topology_p_rewire = parseFloat(document.getElementById('topology_p_rewire').value);
    }
    if (document.getElementById('topology_m')) {
        data.topology_m = parseInt(document.getElementById('topology_m').value);
    }
    if (document.getElementById('topology_k_reg')) {
        data.topology_k_reg = parseInt(document.getElementById('topology_k_reg').value);
    }
    // And other topology parameters...
    
    return data;
}

// Reset all fields to default values
function resetDefaults() {
    setFields(defaults);
    document.getElementById('preset').value = "custom";
    document.getElementById('preset-desc').innerText = presetDescriptions['custom'];
    showModelFields(defaults.neuron_model);
    toggleNoiseOptions();
    toggleSynapseOptions();
    if (window.localStorage) {
        localStorage.removeItem('brian2sim-settings');
    }
}

// Show/hide noise options and enable/disable their fields
function toggleNoiseOptions() {
    const noiseBox = document.getElementById('noise');
    const noiseOptions = document.getElementById('noise-options');
    noiseOptions.style.display = noiseBox.checked ? 'block' : 'none';
    Array.from(noiseOptions.querySelectorAll('input,select')).forEach(el => {
        el.disabled = !noiseBox.checked;
    });
}

// Show/hide synapse options and enable/disable their fields
function toggleSynapseOptions() {
    const synBox = document.getElementById('synapse');
    const synOptions = document.getElementById('synapse-options');
    
    // Check if elements exist to avoid errors
    if (!synBox || !synOptions) return;
    
    // Show/hide based on checkbox state
    synOptions.style.display = synBox.checked ? 'block' : 'none';
    
    // Enable/disable form elements inside
    Array.from(synOptions.querySelectorAll('input, select')).forEach(el => {
        el.disabled = !synBox.checked;
    });
    
    // Also update topology params if visible
    if (synBox.checked) {
        updateTopologyParams();
    }
}

// Show/hide model-specific fields and enable/disable them
function showModelFields(model) {
    const izhFields = document.getElementById('izhikevich-fields');
    const adexFields = document.getElementById('adex-fields');
    const customFields = document.getElementById('custom-fields');
    izhFields.style.display = (model === 'izhikevich') ? 'block' : 'none';
    adexFields.style.display = (model === 'adex') ? 'block' : 'none';
    customFields.style.display = (model === 'custom') ? 'block' : 'none';
    Array.from(izhFields.querySelectorAll('input')).forEach(el => { el.disabled = (model !== 'izhikevich'); });
    Array.from(adexFields.querySelectorAll('input')).forEach(el => { el.disabled = (model !== 'adex'); });
    Array.from(customFields.querySelectorAll('input,textarea')).forEach(el => { el.disabled = (model !== 'custom'); });
    // Show/hide and enable/disable threshold/reset fields
    const thresholdReset = document.getElementById('threshold-reset-fields');
    const thresholdInput = document.getElementById('threshold');
    const resetInput = document.getElementById('reset');
    const help = document.getElementById('threshold-reset-help');
    if (model === 'lif') {
        thresholdReset.style.display = 'block';
        thresholdInput.disabled = false;
        resetInput.disabled = false;
        help.textContent = "Used for LIF only.";
    } else {
        thresholdReset.style.display = 'block';
        thresholdInput.disabled = true;
        resetInput.disabled = true;
        help.textContent = "Ignored for this model.";
    }
    // Update input current help text
    const inputCurrentHelp = document.getElementById('input-current-help');
    if (model === 'adex') {
        inputCurrentHelp.textContent = "Units: pA (picoamperes) for AdEx.";
    } else {
        inputCurrentHelp.textContent = "Units: Arbitrary for LIF/Izhikevich.";
    }
}

// Simple client-side validation for number of neurons and sim time
// Shows alert and prevents submission if invalid
// Hides spinner if validation fails
// (Add more validation as needed)
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('simForm').addEventListener('submit', function(e) {
        let valid = true;
        let msg = [];
        const numNeurons = parseInt(document.querySelector('[name="num_neurons"]').value);
        const simTime = parseFloat(document.querySelector('[name="sim_time"]').value);
        if (isNaN(numNeurons) || numNeurons < 1) {
            valid = false;
            msg.push("Number of neurons must be at least 1.");
        }
        if (isNaN(simTime) || simTime <= 0) {
            valid = false;
            msg.push("Simulation time must be a positive number.");
        }
        if (!valid) {
            e.preventDefault();
            alert("Please fix the following errors:\n- " + msg.join('\n- '));
            document.getElementById('spinner').style.display = 'none';
        }
    });
});

// Accessibility: add focus style for keyboard navigation
// Adds a class when tabbing, removes on mouse click
document.addEventListener('keydown', function(e) {
    if (e.key === "Tab") {
        document.body.classList.add('user-is-tabbing');
    }
});
document.addEventListener('mousedown', function() {
    document.body.classList.remove('user-is-tabbing');
});

// Update topology parameters display based on selected topology type
function updateTopologyParams() {
    const topologyType = document.getElementById('topology_type').value;
    
    // Hide all parameter divs
    document.querySelectorAll('.topology-param').forEach(div => {
        div.style.display = 'none';
    });
    
    // Show appropriate parameters based on selection
    if (topologyType === 'small_world') {
        document.getElementById('small-world-params').style.display = 'block';
        // Make sure we don't reset the value if it's already set
        if (!document.getElementById('topology_p_rewire').value) {
            document.getElementById('topology_p_rewire').value = '0.1';
        }
    } else if (topologyType === 'scale_free') {
        document.getElementById('scale-free-params').style.display = 'block';
    } else if (topologyType === 'regular') {
        document.getElementById('regular-params').style.display = 'block';
    } else if (topologyType === 'modular') {
        document.getElementById('modular-params').style.display = 'block';
    } else {
        // Random is the default
        document.getElementById('random-params').style.display = 'block';
    }
    
    // Save the current state to localStorage if available
    if (window.localStorage) {
        localStorage.setItem('brian2sim-settings', JSON.stringify(getFields()));
    }
}

// Call this at page load to initialize topology parameters correctly
function initializeTopologyParams() {
    // Get the topology type and ensure proper div is shown
    const topologyType = document.getElementById('topology_type').value;
    
    // Hide all parameter divs first
    document.querySelectorAll('.topology-param').forEach(div => {
        div.style.display = 'none';
    });
    
    // Show div appropriate for the current topology
    if (topologyType === 'small_world') {
        document.getElementById('small-world-params').style.display = 'block';
        // Ensure k is even
        let k = parseInt(document.getElementById('topology_k').value);
        if (k % 2 !== 0) {
            document.getElementById('topology_k').value = k + 1;
        }
    } else if (topologyType === 'scale_free') {
        document.getElementById('scale-free-params').style.display = 'block';
    } else if (topologyType === 'regular') {
        document.getElementById('regular-params').style.display = 'block';
    } else if (topologyType === 'modular') {
        document.getElementById('modular-params').style.display = 'block';
    } else {
        // Random is the default
        document.getElementById('random-params').style.display = 'block';
    }
    
    // Add validation on initialization
    if (document.getElementById('topology_k')) {
        ensureEven(document.getElementById('topology_k'));
    }
    if (document.getElementById('topology_k_reg')) {
        ensureEven(document.getElementById('topology_k_reg'));
    }
    if (document.getElementById('topology_p_rewire')) {
        constrainProbability(document.getElementById('topology_p_rewire'));
    }
    if (document.getElementById('topology_p_intra')) {
        constrainProbability(document.getElementById('topology_p_intra'));
    }
    if (document.getElementById('topology_p_inter')) {
        constrainProbability(document.getElementById('topology_p_inter'));
    }
}

// Add this to your document.addEventListener('DOMContentLoaded', function() {...})
document.addEventListener('DOMContentLoaded', function() {
    // Existing code...
    initializeTopologyParams();
});

// Function to collect all current form values
function getSimulationConfig() {
    const config = {};
    
    // Get basic parameters
    config.neuron_model = document.getElementById('neuron_model').value;
    config.threshold = parseFloat(document.getElementById('threshold').value);
    config.reset = parseFloat(document.getElementById('reset').value);
    config.sim_time = parseFloat(document.getElementById('sim_time').value);
    config.input_current = parseFloat(document.getElementById('input_current').value);
    config.num_neurons = parseInt(document.getElementById('num_neurons').value);
    config.current_start = parseFloat(document.getElementById('current_start').value);
    config.current_duration = parseFloat(document.getElementById('current_duration').value);
    
    // Model-specific parameters
    if (config.neuron_model === 'izhikevich') {
        config.izh_a = parseFloat(document.getElementById('izh_a').value);
        config.izh_b = parseFloat(document.getElementById('izh_b').value);
        config.izh_c = parseFloat(document.getElementById('izh_c').value);
        config.izh_d = parseFloat(document.getElementById('izh_d').value);
    } else if (config.neuron_model === 'adex') {
        config.adex_a = parseFloat(document.getElementById('adex_a').value);
        config.adex_b = parseFloat(document.getElementById('adex_b').value);
        config.adex_deltaT = parseFloat(document.getElementById('adex_deltaT').value);
        config.adex_tau_w = parseFloat(document.getElementById('adex_tau_w').value);
    } else if (config.neuron_model === 'custom') {
        config.custom_eqs = document.getElementById('custom_eqs').value;
        config.custom_threshold = document.getElementById('custom_threshold').value;
        config.custom_reset = document.getElementById('custom_reset').value;
    }
    
    // Noise settings
    config.noise_enabled = document.getElementById('noise').checked;
    if (config.noise_enabled) {
        config.noise_intensity = parseFloat(document.getElementById('noise_intensity').value);
        config.noise_method = document.getElementById('noise_method').value;
    }
    
    // Synapse settings
    config.synapse_enabled = document.getElementById('synapse').checked;
    if (config.synapse_enabled) {
        config.syn_weight = parseFloat(document.getElementById('syn_weight').value);
        config.syn_prob = parseFloat(document.getElementById('syn_prob').value);
        
        // Topology settings
        config.topology_type = document.getElementById('topology_type').value;
        if (config.topology_type === 'small_world') {
            config.topology_k = parseInt(document.getElementById('topology_k').value);
            config.topology_p_rewire = parseFloat(document.getElementById('topology_p_rewire').value);
        } else if (config.topology_type === 'scale_free') {
            config.topology_m = parseInt(document.getElementById('topology_m').value);
        } else if (config.topology_type === 'regular') {
            config.topology_k_reg = parseInt(document.getElementById('topology_k_reg').value);
        } else if (config.topology_type === 'modular') {
            config.topology_n_modules = parseInt(document.getElementById('topology_n_modules').value);
            config.topology_p_intra = parseFloat(document.getElementById('topology_p_intra').value);
            config.topology_p_inter = parseFloat(document.getElementById('topology_p_inter').value);
        }
    }
    
    // Output settings
    config.output_type = document.getElementById('output_type').value;
    config.plot_type = document.getElementById('plot_type').value;
    
    // Add timestamp and name
    config.created = new Date().toISOString();
    config.name = `Brian2 Sim Config (${config.neuron_model}) - ${new Date().toLocaleString()}`;
    
    return config;
}

// Function to set form values from configuration
function setSimulationConfig(config) {
    // Set neuron model first (this will show/hide relevant fields)
    document.getElementById('neuron_model').value = config.neuron_model;
    showModelFields(config.neuron_model);
    
    // Set basic parameters
    document.getElementById('threshold').value = config.threshold;
    document.getElementById('reset').value = config.reset;
    document.getElementById('sim_time').value = config.sim_time;
    document.getElementById('input_current').value = config.input_current;
    document.getElementById('num_neurons').value = config.num_neurons;
    document.getElementById('current_start').value = config.current_start;
    document.getElementById('current_duration').value = config.current_duration;
    
    // Model-specific parameters
    if (config.neuron_model === 'izhikevich') {
        document.getElementById('izh_a').value = config.izh_a;
        document.getElementById('izh_b').value = config.izh_b;
        document.getElementById('izh_c').value = config.izh_c;
        document.getElementById('izh_d').value = config.izh_d;
    } else if (config.neuron_model === 'adex') {
        document.getElementById('adex_a').value = config.adex_a;
        document.getElementById('adex_b').value = config.adex_b;
        document.getElementById('adex_deltaT').value = config.adex_deltaT;
        document.getElementById('adex_tau_w').value = config.adex_tau_w;
    } else if (config.neuron_model === 'custom') {
        document.getElementById('custom_eqs').value = config.custom_eqs;
        document.getElementById('custom_threshold').value = config.custom_threshold;
        document.getElementById('custom_reset').value = config.custom_reset;
    }
    
    // Noise settings
    document.getElementById('noise').checked = config.noise_enabled;
    toggleNoiseOptions();  // Update display
    if (config.noise_enabled) {
        document.getElementById('noise_intensity').value = config.noise_intensity;
        document.getElementById('noise_method').value = config.noise_method;
    }
    
    // Synapse settings
    document.getElementById('synapse').checked = config.synapse_enabled;
    toggleSynapseOptions();  // Update display
    if (config.synapse_enabled) {
        document.getElementById('syn_weight').value = config.syn_weight;
        document.getElementById('syn_prob').value = config.syn_prob;
        
        // Topology settings
        document.getElementById('topology_type').value = config.topology_type || 'random';
        updateTopologyParams();

// Set parameter values based on topology type
if (config.topology_type === 'small_world') {
    document.getElementById('topology_k').value = config.topology_k;
    document.getElementById('topology_p_rewire').value = config.topology_p_rewire;
} else if (config.topology_type === 'scale_free') {
    document.getElementById('topology_m').value = config.topology_m;
} else if (config.topology_type === 'regular') {
    document.getElementById('topology_k_reg').value = config.topology_k_reg;
} else if (config.topology_type === 'modular') {
    document.getElementById('topology_n_modules').value = config.topology_n_modules;
    document.getElementById('topology_p_intra').value = config.topology_p_intra;
    document.getElementById('topology_p_inter').value = config.topology_p_inter;
} else {
    // Random topology
    document.getElementById('syn_prob').value = config.syn_prob;
}
    }
    
    // Output settings
    document.getElementById('output_type').value = config.output_type;
    document.getElementById('plot_type').value = config.plot_type;
}

// Export configuration as JSON file download
function exportConfiguration() {
    const config = getSimulationConfig();
    const configJson = JSON.stringify(config, null, 2);
    const blob = new Blob([configJson], {type: 'application/json'});
    
    const filename = config.name.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.json';
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Import configuration from JSON file
function importConfiguration() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const config = JSON.parse(e.target.result);
                setSimulationConfig(config);
                alert(`Configuration "${config.name}" loaded successfully!`);
            } catch (error) {
                alert('Error loading configuration: ' + error.message);
            }
        };
        reader.readAsText(file);
    };
    
    input.click();
}

function prepareCodeGeneration() {
  // Changed to match your form ID in HTML
  const mainForm = document.getElementById('simForm');
  const codeForm = document.getElementById('codeGenForm');
  const hiddenInputs = document.getElementById('hiddenInputs');
  
  hiddenInputs.innerHTML = '';
  
  // Copy all inputs from main form
  const inputs = mainForm.querySelectorAll('input, select, textarea');
  inputs.forEach(input => {
    if (input.name) {
      if (input.type === 'checkbox' || input.type === 'radio') {
        if (input.checked) {
          const hidden = document.createElement('input');
          hidden.type = 'hidden';
          hidden.name = input.name;
          hidden.value = input.value || 'on';
          hiddenInputs.appendChild(hidden);
        }
      } else {
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = input.name;
        hidden.value = input.value;
        hiddenInputs.appendChild(hidden);
      }
    }
  });
  
  // Submit the form
  codeForm.submit();
}

function saveConfigToServer() {
  const config = getSimulationConfig();
  
  fetch('/api/config', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Show success message
      alert(`Configuration saved! ID: ${data.config_id}`);
      
      // Optional: Copy to clipboard for sharing
      navigator.clipboard.writeText(window.location.origin + '/load/' + data.config_id);
    } else {
      alert('Error saving configuration: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error saving configuration');
  });
}

function loadConfigFromServer(configId) {
    if (!configId.trim()) {
        alert('Please enter a configuration ID.');
        return;
    }
    
    fetch(`/api/config/${configId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (data.validation_errors) {
                    alert('Configuration validation failed:\n' + data.validation_errors.join('\n'));
                } else {
                    alert('Error loading configuration: ' + data.error);
                }
            } else {
                // Remove metadata before setting form
                const {_loaded_at, _validation_status, ...cleanConfig} = data;
                setSimulationConfig(cleanConfig);
                alert('Configuration loaded successfully!');
                
                // Save to localStorage as well
                if (window.localStorage) {
                    localStorage.setItem('brian2sim-settings', JSON.stringify(getFields()));
                }
            }
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            alert('Failed to load configuration from server.');
        });
}

// Add this function to ensure even values for k
function ensureEven(input) {
    let value = parseInt(input.value);
    if (isNaN(value)) value = 2;  // Default
    if (value % 2 !== 0) {
        value += 1;  // Make it even
    }
    input.value = value;
}

// Add this function to constrain probability values
function constrainProbability(input) {
    let value = parseFloat(input.value);
    if (isNaN(value)) {
        // Only reset to default if the value is truly invalid
        if (input.id === 'topology_p_rewire') {
            value = 0.1;  // Default for rewiring probability
        } else if (input.id === 'topology_p_intra') {
            value = 0.2;  // Default for intra-module
        } else if (input.id === 'topology_p_inter') {
            value = 0.01; // Default for inter-module
        } else {
            value = 0.2;  // General default
        }
    }
    
    // Allow 0.0 as a valid value - don't reset it!
    value = Math.max(0.0, Math.min(1.0, value));
    input.value = value.toFixed(3);  // Use 3 decimals to allow 0.000
}

// Update your form submission handler
document.querySelector('form').addEventListener('submit', function(e) {
    const topology = document.getElementById('topology_type').value;
    
    // If not using random topology, set to default instead of clearing
    if (topology !== 'random') {
        document.getElementById('syn_prob').value = '0.2';  // Set to default value
    }
});