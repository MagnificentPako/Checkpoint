from flask import Flask, request, render_template, flash, redirect, g
import sqlite3
import uuid
import hashlib
import markdown
from html_sanitizer import Sanitizer

app = Flask(__name__)
app.secret_key = b'i\x18\xeb\x19L\xf66\x9d\xd5j5\x0c\xae\x94\xc8\x1f'

DATABASE = './checkpoint.db'

sanitizer = Sanitizer()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        return upload_checkpoint()
    else:
        return render_template('index.html')

def upload_checkpoint():
    checkpoint = request.form['checkpoint']
    if not checkpoint:
        flash("Checkpoint can't be empty!")
        return redirect('/')
    db = get_db()
    c = db.cursor()
    edit_password = str(uuid.uuid4())
    checkpoint_id = str(uuid.uuid4().hex)
    password_hash = hashlib.sha512(edit_password.encode('utf-8')).hexdigest()
    checkpoint_html = markdown.markdown(checkpoint)
    checkpoint_sanitized = sanitizer.sanitize(checkpoint_html)
    flash("Password used to delete this Checkpoint: " + edit_password)
    c.execute('INSERT INTO checkpoint(id, checkpoint, password_hash) VALUES(?, ?, ?)', (checkpoint_id, checkpoint_sanitized, password_hash))
    db.commit()
    return redirect('/' + checkpoint_id)

@app.route('/<checkpoint_id>')
def show_checkpoint(checkpoint_id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT checkpoint FROM checkpoint WHERE id = ?", (checkpoint_id,))
    res = c.fetchone()
    if not res:
        return redirect('/')
    return render_template('checkpoint.html', content=res[0], checkpoint_id=checkpoint_id)

@app.route('/<checkpoint_id>/delete', methods = ['GET', 'POST'])
def checkpoint_delete(checkpoint_id):
    if request.method == 'POST':
        return delete_checkpoint(checkpoint_id)
    else:
        return show_delete(checkpoint_id)

def delete_checkpoint(checkpoint_id):
    password = request.form['password']
    if not password:
        return redirect('/' + checkpoint_id + '/delete')
    password_hash = hashlib.sha512(password.encode('utf-8')).hexdigest()
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id FROM checkpoint WHERE id = ? AND password_hash = ?', (checkpoint_id, password_hash))
    db.commit()
    res = c.fetchone()
    if not res:
        flash('Wrong password!')
        return redirect('/' + checkpoint_id + '/delete')
    c.execute('DELETE FROM checkpoint WHERE id = ?', (checkpoint_id,))
    db.commit()
    return redirect('/')

def show_delete(checkpoint_id):
    return render_template("delete.html", checkpoint_id=checkpoint_id)