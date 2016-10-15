from urllib.request import urlopen
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd


def is_number(s):
    """
    check if a string represents an integer or float number

    parameter
    --------
        s: a string
    
    return
    ------
        return True iff S represents a number (int or float)
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_daily_data(y, m, d, icao):
    """
    grab daily weather data for an airport from wunderground.com
    
    parameter
    ---------
        y: year
        m: month
        d: day
        ICAO: ICAO identification number for an airport
        
    return
    ------
        a dictionary containing
            "Min Temperature": daily minimum temperature
            "Max Temperature": daily maximum temperature
            "Precipitation": daily precipitation
            "Max Humidity": daily maximum humidity
            "Min Humidify": daily minimum humidify
    """

    # construct url from (y, m, d)
    url = "http://www.wunderground.com/history/airport/" + icao + '/'+\
         str(y) + "/" + str(m) + "/" + str(d) + "/DailyHistory.html"
    page = urlopen(url)
    
    # parse html
    soup = BeautifulSoup(page, 'html5lib')

    # return dictionary
    daily_data = {'Min Temperature':'nan', 'Max Temperature':'nan',
           'Precipitation':'nan', 'Maximum Humidity':'nan', 'Minimum Humidity':'nan'}

    # find rows in the main table
    all_rows = soup.find(id="historyTable").find_all('tr')

    for row in all_rows:
        # attempt to find item name
        try:
            item_name = row.findAll('td', class_='indent')[0].get_text()
        except Exception as e:
            # if run into error, skip this row
            continue
    
        # temperature and precipitation 
        if item_name in ('Min Temperature','Max Temperature', 'Precipitation'):
            try:
                val = row.find_all('span', class_='wx-value')[0].get_text()
            except Exception as e:
                continue
            if is_number(val):
                daily_data[item_name] = val
        
        if item_name in ('Maximum Humidity', 'Minimum Humidity'):
            try:
                val = row.find_all('td')[1].get_text()
            except Exception as e:
                continue
            if is_number(val):
                daily_data[item_name] = val
            
    return daily_data


def write2csv(time_range, icao_list, filename):
    """
    scrape Weather Underground for weather info for airports
    listed in ICAO_LIST for the period in TIME_RANGE
    and write data into FILENAME
    
    parameter
    ---------
        time_range: a timestamp/datetime iterator
        icao_list: a list of standard 4 character strings 
            representing a list of airports
        filename: name of the output file
        
    return
    ------
        None
        output to file FILENAME
    """

    f = open(filename, 'w')
 
    for date in time_range:
        for icao in icao_list:
            
            y, m, d = date.year, date.month, date.day
            
            # get data from Weather Underground
            daily_data = get_daily_data(y, m, d, icao)
            
            min_temp = daily_data['Min Temperature']
            max_temp = daily_data['Max Temperature']
            min_hum = daily_data['Minimum Humidity']
            max_hum = daily_data['Maximum Humidity']
            prec = daily_data['Precipitation']
            
            str2write = ','.join([str(date), icao, min_temp, max_temp, \
                                  min_hum, max_hum, prec])
            str2write +='\n'
            
            # print(str(date), icao)
            f.write(str2write)

    # Done getting data! Close file.
    f.close()

def fetch_df(date):
    """
    build a pandas DataFrame holding weather data from a csv file specified by DATE
    
    parameter
    --------
        date: pandas DatetimeIndex or python Datetime obj
        
    return
    ------
        a DataFrame with the follwing info for 50 cities
            date, icao, min_temperature, max_temperature, 
            min_humidity, max_humidity, precipitation
    """
    filename = 'hw_5_data/weather_data/' + date.strftime('%Y') + '/'+ \
        date.strftime('%Y%m%d')+'.csv'
    col_names = ('date', 'icao', 'min_temp', 'max_temp', 'min_hum', 'max_hum', 'prec')
    df = pd.read_csv(filename, header=None, names=col_names)
    return df


def lat_lon_2_distance(lat1, lon1, lat2, lon2):
    """
    return distance (in km) between two locations (lat1, lon1) and (lat2, lon2)
    
    parameter
    ---------
        lat1, lat2: latitude in degrees
        lon1, lon2: longitude in degrees
        
    return
    ------
        distance in km
    """
    from math import sin, cos, sqrt, atan2, radians

    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    
    return distance



#--------------------------------------------------
#
#        NOT YET FINISHED BELOW
#
#--------------------------------------------------

def AIO_get_data_from_soup(soup):
    """
    find the weather info from SOUP, a html parsed by the BeautifulSoup
    - Taken from function get_daily_data(y, m, d, icao)
    - reimplemented to use together with AsyncIO library to speedup IO

    parameter
    ---------
        soup: a html parsed by the BeautifulSoup

    return
    ------
        same as get_daily_data
    
    """
    # return dictionary
    daily_data = {'Min Temperature':'nan', 'Max Temperature':'nan',
           'Precipitation':'nan', 'Maximum Humidity':'nan', 'Minimum Humidity':'nan'}

    # find rows in the main table
    all_rows = soup.find(id="historyTable").find_all('tr')

    for row in all_rows:
        # attempt to find item name
        try:
            item_name = row.findAll('td', class_='indent')[0].get_text()
        except Exception as e:
            # if run into error, skip this row
            continue
    
        # temperature and precipitation 
        if item_name in ('Min Temperature','Max Temperature', 'Precipitation'):
            try:
                val = row.find_all('span', class_='wx-value')[0].get_text()
            except Exception as e:
                continue
            if is_number(val):
                daily_data[item_name] = val
        
        if item_name in ('Maximum Humidity', 'Minimum Humidity'):
            try:
                val = row.find_all('td')[1].get_text()
            except Exception as e:
                continue
            if is_number(val):
                daily_data[item_name] = val
            
    return daily_data

