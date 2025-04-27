# Brian2 Web Simulation App

A web-based interactive simulator for spiking neural networks using [Brian2](https://brian2.readthedocs.io/) and Flask.
Users can configure neuron and network parameters, run simulations, visualize results, and download data.

## Goal
The main goal of this project is to make neural modeling and simulation with Brian2 accessible and user-friendly, lowering the barrier for learning, teaching, and rapid prototyping in neuroscience.

## Features

- **Multiple neuron models:** LIF, Izhikevich, AdEx, and custom equations.
- **Network options:** Synaptic weights, connection probability, noise, and more.
- **Presets:** Quick-start scenarios for common network types (selectable in the UI).
- **Interactive and static plots:** View results with Plotly or Matplotlib.
- **Download data:** Export simulation results as CSV or JSON.
- **Responsive UI:** Modern, accessible, and mobile-friendly.
- **Automatic Cleanup:** Old output files are automatically deleted from the `output/` folder to save disk space.

## Requirements

- Python 3.8+
- [Brian2](https://brian2.readthedocs.io/)
- Flask
- matplotlib
- pandas
- numpy
- plotly

All dependencies are listed in `requirements.txt`.

## Usage

1. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
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
   - Adjust parameters or select a preset in the left panel.
   - Click "Run Simulation" to see plots and download data.
   - Use output options below the results to change plot type or output.

## Demo Screenshots
![Screenshot1](https://github.com/user-attachments/assets/e7729d8d-6ca5-44c1-abef-70f7b3cf7b17)
![Screenshot2](https://github.com/user-attachments/assets/44af23f9-4713-40e0-a12b-628e64dfda7d)


## File Structure

- `app.py` — Main Flask application and simulation logic.
- `requirements.txt` — Python dependencies.
- `templates/` — Jinja2 HTML templates (main UI in `index.html`).
- `static/` — Static files (CSS in `css/style.css`, JS in `js/main.js`).
- `output/` — Folder for generated plots and data files (auto-cleaned).
- `models/` — Neuron model definitions (LIF, Izhikevich, AdEx, custom).
- `plots/` — Plotting utilities.
- `simulator/` — Simulation logic and helpers.
- `utils/` — Export and utility functions.

## Notes

- **Temporary files** (plots/data) are auto-cleaned from `output/` after ~3 minutes.
- **Custom models:** You can enter your own equations, threshold, and reset rules.
- **Accessibility:** Tooltips and ARIA live regions are included for usability.

## Known Issues

- Large simulations (many neurons or long durations) may take significant time to run and could cause the web interface to become unresponsive.
- Error messages may be generic for some simulation failures.

## Future Features

- Progress bar or loading indicator for long simulations.
- More neuron models and network presets.
- Improved error handling and user feedback.
- **Live Plot Option**: Implement real-time updates of the plots using JavaScript refresh techniques.

## License

This project is licensed under the GNU General Public License v3.0.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) for details.

## Acknowledgments

- [Brian2](https://brian2.readthedocs.io/) for the simulation engine
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Plotly](https://plotly.com/python/) for interactive plotting

*Developed by @Metanome*
