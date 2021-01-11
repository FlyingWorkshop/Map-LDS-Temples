import TempleGuide
import plotly_express as px
import pandas as pd


def report(db: TempleGuide.Database):
    df = pd.DataFrame(data=db.index)
    print(df)


def make_globe(db: TempleGuide.Database):
    """plots every LDS temple on a 3d model of Earth"""
    df = pd.DataFrame(data=db.index)
    fig = px.scatter_geo(df, 'lat', 'lng', color='status', projection='orthographic', hover_name='name')
    fig.show()


def make_bar(db: TempleGuide.Database):
    """makes a bar graph w/ the number of temples dedicated every year"""
    data = sorted([(k, len(v)) for k, v in db.inverted['year'].items()], key=lambda t: t[0])
    df = pd.DataFrame(data, columns=['Year', 'Temples Dedicated'])
    fig = px.bar(df, 'Year', 'Temples Dedicated')
    fig.show()


def search(db: TempleGuide.Database):
    df = pd.DataFrame(data=db.index)
    print(df)


def main():
    db = TempleGuide.Database()
    # report(db)
    # make_bar(db)
    # make_globe(db)


if __name__ == '__main__':
    main()
    
