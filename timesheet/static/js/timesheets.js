document.addEventListener('modalContentLoaded', function(e) {
    const { url, content } = e.detail;
    const modalForm = content.querySelector("form");

    if (modalForm && (modalForm.action.includes("timesheet") || url.includes("timesheet"))) {
        const projectSelect = modalForm.querySelector("#id_project");
        const taskSelect = modalForm.querySelector("#id_task");
        const addTaskBtn = modalForm.querySelector("#addTaskBtn");

        if (projectSelect && taskSelect) {
            function updateTasks(projectId, selectedTask) {
                if (!projectId) {
                    taskSelect.innerHTML = '<option value="">Select task</option>';
                    return;
                }
                fetch(`/tasks/by-project/${projectId}/`, {
                    headers: { "X-Requested-With": "XMLHttpRequest" }
                })
                .then(res => res.json())
                .then(data => {
                    taskSelect.innerHTML = '<option value="">Select task</option>';
                    data.tasks.forEach(task => {
                        const option = new Option(task.title, task.id);
                        if (String(task.id) === String(selectedTask)) {
                            option.selected = true;
                        }
                        taskSelect.add(option);
                    });
                });
            }

            projectSelect.addEventListener("change", function() {
                updateTasks(this.value);
                if (addTaskBtn) {
                    addTaskBtn.disabled = !this.value;
                }
            });

            if (projectSelect.value) {
                updateTasks(projectSelect.value, taskSelect.value);
                if (addTaskBtn) {
                    addTaskBtn.disabled = false;
                }
            } else if (addTaskBtn) {
                addTaskBtn.disabled = true;
            }

            if (addTaskBtn) {
                addTaskBtn.addEventListener("click", function() {
                    const projectId = projectSelect.value;
                    if (!projectId) return;
                    openModal2(`/tasks/create/?modal=1&project=${projectId}`);
                });
            }
        }
    }
});

document.addEventListener('modal2ContentLoaded', function(e) {
    const { url, content } = e.detail;
    const modalContent2 = content;
    const fieldsToHide = ['#id_description', '#id_milestone', '#id_status'];

    fieldsToHide.forEach(selector => {
        const field = modalContent2.querySelector(selector);
        if (field) {
            const wrapper = field.closest('.form-group') || field.parentElement;
            if (wrapper) wrapper.style.display = 'none';
            const label = modalContent2.querySelector(`label[for="${field.id}"]`);
            if (label) label.style.display = 'none';
        }
    });

    const params = new URLSearchParams(url.split('?')[1]);
    const projectId = params.get('project');
    if (projectId) {
        const projectSelect = modalContent2.querySelector('#id_project');
        if (projectSelect) {
            projectSelect.value = projectId;
            projectSelect.dispatchEvent(new Event('change'));
        }
    }

    const form2 = modalContent2.querySelector("form");
    if (form2) {
        form2.addEventListener("submit", function(e){
            e.preventDefault();
            const formData = new FormData(form2);
            fetch(form2.action, {
                method: form2.method,
                headers: { "X-Requested-With": "XMLHttpRequest" },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    closeModal2();
                    const parentModal = document.getElementById('modal-content');
                    const taskSelect = parentModal.querySelector("#id_task");
                    if (taskSelect) {
                        const option = new Option(data.task_name, data.task_id, true, true);
                        taskSelect.add(option);
                        taskSelect.dispatchEvent(new Event('change'));
                    }
                } else if (data.html) {
                    modalContent2.innerHTML = data.html;
                }
            });
        });
    }
});

function filterTimesheets() {
    const searchInput = document.getElementById("search");
    const billableFilter = document.getElementById("filter");
    const tbody = document.getElementById("timesheetTable");

    if (!searchInput || !billableFilter || !tbody) return;

    const searchValue = searchInput.value.toLowerCase();
    const filterValue = billableFilter.value;
    const rows = tbody.querySelectorAll("tr:not(#noResultsRow)");

    let visibleCount = 0;

    rows.forEach(row => {
        // Column 2 is Project, 4 is Task Title, 7 is Billable (Yes/No)
        const project = row.querySelector("td:nth-child(2)").innerText.toLowerCase();
        const task = row.querySelector("td:nth-child(4)").innerText.toLowerCase();
        const billable = row.querySelector("td:nth-child(7)").innerText.trim();

        const matchSearch = project.includes(searchValue) || task.includes(searchValue);
        const matchFilter = filterValue === "" || billable === filterValue;

        if (matchSearch && matchFilter) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }
    });

    let existingNoResultsRow = document.getElementById("noResultsRow");
    if (visibleCount === 0) {
        if (!existingNoResultsRow) {
            const noResultsRow = document.createElement("tr");
            noResultsRow.id = "noResultsRow";
            noResultsRow.innerHTML = `<td colspan="8" class="text-center text-slate-500 py-16 bg-slate-800/20">No matching entries found</td>`;
            tbody.appendChild(noResultsRow);
        }
    } else if (existingNoResultsRow) {
        existingNoResultsRow.remove();
    }
}

const timesheetSearch = document.getElementById("search");
const timesheetFilter = document.getElementById("filter");
if (timesheetSearch) timesheetSearch.addEventListener("keyup", filterTimesheets);
if (timesheetFilter) timesheetFilter.addEventListener("change", filterTimesheets);
