import reverse_geocoder as rg
import json
import argparse
from datetime import datetime
from itertools import groupby


ACCURACY_LIMIT = 500


def addArgParser():
    parser = argparse.ArgumentParser(description='travel_history.py processes your Google location history to turn it into a well formated travel history document.')
    parser.add_argument('file', help='Google location history file')
    parser.add_argument("--accuracy", default=ACCURACY_LIMIT, help="(Int) Accuracy boundary for Google location data. Defaults to 500")
    parser.add_argument("--home", help="(String) Home country code. See README for table of country codes to their countries")

    args = parser.parse_args()
    return args


def has_all_fields(entry):
    return len({'latitudeE7', 'longitudeE7', 'timestamp', 'accuracy'}.intersection(set(entry.keys()))) == 4


def parse_entry(entry):
    lat = entry['latitudeE7'] / 10000000
    lon = entry['longitudeE7'] / 10000000

    time_str = entry['timestamp']
    splitter = '.' if time_str.find('.') != -1 else 'Z'
    time = datetime.strptime(time_str.split(splitter)[0], '%Y-%m-%dT%H:%M:%S') 
    date_str = time.strftime('%d/%m/%Y')

    return ((lat, lon), entry['accuracy'], date_str)


if __name__ == "__main__":

    args = addArgParser()

    with open(args.file) as json_file:
        data = json.load(json_file)

    entries = data['locations']
    valid = filter(has_all_fields, entries)
    parsed = list(map(parse_entry, valid))
    accurate = list(filter(lambda e : e[1] < args.accuracy, parsed))
    lat_lons = list(map(lambda e: e[0], accurate))
    searched = rg.search(lat_lons)
    countries = map(lambda s: s['cc'], searched)
    days_at = list(map(lambda e: (e[0], e[1][2]), zip(countries, accurate)))
    visits = groupby(days_at, lambda e: e[0])

    for country, days in visits: 
        if country == args.home:
            continue
        day_list = list(days)
        enter = day_list[0][1]
        leave = day_list[-1][1]
        print(country, enter, leave, sep=',')
