import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify

app = Flask(__name__)

USD_PER_INC = 0
USD_PER_LAP = 0

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'restoran.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('RESTORAN_SETTINGS', silent=True)

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/admin')
def admin():
    db = get_db()
    cur = db.execute('select english_name, chinese_name, price, image_url from meals')
    meals = cur.fetchall()
    return render_template('admin.html', meals=meals)

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('select english_name, chinese_name, price, image_url from meals')
    meals = cur.fetchall()
    return render_template('index.html', meals=meals)

@app.route('/remove_meal', methods=['POST'])
def remove_meal():
    if not session.get('logged_in'):
        abort(401)
    english_name = request.form['english-name']
    db = get_db()
    print(english_name)
    command = "delete from meals where english_name=?"
    command_args = (english_name,)
    db.execute(command, command_args)
    db.commit()
    flash('Meal successfully removed.')
    return redirect(url_for('admin'))

@app.route('/add_meal', methods=['POST'])
def add_meal():
    if not session.get('logged_in'):
        abort(401)
    english_name, chinese_name, price, image_url = request.form['english-name'], request.form['chinese-name'], request.form['price'], request.form['image-url']
    db = get_db()
    cur = db.execute('select english_name from meals')
    english_names = [row[0] for row in cur.fetchall()]
    if english_name not in english_names:
        if not english_name:
            flash('You must specify the name of the meal you wish to add or update.')
            return redirect(url_for('admin'))
        if not price:
            flash('You must specify the price of the meal you wish to add or update.')
            return redirect(url_for('admin'))
        if not chinese_name:
            chinese_name = ""
        if not image_url:
            image_url = "http://i.imgur.com/baZu5v9.gif"
        command = "insert into meals (english_name, chinese_name, price, image_url) values (?, ?, ?, ?)"
        command_args = [english_name, chinese_name, price, image_url]
    else:
        if not english_name:
            flash('You must specify the name of the meal you wish to add or update.')
            return redirect(url_for('admin'))
        command_args = [english_name]
        command = "update meals set english_name=?"
        if chinese_name:
            command += ", chinese_name=?"
            command_args.append(chinese_name)
        if price:
            command += ", price=?"
            command_args.append(price)
        if image_url:
            command += ", image_url=?"
            command_args.append(image_url)
        command += " where [english_name]=?;"
        command_args.append(english_name)
    db.execute(command, command_args)
    db.commit()
    flash('Meal successfully added or updated.')
    return redirect(url_for('admin'))

@app.route('/get_meals', methods=['GET'])
def get_meals():
    db = get_db()
    cur = db.execute('select * from meals')
    elements = cur.fetchall()
    return jsonify([dict(zip(row.keys(), row)) for row in elements])

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('admin'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()
