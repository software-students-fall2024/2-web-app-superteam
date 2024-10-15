from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Set up MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
print(mongo_uri)

client = MongoClient(mongo_uri)
db = client['library'] 
books_collection = db['books']

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Using "user" and "password" as the login credentials
        if username == "user" and password == "password":
            return redirect(url_for('test'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

@app.route('/test', methods=['GET', 'POST'])
def test():
    books = []
    if request.method == 'POST':
        search_query = request.form['search']
        books = list(books_collection.find({'title': {'$regex': search_query, '$options': 'i'}}))
        print("Books matching search:", books)
    else:
        books = list(books_collection.find())
        print("All books:", books)
    return render_template('test.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add():
    title = request.args.get('title')
    if request.method == 'POST':
        title = request.args.get('title')
        quantity = int(request.form.get('book-quantity'))
        if title:
            books_collection.update_one({'title': title}, {'$inc': {'quantity': quantity}}, upsert=True)
            flash(f'Added {quantity} copy/copies of "{title}".', 'success')
            return redirect(url_for('test'))
    return render_template('add.html', title=title)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    title = request.args.get('title')
    if request.method == 'POST':
        title = request.args.get('title')
        quantity = int(request.form.get('book-quantity'))
        if title:
            books_collection.update_one({'title': title}, {'$inc': {'quantity': -quantity}})
            books_collection.delete_one({'title': title, 'quantity': {'$lte': 0}})
            flash(f'Deleted {quantity} copy/copies of "{title}".', 'info')
            return redirect(url_for('test'))
    return render_template('delete.html', title=title)

@app.route('/calendar')
def calendar():
    books = list(books_collection.find({'due_date': {'$exists': True}}))
    return render_template('calendar.html', books=books)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    title = request.args.get('title')
    author = request.args.get('author')
    
    if request.method == 'POST':
        # Assuming the edit form has fields for title and author to update
        new_title = request.form.get('title')
        new_author = request.form.get('author')

        # Update the book in the database
        books_collection.update_one(
            {'title': title, 'author': author},
            {'$set': {'title': new_title, 'author': new_author}}
        )
        flash(f'Updated book "{title}" to "{new_title}" by "{new_author}".', 'success')
        return redirect(url_for('test'))

    return render_template('edit.html', title=title, author=author)

@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        # Assuming the edit form has fields for title and author to update
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = request.form.get('quantity')
        due_date = request.form.get('due_date')
        book = {
            'title': title,
            'author': author,
            'quantity': int(quantity),  
            'due_date': due_date
        }
        books_collection.insert_one(book)

    return render_template('new.html')

if __name__ == '__main__':
    app.run(debug=True)
