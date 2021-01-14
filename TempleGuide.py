from bs4 import BeautifulSoup
from requests_html import HTMLSession
import googlemaps
import time
import json
import os
import pandas as pd
import plotly_express as px

GOOGLE_API_KEY = 'YOURS_HERE'


class Temple:
    def __init__(self, name=None, dedicated=None, country=None, lat=None, lng=None):
        self.name = name

        # geography (lat/lng/country) filled by google
        self.country = country
        self.lat = lat
        self.lng = lng

        self.status = None
        self.date = None
        self._add_ded_info(dedicated)

    def _add_ded_info(self, ded):
        """sets date and status attrs"""
        if ded and isinstance(ded, str):
            if ded[0].isnumeric():
                self.status = 'Built'
                self.date = time.strptime(ded, '%d %B %Y')[:3]  # tuple (year, month, day)
            else:
                self.status = ded  # ex: 'Construction' 'Renovation' 'Announced'

    def __str__(self):
        return self.name

    def __bool__(self):
        return self.status == 'Built'

class Database:
    def __init__(self, webcache='lds_cache.json', geocache_dir='google_caches'):
        self.temples = []
        self._make_temples(webcache, geocache_dir)

        self.data = None
        self._make_data()

        self.index = None
        self._make_index()

        self._make_shortcuts()

    def _make_temples(self, wc, gc_dir):
        self._check_webcache(wc)  # lists temples' name and dedication
        with open(wc) as f:
            d1 = json.load(f)
        for name, ded in d1.items():
            self._check_geocache(gc_dir, name)
            with open(f'{gc_dir}/{name}.json') as f:
                d2 = json.load(f)
            lat = d2['geometry']['location']['lat']
            lng = d2['geometry']['location']['lng']
            country = ''
            for component in reversed(d2['address_components']):
                if 'country' in component['types']:
                    country = component['long_name']
            self.temples.append(Temple(name=name, dedicated=ded, country=country, lat=lat, lng=lng))

    def _check_webcache(self, wc):
        if not os.path.exists(wc):
            url = 'https://www.churchofjesuschrist.org/temples/list?lang=eng'
            html = self._get_html(url)
            data = self._parse(html)  # data has temples' name and dedication
            with open(wc, 'w') as f:
                json.dump(data, f, indent=4)

    @staticmethod
    def _get_html(url):
        session = HTMLSession()
        r = session.get(url)
        r.html.render()  # renders javascript html and stores it in {obj}.html.html
        return r.html.html

    @staticmethod
    def _parse(html):
        result = {}
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup.main('li'):
            spans = tag('span')
            name = spans[0].text  # temple name (ex: 'Aba Nigeria Temple')
            ded = spans[2].text   # dedication date (ex: '1 January 2001) or status (ex: 'Construction')
            result[name] = ded
        return result

    @staticmethod
    def _check_geocache(gc_dir, temple_name):
        geocache = f'{gc_dir}/{temple_name}.json'
        if not os.path.exists(geocache):
            print(f'Getting "{geocache}"')
            if not os.path.exists(gc_dir):
                os.mkdir(gc_dir)
            gmaps = googlemaps.Client(GOOGLE_API_KEY)
            data = gmaps.geocode(temple_name)[0]  # geocode returns a 1-elem list (elem is a multi-layer dict)
            json.dump(data, open(geocache, 'w'), indent=4)

    def _make_data(self):
        attrs = list(Temple().__dict__)
        d = {attr: [] for attr in attrs}
        for o in self.temples:
            for k, v in o.__dict__.items():
                d[k].append(v)
        self.data = d

    def _make_index(self):
        d = {}
        for o in self.temples:
            for k, v in o.__dict__.items():
                if not v or any(k == s for s in [None, 'name', 'lat', 'lng', 'country']):
                    continue
                if k not in d:
                    d[k] = {}
                if k == 'date':
                    v = v[0]
                if v not in d[k]:
                    d[k][v] = []
                d[k][v].append(o.name)
        self.index = d

    def _make_shortcuts(self):
        """
        Dynamically creates attributes for this instance of Database. These attributes are more human-readable
        shortcuts for the inner values of .data (ex: .temple_countries is the same as .data['country'])
        >>> db = Database()
        >>> db.temple_names[:3]
        ['Aba Nigeria Temple', 'Abidjan Ivory Coast Temple', 'Accra Ghana Temple']
        """
        for attr in self.data.keys():
            shortcut = f'temple_{attr}s'  # ex: temple_names
            if attr[-1] == 'y':
                shortcut = f'temple_{attr[:-1]}ies'  # ex: temple_countries
            if attr[-1] == 's':
                shortcut = f'temple_{attr}es'  # ex: temple_statuses
            setattr(self, shortcut, self.data[attr])


def display(db: Database):
    df = pd.DataFrame(db.data)
    print(df)


def make_globe(db: Database):
    df = pd.DataFrame(db.data)
    fig = px.scatter_geo(df, lat='lat', lon='lng', color='status', hover_name='name', projection='orthographic')
    fig.show()


def make_bar(db: Database):
    data = sorted([(k, len(v)) for k, v in db.index['date'].items()], key=lambda t: t[0])
    df = pd.DataFrame(data, columns=['year', 'temples built'])
    fig = px.bar(df, x='year', y='temples built')
    fig.show()
