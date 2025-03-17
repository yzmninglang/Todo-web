DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS subtasks;

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    image_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    is_completed BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    is_completed BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks (id)
);