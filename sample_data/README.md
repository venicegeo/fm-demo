# sampe_data


# Data Source
The Starbucks data was sourced from: `https://opendata.socrata.com/Business/All-Starbucks-Locations-in-the-World/xy4y-c4mk`.

## Config
Open the config.groovy file and supply your fulcrum email and password.


## Initialize Fulcrum data
1. Go to `https://web.fulcrumapp.com`, sign in and create an app called "Starbucks".
2. Create a form for the app with various text fields for the data.
3. Import the data from the `starbucks_locations.csv` file. 
4. `cd fulcrum`.
5. `grails run-app`.
6. Go to `http://localhost:8080/fulcrum/home`.
7. Use the form to upload all the images from the `./images` folder. 
8. The form will randomly assign two images to each record in the data set. Due to Fulcrum throttling, this will take over 10 hours. 
