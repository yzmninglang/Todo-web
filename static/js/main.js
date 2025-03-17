// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Task completion toggle
    document.querySelectorAll('.task-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const taskId = this.dataset.taskId;
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/tasks/${taskId}/complete`;
            document.body.appendChild(form);
            form.submit();
        });
    });
    
    // Subtask completion toggle
    document.querySelectorAll('.subtask-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const subtaskId = this.dataset.subtaskId;
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/subtasks/${subtaskId}/complete`;
            document.body.appendChild(form);
            form.submit();
        });
    });
    
    // Toggle subtasks visibility
    document.querySelectorAll('.toggle-subtasks-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskItem = this.closest('.task-item');
            const subtasksContainer = taskItem.querySelector('.subtasks-container');
            const icon = this.querySelector('i');
            
            if (subtasksContainer.style.display === 'none') {
                subtasksContainer.style.display = 'block';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            } else {
                subtasksContainer.style.display = 'none';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        });
    });
    
    // Delete task
    document.querySelectorAll('.delete-task-btn').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this task?')) {
                const taskId = this.dataset.taskId;
                fetch(`/tasks/${taskId}`, {
                    method: 'DELETE',
                }).then(response => response.json())
                  .then(data => {
                    if (data.success) {
                        const taskItem = this.closest('.task-item');
                        taskItem.remove();
                    }
                  });
            }
        });
    });
    
    // Delete subtask
    document.querySelectorAll('.delete-subtask-btn').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this subtask?')) {
                const subtaskId = this.dataset.subtaskId;
                fetch(`/subtasks/${subtaskId}`, {
                    method: 'DELETE',
                }).then(response => response.json())
                  .then(data => {
                    if (data.success) {
                        const subtaskItem = this.closest('.subtask-item');
                        subtaskItem.remove();
                    }
                  });
            }
        });
    });
    
    // Initialize FullCalendar
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            selectable: true,
            select: function(info) {
                loadCompletedTasks(info.startStr, getViewType());
            },
            dateClick: function(info) {
                loadCompletedTasks(info.dateStr, getViewType());
            },
            dayCellDidMount: function(arg) {
                // Add dots to dates with tasks
                const date = arg.date.toISOString().split('T')[0];
                if (taskStats && taskStats[date]) {
                    const dotContainer = document.createElement('div');
                    dotContainer.className = 'dot-container';
                    
                    if (taskStats[date].created > 0) {
                        const createdDot = document.createElement('span');
                        createdDot.className = 'calendar-dot created-dot';
                        createdDot.title = `${taskStats[date].created} tasks created`;
                        dotContainer.appendChild(createdDot);
                    }
                    
                    if (taskStats[date].completed > 0) {
                        const completedDot = document.createElement('span');
                        completedDot.className = 'calendar-dot completed-dot';
                        completedDot.title = `${taskStats[date].completed} tasks completed`;
                        dotContainer.appendChild(completedDot);
                    }
                    
                    arg.el.querySelector('.fc-daygrid-day-top').appendChild(dotContainer);
                }
            }
        });
        
        calendar.render();
        
        // Set current date as default selected
        const today = new Date().toISOString().split('T')[0];
        loadCompletedTasks(today, 'day');
        
        // Calendar view type buttons
        document.querySelectorAll('.calendar-view-btn').forEach(button => {
            button.addEventListener('click', function() {
                const viewType = this.dataset.view;
                document.querySelectorAll('.calendar-view-btn').forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Change calendar view based on button clicked
                if (viewType === 'day') {
                    calendar.changeView('timeGridDay');
                } else if (viewType === 'week') {
                    calendar.changeView('timeGridWeek');
                } else if (viewType === 'month') {
                    calendar.changeView('dayGridMonth');
                }
                
                // Load tasks for the selected date and view
                loadCompletedTasks(calendar.getDate().toISOString().split('T')[0], viewType);
            });
        });
    }
    
    // Function to determine current calendar view type
    function getViewType() {
        const activeViewBtn = document.querySelector('.calendar-view-btn.active');
        return activeViewBtn ? activeViewBtn.dataset.view : 'day';
    }
    
    // Function to load completed tasks for a specific date
    function loadCompletedTasks(date, viewType) {
        const container = document.getElementById('completed-tasks-container');
        container.innerHTML = '<p class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading tasks...</p>';
        
        fetch(`/calendar/tasks?date=${date}&view=${viewType}`)
            .then(response => response.json())
            .then(tasks => {
                if (tasks.length === 0) {
                    container.innerHTML = '<p class="text-muted">No completed tasks for this period.</p>';
                    return;
                }
                
                let html = '<ul class="list-group">';
                tasks.forEach(task => {
                    // Format dates
                    const createdDate = new Date(task.created_at).toLocaleString();
                    const completedDate = new Date(task.completed_at).toLocaleString();
                    
                    html += `
                        <li class="list-group-item completed-task">
                            <div class="d-flex w-100 justify-content-between align-items-center">
                                <h6 class="mb-1">${task.title}</h6>
                                <button class="btn btn-sm btn-outline-primary toggle-completed-subtasks-btn">
                                    <i class="fas fa-chevron-down"></i>
                                </button>
                            </div>
                            <p class="mb-1">Created: ${createdDate} → Completed: ${completedDate}</p>
                            
                            ${task.description ? `<p class="mb-1">${task.description}</p>` : ''}
                            ${task.image_path ? `<div class="task-image mb-2"><img src="${task.image_path}" alt="Task image" class="img-thumbnail"></div>` : ''}
                            
                            <div class="completed-subtasks-container mt-3" style="display: none;">
                                <h6>Subtasks:</h6>
                                ${task.subtasks.length > 0 ? 
                                    `<ul class="list-group mb-3">
                                        ${task.subtasks.map(subtask => {
                                            const subtaskCreatedDate = new Date(subtask.created_at).toLocaleString();
                                            const subtaskCompletedDate = subtask.completed_at ? new Date(subtask.completed_at).toLocaleString() : 'Not completed';
                                            
                                            return `
                                                <li class="list-group-item ${subtask.completed ? 'completed-subtask' : ''}">
                                                    <div class="d-flex w-100 justify-content-between">
                                                        <h6 class="mb-1 ${subtask.completed ? 'text-decoration-line-through' : ''}">${subtask.title}</h6>
                                                    </div>
                                                    <p class="mb-0">Created: ${subtaskCreatedDate} → ${subtask.completed ? 'Completed: ' + subtaskCompletedDate : 'Not completed'}</p>
                                                </li>
                                            `;
                                        }).join('')}
                                    </ul>` 
                                : '<p class="text-muted">No subtasks for this task.</p>'}
                            </div>
                        </li>
                    `;
                });
                html += '</ul>';
                
                container.innerHTML = html;
                
                // Add event listeners to toggle completed subtasks
                document.querySelectorAll('.toggle-completed-subtasks-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        const taskItem = this.closest('.completed-task');
                        const subtasksContainer = taskItem.querySelector('.completed-subtasks-container');
                        const icon = this.querySelector('i');
                        
                        if (subtasksContainer.style.display === 'none') {
                            subtasksContainer.style.display = 'block';
                            icon.classList.remove('fa-chevron-down');
                            icon.classList.add('fa-chevron-up');
                        } else {
                            subtasksContainer.style.display = 'none';
                            icon.classList.remove('fa-chevron-up');
                            icon.classList.add('fa-chevron-down');
                        }
                    });
                });
            })
            .catch(error => {
                console.error('Error loading completed tasks:', error);
                container.innerHTML = '<p class="text-danger">Error loading tasks. Please try again.</p>';
            });
    }
});
