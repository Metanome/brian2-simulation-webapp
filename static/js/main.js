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
    custom_eqs: "", custom_threshold: "", custom_reset: ""
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
    synOptions.style.display = synBox.checked ? 'block' : 'none';
    Array.from(synOptions.querySelectorAll('input,select')).forEach(el => {
        el.disabled = !synBox.checked;
    });
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