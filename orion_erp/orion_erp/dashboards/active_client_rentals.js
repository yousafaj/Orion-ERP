// The server returns only Vehicle Movements visible to the signed-in user.
async function render_active_client_rentals() {
    const escape = value => frappe.utils.escape_html(String(value || ""));
    root_element.innerHTML = '<p class="text-muted">Loading active rentals…</p>';
    try {
        const response = await frappe.call({
            method: "orion_erp.orion_erp.doctype.vehicle_movement.vehicle_movement.active_client_rentals"
        });
        const rows = response.message || [];
        const body = rows.map(row => `
            <tr>
                <td><a href="/app/vehicle-movement/${escape(encodeURIComponent(row.name))}">${escape(row.vehicle)}</a></td>
                <td>${escape(row.customer)}</td>
                <td>${escape(row.driver_name || row.driver) || "—"}</td>
                <td>${row.movement_date ? escape(frappe.datetime.str_to_user(row.movement_date)) : "—"}</td>
            </tr>`).join("");
        root_element.innerHTML = `
            <div class="card" style="padding:16px;overflow-x:auto">
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:12px">
                    <strong>Active client rentals</strong>
                    <a href="/app/vehicle-movement" class="btn btn-sm btn-default">Open all mobilizations</a>
                </div>
                ${rows.length ? `<table class="table table-bordered" style="margin-bottom:0">
                    <thead><tr><th>Vehicle</th><th>Client</th><th>Driver</th><th>Start date</th></tr></thead>
                    <tbody>${body}</tbody></table>` :
                    '<p class="text-muted" style="margin:0">No active client rentals have been recorded yet.</p>'}
                ${rows.length === 25 ? '<p class="text-muted" style="margin:8px 0 0">Showing the 25 most recent rentals. Open all mobilizations for the full list.</p>' : ''}
            </div>`;
    } catch (error) {
        root_element.innerHTML = '<p class="text-muted">Active rentals could not be loaded. Open Vehicle Mobilizations for the full list.</p>';
    }
}
render_active_client_rentals();
