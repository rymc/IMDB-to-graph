import sqlite3
VERTEX = False

def open_connection():
    conn = sqlite3.connect('imdb.db')
    cursor = conn.cursor()

    return conn, cursor

stop_words = set()
with open('stop_words') as r:
    for line in r:
        stop_words.add(line.strip())

from nltk import word_tokenize
from nltk.corpus import wordnet as wn

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

from collections import defaultdict

actor_mapping = defaultdict(list)
movie_mapping = defaultdict(list)

import json, pprint
count = 0
conn, cursor = open_connection()


#for each movie create a list of actors and relevant features
# here it is producers and directors and plot keywords
count = 0
genre_count = defaultdict(int)
with open('movies.json', 'w') as w:
    with open('movie_ids.csv') as r:
        for movie_id in r:
            no_plot = False
            movies = defaultdict(set)
            genre=cursor.execute("SELECT distinct(movie_info.info) from movie_info where movie_info.info_type_id=3 and movie_info.movie_id="+movie_id)
            genre = genre.fetchall()   
            if len(genre) != 1 or genre_count[genre[0][0]] >= 2500:
                continue

            movies = defaultdict(lambda: defaultdict(list))
            movie_id = movie_id.rstrip()
            movie_mapping[movie_id] = genre[0][0]
            actors=cursor.execute("SELECT distinct(cast_info.person_id) from cast_info join movie_info on cast_info.movie_id = movie_info.movie_id where (cast_info.role_id=1 or cast_info.role_id=2) and movie_info.movie_id="+movie_id)
            
            actors = actors.fetchall()
            actors = [actor[0] for actor in actors]
            for actor in actors:
                movies[movie_id][actor] = []
            for actor in actors:
                for movie_actor in movies[movie_id]:
                    if actor != movie_actor:
                        movies[movie_id][actor].append((movie_actor, 0))
            

                producers=cursor.execute("SELECT distinct(cast_info.person_id) from cast_info join movie_info on cast_info.movie_id = movie_info.movie_id where cast_info.role_id=3 and movie_info.movie_id="+movie_id)

                producers = producers.fetchall()
                producers = [producer[0] for producer in producers]
                for producer in producers:
                    movies[movie_id][actor].append((producer, 1))


                directors=cursor.execute("SELECT distinct(cast_info.person_id) from cast_info join movie_info on cast_info.movie_id = movie_info.movie_id where cast_info.role_id=8 and movie_info.movie_id="+movie_id)

                directors = directors.fetchall()
                directors = [director[0] for director in directors]
                for director in directors:
                     movies[movie_id][actor].append((director, 2))
            
                plot=cursor.execute("SELECT distinct(movie_info.info) from movie_info where movie_info.info_type_id=98 and movie_info.movie_id="+movie_id)


                plot = plot.fetchone()
                if plot is None:
                    no_plot = True
                    break
                else:
                    tokens = word_tokenize(plot[0])
                    for token in tokens:
                        token = token.lower()
                        token = token.replace(".", "")
                        token = token.replace(",", "")
                        if token not in stop_words and wn.synsets(token):
                            movies[movie_id][actor].append((token,3))
                                    
                movies[movie_id][actor].append((movie_id, 4))

            if len(movies[movie_id]) > 0 and not no_plot:
                genre_count[genre[0][0]] += 1
                json.dump(movies[movie_id], w)
                w.write("\n")

                for actor in actors:
                    actor_mapping[actor].append(genre[0][0])

print genre_count
print "actors " + str(len(actor_mapping))
ctr = defaultdict(int)
ctr_no_maj = 0
ctr_maj = 0
if VERTEX:
    from collections import Counter
    with open('map.csv', 'w') as w:
        for actor, genres in actor_mapping.iteritems():
            ctr[str(len(set(genres)))] += 1
            genres_c = Counter(genres).most_common()
            w.write(str(actor)+"\t")
            w.write(genres_c[0][0])
            if len(set(genres)) > 1:
                top = genres_c[0][1]
                if genres_c[1][1] == top:
                    w.write("\t"+genres_c[1][0])
                    ctr_no_maj += 1

                    if len(set(genres)) > 2 and genres_c[2][1] == top:
                        w.write("\t"+genres_c[2][0])
                        if len(set(genres)) > 3 and genres_c[3][1] == top:
                            w.write("\t"+genres_c[3][0])
                        if len(set(genres)) > 4 and genres_c[4][1] == top:
                            w.write("\t"+genres_c[4][0])
                else:
                    ctr_maj += 1


            w.write("\n")
    #        if len(genres) == 1:

    print ctr

    print ctr_no_maj
    print ctr_maj

else:
    # this is for gssclu
    from collections import Counter
    with open('movie-map.csv', 'w') as w:
        for movie, genre in movie_mapping.iteritems():
            w.write(str(movie)+"\t")
            w.write(genre)
            w.write("\n")

