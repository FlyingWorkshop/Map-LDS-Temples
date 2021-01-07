import json
import os
import googlemaps
import plotly_express as px
import pandas as pd
import datetime
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from tqdm import tqdm


class Temple:
    def __init__(self, name: str, dedicated: str):
        self.name = name
        self.ded = dedicated

        # lat/lng are added by Database() init
        self.lat = None
        self.lng = None

        if self.exists():
            date = dedicated.split()
            self.month = date[1]
            self.year = date[2]
            self.status = 'Built'
        else:
            self.month = None
            self.year = None
            self.status = dedicated  # e.g. 'Construction' 'Announced' 'Renovation'

    def report(self):
        for attr in dir(self):
            print(f'{attr=}')

    def exists(self):
        return self.ded[0].isnumeric()


class Database:
    def __init__(self):
        # cache name + dedication/status of every LDS temple listed on Church website
        url = 'https://www.churchofjesuschrist.org/temples/list?lang=eng'
        source = 'source_cache.json'
        self._cache_source_page(url, source)

        # make a list of Temple objects
        self.temples = []
        self._make_temples(source)  # lat/lng are empty

        # cache Google data for each temple
        dirname = 'google_cache'
        api_key = 'YOURS_HERE'
        self._cache_google_data(api_key, dirname)
        self._add_latlng(dirname)

    def make_bar(self, s: str):
        data = {}
        if s == 'm':
            months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                      'October', 'November', 'December']
            data = {'Time': months, 'Temples Built': [0] * 12}
            for temple in self.temples:
                if temple.exists():
                    i = datetime.datetime.strptime(temple.ded.split()[1], '%B').month
                    data['Temples Built'][i - 1] += 1
        elif s == 'y':
            oldest_ded = 1884
            newest_ded = 2020
            years = list(range(oldest_ded, newest_ded + 1))
            data = {'Time': years, 'Temples Built': [0] * len(years)}
            for temple in self.temples:
                if temple.exists():
                    i = int(temple.ded.split()[2]) - oldest_ded
                    data['Temples Built'][i] += 1
        df = pd.DataFrame.from_dict(data)
        fig = px.bar(df, x='Time', y='Temples Built')
        fig.show()

    def make_globe(self):
        """
        Plots every LDS temple on a 3d plotly globe (orthographic projection)
        """
        data = {'temple': [], 'lat': [], 'lng': [], 'status': []}
        for temple in self.temples:
            data['temple'].append(temple.name)
            data['lat'].append(temple.lat)
            data['lng'].append(temple.lng)
            if temple.exists():
                data['status'].append('Built')
            else:
                data['status'].append(temple.ded)
        df = pd.DataFrame(data=data)
        fig = px.scatter_geo(df, lat='lat', lon='lng', color='status', projection='orthographic', hover_name='temple')
        fig.show()

    @staticmethod
    def _cache_source_page(url, filename):
        if os.path.exists(filename):
            pass

        # get html
        session = HTMLSession()
        r = session.get(url)
        r.html.render()
        html = r.html.html

        # parse html and cache data
        cache = {}
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup.main('li'):
            spans = tag('span')
            name = spans[0].text
            dedicated = spans[2].text
            cache[name] = dedicated

        # store cache as json
        with open(filename, 'w') as f:
            json.dump(cache, f, indent=4)

    def _make_temples(self, source):
        data = json.load(open(source))
        for name, dedicated in data.items():
            temple = Temple(name, dedicated)
            self.temples.append(temple)

    def _cache_google_data(self, api_key: str, dirname):
        if not os.path.exists(dirname):
            os.mkdir(dirname)

        for temple in tqdm(self.temples):
            cache = f'{dirname}/{temple.name}.json'
            if not os.path.exists(cache):
                gmaps = googlemaps.Client(api_key)
                data = gmaps.geocode(temple.name)
                json.dump(data, open(cache, 'w'), indent=4)

    def _add_latlng(self, dirname):
        for temple in self.temples:
            data = json.load(open(f'{dirname}/{temple.name}.json'))[0]
            temple.lat = data['geometry']['location']['lat']
            temple.lng = data['geometry']['location']['lng']
