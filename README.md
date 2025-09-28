# Digital CO2 Footprint – Streamlit App

## Project Overview

The Digital CO2 Footprint application is a Streamlit-based tool designed to calculate the carbon footprint associated with digital activities, such as video streaming. It provides insights for both consumers and producers by estimating CO2 emissions based on user-defined assumptions. The app also offers equivalence metrics, such as the number of electric vehicle kilometers or meatless meals required to offset the emissions.

Model, values and calculations by Le Réveilleur.
Implementation in a streamlit app by EvoSapiens.

### Key Features
- **Customizable Assumptions**: Modify default values for device usage, video resolution, network type, and more.
- **Equivalence Calculations**: Convert CO2 emissions into relatable metrics like EV kilometers or meatless meals.
- **Language Support**: Switch between English and French in the app sidebar.
- **Detailed Insights**: View intermediate calculations and assumptions used in the CO2 footprint estimation.
- **Live Updates**: Adjust assumptions in real-time and see the impact immediately.

## Quick Start (Poetry)

### Prerequisites
- Python 3.12
- Poetry package manager

### Installation

1. Ensure Poetry is installed.

2. Create/select the Python 3.12 virtual environment and install dependencies:

   ```bash
   poetry env use 3.12
   poetry install --no-root
   ```

### Running the App

1. Start the Streamlit application:

   ```bash
   poetry run streamlit run src/app.py
   ```

2. The app should load automatically in your browser.

## Editing Assumptions

- Default values are stored in `src/assumptions.yaml`.
- Modify values directly in the file or adjust them live in the app sidebar.

## Project Structure

- **`src/app.py`**: Entry point for the Streamlit app.
- **`src/calculator.py`**: Core logic for CO2 calculations and equivalence metrics.
- **`src/loader.py`**: Loads assumptions from the YAML configuration file.
- **`src/translations.py`**: Handles language support and translations.
- **`src/assumptions.yaml`**: Contains default assumptions and data values.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
