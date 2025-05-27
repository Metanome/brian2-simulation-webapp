# Brian2 Web Simulation App

A web-based interactive simulator for spiking neural networks using [Brian2](https://brian2.readthedocs.io/) and Flask.
Users can configure neuron and network parameters, run simulations, visualize results, and download data.

## Goal
The main goal of this project is to make neural modeling and simulation with Brian2 accessible and user-friendly, lowering the barrier for learning, teaching, and rapid prototyping in computational neuroscience.

## Features

### 🧠 **Neuron Models**
- **LIF (Leaky Integrate-and-Fire):** Classic computational neuron model
- **Izhikevich:** Biologically realistic with various firing patterns  
- **AdEx (Adaptive Exponential):** Advanced model with adaptation currents
- **Custom:** Write your own differential equations, threshold, and reset rules

### 🕸️ **Network Topologies**
- **Random (Erdős–Rényi):** Basic random connectivity patterns
- **Small World (Watts-Strogatz):** Local clustering with long-range shortcuts
- **Scale-Free (Barabási–Albert):** Hub-based networks with power-law degree distribution
- **Regular Lattice:** Structured ring networks with uniform connectivity
- **Modular:** Community-based networks with intra/inter-module connectivity

### 📊 **Visualization Options**
- **Interactive plots (Plotly):** Zoomable, pannable visualizations
- **Static plots (Matplotlib):** Publication-ready figures
- **Network topology visualization:** See the actual connectivity structure
- **Multiple output types:** Voltage traces, spike rasters, and network graphs

### ⚙️ **Advanced Features**
- **Preset scenarios:** Quick-start configurations for common network types
- **Parameter validation:** Real-time input checking with helpful error messages
- **Configuration management:** Save/load simulation setups with validation
- **Data export:** CSV and JSON formats for further analysis
- **Code generation:** Automatically generate Brian2 Python scripts
- **Responsive UI:** Modern, accessible, and mobile-friendly design
- **Automatic cleanup:** Old output files are automatically deleted to save disk space
- **Memory management:** Smart cache cleanup prevents memory buildup

## Requirements

- Python 3.8+
- [Brian2](https://brian2.readthedocs.io/)
- Flask
- matplotlib
- pandas
- numpy
- plotly
- networkx

All dependencies are listed in `requirements.txt`.

## Installation & Usage

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Metanome/brian2sim-web.git
    cd brian2sim-web
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the app:**
    ```bash
    python app.py
    ```

4. **Open your browser:**
   Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

5. **Configure and run simulations:**
   - Adjust parameters or select a preset in the left panel
   - Choose your desired network topology and connection parameters
   - Select neuron model (LIF, Izhikevich, AdEx, or custom)
   - Click "Run Simulation" to see plots and download data
   - Use output options to switch between interactive and static plots

## Demo Screenshots
![Screenshot1](https://github.com/user-attachments/assets/e7729d8d-6ca5-44c1-abef-70f7b3cf7b17)
![Screenshot2](https://github.com/user-attachments/assets/44af23f9-4713-40e0-a12b-628e64dfda7d)

## File Structure

```
brian2sim-web/
├── app.py                 # Main Flask application and routes
├── simulator.py           # Core Brian2 simulation logic
├── topology.py            # NetworkX-based network topology generation
├── plotting.py            # Visualization utilities (Matplotlib & Plotly)
├── models.py              # Neuron model definitions
├── code_generator.py      # Python code generation utilities
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main UI template
├── static/
│   ├── css/
│   │   └── style.css     # Responsive UI styling
│   └── js/
│       └── main.js       # Frontend logic and interactions
└── output/               # Auto-cleaned simulation results
```

## Configuration Management

The app includes robust configuration management:

- **Save configurations:** Export your simulation setups as JSON
- **Load configurations:** Import previously saved setups with validation
- **Local storage:** Browser remembers your settings between sessions
- **Validation:** Configurations are validated before loading to prevent errors

## Educational Applications

Perfect for:
- **Teaching computational neuroscience:** Students explore concepts without coding
- **Research prototyping:** Quickly test network hypotheses
- **Learning network theory:** Visualize how topologies affect neural dynamics
- **Parameter exploration:** Understand relationships between parameters and behavior

## Technical Notes

- **Memory management:** Automatic Brian2 cache cleanup prevents memory buildup
- **Temporary files:** Plots and data are auto-cleaned after 3 minutes
- **Input validation:** Comprehensive error checking with user-friendly messages
- **Mobile responsive:** Optimized for tablets and mobile devices

## Known Issues

- Large simulations (many neurons or long durations) may take significant time to run
- Very dense networks with many neurons may impact browser performance for interactive plots
- Custom equations require basic knowledge of Brian2 syntax

## Future Features

- **Additional neuron models:** Hodgkin-Huxley, Morris-Lecar, and more
- **Live Plot Option**: Implement real-time updates of the plots using JavaScript refresh techniques.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- New neuron models
- Additional network topologies
- UI/UX improvements
- Documentation enhancements

## License

This project is licensed under the GNU General Public License v3.0.

See [LICENSE](https://github.com/Metanome/brian2sim-web/blob/main/LICENSE) for details.

## Acknowledgments

- [Brian2](https://brian2.readthedocs.io/) for the powerful simulation engine
- [NetworkX](https://networkx.org/) for graph theory and network analysis
- [Flask](https://flask.palletsprojects.com/) for the lightweight web framework
- [Plotly](https://plotly.com/python/) for interactive plotting capabilities
- [Matplotlib](https://matplotlib.org/) for publication-quality static plots

## Citation

If you use this software in your research, please cite:

```bibtex
@software{brian2sim_web,
  title={Brian2 Web Simulation App},
  author={Metanome},
  year={2025},
  url={https://github.com/Metanome/brian2sim-web},
  license={GPL-3.0}
}
```
