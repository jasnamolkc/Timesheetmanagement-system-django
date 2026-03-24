function filterEmployees() {
    const searchInput = document.getElementById("searchInput");
    const roleFilter = document.getElementById("roleFilter");
    const rows = document.querySelectorAll("#employeeTable tr[data-name]");
    const noDataRow = document.getElementById("noDataRow");

    if (!searchInput || !roleFilter || !rows.length) return;

    const searchValue = searchInput.value.toLowerCase();
    const roleValue = roleFilter.value;

    let visibleCount = 0;

    rows.forEach(row => {
        const name = row.dataset.name || "";
        const code = row.dataset.code || "";
        const role = row.dataset.role || "";

        const matchSearch = name.includes(searchValue) || code.includes(searchValue);
        const matchRole = roleValue === "" || role === roleValue;

        if (matchSearch && matchRole) {
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

const employeeSearch = document.getElementById("searchInput");
const employeeRole = document.getElementById("roleFilter");
if (employeeSearch) {
    employeeSearch.addEventListener("keyup", filterEmployees);
}
if (employeeRole) {
    employeeRole.addEventListener("change", filterEmployees);
}
