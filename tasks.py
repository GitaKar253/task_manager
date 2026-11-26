from flask import Blueprint

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify

from helpers import login_required
# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///task_manager.db")

tasks_bp = Blueprint('tasks', __name__)

# Ensure responses aren't cached
@tasks_bp.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@tasks_bp.route("/tasks", methods=["GET", "POST"])
@login_required
def my_tasks():
   return render_template("tasks.html")


@tasks_bp.route("/add_task", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")
    status = request.form.get("status")
    assigned_to = session.get("user_id")

    # Insert into user_tasks
    db.execute(
        'INSERT INTO user_tasks (title, description, due_date, priority, status, assigned_to) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        title, description, due_date, priority, status, assigned_to
    )
    # insert to user activities
    add_audit_activity(assigned_to, "CREATED",  title, description, due_date, priority, status)
    flash("Task created successfully!", "success")
    return render_template("tasks.html")


@tasks_bp.route("/search_tasks", methods=["GET"])
@login_required
def search_tasks():
    assigned_to = session.get("user_id")

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "asc").lower()

    allowed_columns = ["id", "title", "description", "priority", "status", "due_date"]
    if sort_by not in allowed_columns:
        sort_by = "due_date"

    sort_order = "asc" if sort_order == "asc" else "desc"
    offset = (page - 1) * per_page

    # Priority Sort (AI helped with this part)
    if sort_by == "priority":
        if sort_order == "asc":
            order_clause = (
                "ORDER BY CASE priority "
                "WHEN 'high' THEN 1 "
                "WHEN 'medium' THEN 2 "
                "WHEN 'low' THEN 3 "
                "END"
            )
        else:
            order_clause = (
                "ORDER BY CASE priority "
                "WHEN 'low' THEN 1 "
                "WHEN 'medium' THEN 2 "
                "WHEN 'high' THEN 3 "
                "END"
            )
    else:
        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"

    # Count tasks
    total_tasks = db.execute(
        "SELECT COUNT(*) AS count FROM user_tasks WHERE assigned_to=?",
        assigned_to
    )[0]["count"]

    total_pages = max(1, (total_tasks + per_page - 1) // per_page)

    # Main query
    rows = db.execute(
        f"""
        SELECT id, title, description, priority, status, due_date
        FROM user_tasks
        WHERE assigned_to=?
        {order_clause}
        LIMIT ? OFFSET ?
        """,
        assigned_to, per_page, offset
    )

    return jsonify({
        "tasks": rows,
        "current_page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    })


@tasks_bp.route("/delete_task", methods=["POST"])
@login_required
def delete_task():
   if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
   data = request.get_json()
   print("data:" + str(data))
   task_id = data.get("task_id")
   if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
   try:
        tasks = db.execute("SELECT * FROM user_tasks WHERE id=?", task_id)
        task = tasks[0]
        print("task:"+str(task))
        print("task title:" + str(task["title"]))
        db.execute("DELETE FROM user_tasks WHERE id = ?", task_id)
        print(f"Task with ID {task_id} successfully deleted.")
          # insert to user activities
        add_audit_activity(task["assigned_to"], "DELETED",  task["title"],
                           task["description"], task["due_date"], task["priority"], task["status"])
        # 4. Return a successful response
        return jsonify({"message": f"Task {task_id} deleted successfully"}), 200
   except Exception as e:
        # 5. Handle any database or server errors
        print(f"Error deleting task: {e}")
        return jsonify({"error": "Could not delete task due to a server error."}), 500


@tasks_bp.route("/update_task", methods=["POST"])
@login_required
def update_task():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    due_date = data.get("due_date")
    priority = data.get("priority")
    status = data.get("status")
    task_id = data.get("id")
    assigned_to = session.get("user_id")
    db.execute(
        "UPDATE user_tasks SET title=?, description=?, due_date=?, priority=?, status=? WHERE id=?",
        title, description, due_date, priority, status, task_id
    )
    # insert to user activities
    add_audit_activity(assigned_to, "UPDATED",  title, description, due_date, priority, status)
    return jsonify({"message": f"Task {task_id} updated successfully"}), 200

@tasks_bp.route("/history", methods=["GET"])
@login_required
def history():
    return render_template("history.html")


@tasks_bp.route("/user_activities", methods=["GET"])
@login_required
def fetch_user_activities():
    assigned_to = session.get("user_id")
    # Read pagination params (with defaults)
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return jsonify({"error": "Invalid pagination params"}), 400

    # Prevent invalid pagination
    if page < 1: page = 1
    if per_page < 1: per_page = 10

    offset = (page - 1) * per_page

    # Total number of activities
    count_result = db.execute(
        "SELECT COUNT(*) AS total FROM user_activities WHERE assigned_to = ?",
        assigned_to
    )
    total_activities = count_result[0]["total"]

    # Fetch paginated results
    rows = db.execute("""
        SELECT activity_time, activity_type, title, description, priority, status, due_date
        FROM user_activities
        WHERE assigned_to = ?
        ORDER BY activity_time DESC
        LIMIT ? OFFSET ?
    """, assigned_to, per_page, offset)

    # Calculate total pages
    total_pages = (total_activities + per_page - 1) // per_page

    response = {
        "user_activities": rows,
        "current_page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "total_activities": total_activities,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    return jsonify(response), 200



def add_audit_activity(assigned_to, activity_type, title, description, due_date, priority, status):
    try:
        db.execute(
            'INSERT INTO user_activities (assigned_to, activity_type, title, description, due_date, priority, status) '
            'VALUES (?, ?, ?, ?, ?, ?, ? )',
            assigned_to, activity_type, title, description, due_date, priority, status
        )
    except Exception as e:
          print(f"Error inserting to user activity : {e}")
