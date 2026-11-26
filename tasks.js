/* My dad and AI helped with some of the script for this page */

let currentPage = 1;
let perPage = 10;
let sortBy = "due_date";
let sortOrder = "desc";

let allTasksData = {};
let taskIdToDelete = null;

/* Formatter */
function formatPriority(p) {
    const badge = {
        high: "danger",
        medium: "warning",
        low: "secondary"
    }[p] || "info";

    const label = {
        high: "High",
        medium: "Medium",
        low: "Low"
    }[p] || p;

    return `<span class="badge badge-${badge}">${label}</span>`;
}

function formatStatus(s) {
    const badge = {
        pending: "secondary",
        in_progress: "primary",
        done: "success"
    }[s] || "info";

    const label = {
        pending: "Pending",
        in_progress: "In Progress",
        done: "Done"
    }[s] || s;

    return `<span class="badge badge-${badge}">${label}</span>`;
}

/* Sort */
function updateSortUI() {
    document.querySelectorAll("th.sortable .sort-arrow").forEach(el => {
        el.textContent = "";
    });

    const active = document.querySelector(`th[data-col="${sortBy}"] .sort-arrow`);
    if (active) active.textContent = sortOrder === "asc" ? "▲" : "▼";
}

/* Load Tasks */
async function loadTasks() {
    const container = document.getElementById("task-table-container");
    container.innerHTML = "<p>Loading tasks...</p>";

    const res = await fetch(
        `/search_tasks?page=${currentPage}&per_page=${perPage}&sort_by=${sortBy}&sort_order=${sortOrder}`
    );
    const data = await res.json();

    allTasksData = {};
    data.tasks.forEach(t => (allTasksData[t.id] = t));

    renderTasksTable(data);

    document.getElementById("page-info").textContent =
        `Page ${data.current_page} of ${data.total_pages}`;

    document.getElementById("prev-btn").disabled = !data.has_prev;
    document.getElementById("next-btn").disabled = !data.has_next;
}

/* Render Table */
function renderTasksTable(data) {
    const container = document.getElementById("task-table-container");

    if (!data.tasks.length) {
        container.innerHTML = `<p class="text-center mt-4">No tasks found.</p>`;
        return;
    }

    let html = `
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th class="sortable" data-col="title">Title <span class="sort-arrow"></span></th>
                    <th class="sortable" data-col="description">Description <span class="sort-arrow"></span></th>
                    <th class="sortable" data-col="priority">Priority <span class="sort-arrow"></span></th>
                    <th class="sortable" data-col="status">Status <span class="sort-arrow"></span></th>
                    <th class="sortable" data-col="due_date">Due Date <span class="sort-arrow"></span></th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.tasks.forEach(t => {
        const due = t.due_date ? new Date(t.due_date).toLocaleDateString() : "—";

        html += `
            <tr>
                <td>${t.title}</td>
                <td>${t.description || "-"}</td>
                <td>${formatPriority(t.priority)}</td>
                <td>${formatStatus(t.status)}</td>
                <td>${due}</td>
                <td>
                    <button class="btn btn-info btn-sm" onclick="openEditModal(${t.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteTask(${t.id})">Delete</button>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    updateSortUI();
}


function changeSort(column) {
    if (sortBy === column) {
        sortOrder = sortOrder === "asc" ? "desc" : "asc";
    } else {
        sortBy = column;
        sortOrder = "asc";
    }
    loadTasks();
}

/* Create Task */
async function createTask(e) {
    e.preventDefault();

    const formData = new FormData(e.target);

    const res = await fetch("/add_task", {
        method: "POST",
        body: formData
    });

    if (res.ok) {
        showToast("Task created successfully!", "success");
        e.target.reset();
        currentPage = 1;
        loadTasks();
    } else {
        showToast("Failed to create task", "danger");
    }
}

/* Edit Task */
function openEditModal(id) {
    const t = allTasksData[id];

    document.getElementById("edit-task-id").value = t.id;
    document.getElementById("edit-title").value = t.title;
    document.getElementById("edit-description").value = t.description || "";
    document.getElementById("edit-priority").value = t.priority;
    document.getElementById("edit-status").value = t.status;

    if (t.due_date) document.getElementById("edit-due_date").value = t.due_date;

    $("#editTaskModal").modal("show");
}

async function saveTask() {
    $("#editTaskModal").modal("hide");

    const formData = new FormData(document.getElementById("editTaskForm"));
    const payload = {};
    formData.forEach((v, k) => (payload[k] = v));

    const res = await fetch("/update_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) showToast("Task updated successfully!", "success");
    else showToast("Failed to update task", "danger");

    loadTasks();
}

/* Delete Task */
function deleteTask(id) {
    taskIdToDelete = id;
    $("#deleteConfirmModal").modal("show");
}

async function confirmDeletion() {
    $("#deleteConfirmModal").modal("hide");

    const res = await fetch("/delete_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskIdToDelete })
    });

    if (res.ok) showToast("Task deleted!", "success");
    else showToast("Failed to delete task", "danger");

    loadTasks();
}

/* init */
document.addEventListener("DOMContentLoaded", () => {
    const createForm = document.getElementById("createTaskForm");
    if (createForm) createForm.addEventListener("submit", createTask);

    document.getElementById("saveTaskButton").addEventListener("click", saveTask);
    document.getElementById("confirmDeleteButton").addEventListener("click", confirmDeletion);

    document.getElementById("prev-btn").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadTasks();
        }
    });

    document.getElementById("next-btn").addEventListener("click", () => {
        currentPage++;
        loadTasks();
    });

    document.addEventListener("click", (e) => {
        const th = e.target.closest("th.sortable");
        if (th) changeSort(th.dataset.col);
    });

    loadTasks();
});
