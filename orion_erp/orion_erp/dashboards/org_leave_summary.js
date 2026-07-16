frappe.dom.freeze("Loading Leave Summary...");

async function load_org_leave_summary() {
    root_element.innerHTML = "";

    try {
        const { message: data } = await frappe.call({
            method: "orion_erp.api.get_org_leave_summary"
        });

        if (!data || !data.rows || !data.rows.length) {
            root_element.innerHTML = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="font-size:64px;margin-bottom:20px;opacity:0.3">&#x1F4CA;</div>
    <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">No Leave Data Found</h3>
    <p style="margin:0;color:#9ca3af;font-size:14px">No leave allocations exist in the organisation yet.</p>
</div>`;
            frappe.dom.unfreeze();
            return;
        }

        const kpi = data.kpi;
        const rows = data.rows;
        const total_rows = rows.length;

        // Build unique filter values
        const companies = [...new Set(rows.map(r => r.company).filter(Boolean))].sort();
        const departments = [...new Set(rows.map(r => r.department).filter(Boolean))].sort();
        const leave_types = [...new Set(rows.map(r => r.leave_type).filter(Boolean))].sort();

        let table_rows = "";
        rows.forEach((r, idx) => {
            const esc_emp = frappe.utils.escape_html(r.employee || "");
            const esc_name = frappe.utils.escape_html(r.employee_name || "");
            const esc_dept = frappe.utils.escape_html(r.department || "");
            const esc_type = frappe.utils.escape_html(r.leave_type || "");
            const bal = Number(r.available_balance || 0);
            const badge_color = bal > 0 ? "linear-gradient(135deg,#16a34a,#15803d)" : "#9ca3af";

            table_rows += `<tr data-dept="${esc_dept}" data-leave="${esc_type}" style="background:${idx % 2 === 0 ? '#ffffff' : '#f8fafc'}">
<td style="padding:8px 16px;font-size:13px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0;cursor:pointer" class="emp-link" data-name="${esc_emp}"><b>${esc_name}</b><br><span style="color:#64748b;font-size:11px;white-space:nowrap">${esc_emp}</span></td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_dept}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_type}</td>
<td style="padding:8px 16px;text-align:center;border-bottom:1px solid #f0f0f0">
<span style="display:inline-block;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;color:#fff;background:${badge_color};box-shadow:0 2px 6px rgba(22,163,74,0.25);min-width:50px">${bal}</span>
</td></tr>`;
        });

        const html = `<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;padding:10px 20px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:8px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:12px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:24px;line-height:1">&#x1F4CA;</div>
        <div style="flex:1">
            <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px">Organisation-wide Leave Summary</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:0">Real-time Organisation Leave Balances</div>
        </div>
        <div class="header-actions">
            <button id="openEmpListBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.2);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-external-link" style="font-size:11px"></i> Open Employee List
            </button>
            <button id="leaveBalanceReportBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.2);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-bar-chart" style="font-size:11px"></i> Leave Balance Report
            </button>
            <button id="refreshBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.15);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:11px"></i> Refresh
            </button>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#eff6ff;border-radius:10px;border:1px solid #bfdbfe;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:15px;flex-shrink:0"><i class="fa fa-users"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Total Employees</div>
                <div style="font-size:22px;font-weight:800;color:#1d4ed8;line-height:1">${kpi.total_employees}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Active</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#dcfce7,#f0fdf4);color:#16a34a;font-size:15px;flex-shrink:0"><i class="fa fa-check-circle"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">With Allocation</div>
                <div style="font-size:22px;font-weight:800;color:#15803d;line-height:1">${kpi.employees_with_allocation}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Employees</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:15px;flex-shrink:0"><i class="fa fa-calculator"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Total Balance</div>
                <div style="font-size:22px;font-weight:800;color:#d97706;line-height:1">${kpi.total_balance}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Days</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fafafa;border-radius:10px;border:1px solid #e5e7eb;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#f3f4f6,#f9fafb);color:#6b7280;font-size:15px;flex-shrink:0"><i class="fa fa-bar-chart"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Average Balance</div>
                <div style="font-size:22px;font-weight:800;color:#1f2937;line-height:1">${kpi.avg_balance}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Per Employee</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 16px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:13px;font-weight:700;color:#374151;display:flex;align-items:center;gap:6px;margin-right:auto">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:12px"></i> Leave Balance Details
                <span style="font-size:11px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:1px 8px;border-radius:10px;margin-left:4px">${total_rows}</span>
            </div>
            <select id="deptFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Departments</option></select>
            <select id="leaveFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Leave Types</option></select>
            <button id="exportBtn" style="display:flex;align-items:center;gap:4px;padding:4px 10px;border:none;border-radius:5px;background:#16a34a;color:#fff;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-download" style="font-size:10px"></i> Export</button>
        </div>

        <div class="table-container" style="max-height:450px">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Employee</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Department</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:120px">Available Balance</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:6px 16px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#6b7280">
            <span>Showing ${total_rows} allocation record${total_rows !== 1 ? 's' : ''}</span>
            <span style="font-size:10px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

        root_element.innerHTML = html;

        // Populate filters
        function fill(id, arr) {
            const s = $(root_element).find(id);
            arr.forEach(v => s.append(`<option>${v}</option>`));
        }
        fill("#deptFilter", departments);
        fill("#leaveFilter", leave_types);

        function apply() {
            const d = $("#deptFilter", root_element).val();
            const l = $("#leaveFilter", root_element).val();
            $("tbody tr", root_element).each(function () {
                let ok = true;
                if (d && $(this).data("dept") !== d) ok = false;
                if (l && $(this).data("leave") !== l) ok = false;
                $(this).toggle(ok);
            });
        }

        $(".emp-link", root_element).on("click", function (e) {
            e.stopPropagation();
            const name = $(this).data("name");
            if (name) frappe.set_route("Form", "Employee", name);
        });

        $("#deptFilter,#leaveFilter", root_element).on("change", apply);
        $("#refreshBtn", root_element).on("click", function (e) { e.stopPropagation(); load_org_leave_summary(); });
        $("#openEmpListBtn", root_element).on("click", function (e) { e.stopPropagation(); frappe.set_route("List", "Employee"); });
        $("#leaveBalanceReportBtn", root_element).on("click", function (e) { e.stopPropagation(); frappe.set_route("query-report", "Leave Balance Report"); });

        $("#exportBtn", root_element).on("click", function () {
            const dept = $("#deptFilter", root_element).val() || "All Departments";
            const ltype = $("#leaveFilter", root_element).val() || "All Leave Types";
            const today = frappe.datetime.get_today();
            const csv = [];
            csv.push('"ORGANISATION-WIDE LEAVE SUMMARY"');
            csv.push('');
            csv.push('"Export Date","' + frappe.datetime.str_to_user(today) + '"');
            csv.push('"Department","' + dept + '"');
            csv.push('"Leave Type","' + ltype + '"');
            csv.push('');
            csv.push('"Total Employees","' + kpi.total_employees + '","With Allocation","' + kpi.employees_with_allocation + '","Total Balance","' + kpi.total_balance + '"');
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
            link.download = "Org_Leave_Summary_" + today + ".csv";
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
        $("#retryBtn", root_element).on("click", function (e) { e.stopPropagation(); load_org_leave_summary(); });
    } finally {
        frappe.dom.unfreeze();
    }
}

load_org_leave_summary();
