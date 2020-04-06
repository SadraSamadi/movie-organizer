import shutil
from datetime import datetime
from json import JSONEncoder, dump
from os import listdir, path, mkdir

import requests
from guessit import guessit
from pathvalidate import sanitize_filename

root = 'G:\\Videos\\Movies'
base_url = 'https://api.themoviedb.org/3'
image_base_url = 'https://image.tmdb.org/t/p'
api_key = 'c73f3083988325a968f198ad0956a3cd'


class Serializer(JSONEncoder):

    def default(self, o):
        return str(o)


def get_file_info():
    for file_name in listdir(root):
        file_path = path.join(root, file_name)
        if path.isfile(file_path):
            yield file_name, guessit(file_name)


def get_movie_id(file_info):
    response = requests.get(f'{base_url}/search/movie', params={
        'api_key': api_key,
        'include_adult': True,
        'query': file_info.get('title'),
        'year': file_info.get('year')
    })
    data = response.json()
    total_results = data['total_results']
    print('TOTAL RESULTS:', total_results)
    if total_results == 1:
        result = data['results'][0]
        return result['id']


def get_movie_details(movie_id):
    response = requests.get(f'{base_url}/movie/{movie_id}', params={
        'api_key': api_key,
        'append_to_response': ''
    })
    return response.json()


def download_image(directory, file_name, image_path):
    print('DOWNLOADING IMAGE:', directory, file_name)
    if not image_path:
        return
    response = requests.get(f'{image_base_url}/original{image_path}', params={'api_key': api_key})
    file_path = path.join(directory, file_name + '.' + image_path.split('.')[-1])
    with open(file_path, 'wb') as f:
        f.write(response.content)
    print('IMAGE DOWNLOADED:', len(response.content), '(bytes)')


def create_collection(movie_details):
    collection = movie_details['belongs_to_collection']
    if collection:
        print('CREATING COLLECTION:', collection['name'])
        collection_id = collection['id']
        response = requests.get(f'{base_url}/collection/{collection_id}', params={'api_key': api_key})
        collection_details = response.json()
        name = sanitize_filename(collection_details['name'])
        parent = path.join(root, name)
        if not path.exists(parent):
            mkdir(parent)
            details_path = path.join(parent, 'collection.json')
            with open(details_path, 'w') as f:
                dump(collection_details, f, indent=2)
            download_image(parent, 'backdrop', collection_details['backdrop_path'])
            download_image(parent, 'poster', collection_details['poster_path'])
            print('COLLECTION CREATED!')
        return parent
    else:
        print('NO COLLECTION!!!')
        return root


def move_movie(parent, movie):
    file_name = movie['file_name']
    print('MOVING MOVIE...')
    movie_details = movie['movie_details']
    title = movie_details['title']
    date = datetime.strptime(movie_details['release_date'], '%Y-%m-%d')
    name = sanitize_filename(title)
    movie_dir = path.join(parent, f'[{date.year}] {name}')
    if not path.exists(movie_dir):
        mkdir(movie_dir)
        details_path = path.join(movie_dir, 'movie.json')
        with open(details_path, 'w') as f:
            dump(movie, f, indent=2, cls=Serializer)
        download_image(movie_dir, 'backdrop', movie_details['backdrop_path'])
        download_image(movie_dir, 'poster', movie_details['poster_path'])
        original_file = path.join(root, file_name)
        ext = file_name.split('.')[-1].lower()
        movie_file = path.join(movie_dir, f'{name} ({date.year}).{ext}')
        shutil.move(original_file, movie_file)
        print('.: SUCCESSFULLY MOVED :.')
    else:
        print('MOVIE EXISTS!!!')


def main():
    for file_name, file_info in get_file_info():
        print(file_name)
        print(file_info)
        movie_id = get_movie_id(file_info)
        if movie_id:
            movie_details = get_movie_details(movie_id)
            parent = create_collection(movie_details)
            move_movie(parent, {
                'file_name': file_name,
                'file_info': file_info,
                'movie_details': movie_details
            })
        else:
            print('MOVIE NOT FOUND!!!')
        print('-' * 80)


if __name__ == '__main__':
    main()
