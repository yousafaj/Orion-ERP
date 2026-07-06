frappe.dom.freeze("Loading Pending Leave Applications...");

async function load_pending_leaves() {
    root_element.innerHTML = "";

    try {
        const { message: emp } = await frappe.db.get_value(
            "Employee",
            { user_id: frappe.session.user },
            ["name", "employee_name"]
        );

        if (!emp) {
            root_element.innerHTML = [
                '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">',
                '<div style="font-size:64px;margin-bottom:20px;opacity:0.3">&#x1F464;</div>',
                '<h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">No Employee Linked</h3>',
                '<p style="margin:0;color:#9ca3af;font-size:14px">No employee record is linked to your user account.</p>',
                '</div>'
            ].join('');
            frappe.dom.unfreeze();
            return;
        }

        const employee = emp.name;
        const employee_name = emp.employee_name;

        const { message: leave_data } = await frappe.call({
            method: "orion_erp.api.get_pending_leave_applications"
        });

        if (!leave_data || !leave_data.length) {
            let html = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="font-size:64px;margin-bottom:20px;opacity:0.3">&#x2705;</div>
    <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">No Pending Leave Applications</h3>
    <p style="margin:0;color:#9ca3af;font-size:14px">All your leave applications have been processed.</p>
</div>`;
            root_element.innerHTML = html;
            frappe.dom.unfreeze();
            return;
        }

        let pending_count = leave_data.length;
        let total_requested_days = 0;
        let latest_request = "";

        let table_rows = "";
        leave_data.forEach((row, idx) => {
            const days = Number(row.total_days || 0);
            total_requested_days += days;

            const escaped_type = frappe.utils.escape_html(row.leave_type);
            const escaped_status = frappe.utils.escape_html(row.status);

            let status_badge_color = "#f59e0b";
            let status_bg = "#fffbeb";

            const s = (row.status || "").toLowerCase();
            if (s.indexOf("approve") !== -1) {
                status_badge_color = "#16a34a";
                status_bg = "#f0fdf4";
            } else if (s.indexOf("reject") !== -1) {
                status_badge_color = "#ef4444";
                status_bg = "#fef2f2";
            } else if (s.indexOf("cancel") !== -1) {
                status_badge_color = "#6b7280";
                status_bg = "#f3f4f6";
            }

            table_rows += [
                '<tr style="background:', (idx % 2 === 0 ? '#ffffff' : '#f8fafc'), '">',
                '<td style="padding:14px 20px;font-size:13px;font-weight:500;color:#2563eb;border-bottom:1px solid #f0f0f0;cursor:pointer" class="app-link" data-name="', frappe.utils.escape_html(row.name), '">',
                frappe.utils.escape_html(row.name), '</td>',
                '<td style="padding:14px 20px;font-size:14px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0">', escaped_type, '</td>',
                '<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">', frappe.datetime.str_to_user(row.from_date), '</td>',
                '<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">', frappe.datetime.str_to_user(row.to_date), '</td>',
                '<td style="padding:14px 20px;text-align:center;font-weight:600;font-size:14px;color:#1f2937;border-bottom:1px solid #f0f0f0">', days, '</td>',
                '<td style="padding:14px 20px;text-align:center;border-bottom:1px solid #f0f0f0">',
                '<span style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;color:', status_badge_color, ';background:', status_bg, ';border:1px solid ', status_badge_color, '33">',
                escaped_status, '</span></td>',
                '</tr>'
            ].join('');
        });

        if (leave_data.length > 0) {
            const latest = leave_data[0];
            latest_request = frappe.datetime.str_to_user(latest.from_date) + " - " + frappe.datetime.str_to_user(latest.to_date);
        }

        let html = `
<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:20px 28px;display:flex;align-items:center;gap:16px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:32px;line-height:1">&#x23F3;</div>
        <div style="flex:1">
            <div style="font-size:20px;font-weight:700;color:#fff;letter-spacing:-0.3px">Pending Leave Applications</div>
            <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:2px">Applications Awaiting Approval</div>
        </div>
        <div style="display:flex;gap:10px">
            <button id="openLeaveListBtn" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border:none;border-radius:8px;background:rgba(255,255,255,0.2);color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-external-link" style="font-size:12px"></i> Open Leave Application
            </button>
            <button id="refreshBtn" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border:none;border-radius:8px;background:rgba(255,255,255,0.15);color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:12px"></i> Refresh
            </button>
        </div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:20px 24px;background:#ffffff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb">

        <div style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#f8fafc;border-radius:10px;border:1px solid #e5e7eb;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:20px;flex-shrink:0"><i class="fa fa-user"></i></div>
            <div style="overflow:hidden">
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Employee</div>
                <div style="font-size:15px;font-weight:700;color:#1f2937;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${frappe.utils.escape_html(employee_name)}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:1px">${frappe.utils.escape_html(employee)}</div>
            </div>
        </div>

        <div style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:20px;flex-shrink:0"><i class="fa fa-clock-o"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Pending Requests</div>
                <div style="font-size:28px;font-weight:800;color:#d97706;line-height:1.1">${pending_count}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">Awaiting Approval</div>
            </div>
        </div>

        <div style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dcfce7,#f0fdf4);color:#16a34a;font-size:20px;flex-shrink:0"><i class="fa fa-calculator"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Total Requested Days</div>
                <div style="font-size:28px;font-weight:800;color:#15803d;line-height:1.1">${total_requested_days}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">Days Pending</div>
            </div>
        </div>

        <div style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#eff6ff;border-radius:10px;border:1px solid #bfdbfe;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:20px;flex-shrink:0"><i class="fa fa-calendar-check-o"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Latest Request</div>
                <div style="font-size:13px;font-weight:700;color:#1d4ed8;line-height:1.1;white-space:nowrap">${latest_request || "N/A"}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">Most Recent</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;padding:14px 20px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:14px;font-weight:700;color:#374151;display:flex;align-items:center;gap:8px">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:13px"></i> Leave Applications
                <span style="font-size:12px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:2px 10px;border-radius:12px;margin-left:4px">${pending_count}</span>
            </div>
        </div>

        <div class="table-container">
            <table style="width:100%;border-collapse:collapse;font-size:14px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Application</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">From</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">To</th>
                        <th style="padding:12px 20px;text-align:center;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:80px">Days</th>
                        <th style="padding:12px 20px;text-align:center;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:140px">Status</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:10px 20px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#6b7280">
            <span>Showing ${pending_count} pending application${pending_count !== 1 ? 's' : ''}</span>
            <span style="font-size:11px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

        root_element.innerHTML = html;

        $(".app-link", root_element).on("click", function (e) {
            e.stopPropagation();
            const name = $(this).data("name");
            if (name) {
                frappe.set_route("Form", "Leave Application", name);
            }
        });

        $("#openLeaveListBtn", root_element).on("click", function (e) {
            e.stopPropagation();
            frappe.set_route("List", "Leave Application");
        });

        $("#refreshBtn", root_element).on("click", function (e) {
            e.stopPropagation();
            frappe.dom.freeze("Refreshing...");
            load_pending_leaves();
        });

        frappe.dom.unfreeze();
    } catch (e) {
        console.error(e);
        let html = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="width:60px;height:60px;border-radius:50%;background:#fef2f2;display:flex;align-items:center;justify-content:center;margin-bottom:16px;font-size:28px;color:#ef4444">&#x26A0;</div>
    <h3 style="margin:0 0 8px;color:#991b1b;font-weight:600;font-size:18px">Unable to Load Data</h3>
    <p style="margin:0 0 16px;color:#b91c1c;font-size:14px;max-width:400px;text-align:center">${frappe.utils.escape_html(e.message || String(e))}</p>
    <button id="retryBtn" style="padding:10px 24px;border:none;border-radius:8px;background:#ef4444;color:#fff;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit">Try Again</button>
</div>`;
        root_element.innerHTML = html;
        $("#retryBtn", root_element).on("click", function (e) {
            e.stopPropagation();
            load_pending_leaves();
        });
    } finally {
        frappe.dom.unfreeze();
    }
}

load_pending_leaves();
