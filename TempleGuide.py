import json
import os
import googlemaps
import plotly_express as px
import pandas as pd
import datetime
from bs4 import BeautifulSoup
from requests_html import HTMLSession

GOOGLE_API_KEY = 'FILL'


class Temple:
    def __init__(self, name: str, dedicated: str):
        self.name = name
        self.ded = dedicated
        self.lat = None
        self.lng = None

    def report(self):
        print(f'Name: {self.name}')
        print(f'Dedicated: {self.ded}')
        print(f'Lat: {self.lat}')
        print(f'Lng: {self.lng}')

    def exists(self):
        return not any(self.ded == s for s in ['Construction', 'Announced', 'Renovation'])


class Database:
    def __init__(self):
        self.temples = []
        self._cache_root()
        self._make_temples()   # temples' lat/lng are empty
        self._cache_leaves()
        self._add_geocodes()   # temples' lat/lng are filled

    def make_bar(self, s):
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

    def _cache_root(self):
        if os.path.exists('root.json'):
            pass
        url = 'https://www.churchofjesuschrist.org/temples/list?lang=eng'
        html = self._get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        cache = {}
        for tag in soup.main('li'):
            spans = tag('span')
            name, dedicated = spans[0].text, spans[2].text
            cache[name] = dedicated
        with open('root.json', 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)

    def _make_temples(self):
        """
        root.json needs to exist for this method to work
        """
        data = json.load(open('root.json'))
        for name, dedicated in data.items():
            temple = Temple(name, dedicated)
            self.temples.append(temple)

    def _cache_leaves(self):
        for temple in self.temples:
            if os.path.exists(f'Leaves/{temple.name}.json'):
                continue
            gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
            data = gmaps.geocode(temple.name)
            json.dump(data, open(f'Leaves/{temple.name}.json', 'w'), indent=4)

    def _add_geocodes(self):
        for temple in self.temples:
            data = json.load(open(f'Leaves/{temple.name}.json'))[0]
            temple.lat = data['geometry']['location']['lat']
            temple.lng = data['geometry']['location']['lng']

    @staticmethod
    def _get_html(url) -> object:
        session = HTMLSession()
        r = session.get(url)
        r.html.render()
        return r.html.html
