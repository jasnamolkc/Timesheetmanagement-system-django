document.addEventListener('modalContentLoaded', function(e) {
    const { url, content } = e.detail;
    const modalForm = content.querySelector("form");

    if (modalForm && (modalForm.action.includes("task") || url.includes("task"))) {
        const projectSelect = modalForm.querySelector("#id_project");
        const milestoneSelect = modalForm.querySelector("#id_milestone");
        const employeeSelect = modalForm.querySelector("#id_assigned_to");

        if (projectSelect) {
            projectSelect.addEventListener("change", function() {
                const projectId = this.value;
                const selectedMilestone = milestoneSelect ? milestoneSelect.value : null;
                const selectedEmployee = employeeSelect ? employeeSelect.value : null;

                if (milestoneSelect) {
                    if (!projectId) {
                        milestoneSelect.innerHTML = '<option value="">No Milestone</option>';
                    } else {
                        fetch(`/milestones-by-project/${projectId}/`)
                        .then(res => res.json())
                        .then(data => {
                            milestoneSelect.innerHTML = '<option value="">No Milestone</option>';
                            data.milestones.forEach(m => {
                                const option = new Option(m.name, m.id);
                                if (String(m.id) === String(selectedMilestone)) {
                                    option.selected = true;
                                }
                                milestoneSelect.add(option);
                            });
                        });
                    }
                }

                if (employeeSelect) {
                    if (!projectId) {
                        employeeSelect.innerHTML = '<option value="">Unassigned</option>';
                    } else {
                        fetch(`/employees-by-project/${projectId}/`)
                        .then(res => res.json())
                        .then(data => {
                            employeeSelect.innerHTML = '<option value="">Unassigned</option>';
                            data.employees.forEach(emp => {
                                const option = new Option(emp.name, emp.id);
                                if (String(emp.id) === String(selectedEmployee)) {
                                    option.selected = true;
                                }
                                employeeSelect.add(option);
                            });
                        });
                    }
                }
            });

            if (projectSelect.value) {
                projectSelect.dispatchEvent(new Event("change"));
            }
        }
    }
});

document.addEventListener("change", function(e){
    if(e.target.id === "task-images"){
        const preview = document.getElementById("image-preview");
        if (!preview) return;
        preview.innerHTML = "";
        const files = e.target.files;
        for(let i=0;i<files.length;i++){
            const reader = new FileReader();
            reader.onload = function(event){
                const img = document.createElement("img");
                img.src = event.target.result;
                img.className = "w-full h-24 object-cover rounded-lg border border-slate-700";
                preview.appendChild(img);
            };
            reader.readAsDataURL(files[i]);
        }
    }
});

function deleteTaskImage(id) {
    fetch(`/delete-task-image/${id}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(res => res.json())
    .then(data => {
        if(data.success){
            const imgDiv = document.getElementById("task-image-" + id);
            if(imgDiv){
                imgDiv.remove();
            }
        }
    });
}

function filterTasks() {
    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const projectFilter = document.getElementById("projectFilter");
    const rows = document.querySelectorAll("#taskTable tr[data-title]");
    const noDataRow = document.getElementById("noDataRow");

    if (!searchInput || !statusFilter || !projectFilter || !rows.length) return;

    const searchValue = searchInput.value.toLowerCase();
    const statusValue = statusFilter.value;
    const projectValue = projectFilter.value;

    let visibleCount = 0;

    rows.forEach(row => {
        const title = row.dataset.title || "";
        const status = row.dataset.status || "";
        const project = row.dataset.project || "";

        const matchSearch = title.includes(searchValue);
        const matchStatus = statusValue === "" || status === statusValue;
        const matchProject = projectValue === "" || project === projectValue;

        if (matchSearch && matchStatus && matchProject) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }
    });

    if (noDataRow) {
        noDataRow.style.display = (visibleCount === 0) ? "" : "none";
    }
}

const taskSearch = document.getElementById("searchInput");
const taskStatus = document.getElementById("statusFilter");
const taskProject = document.getElementById("projectFilter");

if (taskSearch) taskSearch.addEventListener("keyup", filterTasks);
if (taskStatus) taskStatus.addEventListener("change", filterTasks);
if (taskProject) taskProject.addEventListener("change", filterTasks);
