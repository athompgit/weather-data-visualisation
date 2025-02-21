# weather-data-visualisation

#This app provides an interactive way to explore historical temperature data for various locations. Users can search for locations, select a date range, and view temperature trends over time.  

#Clone respository:
```bash
   git clone [https://github.com/](https://github.com/)athompgit/weather-data-visualisation.git

#Activate Virtual Environment:
cat create-venv.sh
#!/bin/bash

if [[ ! -d storage-valuer-venv ]]
then
  python3 -m venv storage-valuer-venv
  ./storage-valuer-venv/bin/python -m pip install --upgrade pip
fi

source storage-valuer-venv/bin/activate

#Install requirements.txt
python3 -m pip install -r requirements.txt

#Run the app
python3 main.py

#Full functionality still in progress

#Functions & Usage will include:
#Location search & select with dropdown and LineEdit
#Display live and historical data
#Date range picker
#Interactive graphs


