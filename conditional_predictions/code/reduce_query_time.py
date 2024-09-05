from getgfs import Forecast, url, Coordinate, Variable
import numpy as np
import requests, json, os, re, dateutil.parser, sys, warnings
from scipy.interpolate import interp1d
import math



class ExtendedForecast(Forecast):
    def __init__(self, resolution, timestep):
        super().__init__(resolution, timestep)
        self.query_s = 999
        self.idxs = [999,999]
        self.middle = [999,999]
        self.datasave = []

    def get(self, variables, date_time, lat, lon):
        """Returns the latest forecast available for the requested date and time

        Note
        ----
        - "raw" since you have to put indexes in rather than coordinates and it returns a file object rather than a processed file
        - If a variable has level dependance, you get all the levels - it seems extremely hard to impliment otherwise

        Args:
            variables (list): list of required variables by short name
            date_time (string): datetime requested (parser used so any format fine)
            lat (string or number): latitude in the format "[min:max]" or a single value
            lon (string or number): longitude in the format "[min:max]" or a single value

        Raises:
            ValueError: Invalid variable choice
            ValueError: Level dependance needs to be specified for chosen variable
            Exception: Unknown failure to download the file

        Returns:
            File Object: File object with the downloaded variable data (see File documentation)
        """

        # Get forecast date run, date, time
        forecast_date, forecast_time, query_time = self.datetime_to_forecast(date_time)
        print(forecast_date, forecast_time, query_time)
        # Get latitude
        lat1 = self.value_input_to_index("lat", lat)

        start = int(lat1[1:-1])-7
        end = int(lat1[1:-1])+7
        lat = "["+str(start) + ":" + str(end) +"]"

        # Get longitude
        lon1 = self.value_input_to_index("lon", lon)
        # lon = "[" + str(int(lon[1:-1])) + "]"
        start = int(lon1[1:-1])-7
        end = int(lon1[1:-1])+7
        lon = "["+str(start) + ":" + str(end) +"]"

        self.idxs = [int(lat1[1:-1]),int(lon1[1:-1])]
        # Get lev
        lev = "[0:%s]" % int(
            (self.coords["lev"]["minimum"] - self.coords["lev"]["maximum"])
            / self.coords["lev"]["resolution"]
        )

        # Make query
        query = ""
        for variable in variables:
            if variable not in self.variables.keys():
                raise ValueError(
                    "The variable {name} is not a valid choice for this weather model".format(
                        name=variable
                    )
                )
            if self.variables[variable]["level_dependent"] == True and lev == []:
                raise ValueError(
                    "The variable {name} requires the altitude/level to be defined".format(
                        name=variable
                    )
                )
            elif self.variables[variable]["level_dependent"] == True:
                query += "," + variable + query_time + lev + lat + lon

            else:
                query += "," + variable + query_time + lat + lon


        if query_time!=self.query_s:
            self.middle = [int(lat1[1:-1]),int(lon1[1:-1])]
            query = query[1:]
            print(url.format(
                    res=self.resolution,
                    step=self.timestep,
                    date=forecast_date,
                    hour=int(forecast_time),
                    info="ascii?{query}".format(query=query),
                ))
            r = requests.get(
                url.format(
                    res=self.resolution,
                    step=self.timestep,
                    date=forecast_date,
                    hour=int(forecast_time),
                    info="ascii?{query}".format(query=query),
                )
            )
            if r.status_code != 200:
                raise Exception(
                    """The forecast information could not be downloaded. 
            This error should never occure but it may be helpful to know the requested information was:
            - Forecast date: {f_date}
            - Forecast time: {f_time}
            - Query time: {q_time}
            - Latitude: {lat}
            - Longitude: {lon}""".format(
                        f_date=forecast_date,
                        f_time=forecast_time,
                        q_time=query_time,
                        lat=lat,
                        lon=lon,
                    )
                )
            elif r.text[:6] == "<html>":
                raise Exception(
                    """The forecast information could not be downloaded. 
            This error should never occure but it may be helpful to know the requested information was:
            - Forecast date: {f_date}
            - Forecast time: {f_time}
            - Query time: {q_time}
            - Latitude: {lat}
            - Longitude: {lon}
    
            The response given was: {res}
    
            Sometimes forcasts do not becone available when they should (e.g. when 06hr is availble in 0p25 it isn't in 0p50)""".format(
                        f_date=forecast_date,
                        f_time=forecast_time,
                        q_time=query_time,
                        lat=lat,
                        lon=lon,
                        res=re.findall(
                            """(<h2>GrADS Data Server - error<\/h2>)((.|\n)*)(Check the syntax of your request, or click <a href=".help">here<\/a> for help using the server.)""",
                            r.text,
                        ),
                    )
                )
            else:
                self.query_s = query_time
                return File(r.text)
        self.query_s = query_time
        return 1

    def get_windprofile(self, date_time, lat, lon):
        info = self.get(
            ["ugrdprs", "vgrdprs", "ugrd10m", "vgrd10m", "hgtsfc", "hgtprs"],
            date_time,
            lat,
            lon,
        )
        if info != 1:
            u_wind = list(info.variables["ugrdprs"].data.flatten()) + list(
                info.variables["ugrd10m"].data.flatten()
            )
            v_wind = list(info.variables["vgrdprs"].data.flatten()) + list(
                info.variables["vgrd10m"].data.flatten()
            )

            # at the altitudes we are concerned with the geopotential height and altitude are within 0.5km of eachother
            alts = list(info.variables["hgtprs"].data.flatten()) + list(
                info.variables["hgtsfc"].data.flatten() + 10
            )
            grid = int(math.sqrt(len(alts)/42))
            self.datasave = [np.array(alts).reshape(42,grid, grid),np.array(u_wind).reshape(42,grid, grid),np.array(v_wind).reshape(42,grid, grid)]


        alts = []
        u_wind = []
        v_wind = []

        for layers in self.datasave[0]:
            alts.append(layers[self.idxs[0]-self.middle[0]+7][self.idxs[1]-self.middle[1]+7])

        for layers in self.datasave[1]:
            u_wind.append(layers[self.idxs[0] - self.middle[0] + 7][self.idxs[1] - self.middle[1] + 7])

        for layers in self.datasave[2]:
            v_wind.append(layers[self.idxs[0] - self.middle[0] + 7][self.idxs[1] - self.middle[1] + 7])

        return interp1d(
            alts, u_wind, fill_value=(u_wind[-1], u_wind[-2]), bounds_error=False
        ), interp1d(
            alts, v_wind, fill_value=(v_wind[-1], v_wind[-2]), bounds_error=False
        )



class File:
    """Holds the variables and information from a text file returned by the forecast site"""

    def __init__(self, text):
        """Decode an OpenDAP https://nomads.ncep.noaa.gov/ text file

        Args:
            text (string): OpenDAP text file as a string
        """
        text = text.splitlines()
        # Get variable name and dimensionality
        ind_head = 0
        variables = []
        while ind_head < len(text):
            try:
                variable_name = re.findall("(.*?), ", text[ind_head])[0]
            except IndexError:
                raise ValueError("Likely that file entered was not the correct format")
            dims = re.findall("\[(.*?)\]", text[ind_head])
            dims.reverse()
            lines_data = 0
            for dim in dims[1:]:
                lines_data = int(dim) * (lines_data + 1)
            dims.reverse()

            lines_meta = len(dims) * 2  # Starts +1 from end of lines data
            name_line = True
            coords = []
            for line in text[
                ind_head + 2 + lines_data : ind_head + 3 + lines_data + lines_meta
            ]:
                if name_line:
                    name = re.findall("(.*?), ", line)[0]
                    name_line = False
                else:
                    coords.append(
                        Coordinate(name, [float(v[:-1]) for v in line.split()])
                    )
                    name_line = True

            data = np.zeros(tuple([int(d) for d in dims]))
            data[:] = np.nan
            for line in text[ind_head + 1 : ind_head + 1 + lines_data - 1]:
                if len(line) > 0 and line[0] == "[":
                    position = [int(v) for v in re.findall("\[(.*?)\]", line)]
                    values = line.split()[1:]
                    if len(values) > 1:
                        for ind, value in enumerate(values):
                            if value[-1] == ",":
                                value = value[:-1]
                            data = replace_val(data, float(value), position + [ind])
                    else:
                        data = replace_val(data, float(values[0]), position)

            coords = {c.name: c for c in coords}
            variables.append(Variable(variable_name, coords, data))

            ind_head += lines_data + lines_meta + 2

        self.variables = {v.name: v for v in variables}

    def __str__(self):
        print(type(self))
        return "File containing %s" % self.variables.keys()


def replace_val(arr, val, position):
    """Inserts a value into a 1 to 4 dimensional numpy array

    Note
    ----
    I am sure there are better ways todo this but I couldn't find any after quite a search

    Args:
        arr (numpy array): Array to insert into
        val (float/int): Value to insert
        position (tuple): Coordinate position in array

    Raises:
        TypeError: Position invalid
        ValueError: Dimensionality of array too high

    Returns:
        [type]: [description]
    """
    if not isinstance(position, list):
        raise TypeError("Wrong type entered for replacement position")
    # I wish I could find a proper way todo this, np.put only works for 1D arrays
    if len(position) == 1:
        arr[position[0]] = val
    elif len(position) == 2:
        arr[position[0]][position[1]] = val
    elif len(position) == 3:
        arr[position[0]][position[1]][position[2]] = val
    elif len(position) == 4:
        arr[position[0]][position[1]][position[2]][position[3]] = val
    else:
        raise ValueError(
            "Number of dimensions for value replacement not supported, please edit and make pull request it will be very easy"
        )

    return arr