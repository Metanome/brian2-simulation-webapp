# Brian2 Web Simulation App

A web-based interactive simulator for spiking neural networks using [Brian2](https://brian2.readthedocs.io/) and Flask.  
Users can configure neuron and network parameters, run simulations, visualize results, and download data.

## Features

- **Leaky Integrate-and-Fire (LIF) Neuron Simulation:**  
  Simulate customizable networks of LIF neurons with adjustable parameters.
- **Interactive Web Interface:**  
  User-friendly form for setting thresholds, reset values, simulation time, input current, noise, synaptic weights, and more.
- **Presets:**  
  Quickly load common network configurations for demonstration or exploration.
- **Visualization:**  
  - Membrane potential plots for each neuron  
  - Spike raster plots for network activity
- **Data Export:**  
  Download simulation results as CSV or JSON for further analysis.
- **Automatic Cleanup:**  
  Old output files are automatically deleted to save disk space.

## Usage

1. **Install dependencies:**

    ```bash
    pip install flask brian2 matplotlib pandas numpy
    ```

2. **Clone the repository:**

    ```bash
    git clone https://github.com/Metanome/brian2sim-web.git
    cd brian2sim-web
    ```

3. **Run the app:**

    ```bash
    python app.py
    ```

4. **Open your browser:**  
   Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

5. **Configure and run simulations:**  
   - Adjust parameters or select a preset.
   - Click "Run Simulation" to see plots and download data.

## Known Issues

- Large simulations (many neurons or long durations) may take significant time to run and could cause the web interface to become unresponsive.
- No progress bar or feedback for long-running simulations.
- No persistent storage: all output files are deleted after 10 minutes.
- Error messages may be generic for some simulation failures.

## Future Features

- Asynchronous/background simulation execution for better responsiveness.
- Progress bar or loading indicator for long simulations.
- More neuron models and network presets.
- Improved error handling and user feedback.
- **Interactive Visualizations with Plotly**: Add interactive, dynamic plots for a more engaging user experience.
- **Live Plot Option**: Implement real-time updates of the plots using JavaScript refresh techniques.

## License

This project is licensed under the GNU General Public License v3.0.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) for details.

## Acknowledgments

- [Brian2](https://brian2.readthedocs.io/) for the simulation engine
- [Flask](https://flask.palletsprojects.com/) for the web framework

*Developed by @Metanome*
