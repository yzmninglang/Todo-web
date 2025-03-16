from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import calendar

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATABASE'] = 'todo.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database functions
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        db.commit()

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_week_dates(date):
    """Get start and end dates for the week containing the given date"""
    start_of_week = date - timedelta(days=date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

# Make helper functions available to templates
@app.context_processor
def utility_processor():
    return dict(get_week_dates=get_week_dates)

# Routes
@app.route('/')
def index():
    view_type = request.args.get('view', 'daily')
    selected_date = request.args.get('date')
    
    # Default to today if no date is selected
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()
    
    db = get_db()
    
    # Get incomplete todos
    incomplete_todos = db.execute(
        'SELECT * FROM todos WHERE completed = 0 ORDER BY created DESC'
    ).fetchall()
    
    # Get completed todos based on view type
    if view_type == 'daily':
        completed_todos = db.execute(
            'SELECT * FROM todos WHERE completed = 1 AND date(completed_at) = date(?) ORDER BY completed_at DESC',
            (selected_date,)
        ).fetchall()
    elif view_type == 'weekly':
        start_date, end_date = get_week_dates(selected_date)
        completed_todos = db.execute(
            'SELECT * FROM todos WHERE completed = 1 AND date(completed_at) BETWEEN date(?) AND date(?) ORDER BY completed_at DESC',
            (start_date, end_date)
        ).fetchall()
    
    # Calculate previous and next days/weeks for navigation
    if view_type == 'daily':
        prev_date = selected_date - timedelta(days=1)
        next_date = selected_date + timedelta(days=1)
    else:  # weekly
        prev_date = selected_date - timedelta(weeks=1)
        next_date = selected_date + timedelta(weeks=1)
    
    # Generate calendar data for the current month
    cal = calendar.monthcalendar(selected_date.year, selected_date.month)
    month_name = calendar.month_name[selected_date.month]
    
    return render_template(
        'index.html', 
        incomplete_todos=incomplete_todos,
        completed_todos=completed_todos,
        selected_date=selected_date,
        view_type=view_type,
        prev_date=prev_date,
        next_date=next_date,
        calendar_data=cal,
        month_name=month_name,
        current_year=selected_date.year,
        current_month=selected_date.month
    )

# Rest of the code remains the same...
@app.route('/create', methods=['POST'])
def create_todo():
    title = request.form.get('title')
    description = request.form.get('description')
    
    if not title:
        flash('Title is required!')
        return redirect(url_for('index'))
        
    # Image handling
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid duplicates
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            image_filename = f"{timestamp}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
    
    db = get_db()
    db.execute(
        'INSERT INTO todos (title, description, image_path, created) VALUES (?, ?, ?, ?)',
        (title, description, image_filename, datetime.now())
    )
    db.commit()
    flash('Todo added successfully!')
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update_todo(id):
    completed = request.form.get('completed') == 'on'
    
    db = get_db()
    if completed:
        # If marked as completed, set completed_at timestamp
        db.execute(
            'UPDATE todos SET completed = ?, completed_at = ? WHERE id = ?',
            (completed, datetime.now(), id)
        )
    else:
        # If unmarked, clear completed_at timestamp
        db.execute(
            'UPDATE todos SET completed = ?, completed_at = NULL WHERE id = ?',
            (completed, id)
        )
    db.commit()
    flash('Todo updated successfully!')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_todo(id):
    db = get_db()
    
    # Get image path before deleting
    todo = db.execute('SELECT image_path FROM todos WHERE id = ?', (id,)).fetchone()
    
    if todo['image_path']:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], todo['image_path']))
        except OSError:
            pass  # File may not exist
    
    db.execute('DELETE FROM todos WHERE id = ?', (id,))
    db.commit()
    flash('Todo deleted successfully!')
    return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    flash('File is too large! Maximum size is 16MB.')
    return redirect(url_for('index'))

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

if __name__ == '__main__':
    app.run(debug=True)