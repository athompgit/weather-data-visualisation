# Weather Data Visualisation

This app provides an interactive way to explore historical weather data for various locations. Users can search for locations, select a date range, and view weather trends over time.

**Status:** Full functionality is still in progress.

## Prerequisites (macOS)

Before you begin, ensure you have the required tools installed. These instructions assume you are using macOS.

1.  **Check for Homebrew:** Homebrew is a package manager for macOS that simplifies installing software. Open your Terminal and run:
    ```bash
    brew --version
    ```
    If not installed, install it by running the command found on the [official Homebrew website](https://brew.sh/):
    ```bash
    /bin/bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"
    ```

2.  **Check for Python 3:** This application requires Python 3. Check if it's installed:
    ```bash
    python3 --version
    ```
    If it's not installed or you need a specific version, you can install it using Homebrew:
    ```bash
    brew install python3
    ```

3.  **Check for Git:** Git is needed to download (clone) the project code. Check if it's installed:
    ```bash
    git --version
    ```
    If not installed, you can install it via Homebrew (`brew install git`) or download it from the [official Git website](https://git-scm.com/downloads).

## Installation & Setup

Follow these steps in your Terminal to download and set up the application:

1.  **Clone the Repository:** Download the project code from GitHub.
    ```bash
    git clone [https://github.com/athompgit/weather-data-visualisation.git](https://github.com/athompgit/weather-data-visualisation.git)
    ```

2.  **Navigate into Project Directory:** Change your terminal's location to the newly downloaded folder.
    ```bash
    cd weather-data-visualisation
    ```

3.  **Create a Virtual Environment:** This creates an isolated space for the Python packages this project needs, preventing conflicts with other projects.
    ```bash
    python3 -m venv .venv
    ```
    *(This creates a hidden folder named `.venv`)*

4.  **Activate the Virtual Environment:** Before installing packages or running the app, you need to activate this environment.
    ```bash
    source .venv/bin/activate
    ```
    *(Your terminal prompt should now show `(.venv)` at the beginning)*. You'll need to run this activation command every time you open a new terminal window to work on this project.

5.  **Install Dependencies:** Upgrade `pip` (Python's package installer) and install all the required libraries listed in the `requirements.txt` file.
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

## Running the Application

Ensure your virtual environment is still activated (you see `(.venv)` in your terminal prompt). Then, run the main application script:

```bash
python3 main.py
