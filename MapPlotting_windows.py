import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import holidays
# file opening
data = requests.get("https://kiosks.bicycletransit.workers.dev/phl").json()
trip_data_2022_4 = pd.read_csv("indego-trips-2022-q4.csv", low_memory=False)
trip_data_2022_3 = pd.read_csv("indego-trips-2022-q3.csv", low_memory=False)
trip_data_2022_2 = pd.read_csv("indego-trips-2022-q2.csv", low_memory=False)
trip_data_2022_1 = pd.read_csv("indego-trips-2022-q1.csv", low_memory=False)
trip_data_2021_1 = pd.read_csv("indego-trips-2021-q1.csv", low_memory=False)
trip_data_2021_2 = pd.read_csv("indego-trips-2021-q2.csv", low_memory=False)
trip_data_2021_3 = pd.read_csv("indego-trips-2021-q3.csv", low_memory=False)
trip_data_2021_4 = pd.read_csv("indego-trips-2021-q4.csv", low_memory=False)
station_data = pd.read_csv("indego-stations-2022-10-01.csv", low_memory=False)
# puts elements of data structure into list


def into_list(structure):
    list = []
    for i in structure:
        list.append(i)
    return (list)


# combining indexies
full_data = trip_data_2022_4.set_index("start_station").join(
    station_data.set_index("Station_ID"))
full_data_end = trip_data_2022_4.set_index(
    "end_station").join(station_data.set_index("Station_ID"))
stations = list(
    station_data.loc[station_data.Status == "Active", "Station_Name"])

# creating date lists
dates_2022_Q4 = pd.date_range(start="2022/10/01", end="2022/12/31", freq="D")
dates_2022 = pd.date_range(start="2022/01/01", end="2022/12/31", freq="D")
dates_2021 = pd.date_range(start="2021/01/01", end="2021/12/31", freq="D")

# creating lists from data structures
dates_2021 = into_list(dates_2021)
dates_2022 = into_list(dates_2022)
dates_2022_Q4 = into_list(dates_2022_Q4)
to_select = []

# holidays
us_holidays = holidays.CountryHoliday('US', prov=None, state='PA')

# getting dates for input parameters
d = datetime.today()
d_str = d.strftime("%m-%d-%Y")
day = d + timedelta(days=14)
first_day = datetime.strptime("10-01-2022", "%m-%d-%Y")
last_day = datetime.strptime("12-31-2022", "%m-%d-%Y")

# streamlit sidebar markdown + prompts to show data for
st.sidebar.markdown("# Pick a location to show data for")
selected_answer = st.sidebar.selectbox("Pick a location", stations)

st.sidebar.markdown("# Select a date range to show trip data for")
start_date = st.sidebar.date_input(
    'Pick a start date', value=first_day, min_value=first_day)
start_date_str = start_date.strftime("%m/%d/%Y")

end_date = st.sidebar.date_input(
    'Pick an end date', value=start_date, min_value=start_date, max_value=last_day)
end_date_str = end_date.strftime("%m/%d/%Y")

st.sidebar.markdown(
    "# Select a future (or the current) date to take out a bike on")
selected_date = st.sidebar.date_input(
    "Pick a date", value=d, min_value=d, max_value=day)
selected_date_str = selected_date.strftime("%m/%d/%Y")

# gets a time at every half hour for sorting on line 234 loop
times = []
times_before = pd.date_range(
    start=selected_date_str, periods=49, freq="0h30min")
times = into_list(times_before)

# list and dictionary defining for map
longitude = []
latitude = []
names = []
bikes_amount = []
docks = []
classic = []
electric = []

# loops through json file and grabs elements for each station
for station in data['features']:
    longitude.append(station['geometry']['coordinates'][0])
    latitude.append(station['geometry']['coordinates'][1])
    names.append(station['properties']['name'])
    bikes_amount.append(station['properties']['bikesAvailable'])
    docks.append(station['properties']['docksAvailable'])
    classic.append(station['properties']['classicBikesAvailable'])
    electric.append(station['properties']['electricBikesAvailable'])

stations_coords = list(zip(latitude, longitude, names,
                       bikes_amount, docks, classic, electric))

# creating dataframe
all_points = pd.DataFrame(
    stations_coords,
    columns=['lat', 'lon', 'station_name', 'Bikes Available',
             'Docks Available', 'Classic Bikes Available', 'Electric Bikes Available']
)
# for graphs
# all the start and end times at a station
start_times = full_data.loc[full_data.Station_Name ==
                            selected_answer, "start_time"]
end_times = full_data_end.loc[full_data_end.Station_Name ==
                              selected_answer, "end_time"]
# line would start at 0, then at first date this zero is for 0,0 so the first data point doesnt start before first date
average_trips_start = [0]
average_trips_end = [0]
# gets the amount of trips started in a day and appends the number to a list
for i in dates_2022_Q4:
    trips_per_day = 0
    # if the date is between the date range
    if (i.date() >= start_date and i.date() <= end_date):
        i = i.strftime(f"%m/{i.day}/%Y")  
        for j in start_times:
            trip_date = j.split(" ")
            trip_day = trip_date[0]
            if i == trip_day:
                trips_per_day += 1
        average_trips_start.append(trips_per_day)

# gets the amount of trips ended in a day and appends the number to a list
for i in dates_2022_Q4:
    trips_per_day = 0
    # if the date is between the date range
    if (i.date() >= start_date and i.date() <= end_date):
        i = i.strftime(f"%m/{i.day}/%Y")
        for j in end_times:
            trip_date = j.split(" ")
            trip_day = trip_date[0]
            if i == trip_day:
                trips_per_day += 1
        average_trips_end.append(trips_per_day)

# selected day of week
dayofweek = selected_date.strftime("%A")

# getting date for last year and year before
date_2022 = selected_date.replace(year=2022)
date_2021 = selected_date.replace(year=2021)

# for sorting trips
# determining quarter of wanted date in 2020, 2019 so it can get the correct dataset
first_quarter_end = datetime.strptime("03-31-2023", "%m-%d-%Y").date()
second_quarter_end = datetime.strptime("06-30-2023", "%m-%d-%Y").date()
third_quarter_end = datetime.strptime("09-30-2023", "%m-%d-%Y").date()

# getting the dataset needed for the date selected
# first quarter
if selected_date <= first_quarter_end:
    full_data_1 = trip_data_2021_1.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_1 = trip_data_2021_1.set_index(
        "end_station").join(station_data.set_index("Station_ID"))
    full_data_2 = trip_data_2022_1.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_2 = trip_data_2022_1.set_index(
        "end_station").join(station_data.set_index("Station_ID"))

# second quarter
elif selected_date > first_quarter_end and selected_date <= second_quarter_end:
    full_data_1 = trip_data_2021_2.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_1 = trip_data_2021_2.set_index(
        "end_station").join(station_data.set_index("Station_ID"))
    full_data_2 = trip_data_2022_2.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_2 = trip_data_2022_2.set_index(
        "end_station").join(station_data.set_index("Station_ID"))

# third quarter
elif selected_date > second_quarter_end and selected_date <= third_quarter_end:
    full_data_1 = trip_data_2021_3.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_1 = trip_data_2021_3.set_index(
        "end_station").join(station_data.set_index("Station_ID"))
    full_data_2 = trip_data_2022_3.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_2 = trip_data_2022_3.set_index(
        "end_station").join(station_data.set_index("Station_ID"))

# fourth quarter
else:
    full_data_1 = trip_data_2021_4.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_1 = trip_data_2021_4.set_index(
        "end_station").join(station_data.set_index("Station_ID"))
    full_data_2 = trip_data_2022_4.set_index(
        "start_station").join(station_data.set_index("Station_ID"))
    full_data_end_2 = trip_data_2022_4.set_index(
        "end_station").join(station_data.set_index("Station_ID"))

# making list of all times in the same quarter at the selected station withnin the 2 years
start_times = []
start_times1 = full_data_1.loc[full_data_1.Station_Name ==
                               selected_answer, "start_time"]
start_times2 = full_data_2.loc[full_data_2.Station_Name ==
                               selected_answer, "start_time"]

# getting elements into datetime
for i in start_times1:
    j = datetime.strptime(i, "%m/%d/%Y %H:%M")
    start_times.append(j)
for i in start_times2:
    j = datetime.strptime(i, "%m/%d/%Y %H:%M")
    start_times.append(j)
end_times = []
end_times1 = full_data_end_1.loc[full_data_end_1.Station_Name ==
                                 selected_answer, "end_time"]
end_times2 = full_data_end_2.loc[full_data_end_2.Station_Name ==
                                 selected_answer, "end_time"]
for i in end_times1:
    j = datetime.strptime(i, "%m/%d/%Y %H:%M")
    end_times.append(j)
for i in end_times2:
    j = datetime.strptime(i, "%m/%d/%Y %H:%M")
    end_times.append(j)

# creating lists
day_trip_start_2022 = []
day_trip_start_2021 = []
day_trip_end_2022 = []
day_trip_end_2021 = []

# all start trips at the station are in start_times and end trips in end_times
# narrowing down trips to only trips on the wanted day in 2020, 2019
for i in start_times:
    if i.strftime("%Y") == "2022":
        if (i.strftime("%m/%d/%Y") == date_2022.strftime("%m/%d/%Y")):
            day_trip_start_2022.append(i)
    elif i.strftime("%Y") == "2021":
        if (i.strftime("%m/%d/%Y") == date_2021.strftime("%m/%d/%Y")):
            day_trip_start_2021.append(i)
for i in end_times:
    if i.strftime("%Y") == "2022":
        if (i.strftime("%m/%d/%Y") == date_2022.strftime("%m/%d/%Y")):
            day_trip_end_2022.append(i)
    elif i.strftime("%Y") == "2021":
        if (i.strftime("%m/%d/%Y") == date_2021.strftime("%m/%d/%Y")):
            day_trip_end_2021.append(i)
# getting trips ended andstarted in 2020 and 2019

# lists that will go into graphs
halfhour_2022_netchange = [0]
halfhour_2021_netchange = [0]

# gets trips started and ended for each half hour period
for i in range(0, 48):
    # getting start and end of range
    start_time = times[i]
    end_time = times[i+1]
    # counters
    trip_2022_start_counter = 0
    trip_2021_start_counter = 0
    trip_2022_end_counter = 0
    trip_2021_end_counter = 0
    # started/2022 during halfhour
    for i in day_trip_start_2022:
        if (i >= start_time.replace(year=2022)) and (i < end_time.replace(year=2022)):
            trip_2022_start_counter += 1

    # started/2021 during halfhour
    for i in day_trip_start_2021:
        if (i >= start_time.replace(year=2021)) and (i < end_time.replace(year=2021)):
            trip_2021_start_counter += 1

    # ended/2022 during half hour
    for i in day_trip_end_2022:
        if (i >= start_time.replace(year=2022)) and (i < end_time.replace(year=2022)):
            trip_2022_end_counter += 1

    # ended/2021 during half hour
    for i in day_trip_end_2021:
        if (i >= start_time.replace(year=2021)) and (i < end_time.replace(year=2021)):
            trip_2021_end_counter += 1

    # adding net change to lists
    halfhour_2022_netchange.append(
        trip_2022_end_counter - trip_2022_start_counter)
    halfhour_2021_netchange.append(
        trip_2021_end_counter - trip_2021_start_counter)

# setting up ticks
times_ticks = []
for i in range(0, 48):
    times_ticks.append(times[i].strftime("%H:%M") +
                       " - " + times[i+1].strftime("%H:%M"))

# display map data + amount of bikes available guau so efficent u so cool
st.header("Map of all stations and current data from the stations")
fig = px.scatter_mapbox(all_points, lat="lat", lon="lon", hover_name="station_name", hover_data=[
                        "Bikes Available", 'Docks Available', 'Classic Bikes Available', 'Electric Bikes Available'], color_discrete_sequence=["fuchsia"], zoom=3, height=300)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(figure_or_data=fig, use_container_width=True)

# checks if the range of dates is valid if not/ lists will be empty so no data
if (start_date < end_date):
    st.header("Trips ended and started at " + selected_answer +
              " between " + start_date_str + " and " + end_date_str)
    dates_list = []

    # gets all the dates within the range
    for i in range(dates_2022_Q4.index(pd.Timestamp(start_date)), dates_2022_Q4.index(pd.Timestamp(end_date)) + 1):
        j = dates_2022_Q4[i]
        k = j.strftime("%m/%d/%Y")
        dates_list.append(k)

    # holidays
    holidays = []
    for i in range(0, len(dates_list)):
        if dates_list[i] in us_holidays:
            holidays.append(dates_list[i] + " " +
                            us_holidays.get(dates_list[i]))

    # creating trips started graph
    st.write("The holidays for this date range are:")
    for i in holidays:
        st.write(i)
    fig = plt.figure()
    ax = plt.axes()
    x_values = np.arange(1, dates_2022_Q4.index(pd.Timestamp(end_date)) + 2 - 
                         dates_2022_Q4.index(pd.Timestamp(start_date)), 1)
    plt.xticks(x_values, dates_list)
    ax.tick_params(axis='x', rotation=70, labelsize=3)
    plt.xlabel("Days")
    plt.title("Trips started")
    plt.plot(average_trips_start)
    st.pyplot(fig)

    # create graph for trips ended
    fig1 = plt.figure()
    ax1 = plt.axes()
    plt.xticks(x_values, dates_list)
    plt.title("Trips ended")
    plt.xlabel("Days")
    ax1.tick_params(axis='x', rotation=70, labelsize=3)
    plt.plot(average_trips_end)
    st.pyplot(fig1)

else:
    st.write("Select new end date//can't be before start date")

# graphing half hour graphs
st.header("Based on the date you want to take a bike out on, these graphs show data from each half hour on the same " +
          dayofweek + " in 2022 and 2021")

# trips started
fig = plt.figure()
ax = plt.axes()
x_values = np.arange(1, len(times_ticks) + 1, 1)
plt.xticks(x_values, times_ticks)
ax.tick_params(axis='x', rotation=70, labelsize=5)
plt.xlabel("Time")
plt.ylabel("Net change in bikes per half hour")
plt.title("Trips in 2022")
plt.plot(halfhour_2022_netchange)
st.pyplot(fig)

# display if date is holiday
if date_2022 in us_holidays:
    st.write(us_holidays.get(date_2022))

# create graph for trips ended
fig1 = plt.figure()
ax1 = plt.axes()
plt.xticks(x_values, times_ticks)
plt.title("Trips in 2021")
plt.xlabel("Time")
plt.ylabel("Net change in bikes per half hour")
ax1.tick_params(axis='x', rotation=70, labelsize=5)
plt.plot(halfhour_2021_netchange)
st.pyplot(fig1)
# will display if date is holiday
if date_2021 in us_holidays:
    st.write(us_holidays.get(date_2021))
st.write("""The y axis (Net change in bikes per half hour) is calculated by subtracting the trips that ended
at the station by the trips that ended at the station during the half hour peroid. This number will be
the overall net change in bikes available at the station through the half hour. This also means that
this number does not calculate the activity of the station as a value of \"0\" could mean that
five trips started and ended at the station or that nobody used the station in the half hour.""")
