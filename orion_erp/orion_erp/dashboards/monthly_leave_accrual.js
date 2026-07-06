frappe.dom.freeze("Loading Monthly Leave Accrual...");

async function load_monthly_accrual() {
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

        const { message: accrual_data } = await frappe.call({
            method: "orion_erp.api.get_monthly_leave_accrual"
        });

        if (!accrual_data || !accrual_data.length) {
            let html = `
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <div style="font-size:64px;margin-bottom:20px;opacity:0.3">&#x1F4CA;</div>
    <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">No Leave Accrued This Month</h3>
    <p style="margin:0;color:#9ca3af;font-size:14px">No leave types are accruing in the current month.</p>
</div>`;
            root_element.innerHTML = html;
            frappe.dom.unfreeze();
            return;
        }

        let total_types = accrual_data.length;
        let total_days = 0;

        let table_rows = "";
        accrual_data.forEach((row, idx) => {
            const days = Number(row.earned_days || 0);
            total_days += days;

            table_rows += [
                '<tr style="background:', (idx % 2 === 0 ? '#ffffff' : '#f8fafc'), '">',
                '<td style="padding:14px 20px;font-size:14px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0">', frappe.utils.escape_html(row.leave_type), '</td>',
                '<td style="padding:14px 20px;text-align:center;border-bottom:1px solid #f0f0f0">',
                '<span style="display:inline-block;padding:4px 16px;border-radius:20px;font-size:13px;font-weight:700;color:#fff;background:linear-gradient(135deg,#2563eb,#1d4ed8);box-shadow:0 2px 6px rgba(37,99,235,0.25);min-width:60px">',
                days, '</span></td>',
                '</tr>'
            ].join('');
        });

        const now = new Date();
        const month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

        let html = `
<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;padding:20px 24px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:10px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:20px 28px;display:flex;align-items:center;gap:16px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:32px;line-height:1">&#x1F4C8;</div>
        <div style="flex:1">
            <div style="font-size:20px;font-weight:700;color:#fff;letter-spacing:-0.3px">Monthly Leave Accrual Summary</div>
            <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:2px">Current Month Accrual Overview</div>
        </div>
        <div class="header-actions">
            <button id="openAllocBtn" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border:none;border-radius:8px;background:rgba(255,255,255,0.2);color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-external-link" style="font-size:12px"></i> Open Leave Allocations
            </button>
            <button id="refreshBtn" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border:none;border-radius:8px;background:rgba(255,255,255,0.15);color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:12px"></i> Refresh
            </button>
        </div>
    </div>

    <div class="kpi-grid">

        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#f8fafc;border-radius:10px;border:1px solid #e5e7eb;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:20px;flex-shrink:0"><i class="fa fa-user"></i></div>
            <div style="overflow:hidden">
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Employee</div>
                <div style="font-size:15px;font-weight:700;color:#1f2937;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${frappe.utils.escape_html(employee_name)}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:1px">${frappe.utils.escape_html(employee)}</div>
            </div>
        </div>

        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#eff6ff;border-radius:10px;border:1px solid #bfdbfe;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:20px;flex-shrink:0"><i class="fa fa-calendar"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Current Month</div>
                <div style="font-size:15px;font-weight:700;color:#1d4ed8;line-height:1.1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${month_names[now.getMonth()]} ${now.getFullYear()}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">Accrual Period</div>
            </div>
        </div>

        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dcfce7,#f0fdf4);color:#16a34a;font-size:20px;flex-shrink:0"><i class="fa fa-tags"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Types Accrued</div>
                <div style="font-size:28px;font-weight:800;color:#15803d;line-height:1.1">${total_types}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">This Month</div>
            </div>
        </div>

        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#eff6ff;border-radius:10px;border:1px solid #bfdbfe;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:20px;flex-shrink:0"><i class="fa fa-calculator"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Total Earned</div>
                <div style="font-size:28px;font-weight:800;color:#1d4ed8;line-height:1.1">${total_days.toFixed(2)}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">Days This Month</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;padding:14px 20px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:14px;font-weight:700;color:#374151;display:flex;align-items:center;gap:8px">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:13px"></i> Monthly Accrual Details
                <span style="font-size:12px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:2px 10px;border-radius:12px;margin-left:4px">${total_types}</span>
            </div>
        </div>

        <div class="table-container">
            <table style="width:100%;border-collapse:collapse;font-size:14px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:12px 20px;text-align:center;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:180px">Earned This Month</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:10px 20px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#6b7280">
            <span>Showing ${total_types} leave type${total_types !== 1 ? 's' : ''}</span>
            <span style="font-size:11px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

        root_element.innerHTML = html;

        $("#openAllocBtn", root_element).on("click", function (e) {
            e.stopPropagation();
            frappe.set_route("List", "Leave Allocation");
        });

        $("#refreshBtn", root_element).on("click", function (e) {
            e.stopPropagation();
            frappe.dom.freeze("Refreshing...");
            load_monthly_accrual();
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
            load_monthly_accrual();
        });
    } finally {
        frappe.dom.unfreeze();
    }
}

load_monthly_accrual();
