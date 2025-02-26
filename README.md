# weather-data-visualisation

#This app provides an interactive way to explore historical weather data for various locations. Users can search for locations, select a date range, and view weather trends over time.  

#Instructions on downloading and running weather app

#Copy this shell script(code view) into your Terminal(MacOS)

#!/bin/bash
if ! command -v brew &>/dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
if ! command -v python3 &>/dev/null; then
    brew install python3
fi
wdvApp_url="https://github.com/athompgit/weather-data-visualisation.git"
git clone "$wdvApp_url"
wdvApp=$(basename "$wdvApp_url" .git)
cd "$wdvApp"
python3 -m venv .venv
source .venv/bin/activate 
pip install --upgrade pip
pip install -r requirements.txt
python3 main.py



#Full functionality still in progress

#Functions & Usage will include:
#Location search & select with dropdown and LineEdit
#Display live and historical data
#Date range picker
#Interactive graphs


