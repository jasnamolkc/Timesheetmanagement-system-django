document.addEventListener('modalContentLoaded', function(e) {
    const { url, content } = e.detail;
    const modalForm = content.querySelector("form");

    if (modalForm && (modalForm.action.includes("project") || url.includes("project"))) {
        // If needed, specific project modal initialization can go here.
    }
});

let currentProjectId = null;

function openArchiveModal(projectId, projectName, isArchived) {
    currentProjectId = projectId;
    const action = (isArchived === "True") ? "unarchive" : "archive";
    document.getElementById("archiveMessage").innerText = `Are you sure you want to ${action} "${projectName}"?`;
    document.getElementById("archiveModal").classList.remove("hidden");
    document.getElementById("archiveModal").classList.add("flex");
}

function closeArchiveModal() {
    document.getElementById("archiveModal").classList.add("hidden");
}

const confirmArchiveBtn = document.getElementById("confirmArchiveBtn");
if (confirmArchiveBtn) {
    confirmArchiveBtn.addEventListener("click", function () {
        if (currentProjectId) {
            document.getElementById(`archive-form-${currentProjectId}`).submit();
        }
    });
}

document.addEventListener("click", function (e) {
    // DOCUMENT (Inside Project Edit Form)
    if (e.target && e.target.id === "add-document") {
        const container = document.getElementById("document-container");
        const template = document.getElementById("empty-document-form");
        const totalForms = document.querySelector('input[name="documents-TOTAL_FORMS"]');
        if (!container || !template || !totalForms) return;

        let formIdx = parseInt(totalForms.value);
        let newForm = template.innerHTML.replace(/__prefix__/g, formIdx);
        container.insertAdjacentHTML("beforeend", newForm);
        totalForms.value = formIdx + 1;
    }

    // MILESTONE (Inside Project Edit Form)
    if (e.target && e.target.id === "add-milestone") {
        const container = document.getElementById("milestone-container");
        const template = document.getElementById("empty-milestone-form");
        const totalForms = document.querySelector('input[name="milestones-TOTAL_FORMS"]');
        if (!container || !template || !totalForms) return;

        let formIdx = parseInt(totalForms.value);
        let newForm = template.innerHTML.replace(/__prefix__/g, formIdx);
        container.insertAdjacentHTML("beforeend", newForm);
        totalForms.value = formIdx + 1;
    }
});

function filterMilestones() {
    const projectFilter = document.getElementById("projectFilter");
    const statusFilter = document.getElementById("statusFilter");
    const startDateFilter = document.getElementById("startDateFilter");
    const endDateFilter = document.getElementById("endDateFilter");
    const tbody = document.getElementById("milestoneTable");
    const rows = document.querySelectorAll(".milestone-row");

    if (!projectFilter || !rows.length) return;

    const projectVal = projectFilter.value.toLowerCase();
    const statusVal = statusFilter.value;
    const startVal = startDateFilter.value;
    const endVal = endDateFilter.value;

    let visibleCount = 0;

    rows.forEach(row => {
        const project = row.dataset.project.toLowerCase();
        const status = row.dataset.status;
        const start = row.dataset.start;
        const due = row.dataset.due;

        const matchProject = projectVal === "" || project === projectVal;
        const matchStatus = statusVal === "" || status === statusVal;
        const matchStart = startVal === "" || start >= startVal;
        const matchEnd = endVal === "" || due <= endVal;

        if (matchProject && matchStatus && matchStart && matchEnd) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }
    });

    // Handle empty state
    let noResultsRow = document.getElementById("noMilestoneResults");
    if (visibleCount === 0) {
        if (!noResultsRow) {
            noResultsRow = document.createElement("tr");
            noResultsRow.id = "noMilestoneResults";
            noResultsRow.innerHTML = `<td colspan="5" class="px-6 py-16 text-center text-slate-500 bg-slate-800/20 italic">No milestones match your filters</td>`;
            tbody.appendChild(noResultsRow);
        }
    } else if (noResultsRow) {
        noResultsRow.remove();
    }
}

const milestoneProj = document.getElementById("projectFilter");
const milestoneStatus = document.getElementById("statusFilter");
const milestoneStart = document.getElementById("startDateFilter");
const milestoneEnd = document.getElementById("endDateFilter");

if (milestoneProj) milestoneProj.addEventListener("change", filterMilestones);
if (milestoneStatus) milestoneStatus.addEventListener("change", filterMilestones);
if (milestoneStart) milestoneStart.addEventListener("change", filterMilestones);
if (milestoneEnd) milestoneEnd.addEventListener("change", filterMilestones);
