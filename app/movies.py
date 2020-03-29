from requests import get
from json import loads
from urllib.parse import quote
from .settings import API_MOVIE_KEY


def get_movie(movie):
    r = get(f'http://www.omdbapi.com/?t={quote(movie)}&apikey={API_MOVIE_KEY}')
    if r.status_code != 200:
        raise ValueError('Api not found')
    return loads(r.text)


def search_reg(msg):
    reg = {
        'movie:': search_movie,
        ' vs ': compare_movie,
    }

    for k, v in reg.items():
        array = msg.lower().split(k)
        if len(array) == 1:
            continue
        try:
            return v(*array)
        except:
            continue

    return None, None


def search_movie(_, movie_text):
    movie = get_movie(movie_text)
    if 'Response' in movie and movie['Response'] == 'False':
        return 'Movie not found!', None
    return f'{movie["Title"]} [{movie["Year"]}] {movie["Production"]} - {movie["imdbRating"]}', movie['Poster']


def compare_movie(a, b):
    movie_a = get_movie(a)
    if 'Response' in movie_a and movie_a['Response'] == 'False':
        return f'Movie {a} not found!', None

    movie_b = get_movie(b)
    if 'Response' in movie_b and movie_b['Response'] == 'False':
        return f'Movie {b} not found!', None

    rate_a = float(movie_a["imdbRating"])
    rate_b = float(movie_b["imdbRating"])
    if rate_a > rate_b:
        return f'{a}({movie_a["imdbRating"]}) is more popular than {b}({movie_b["imdbRating"]})', movie_a['Poster']
    elif rate_b > rate_a:
        return f'{b}({movie_b["imdbRating"]}) is more popular than {a}({movie_a["imdbRating"]})', movie_b['Poster']
    return 'both has the same popularity', None
