frappe.dom.freeze("Loading Rejoining Overdue Dashboard...");

async function load_rejoining_overdue() {
    root_element.innerHTML = "";

    try {
        const { message: data } = await frappe.call({
            method: "orion_erp.api.get_rejoining_overdue"
        });

        if (!data || !data.rows || !data.rows.length) {
            root_element.innerHTML = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="font-size:64px;margin-bottom:20px;opacity:0.3">&#x2705;</div>
    <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">No Overdue Rejoinings</h3>
    <p style="margin:0;color:#9ca3af;font-size:14px">All leave applications have their Rejoining Forms submitted.</p>
</div>`;
            frappe.dom.unfreeze();
            return;
        }

        const kpi = data.kpi;
        const rows = data.rows;
        const total_rows = rows.length;

        const companies = [...new Set(rows.map(r => r.company).filter(Boolean))].sort();
        const departments = [...new Set(rows.map(r => r.department).filter(Boolean))].sort();
        const leave_types = [...new Set(rows.map(r => r.leave_type).filter(Boolean))].sort();

        let table_rows = "";
        rows.forEach((r, idx) => {
            const esc_emp = frappe.utils.escape_html(r.employee || "");
            const esc_emp_name = frappe.utils.escape_html(r.employee_name || "");
            const esc_name = frappe.utils.escape_html(r.name || "");
            const esc_type = frappe.utils.escape_html(r.leave_type || "");
            const esc_dept = frappe.utils.escape_html(r.department || "");
            const esc_company = frappe.utils.escape_html(r.company || "");
            const from_date = frappe.datetime.str_to_user(r.from_date);
            const to_date = frappe.datetime.str_to_user(r.to_date);
            const leave_end = frappe.datetime.str_to_user(r.leave_end_date);
            const expected_rejoin = frappe.datetime.str_to_user(r.expected_rejoining_date);
            const overdue = Number(r.overdue_days || 0);

            let severity_color = "#15803d";
            let severity_bg = "#f0fdf4";
            let severity_border = "#bbf7d0";
            if (overdue > 30) {
                severity_color = "#dc2626";
                severity_bg = "#fef2f2";
                severity_border = "#fecaca";
            } else if (overdue > 7) {
                severity_color = "#d97706";
                severity_bg = "#fffbeb";
                severity_border = "#fde68a";
            }

            table_rows += `<tr data-company="${esc_company}" data-dept="${esc_dept}" data-leave="${esc_type}" style="background:${idx % 2 === 0 ? '#ffffff' : '#f8fafc'}">
<td style="padding:8px 16px;font-size:12px;font-weight:500;color:#2563eb;border-bottom:1px solid #f0f0f0;white-space:nowrap">${esc_emp}</td>
<td style="padding:8px 16px;font-size:13px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0"><b>${esc_emp_name}</b></td>
<td style="padding:8px 16px;font-size:12px;font-weight:500;color:#2563eb;border-bottom:1px solid #f0f0f0;cursor:pointer" class="app-link" data-name="${esc_name}">${esc_name}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_type}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${from_date}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${to_date}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${leave_end}</td>
<td style="padding:8px 16px;font-size:12px;color:#2563eb;font-weight:600;border-bottom:1px solid #f0f0f0;white-space:nowrap">${expected_rejoin}</td>
<td style="padding:8px 16px;text-align:center;border-bottom:1px solid #f0f0f0">
<span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;color:${severity_color};background:${severity_bg};border:1px solid ${severity_border}">${overdue} day${overdue !== 1 ? 's' : ''}</span>
</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_dept}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${esc_company}</td>
</tr>`;
        });

        const html = `<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;padding:10px 20px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:8px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}.filter-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 16px;background:#f8fafc;border-bottom:1px solid #e5e7eb}.filter-bar select{padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer;min-width:120px}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#991b1b,#dc2626,#ef4444);border-radius:12px 12px 0 0;padding:12px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 16px rgba(220,38,38,0.25)">
        <div style="font-size:24px;line-height:1">&#x23F0;</div>
        <div style="flex:1">
            <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px">Rejoining Overdue</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:0">Leave Applications Past End Date Without Rejoining Form</div>
        </div>
        <div class="header-actions">
            <button id="openListBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.2);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-external-link" style="font-size:11px"></i> Open List
            </button>
            <button id="refreshBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.15);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:11px"></i> Refresh
            </button>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fef2f2;border-radius:10px;border:1px solid #fecaca;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fee2e2,#fef2f2);color:#dc2626;font-size:15px;flex-shrink:0"><i class="fa fa-exclamation-circle"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Total Overdue</div>
                <div style="font-size:22px;font-weight:800;color:#dc2626;line-height:1">${kpi.total}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Rejoinings Pending</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:15px;flex-shrink:0"><i class="fa fa-clock-o"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">1–7 Days</div>
                <div style="font-size:22px;font-weight:800;color:#d97706;line-height:1">${kpi.overdue_1_7}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Recently Overdue</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fff7ed;border-radius:10px;border:1px solid #fed7aa;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#ffedd5,#fff7ed);color:#ea580c;font-size:15px;flex-shrink:0"><i class="fa fa-warning"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">8–30 Days</div>
                <div style="font-size:22px;font-weight:800;color:#ea580c;line-height:1">${kpi.overdue_8_30}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Moderate</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fef2f2;border-radius:10px;border:1px solid #fecaca;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fee2e2,#fef2f2);color:#991b1b;font-size:15px;flex-shrink:0"><i class="fa fa-times-circle"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">30+ Days</div>
                <div style="font-size:22px;font-weight:800;color:#991b1b;line-height:1">${kpi.overdue_30_plus}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Critical</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div class="filter-bar">
            <div style="font-size:13px;font-weight:700;color:#374151;display:flex;align-items:center;gap:6px;margin-right:auto">
                <i class="fa fa-list-alt" style="color:#dc2626;font-size:12px"></i> Overdue Records
                <span id="visibleCount" style="font-size:11px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:1px 8px;border-radius:10px;margin-left:4px">${total_rows}</span>
            </div>
            <select id="companyFilter"><option value="">All Companies</option></select>
            <select id="deptFilter"><option value="">All Departments</option></select>
            <select id="leaveFilter"><option value="">All Leave Types</option></select>
            <button id="clearFilters" style="display:flex;align-items:center;gap:4px;padding:4px 10px;border:1px solid #d1d5db;border-radius:5px;background:#fff;color:#374151;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-times" style="font-size:10px"></i> Clear</button>
            <button id="exportBtn" style="display:flex;align-items:center;gap:4px;padding:4px 10px;border:none;border-radius:5px;background:#16a34a;color:#fff;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-download" style="font-size:10px"></i> Export</button>
        </div>

        <div class="table-container" style="max-height:500px">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap">Employee ID</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Employee Name</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap">Leave Application</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap">From Date</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap">To Date</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap">Leave End Date</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;white-space:nowrap">Expected Rejoining</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:90px">Overdue Days</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Department</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Company</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:6px 16px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#6b7280">
            <span id="footerInfo">Showing ${total_rows} overdue rejoining${total_rows !== 1 ? 's' : ''}</span>
            <span style="font-size:10px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

        root_element.innerHTML = html;

        function fillSelect(id, values) {
            const sel = $(root_element).find(id);
            values.forEach(v => sel.append(`<option>${frappe.utils.escape_html(v)}</option>`));
        }
        fillSelect("#companyFilter", companies);
        fillSelect("#deptFilter", departments);
        fillSelect("#leaveFilter", leave_types);

        function applyFilters() {
            const c = $("#companyFilter", root_element).val();
            const d = $("#deptFilter", root_element).val();
            const l = $("#leaveFilter", root_element).val();
            let visible = 0;
            $("tbody tr", root_element).each(function () {
                let ok = true;
                if (c && $(this).data("company") !== c) ok = false;
                if (d && $(this).data("dept") !== d) ok = false;
                if (l && $(this).data("leave") !== l) ok = false;
                $(this).toggle(ok);
                if (ok) visible++;
            });
            $("#visibleCount", root_element).text(visible);
            $("#footerInfo", root_element).text("Showing " + visible + " overdue rejoining" + (visible !== 1 ? "s" : ""));
        }

        $("#companyFilter,#deptFilter,#leaveFilter", root_element).on("change", applyFilters);

        $("#clearFilters", root_element).on("click", function (e) {
            e.stopPropagation();
            $("#companyFilter,#deptFilter,#leaveFilter", root_element).val("");
            applyFilters();
        });

        $(".app-link", root_element).on("click", function (e) {
            e.stopPropagation();
            const name = $(this).data("name");
            if (name) frappe.set_route("Form", "Leave Application", name);
        });

        $("#refreshBtn", root_element).on("click", function (e) { e.stopPropagation(); load_rejoining_overdue(); });
        $("#openListBtn", root_element).on("click", function (e) { e.stopPropagation(); frappe.set_route("List", "Leave Application"); });

        $("#exportBtn", root_element).on("click", function () {
            const today = frappe.datetime.get_today();
            const comp = $("#companyFilter", root_element).val() || "All";
            const dept = $("#deptFilter", root_element).val() || "All";
            const lt = $("#leaveFilter", root_element).val() || "All";
            const csv = [];
            csv.push('"REJOINING OVERDUE REPORT"');
            csv.push('');
            csv.push('"Export Date","' + frappe.datetime.str_to_user(today) + '"');
            csv.push('"Company","' + comp + '","Department","' + dept + '","Leave Type","' + lt + '"');
            csv.push('');
            csv.push('"Total Overdue","' + kpi.total + '"');
            csv.push('"1-7 Days","' + kpi.overdue_1_7 + '","8-30 Days","' + kpi.overdue_8_30 + '","30+ Days","' + kpi.overdue_30_plus + '"');
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
            link.download = "Rejoining_Overdue_" + today + ".csv";
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
        $("#retryBtn", root_element).on("click", function (e) { e.stopPropagation(); load_rejoining_overdue(); });
    } finally {
        frappe.dom.unfreeze();
    }
}

load_rejoining_overdue();
