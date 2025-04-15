from flask import Flask, request, send_file, render_template
from brian2 import *
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Simulation setup
def setup_brian_sim(threshold=1.0, reset=0.0, sim_time=100.0):
    start_scope()
    prefs.codegen.target = 'numpy'  # Use numpy to avoid C++ dependency

    eqs = 'dv/dt = -v / (10*ms) : 1'
    G = NeuronGroup(1, eqs, threshold=f'v > {threshold}',
                   reset=f'v = {reset}', method='exact')
    G.v = 1

    M = StateMonitor(G, 'v', record=True)
    run(sim_time * ms)

    return M

# Plotting the result
def plot_simulation(M):
    plt.figure(figsize=(10, 4))
    plt.plot(M.t/ms, M.v[0])
    plt.xlabel('Time (ms)')
    plt.ylabel('Membrane potential (v)')
    plt.title('Brian2 Simulation')
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    threshold = float(request.form.get('threshold', 1.0))
    reset = float(request.form.get('reset', 0.0))
    sim_time = float(request.form.get('sim_time', 100.0))

    M = setup_brian_sim(threshold, reset, sim_time)
    image = plot_simulation(M)

    with open('static/sim_result.png', 'wb') as f:
        f.write(image.read())
        image.seek(0)

    return render_template('index.html', img_url='/static/sim_result.png',
                           threshold=threshold, reset=reset, sim_time=sim_time)

if __name__ == '__main__':
    app.run(debug=True)
