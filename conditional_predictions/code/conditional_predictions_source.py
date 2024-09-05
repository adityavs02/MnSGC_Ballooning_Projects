# Library with excel-based commands
import csv

# Library with bulit-in math functions
import math

# Class used to reduce the query time from NOAA (National Oceanic and Atmospheric Administration)
from reduce_query_time import ExtendedForecast

# Python extension of the Proj library, which allows for conversion between different coordinate systems
from pyproj import Transformer

# Library that makes kml functions simpler
import simplekml

# Specify where the csv and kml files for the prediction should be saved
location = '/Users/MNSGC-5/Downloads/'

# Set iniital latitude and longitude
lat = 44.1388
long = -93.9975

# Set initial altitude (m), ascent rate (m/s), descent rate (m/s), and final altitude (m)
altitude = 300
ascent_rate = 5
descent_rate = 7 # Assumed to be the descent rate at sea level
final_altitude = 30000

# Set initial datetime (in UTC)
minutes = 00
hours = 15
date = 25
year = "202308"

# List created to store different data sets as a csv file
full_data = []

# List created to store only lat-long data sets
lat_long_only = []

# Booleans to start and end the condition for the prediction
start_condition = False
end_condition = False

# Method to generate a excel list of all datetimes, latitudes, longitudes, and altitudes in a prediction --Called prediction_data
def create_csv_file(datetime, lat, long, altitude):
        # Opens the predicition data csv file and initializes the header and the list of data that needs to be added
    with open(location + 'prediction_data.csv', 'w', newline = '') as f:
        header = ['datetime', 'latitude', 'longitude', 'altitude']
        data = [datetime, lat, long, altitude]

        # create the csv writer
        writer = csv.writer(f)

        # write a row to the csv file
        full_data.append(data)
        writer.writerow(header)
        writer.writerows(full_data)

# Methods to return the path condition values --Easier for readability
def constant_float_condition(duration_val, altitude_val):
    return duration_val, altitude_val

def gps_fence_condition(lat_val_s, long_val_s, lat_val_e, long_val_e):
    return lat_val_s, long_val_s, lat_val_e, long_val_e

def real_time_condition(real_time):
    return real_time

# Method to convert between coordinate systems
def convert_coordinate_systems(start_system, end_system, x_position, y_position):
    # Creates transformer object from pyproj library
    transformer = Transformer.from_crs(start_system, end_system)

    # Stores transformed coordinates in variable 'new_coordinates'
    new_coordinates = transformer.transform(x_position, y_position)

    # Assigns x and y to the first second indexes of new_coordinates, respectively
    new_x = new_coordinates[0]
    new_y = new_coordinates[1]

    return new_x, new_y  

# Uses NASA's Earth Atmosphere Model for determining the density at specific altitudes to calculate the descent rate
def get_descent_rate(altitude):
    temp, pressure = 0, 0
    
    if altitude > 25000:
        temp = -131.21 + (0.00299 * altitude)
        pressure = 2.488 * pow((temp + 273.1) / 216.6, -11.388)

    if altitude <= 25000 and altitude > 11000:
        temp = -56.46
        pressure = 22.65 * math.exp(1.73 - (0.000157 * altitude))
    if altitude <= 11000:
        temp = 15.04 - (0.00649 * altitude)
        pressure = 101.29 * pow((temp + 273.1) / 288.08, 5.256)

    density = pressure / (0.2869 * (temp + 273.1))

    return (descent_rate * 60 * 1.1045) / (math.sqrt(density))

# Creating the kml file --Its name is 'map_kml'
def create_kml(list, file_name):
    with open(location + file_name, 'w', newline = '') as k:
        map_kml = simplekml.Kml()

        map = map_kml.newlinestring(name = 'Path', description = "Path", coords = list)

        map.style.linestyle.color = simplekml.Color.black
        map.style.linestyle.width = 5

    map_kml_path = location + file_name
    map_kml.save(map_kml_path)

# Converts initial latitude and longitude from WGS84 to the US State Plane
state_start_lat, state_start_long = convert_coordinate_systems(4326, 26993, lat, long)  

# Initializes a forecast object from the 'getgfs' library with resolution at 0p25
forecast = ExtendedForecast(resolution ='0p25', timestep ='1hr')

# Through this condition, the balloon's ascent breaks when it has reached the float altitude (m) --it breaks for the lenght of the float duration (min)
# The float duration and float altitudes must have values since they are part of the CONSTANT Condition
float_duration, float_altitude = constant_float_condition(0, 24000)

# A GPS Fence is made from and input of 2 lat and 2 long values to create a boundary around the path of the balloon
# When the balloon reaches any of the edges of this fence, its descent path is immediately started
# Set values if this condition is being used, else set as False
gps_lat_up, gps_long_left, gps_lat_down, gps_long_right = gps_fence_condition(44.53, -94.5, 44.32, -93.3)

# When the balloon path time becomes equal to this value, its descent path is immediately started
# Set values if this condition is being used, else set as False
real_time_val = real_time_condition(False)

# Leave these booleans alone --They are for determining if the gps fence or real time conditions are being met
gps_fence = True
real_time = True

while altitude >= 0:
    # Creates variable 'datetime' to be manipulated by the hours and minutes
    if minutes < 10:
        datetime = year + str(date) + " " + str(hours) + ":0" + str(minutes)
        time = str(hours) + ":0" + str(minutes)
    else:
        datetime = year + str(date) + " " + str(hours) + ":" + str(minutes)
        time = str(hours) + ":" + str(minutes)  

    print(datetime)
    print(altitude)
    print(lat, long)
    print()

    create_csv_file(datetime, lat, long, altitude)

    lat_long_only.append((long, lat))

    # Returns the u- and v-components of wind in meters per second
    u_component, v_component = forecast.get_windprofile(datetime, lat, long)

    # Converts u- and v-components to meters per minute
    u_to_min = u_component(altitude) * 60
    v_to_min = v_component(altitude) * 60

    # Adds the change in direction to the latitude and longitude in the US State Plane
    state_start_lat += u_to_min
    state_start_long += v_to_min

    # Converts the new latitude and longitude from the US State Plane to WGS84
    lat, long = convert_coordinate_systems(26993, 4326, state_start_lat, state_start_long)

    # For if there is a gps fence condition:
    if gps_fence == True:
        # 0.01 is the max difference the lat or long can have with the gps fence
        if abs(lat - gps_lat_up) <= 0.01 or abs(long - gps_long_left) <= 0.01 or abs(lat - gps_lat_down) <= 0.01 or abs(long - gps_long_right) <= 0.01:
            gps_fence = False

    # For if there is a real time condition:
    if real_time == True and time == real_time_val:
        real_time = False

    # The CONSTANT Condition --> This toggles between ascent, float, and descent states based on set parameters
    if altitude < float_altitude and gps_fence == True and real_time == True:
        altitude += (ascent_rate * 60)
        if altitude > float_altitude:
            altitude = float_altitude
    elif float_duration >= 0 and end_condition == False and gps_fence == True and real_time == True:
        start_condition = True
    else:
        float_altitude = -1 # Sets the float altitude to an impossible amount for the first condition to run
        altitude -= get_descent_rate(altitude)

    if start_condition == True and gps_fence == True and real_time == True:
        float_duration = float_duration - 1
        altitude = altitude

    if float_duration <= 0 or gps_fence == False or real_time == False:
        start_condition = False
        end_condition = True
        float_altitude = final_altitude
        float_duration = 1 # Sets the float duration to an impossible amount for this condition to run again

    minutes += 1

    # Manipulates hours in 'datetime' if minutes equals 60 and hours equals 24
    if minutes == 60:
        minutes = 0
        hours += 1
        if hours == 24:
            hours = 0
            date += 1

create_kml(lat_long_only, 'map_kml')

create_kml([(gps_long_left, gps_lat_up), (gps_long_right, gps_lat_up)], 'fence_kml')
create_kml([(gps_long_left, gps_lat_up), (gps_long_left, gps_lat_down)], 'fence_kml')
create_kml([(gps_long_left, gps_lat_down), (gps_long_right, gps_lat_down)], 'fence_kml')
create_kml([(gps_long_right, gps_lat_down), (gps_long_right, gps_lat_up)], 'fence_kml')