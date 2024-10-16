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


@app.route('/quantity', methods=['GET', 'POST'])
def quantity():
    title = request.args.get('title')
    book = books_collection.find_one({'title': title})
    
    if request.method == 'POST':
        new_quantity = int(request.form.get('new_quantity'))
        
        if new_quantity == 0:
            # Delete the book entry if the new quantity is 0
            books_collection.delete_one({'title': title})
            flash(f'Book "{title}" has been removed from the library.', 'info')
        else:
            # Get current due_dates array
            due_dates = book.get('due_dates', [])
            current_quantity = len(due_dates)

            if new_quantity > current_quantity:
                # Add new available entries (null) to due_dates
                due_dates.extend([None] * (new_quantity - current_quantity))
            elif new_quantity < current_quantity:
                # Remove entries starting from available copies
                due_dates = [date for date in due_dates if date is not None] + [None] * new_quantity
                due_dates = due_dates[:new_quantity]

            # Update book record with new due_dates array and quantity
            books_collection.update_one(
                {'title': title},
                {'$set': {
                    'due_dates': due_dates,
                    'quantity': new_quantity
                }}
            )
            flash(f'Successfully updated quantity for "{title}" to {new_quantity}.', 'success')

        return redirect(url_for('test'))

    return render_template('quantity.html', title=title, quantity=book['quantity'])

# Replacing the old delete page with a new lending page
@app.route('/lend', methods=['GET', 'POST'])
def lend():
    title = request.args.get('title')
    book = books_collection.find_one({'title': title})

    if request.method == 'POST':
        due_date = request.form.get('due_date')
        # Find the first available copy (None) in due_dates and assign a due date
        for i in range(len(book['due_dates'])):
            if book['due_dates'][i] is None:
                book['due_dates'][i] = due_date
                break

        books_collection.update_one(
            {'title': title},
            {'$set': {'due_dates': book['due_dates']}}
        )
        flash(f'Successfully lent out "{title}" with due date {due_date}.', 'success')
        return redirect(url_for('test'))

    available_count = sum(1 for due_date in book['due_dates'] if due_date is None)
    return render_template('lend.html', title=title, available_count=available_count)


@app.route('/calendar')
def calendar():
    books = list(books_collection.find({'due_dates': {'$exists': True}}))
    
    for book in books:
        available_count = sum(1 for due_date in book['due_dates'] if due_date is None)
        book['available_count'] = available_count
    
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
@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':

        title = request.form.get('title')
        author = request.form.get('author')
        quantity = int(request.form.get('quantity'))
    
        due_dates = [None] * quantity
        
        book = {
            'title': title,
            'author': author,
            'quantity': quantity,
            'due_dates': due_dates
        }

        books_collection.insert_one(book)
        
        flash(f'New book "{title}" by {author} added with quantity {quantity}.', 'success')
        return redirect(url_for('test'))

    return render_template('new.html')

if __name__ == '__main__':
    app.run(debug=True)
