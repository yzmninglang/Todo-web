import os
import sqlite3
from datetime import datetime
from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

# Configuration
DATABASE = 'todo.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
Default_Calendar = 'weekly'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.secret_key = 'your_secret_key'  # Replace with a real secret key in production

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection helpers
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Initialize the database
@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')

# Routes
@app.route('/')
def index():
    db = get_db()
    incomplete_tasks = db.execute(
        'SELECT * FROM tasks WHERE is_completed = 0 ORDER BY created_at DESC'
    ).fetchall()
    
    completed_tasks = db.execute(
        'SELECT * FROM tasks WHERE is_completed = 1 ORDER BY completed_at DESC'
    ).fetchall()
    
    return render_template('index.html', 
                           incomplete_tasks=incomplete_tasks, 
                           completed_tasks=completed_tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form.get('description', '')
    image_path = None
    
    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = os.path.join('uploads', filename)
    
    db = get_db()
    db.execute(
        'INSERT INTO tasks (title, description, image_path) VALUES (?, ?, ?)',
        (title, description, image_path)
    )
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    db = get_db()
    db.execute(
        'UPDATE tasks SET is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?',
        (task_id,)
    )
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/uncomplete_task/<int:task_id>', methods=['POST'])
def uncomplete_task(task_id):
    db = get_db()
    db.execute(
        'UPDATE tasks SET is_completed = 0, completed_at = NULL WHERE id = ?',
        (task_id,)
    )
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    db = get_db()
    # Delete subtasks first
    db.execute('DELETE FROM subtasks WHERE task_id = ?', (task_id,))
    # Then delete the task
    db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/add_subtask/<int:task_id>', methods=['POST'])
def add_subtask(task_id):
    title = request.form['title']
    
    db = get_db()
    db.execute(
        'INSERT INTO subtasks (task_id, title) VALUES (?, ?)',
        (task_id, title)
    )
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/complete_subtask/<int:subtask_id>', methods=['POST'])
def complete_subtask(subtask_id):
    db = get_db()
    db.execute(
        'UPDATE subtasks SET is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?',
        (subtask_id,)
    )
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/delete_subtask/<int:subtask_id>', methods=['POST'])
def delete_subtask(subtask_id):
    db = get_db()
    db.execute('DELETE FROM subtasks WHERE id = ?', (subtask_id,))
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/get_subtasks/<int:task_id>')
def get_subtasks(task_id):
    db = get_db()
    subtasks = db.execute(
        'SELECT * FROM subtasks WHERE task_id = ? ORDER BY created_at ASC',
        (task_id,)
    ).fetchall()
    
    result = []
    for subtask in subtasks:
        result.append({
            'id': subtask['id'],
            'title': subtask['title'],
            'created_at': subtask['created_at'],
            'completed_at': subtask['completed_at'],
            'is_completed': subtask['is_completed']
        })
    
    return jsonify(result)

@app.route('/calendar')
def calendar():
    from datetime import timedelta

    view_type = request.args.get('view', 'daily')  # daily, weekly, monthly
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        selected_date = datetime.now()
    
    db = get_db()
    # Default_Calendar
    week_days = []
    # 传递上下两个星期
    week_start = selected_date - timedelta(days=selected_date.weekday())
    prev_week_start = week_start - timedelta(days=7)
    next_week_start = week_start + timedelta(days=7)
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    # if view_type == 'daily':
    #     # Get tasks for the selected day
    #     date_filter = selected_date.strftime('%Y-%m-%d')
    #     completed_tasks = db.execute(
    #         "SELECT * FROM tasks WHERE date(completed_at) = ? AND is_completed = 1 ORDER BY completed_at",
    #         (date_filter,)
    #     ).fetchall()
        
    #     created_tasks = db.execute(
    #         "SELECT * FROM tasks WHERE date(created_at) = ? ORDER BY created_at",
    #         (date_filter,)
    #     ).fetchall()
    

    
    if view_type == 'monthly':
        # Get tasks for the selected month
        month_start = selected_date.replace(day=1)
        next_month = month_start.replace(month=month_start.month % 12 + 1, year=month_start.year + (month_start.month == 12))
        
        completed_tasks = db.execute(
            "SELECT * FROM tasks WHERE date(completed_at) >= ? AND date(completed_at) < ? AND is_completed = 1 ORDER BY completed_at",
            (month_start.strftime('%Y-%m-%d'), next_month.strftime('%Y-%m-%d'))
        ).fetchall()
        
        created_tasks = db.execute(
            "SELECT * FROM tasks WHERE date(created_at) >= ? AND date(created_at) < ? ORDER BY created_at",
            (month_start.strftime('%Y-%m-%d'), next_month.strftime('%Y-%m-%d'))
        ).fetchall()

    else :
        # Get ISO week start and end date
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)
        # 生成一周的所有日期
        week_days = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        # view_type == 'monthly':
        completed_tasks = db.execute(
            "SELECT * FROM tasks WHERE date(completed_at) BETWEEN ? AND ? AND is_completed = 1 ORDER BY completed_at",
            (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
        ).fetchall()
        
        created_tasks = db.execute(
            "SELECT * FROM tasks WHERE date(created_at) BETWEEN ? AND ? ORDER BY created_at",
            (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
        ).fetchall()
    # Get calendar data for the entire month
    month_start = selected_date.replace(day=1)
    
    # Get completion status for each day in the month
    completed_days = db.execute(
        "SELECT DISTINCT date(completed_at) as day FROM tasks WHERE strftime('%Y-%m', completed_at) = ? AND is_completed = 1",
        (month_start.strftime('%Y-%m'),)
    ).fetchall()
    
    created_days = db.execute(
        "SELECT DISTINCT date(created_at) as day FROM tasks WHERE strftime('%Y-%m', created_at) = ?",
        (month_start.strftime('%Y-%m'),)
    ).fetchall()
    
    completed_days_set = {row['day'] for row in completed_days}
    created_days_set = {row['day'] for row in created_days}
    
    return render_template('calendar.html',
                           view_type=view_type,
                           selected_date=selected_date,
                           completed_tasks=completed_tasks,
                           created_tasks=created_tasks,
                           completed_days=completed_days_set,
                           created_days=created_days_set,
                           week_days=week_days,
                           prev_week=prev_week_start,
                           next_week=next_week_start,
                           week_end = week_end,
                           week_start = week_start)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)