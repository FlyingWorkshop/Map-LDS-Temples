import json
import os
import googlemaps
import plotly_express as px
import pandas as pd

from bs4 import BeautifulSoup
from requests_html import HTMLSession

GOOGLE_API_KEY = 'FILL'


class Temple:
    def __init__(self, name, dedicated):
        self.name = name
        self.dedicated = dedicated
        self.lat = None
        self.lng = None

    def report(self):
        print(f'Name: {self.name}')
        print(f'Dedicated: {self.dedicated}')
        print(f'Lat: {self.lat}')
        print(f'Lng: {self.lng}')


class Database:
    def __init__(self):
        self.temples = []

        self.__cache_root()
        self.__make_temples()   # temples' lat/lng are empty
        self.__cache_leaves()
        self.__add_geocodes()   # temples' lat/lng are filled

        self.data = {'Temple': [], 'Latitude': [], 'Longitude': [], 'Status': []}
        self.__make_data()

    def __cache_root(self):
        if os.path.exists('root.json'):
            pass
        url = 'https://www.churchofjesuschrist.org/temples/list?lang=eng'
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        cache = {}
        for tag in soup.main('li'):
            spans = tag('span')
            name, dedicated = spans[0].text, spans[2].text
            cache[name] = dedicated
        with open('root.json', 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)

    def __make_temples(self) -> list:
        """
        root.json needs to exist for this method to work
        """
        data = json.load(open('root.json'))
        for name, dedicated in data.items():
            temple = Temple(name, dedicated)
            self.temples.append(temple)

    def __cache_leaves(self):
        for temple in self.temples:
            if os.path.exists(f'Leaves/{temple.name}.json'):
                continue
            gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
            data = gmaps.geocode(temple.name)
            json.dump(data, open(f'Leaves/{temple.name}.json', 'w'), indent=4)

    def __add_geocodes(self):
        for temple in self.temples:
            data = json.load(open(f'Leaves/{temple.name}.json'))[0]
            temple.lat = data['geometry']['location']['lat']
            temple.lng = data['geometry']['location']['lng']

    def __make_data(self):
        for temple in self.temples:
            self.data['Temple'].append(temple.name)
            self.data['Latitude'].append(temple.lat)
            self.data['Longitude'].append(temple.lng)
            if temple.dedicated != 'Construction' and temple.dedicated != 'Announced':
                self.data['Status'].append('Built')
            else:
                self.data['Status'].append(temple.dedicated)

    @staticmethod
    def get_html(url) -> object:
        session = HTMLSession()
        r = session.get(url)
        r.html.render()
        return r.html.html


def main():
    db = Database()
    df = pd.DataFrame(data=db.data)
    fig = px.scatter_geo(df, lat='Latitude', lon='Longitude', color='Status',
                         projection='orthographic')
    fig.show()


if __name__ == '__main__':
    main()
