# Brian2 Simulation Web App

This web application allows users to interact with and run Brian2 neural simulations through a simple, intuitive GUI. Users can configure simulation parameters, visualize membrane potential and spike raster plots, and download simulation data in CSV and JSON formats.

## Features

- **Customizable Simulation Parameters**: Adjust threshold, reset potential, simulation time, input current, and more.
- **Neuron Configuration**: Set the number of neurons and configure current injection timing.
- **Noise Options**: Add noise with either additive or multiplicative methods.
- **Synaptic Interactions**: Enable synapses with customizable synaptic weight and connection probability.
- **Plot Outputs**: Visualize membrane potential over time and spike raster plots.
- **Download Data**: Export simulation data in CSV and JSON formats.

## Technologies Used

- **Flask**: Backend framework for handling requests and rendering templates.
- **Brian2**: The neural simulation engine for modeling spiking neural networks.
- **Matplotlib**: For plotting membrane potential and spike raster graphs.
- **Pandas**: For handling and exporting simulation data in CSV format.
- **HTML/CSS/JavaScript**: For the frontend interface and dynamic interactions.

## Installation

To run the project locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/metanome/brian2-simulation-webapp.git
   cd brian2-simulation-webapp
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage

1. **Preset Selection**: Choose a preset for quick configuration or manually input the parameters.
2. **Simulation Parameters**: Customize the simulation by adjusting parameters like threshold, reset potential, simulation time, and input current.
3. **Noise Settings**: Optionally add noise with adjustable intensity and method (additive or multiplicative).
4. **Synaptic Interactions**: Enable synapses and set their weight and connection probability.
5. **Run Simulation**: After configuring the simulation, click the "Run Simulation" button to generate the plots and download data.
6. **View and Download Results**: Once the simulation is complete, you can view the generated plots and download the data in CSV or JSON format.

## Future Features

- **Interactive Visualizations with Plotly**: Add interactive, dynamic plots for a more engaging user experience.
- **Live Plot Option**: Implement real-time updates of the plots using JavaScript refresh techniques.
- **Additional Presets**: Include more presets for different neuron models and configurations.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
