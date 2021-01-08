import json
import os
import googlemaps
import plotly_express as px
import pandas as pd
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import datetime


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

    def exists(self):
        return self.ded[0].isnumeric()


class Database:
    def __init__(self):
        self._cache_source('lds_cache.json')

        self.temples = []
        self._make_temples('lds_cache.json')  # lat/lng are empty

        self._cache_google_data('AIzaSyAZ-56NcO_k6FtpBNFEy4NNCu1h1YOXRkg', 'google_caches')
        self._fill_temple_coords('google_caches')

        self.mega_index = {}
        self._make_mega_index()

    def _cache_source(self, file):
        if not os.path.exists(file):
            html = self._get_html('https://www.churchofjesuschrist.org/temples/list?lang=eng')
            data = self._parse_html(html)
            with open(file, 'w') as f:
                json.dump(data, f, indent=4)

    @staticmethod
    def _get_html(url):
        session = HTMLSession()
        r = session.get(url)
        r.html.render()
        return r.html.html

    @staticmethod
    def _parse_html(html):
        d = {}
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup.main('li'):
            spans = tag('span')
            name = spans[0].text  # temple name (ex: 'Aba Nigeria Temple')
            ded = spans[2].text  # either status (ex: 'Construction') or dedication date (ex: '1 January 2001)
            d[name] = ded
        return d

    def _make_temples(self, source):
        data = json.load(open(source))
        for name, dedicated in data.items():
            temple = Temple(name, dedicated)
            self.temples.append(temple)

    def _cache_google_data(self, api_key: str, dirname):
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        for temple in self.temples:
            cache = f'{dirname}/{temple.name}.json'
            if not os.path.exists(cache):
                print(f'Getting {cache}...')
                gmaps = googlemaps.Client(api_key)
                data = gmaps.geocode(temple.name)
                json.dump(data, open(cache, 'w'), indent=4)

    def _fill_temple_coords(self, dirname):
        for temple in self.temples:
            data = json.load(open(f'{dirname}/{temple.name}.json'))[0]
            temple.lat = data['geometry']['location']['lat']
            temple.lng = data['geometry']['location']['lng']

    def _make_mega_index(self):
        attrs = list(self.temples[0].__dict__)[-3:]
        d1 = {k1: {} for k1 in attrs}
        for temple in self.temples:
            for k1 in attrs:
                d2 = d1[k1]
                k2 = temple.__dict__[k1]
                if k2 not in d2:
                    d2[k2] = []
                d2[k2].append(temple.name)
        self.mega_index = d1

    def report_mega_index(self):
        for title, index in self.mega_index.items():
            print('####')
            print(title.capitalize() + ': ')
            for k, v in index.items():
                print(k, len(v))
            print('####')
            print('')

    def make_globe(self):
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
