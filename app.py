# Make sure that you pip install all the libraries before running the project
from flask import Flask, render_template, request
import difflib
from imdb import IMDb
import imdb
import requests
import pickle

app = Flask(__name__)

ia = IMDb()
movies = pickle.load(open('artifacts/new_df.pkl', 'rb'))
similarity = pickle.load(open('artifacts/similarity_new.pkl', 'rb'))

# First Page Function and Route
@app.route('/')
def home():
    url = 'https://api.themoviedb.org/3/movie/latest'
    params = {'api_key': '8e95934e4df34e2fb4934f3b34b18f58', 'language': 'en-US'}
    response = requests.get(url, params=params)
    data = response.json()
    ia = imdb.IMDb()
    movies = ia.get_top250_movies()[:10]

    imdb_id = response.json()['imdb_id']
    imdb_url = None
    if imdb_id is not None:
        imdb_url = f'https://www.imdb.com/title/{imdb_id}'

    return render_template('page1.html', data=data, movies=movies, imdb_url=imdb_url )  

# Additional Second Page functions
def get_imdb_url(movie_name):
        search_results = ia.search_movie(movie_name)
        if search_results:
            movie_id = search_results[0].getID()
            return ia.get_imdbURL(ia.get_movie(movie_id))

def get_imdb_rating(imdb_id):
    movie = ia.get_movie(imdb_id)
    if 'rating' in movie:
        return movie['rating']
    else:
        return None

movies_list = movies['title'].values

def recommend(movie_name, num_movies):
        list_of_all_titles = movies['title'].tolist()
        find_close_match = difflib.get_close_matches(
            movie_name, list_of_all_titles)
        close_match = find_close_match[0]
        index_of_the_movie = movies[movies['title'] == close_match].index[0]
        similarity_score = list(enumerate(similarity[index_of_the_movie]))
        sorted_similar_movies = sorted(
            similarity_score, key=lambda x: x[1], reverse=True)
        recommended_movie_names = []
        i = 1
        for movie in sorted_similar_movies:
            index = movie[0]
            title_from_index = movies[movies.index == index]['title'].values[0]
            if (title_from_index == movie_name):
                continue
            if (i <= num_movies):
                recommended_movie_names.append(title_from_index)
                i += 1
            else:
                break
        return recommended_movie_names

# Second Page Main Function and Route
@app.route('/recommend', methods=['GET', 'POST'])
def page2():
    if request.method == 'POST':

        selected_movie = request.form.get('selected_movie')
        num_movies = int(request.form.get('num_movies'))
        sort_order = request.form.get('sort_order')

        recommended_movie_names = recommend(selected_movie, num_movies)
        if sort_order == 'asc':
            recommended_movie_names = sorted(recommended_movie_names, key=lambda x: get_imdb_rating(
                ia.search_movie(x)[0].getID()) or 0)
        else:
            recommended_movie_names = sorted(recommended_movie_names, key=lambda x: get_imdb_rating(
                ia.search_movie(x)[0].getID()) or 0, reverse=True)
        
        movie_data = {}
        for movie_name in recommended_movie_names:
                movie = ia.search_movie(movie_name)[0]
                imdb_url = get_imdb_url(movie_name)
                imdb_id = movie.getID()
                rating = get_imdb_rating(imdb_id)
                cover_url = movie.data["cover url"]
                movie_data[movie_name] = {
                    'imdb_url': imdb_url,
                    'imdb_id': imdb_id,
                    'cover_url': cover_url,
                    'rating': rating
                }
        return render_template('page2.html', movies=movies_list, recommended_movie_names=recommended_movie_names, movie_data=movie_data,get_imdb_rating=get_imdb_rating)

    return render_template('page2.html', movies=movies_list)


if __name__ == '__main__':
    app.run(debug=True)