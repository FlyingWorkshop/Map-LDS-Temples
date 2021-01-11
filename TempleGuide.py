from bs4 import BeautifulSoup
from requests_html import HTMLSession
import googlemaps
import json
import os


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
            self.year = int(date[2])
            self.status = 'Built'
        else:
            self.month = None
            self.year = None
            self.status = dedicated  # e.g. 'Construction' 'Announced' 'Renovation'

    def exists(self):
        return self.ded[0].isnumeric()


class Database:
    def __init__(self):
        webcache = 'lds_cache.json'
        self._cache_source(webcache)

        gcache_dir = 'google_caches'
        self.temples = []
        self._make_temples(webcache)  # lat/lng are empty
        self._cache_gdata(gcache_dir, 'YOUR KEY HERE')
        self._fill_coords(gcache_dir)

        self.index = None
        self.inverted = None
        self._make_index()
        self._make_inverted()

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

    def _cache_gdata(self, dirname, api_key):
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        for temple in self.temples:
            cache = f'{dirname}/{temple.name}.json'
            if not os.path.exists(cache):
                print(f'Getting {cache}...')
                gmaps = googlemaps.Client(api_key)
                data = gmaps.geocode(temple.name)
                json.dump(data, open(cache, 'w'), indent=4)

    def _fill_coords(self, dirname):
        for temple in self.temples:
            data = json.load(open(f'{dirname}/{temple.name}.json'))[0]
            temple.lat = data['geometry']['location']['lat']
            temple.lng = data['geometry']['location']['lng']

    def _make_index(self):
        attrs = list(self.temples[0].__dict__)
        self.index = {attr: [] for attr in attrs}
        for temple in self.temples:
            for attr in attrs:
                inside = self.index[attr]       # list
                elem = temple.__dict__[attr]    # elem is the value of a given attr for this temple (ex: 'August')
                inside.append(elem)

    def _make_inverted(self):
        attrs = list(self.temples[0].__dict__)[-3:]
        outer = {attr: {} for attr in attrs}  # keys are literals of attrs of class Temple (ex: 'month)
        for temple in self.temples:
            for attr in attrs:
                inner = outer[attr]          # inner is a subdict of outer
                key = temple.__dict__[attr]  # keys are values of attrs of this Temple object (ex: 'August')
                if not key:
                    continue
                if key not in inner:
                    inner[key] = []
                inner[key].append(temple.name)
        self.inverted = outer

    def report_inverted_index(self):
        for title, index in self.mega_index.items():
            print('####')
            print(title.capitalize() + ': ')
            for k, v in index.items():
                print(k, len(v))
            print('####')
            print('')
