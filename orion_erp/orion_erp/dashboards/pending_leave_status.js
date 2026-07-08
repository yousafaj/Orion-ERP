frappe.dom.freeze("Loading Pending Leave Status...");

async function load_pending_leave_status() {
    root_element.innerHTML = "";

    try {
        const { message: data } = await frappe.call({
            method: "orion_erp.api.get_pending_leave_status"
        });

        if (!data || !data.rows || !data.rows.length) {
            root_element.innerHTML = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="font-size:64px;margin-bottom:20px;opacity:0.3">&#x2705;</div>
    <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">No Pending Applications</h3>
    <p style="margin:0;color:#9ca3af;font-size:14px">All leave applications have been processed.</p>
</div>`;
            frappe.dom.unfreeze();
            return;
        }

        const kpi = data.kpi;
        const rows = data.rows;
        const total_rows = rows.length;

        let table_rows = "";
        rows.forEach((r, idx) => {
            const esc_name = frappe.utils.escape_html(r.name || "");
            const esc_emp = frappe.utils.escape_html(r.employee || "");
            const esc_emp_name = frappe.utils.escape_html(r.employee_name || "");
            const esc_type = frappe.utils.escape_html(r.leave_type || "");
            const esc_approver = frappe.utils.escape_html(r.current_approver || "");
            const esc_wf = frappe.utils.escape_html(r.workflow_state || "");
            const esc_status = frappe.utils.escape_html(r.status || "");
            const post_date = frappe.datetime.str_to_user(r.posting_date);
            const age = Number(r.age_days || 0);

            // Color-code workflow state
            let wf_color = "#6b7280";
            let wf_bg = "#f3f4f6";
            let wf_border = "#e5e7eb";
            const wf_lower = (r.workflow_state || "").toLowerCase();
            if (wf_lower.indexOf("open") !== -1) {
                wf_color = "#f59e0b"; wf_bg = "#fffbeb"; wf_border = "#fde68a";
            } else if (wf_lower.indexOf("approver 1") !== -1) {
                wf_color = "#2563eb"; wf_bg = "#eff6ff"; wf_border = "#bfdbfe";
            } else if (wf_lower.indexOf("approver 2") !== -1 || wf_lower.indexOf("approver 3") !== -1) {
                wf_color = "#7c3aed"; wf_bg = "#f5f3ff"; wf_border = "#ddd6fe";
            } else if (wf_lower.indexOf("approver 4") !== -1 || wf_lower.indexOf("approver 5") !== -1) {
                wf_color = "#dc2626"; wf_bg = "#fef2f2"; wf_border = "#fecaca";
            }

            let age_color = "#15803d";
            if (age > 7) age_color = "#dc2626";
            else if (age > 3) age_color = "#d97706";

            table_rows += `<tr style="background:${idx % 2 === 0 ? '#ffffff' : '#f8fafc'}">
<td style="padding:8px 16px;font-size:12px;font-weight:500;color:#2563eb;border-bottom:1px solid #f0f0f0;cursor:pointer" class="app-link" data-name="${esc_name}">${esc_name}</td>
<td style="padding:8px 16px;font-size:13px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0"><b>${esc_emp_name}</b><br><span style="color:#64748b;font-size:11px;white-space:nowrap">${esc_emp}</span></td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_type}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${post_date}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_approver || '—'}</td>
<td style="padding:8px 16px;text-align:center;border-bottom:1px solid #f0f0f0">
<span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;color:${wf_color};background:${wf_bg};border:1px solid ${wf_border}">${esc_wf}</span>
</td>
<td style="padding:8px 16px;text-align:center;font-weight:700;font-size:13px;color:${age_color};border-bottom:1px solid #f0f0f0">${age}d</td>
<td style="padding:8px 16px;text-align:center;border-bottom:1px solid #f0f0f0">
<span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;color:#f59e0b;background:#fffbeb;border:1px solid #fde68a">${esc_status}</span>
</td></tr>`;
        });

        const html = `<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;padding:10px 20px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:8px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:12px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:24px;line-height:1">&#x1F4CB;</div>
        <div style="flex:1">
            <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px">Pending Leave Application Status</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:0">Complete Overview of Pending Applications</div>
        </div>
        <div class="header-actions">
            <button id="openWfBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.2);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-external-link" style="font-size:11px"></i> Open Workflow Queue
            </button>
            <button id="refreshBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.15);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:11px"></i> Refresh
            </button>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:15px;flex-shrink:0"><i class="fa fa-clock-o"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Total Pending</div>
                <div style="font-size:22px;font-weight:800;color:#d97706;line-height:1">${kpi.total_pending}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Applications</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#eff6ff;border-radius:10px;border:1px solid #bfdbfe;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:15px;flex-shrink:0"><i class="fa fa-user"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Manager Pending</div>
                <div style="font-size:22px;font-weight:800;color:#1d4ed8;line-height:1">${kpi.manager_pending}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Level 1</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f5f3ff;border-radius:10px;border:1px solid #ddd6fe;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#ede9fe,#f5f3ff);color:#7c3aed;font-size:15px;flex-shrink:0"><i class="fa fa-users"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">HR Pending</div>
                <div style="font-size:22px;font-weight:800;color:#6d28d9;line-height:1">${kpi.hr_pending}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Level 2–3</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fef2f2;border-radius:10px;border:1px solid #fecaca;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fee2e2,#fef2f2);color:#ef4444;font-size:15px;flex-shrink:0"><i class="fa fa-flag"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Final Approval</div>
                <div style="font-size:22px;font-weight:800;color:#dc2626;line-height:1">${kpi.final_pending}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Level 4–5</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;padding:10px 16px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:13px;font-weight:700;color:#374151;display:flex;align-items:center;gap:6px;margin-right:auto">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:12px"></i> Pending Applications
                <span style="font-size:11px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:1px 8px;border-radius:10px;margin-left:4px">${total_rows}</span>
            </div>
            <button id="exportBtn" style="display:flex;align-items:center;gap:4px;padding:4px 10px;border:none;border-radius:5px;background:#16a34a;color:#fff;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-download" style="font-size:10px"></i> Export</button>
        </div>

        <div class="table-container" style="max-height:450px">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Application</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Employee</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Submitted</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Current Approver</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:130px">Workflow State</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:60px">Age</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:100px">Status</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:6px 16px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#6b7280">
            <span>Showing ${total_rows} pending application${total_rows !== 1 ? 's' : ''}</span>
            <span style="font-size:10px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

        root_element.innerHTML = html;

        $(".app-link", root_element).on("click", function (e) {
            e.stopPropagation();
            const name = $(this).data("name");
            if (name) frappe.set_route("Form", "Leave Application", name);
        });

        $("#refreshBtn", root_element).on("click", function (e) { e.stopPropagation(); load_pending_leave_status(); });
        $("#openWfBtn", root_element).on("click", function (e) { e.stopPropagation(); frappe.set_route("List", "Leave Application"); });

        $("#exportBtn", root_element).on("click", function () {
            const today = frappe.datetime.get_today();
            const csv = [];
            csv.push('"PENDING LEAVE APPLICATION STATUS"');
            csv.push('');
            csv.push('"Export Date","' + frappe.datetime.str_to_user(today) + '"');
            csv.push('"Total Pending","' + kpi.total_pending + '","Manager","' + kpi.manager_pending + '","HR","' + kpi.hr_pending + '","Final","' + kpi.final_pending + '"');
            csv.push('');
            csv.push('');
            const headers = [];
            $("table thead th", root_element).each(function () { headers.push('"' + $(this).text().trim().replace(/"/g, '""') + '"'); });
            csv.push(headers.join(","));
            $("table tbody tr:visible", root_element).each(function () {
                const row = [];
                $(this).find("td").each(function () {
                    row.push('"' + $(this).text().replace(/\n/g, " ").trim().replace(/"/g, '""') + '"');
                });
                csv.push(row.join(","));
            });
            const blob = new Blob([csv.join("\n")], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = "Pending_Leave_Status_" + today + ".csv";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });

        frappe.dom.unfreeze();
    } catch (e) {
        console.error(e);
        root_element.innerHTML = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="width:60px;height:60px;border-radius:50%;background:#fef2f2;display:flex;align-items:center;justify-content:center;margin-bottom:16px;font-size:28px;color:#ef4444">&#x26A0;</div>
    <h3 style="margin:0 0 8px;color:#991b1b;font-weight:600;font-size:18px">Unable to Load Data</h3>
    <p style="margin:0 0 16px;color:#b91c1c;font-size:14px;max-width:400px;text-align:center">${frappe.utils.escape_html(e.message || String(e))}</p>
    <button id="retryBtn" style="padding:10px 24px;border:none;border-radius:8px;background:#ef4444;color:#fff;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit">Try Again</button>
</div>`;
        $("#retryBtn", root_element).on("click", function (e) { e.stopPropagation(); load_pending_leave_status(); });
    } finally {
        frappe.dom.unfreeze();
    }
}

load_pending_leave_status();