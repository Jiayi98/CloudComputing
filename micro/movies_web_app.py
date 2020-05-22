import os
import time

from flask import request
from flask import Flask, render_template
import mysql.connector
from mysql.connector import errorcode


application = Flask(__name__)
app = application
    
def create_db():
    username = os.environ.get("USER", None) or os.environ.get("username", None)
    password = os.environ.get("PASSWORD", None) or os.environ.get("password", None)
    hostname = os.environ.get("HOST", None) or os.environ.get("dbhost", None)
    print('In create db ~~~~~~~~', username, password, hostname)
    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password)

    cur = cnx.cursor()

    cur.execute("CREATE DATABASE IF NOT EXISTS mymovies;")
    cur.execute("USE mymovies;")
    # for x in cur:
    #    print(x)
    cnx.commit()

def get_db_creds():
    # db = os.environ.get("DB", None) or os.environ.get("database", None)
    username = os.environ.get("USER", None) or os.environ.get("username", None)
    password = os.environ.get("PASSWORD", None) or os.environ.get("password", None)
    hostname = os.environ.get("HOST", None) or os.environ.get("dbhost", None)
    db = "mymovies"
    print('~~~~~~~~',db, username, password, hostname)
    return db, username, password, hostname
   
def create_movies_table():
    # Check if table exists or not. Create and populate it only if it does not exist.
    db, username, password, hostname = get_db_creds()
    table_ddl = 'DROP TABLE IF EXISTS movies; CREATE TABLE movies(ID INT UNSIGNED NOT NULL AUTO_INCREMENT, ' \
                'Year TEXT, ' \
                'Title TEXT,' \
                'Director TEXT,' \
                'Actor TEXT,' \
                'Release_Date TEXT,' \
                'Rating FLOAT,' \
                'PRIMARY KEY (ID))'

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        #try:
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)
        #except Exception as exp1:
        #    print(exp1)

    cur = cnx.cursor()

    try:
        cur.execute(table_ddl)
        cnx.commit()
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)

@app.route('/add_movie', methods=['POST'])
def add_movie():
    print("Received request.")
    year = request.form['year']
    title = request.form['title']
    director = request.form['director']
    actor = request.form['actor']
    release_date = request.form['release_date']
    rating = request.form['rating']

    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)

    cur = cnx.cursor()

    # check if the title is unique
    cur.execute("SELECT * FROM movies WHERE Upper(Title)='{}'".format(title.upper()))
    rows = cur.fetchall()
    if len(rows) > 0:
        msg = 'Failure message: "Movie {} could not be inserted - already exist"'.format(title)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', message=msg)

    try:
        insert_stmt = (
            "INSERT INTO movies (Year, Title, Director, Actor, Release_date, Rating) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        data = (year, title, director, actor, release_date, rating)
        cur.execute(insert_stmt, data)
        cnx.commit()
    except mysql.connector.Error as err:
        print(err.msg)
        cur.close()
        cnx.close()
        msg = "Failure message: Movie {} could not be inserted- {}".format(title, err.msg)
        return render_template('index_movies.html', message=msg)

    # successfully inserted
    message = 'Success message: "Movie {} successfully inserted"'.format(title)
    cur.close()
    cnx.close()
    return render_template('index_movies.html', message=message)


@app.route('/update_movie', methods=['POST'])
def update_movie():
    print("Received request.")
    title = request.form['title']
    if len(title) == 0:
        return render_template('index_movies.html', message='Failure message: Title can not be empty')

    year = request.form['year']
    director = request.form['director']
    actor = request.form['actor']
    release_date = request.form['release_date']
    rating = request.form['rating']

    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)

    cur = cnx.cursor()
    cur.execute("SELECT * FROM movies WHERE Upper(Title)='{}'".format(title.upper()))
    rows = cur.fetchall()
    # movie does not exist
    if len(rows) == 0:
        msg = 'Failure message: "Movie with {} does not exist"'.format(title)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', message=msg)
    else:
        # if any empty input, then keep value unchanged
        for row in rows:
            if not year:
                year = row[1]
            if not director:
                director = row[3]
            if not actor:
                actor = row[4]
            if not release_date:
                release_date = row[5]
            if not rating:
                rating = row[6]
    try:
        # update, case sensitive matching, title should be exactly same
        update_stmt = "UPDATE movies SET Year='{}', Director='{}', Actor='{}', Release_date='{}', Rating='{}' WHERE Title='{}';".format(year, director, actor, release_date, rating, title)
        cur.execute(update_stmt)
        cnx.commit()
    except mysql.connector.Error as err:
        print(err.msg)
        cur.close()
        cnx.close()
        msg = 'Failure message: "Movie {} could not be updated- {}"'.format(title, err.msg)
        return render_template('index_movies.html', message=msg)

    # successfully updated
    message = 'Success message: "Movie {} successfully updated"'.format(title)
    cur.close()
    cnx.close()
    return render_template('index_movies.html', message=message)


@app.route('/delete_movie', methods=['POST'])
def delete_movie():
    print("Received request.")
    title = request.form['delete_title']
    if len(title) == 0:
        return render_template('index_movies.html', message='Failure message: Title can not be empty')

    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)

    cur = cnx.cursor()
    # case insensitive matching
    cur.execute("SELECT * FROM movies WHERE Upper(Title)='{}'".format(title.upper()))
    rows = cur.fetchall()
    # movie does not exist
    if len(rows) == 0:
        msg = 'Failure message: "Movie with {} does not exist"'.format(title)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', message=msg)

    try:
        delete_stm = "DELETE FROM movies WHERE Title='{}';".format(title)
        cur.execute(delete_stm)
        cnx.commit()
    except mysql.connector.Error as err:
        print(err.msg)
        reason = err.msg
        msg = 'Failure message: "Movie {} could not be deleted - {}"'.format(title, reason)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', message=err.msg)
    # successfully delete
    msg = 'Success message: "Movie {} successfully deleted"'.format(title)
    cur.close()
    cnx.close()
    return render_template('index_movies.html', message=msg)


@app.route('/search_movie', methods=['POST'])
def search_movie():
    print("Received request.")
    actor = request.form['search_actor']
    if len(actor) == 0:
        return render_template('index_movies.html', message='Failure message: Actor can not be empty')

    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)

    cur = cnx.cursor()
    try:
        # case insensitive matching
        cur.execute("SELECT Title, Year, Actor FROM movies WHERE Upper(Actor)='{}'".format(actor.upper()))
        rows = cur.fetchall()
    except mysql.connector.Error as err:
        print(err.msg)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', message=err.msg)

    if len(rows) == 0:
        msg = 'Message: "No movies found for actor {}"'.format(actor)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', message=msg)
    else:
        entries = []
        for row in rows:
            res = "<{}, {}, {}>".format(row[0], row[1], row[2])
            entries.append(res)
        cur.close()
        cnx.close()
        return render_template('index_movies.html', entries=entries)


@app.route('/highest_rating', methods=['GET'])
def highest_rating():

    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)

    cur = cnx.cursor()
    try:
        cur.execute("SELECT Title, Year, Actor, Director, Rating FROM movies " 
                    "JOIN (SELECT MAX(Rating) as highest " 
                    "FROM movies )t1 " 
                    "ON Rating = t1.highest " 
                    "WHERE Rating = t1.highest;")
        rows = cur.fetchall()
    except mysql.connector.Error as err:
        print(err.msg)
        return render_template('index_movies.html', message=err.msg)
    entries = []
    for row in rows:
        res = "<{}, {}, {}, {}, {}>".format(row[0], row[1], row[2], row[3], row[4])
        entries.append(res)

    cur.close()
    cnx.close()
    return render_template('index_movies.html', entries=entries)


@app.route('/lowest_rating', methods=['GET'])
def lowest_rating():
    print("Received request.")

    db, username, password, hostname = get_db_creds()

    cnx = ''
    try:
        cnx = mysql.connector.connect(user=username, password=password,
                                      host=hostname,
                                      database=db)
    except Exception as exp:
        print(exp)
        import pymysql
        cnx = pymysql.connect(unix_socket=hostname, user=username, passwd=password, db=db)

    cur = cnx.cursor()
    try:
        cur.execute("SELECT Title, Year, Actor, Director, Rating FROM movies "
                    "JOIN (SELECT MIN(Rating) as lowest "
                    "FROM movies )t1 "
                    "ON Rating = t1.lowest "
                    "WHERE Rating = t1.lowest;")
        rows = cur.fetchall()
    except mysql.connector.Error as err:
        print(err.msg)
        return render_template('index_movies.html', message=err.msg)

    entries = []
    for row in rows:
        res = "<{}, {}, {}, {}, {}>".format(row[0], row[1], row[2], row[3], row[4])
        entries.append(res)
    cur.close()
    cnx.close()
    return render_template('index_movies.html', entries=entries)



@app.route('/')
def hello_movies():
    print("Inside hello")
    print("Printing available environment variables")
    create_db()
    create_movies_table()
    print(os.environ)
    print("Before displaying index_movies.html")
    return render_template('index_movies.html',)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
