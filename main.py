from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
import mysql.connector
from datetime import date
import bcrypt
import smtplib

smpt_server = 'smpt.gmail.com'
port = 587


con = mysql.connector.connect(user='admin', password='BybByb1234!?',host='forum-database.c9u8kasekpqr.eu-north-1.rds.amazonaws.com',database ='forum')

cursor = con.cursor()

app = Flask(__name__)

app.secret_key = 'secretkey'

@app.route("/")
@app.route('/login', methods = ['GET','POST'])
def login():                                                                                        # strona logowania
    msg =''
    if request.method == "POST" and 'username' in request.form and 'password' in request.form:
        username = request.form['username']                                                         # pobieranie danych logowania od użytkownika
        password = request.form['password'].encode('utf-8')
        cursor.execute('SELECT * FROM users WHERE username = %s ', (username,))     # wyszukiwanie użytkownika w tabeli users bazy danych
        user = cursor.fetchone()
        print(user)
        if not user:
            msg = "Błędne dane logowania!"
        else:
            passwd_hash = user[3].encode('utf-8')

            if bcrypt.checkpw(password,passwd_hash):                                                # sprawdzanie hasła
                session['loggedin'] = True
                session["id"] = user[0]
                session["username"] = user[1]
                print(session)
                return redirect(url_for('index'))                                                   # przekierowanie na stronę główną
            else:
                msg = "Błędne dane logowania!"

    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.clear()                                                                                  # czyszczenie sesji

    return redirect(url_for('login'))                                                                # przekierowanie na stronę rejestracji


@app.route('/register', methods = ['GET', 'POST'])                                              # strona rejestracji
def register(): 
    msg =''
    if request.method == "POST" and 'email' in request.form and 'username' in request.form and 'password' in request.form:

        email = request.form['email']
        username = request.form['username']                                                         # pobieranie danych konta od użytkownika
        password = request.form['password'].encode('utf-8')
        cursor.execute('SELECT email, username FROM users WHERE username = %s OR email = %s', (username, email))
        user_exists = cursor.fetchone()
        if user_exists:
            if user_exists[0]==email:                                                               # sprawdzanie czy dane konta nie zostały już użyte
                msg = "Konto istnieje"
                username_value = username
                return render_template('register.html', msg=msg, username_value=username_value)
            elif user_exists[1]==username:
                msg = "Konto już istnieje"
                email_value = email
                return render_template('register.html', msg=msg, email_value=email_value)
        else:
            hash = bcrypt.hashpw(password, bcrypt.gensalt())                                        # hashowanie hasła z solą
            password_hashed = hash.decode('utf-8')
            cursor.execute('INSERT INTO  users (email,username,password_hash) values (%s, %s, %s)', (email,username,password_hashed))
            con.commit()                                                                            # wprowadzenie danych konta do bazy danych
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            session['loggedin'] = True
            session["id"] = user[0]
            session["username"] = user[2]
            return redirect(url_for('login'))
    return render_template('register.html', msg=msg)


@app.route("/index", methods = ['GET','POST'])                                                 # strona główna
def index():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    cursor.execute('SELECT posts.id, posts.title, posts.content, posts.created_at, users.username FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.created_at DESC')
    posts_data = cursor.fetchall()                                                                  # pobieranie wszystkich postów
    posts = []
    for post in posts_data:
        cursor.execute('SELECT comments.content, comments.user_id, users.id FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id = %s ORDER BY comments.created_at DESC',(post[0],))
        comments = cursor.fetchall()                                                                # pobieranie komentarzy do każdego posta
        posts.append({
            'id': post[0],
            'title': post[1],
            'content': post[2],
            'created_at': post[3],
            'username': post[4],
            'comments': [{'content': c[0], 'created_at': c[1], 'username': c[2]} for c in comments],
            'comment_count': len(comments)
        })
    return render_template('index.html', username = session['username'], posts = posts)



@app.route("/add_post", methods = ['GET','POST'])                                              # strona tworzenia nowego posta
def add_post():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form['post_title']                                                          # pobieranie zawartości posta
        content = request.form['content']
        cursor.execute('INSERT INTO posts (user_id,title,content) VALUES (%s,%s,%s)', (session['id'], title,content))
        con.commit()                                                                                # dodawanie zawartości posta do bazy danych
        return redirect(url_for('index'))
    return render_template('add_post.html',username = session['username'])


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])                                      # strona wyświetlania posta
def view_post(post_id):
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    cursor.execute(
        'SELECT posts.id, posts.title, posts.content, posts.created_at, users.username '
        'FROM posts JOIN users ON posts.user_id = users.id WHERE posts.id = %s',
        (post_id,)
    )
    post = cursor.fetchone()                                                                        # pobieranie posta
    if not post:
        return "Post nie istnieje", 404

    cursor.execute(
        'SELECT comments.id, comments.content, comments.created_at, users.username '
        'FROM comments JOIN users ON comments.user_id = users.id '
        'WHERE comments.post_id = %s ORDER BY comments.created_at ASC',
        (post_id,)
    )
    comments_data = cursor.fetchall()                                                               # pobieranie komentarzy do posta
    comments = [{'id': c[0], 'content': c[1], 'created_at': c[2], 'username': c[3]} for c in comments_data]

    if request.method == "POST":
        content = request.form['content']
        if content.strip() != "":                                                                   # dodawanie komentarza
            cursor.execute(
                'INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)',
                (post_id, session['id'], content)
            )
            con.commit()
            return redirect(url_for('view_post', post_id=post_id))                          # odświeżenie strony z nowym komentarzem

    post_dict = {
        'id': post[0],
        'title': post[1],
        'content': post[2],
        'created_at': post[3],
        'username': post[4],
        'comments': comments
    }

    return render_template('view_post.html', post=post_dict, username=session['username'])


@app.route('/health')
def health():
    return 'OK', 200

app.run("0.0.0.0",port="4999")

