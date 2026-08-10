frappe.dom.freeze("Loading Emergency Leave Approval Queue...");

const APPROVAL_STATES = [
    "Open",
    "Pending Approval from Approver 1",
    "Pending Approval from Approver 2",
    "Pending Approval from Approver 3",
    "Pending Approval from Approver 4",
    "Pending Approval from Approver 5"
];

if (!(frappe.user_roles || []).includes("Leave Approver")) {
    root_element.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
        <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">You are not assigned the Leave Approver role.</h3>
    </div>`;
    frappe.dom.unfreeze();
    return;
}

frappe.db.get_list("Leave Application",{
    fields:[
        "name","employee","employee_name","department","company",
        "leave_type","from_date","to_date","posting_date",
        "total_leave_days","custom_approval_status",
        "leave_approver","custom_leave_approver_1",
        "custom_leave_approver_2","custom_leave_approver_4",
        "custom_leave_approver_5","modified"
    ],
    filters:{
        docstatus:0,
        leave_type:"EMERGENCY LEAVE",
        custom_approval_status:["in",APPROVAL_STATES]
    },
    limit:2000,
    order_by:"modified desc"
}).then(async data=>{

    const ids=[...new Set(
        data.flatMap(r=>[
            r.leave_approver,
            r.custom_leave_approver_1,
            r.custom_leave_approver_2,
            r.custom_leave_approver_4,
            r.custom_leave_approver_5
        ]).filter(Boolean)
    )];

    let userMap={};

    if(ids.length){
        const users=await frappe.db.get_list("User",{
            fields:["name","full_name"],
            filters:{name:["in",ids]},
            limit:ids.length
        });
        users.forEach(u=>userMap[u.name]=u.full_name||u.name);
    }

    function approverInfo(r){
        switch(r.custom_approval_status){
            case "Open":
            case "Pending Approval from Approver 1":
                return {
                    level:"Approver 1",
                    user:userMap[r.leave_approver] || r.leave_approver || "-"
                };
            case "Pending Approval from Approver 2":
                return {
                    level:"Approver 2",
                    user:userMap[r.custom_leave_approver_1] || r.custom_leave_approver_1 || "-"
                };
            case "Pending Approval from Approver 3":
                return {
                    level:"Approver 3",
                    user:userMap[r.custom_leave_approver_2] || r.custom_leave_approver_2 || "-"
                };
            case "Pending Approval from Approver 4":
                return {
                    level:"Approver 4",
                    user:userMap[r.custom_leave_approver_4] || r.custom_leave_approver_4 || "-"
                };
            case "Pending Approval from Approver 5":
                return {
                    level:"Approver 5",
                    user:userMap[r.custom_leave_approver_5] || r.custom_leave_approver_5 || "-"
                };
            default:
                return {level:"-",user:"-"};
        }
    }

    data.forEach(r=>{
        const a=approverInfo(r);
        r.pending_level=a.level;
        r.current_approver=a.user;
        r.age=frappe.datetime.get_day_diff(frappe.datetime.get_today(),r.posting_date);
    });

    let overdue=data.filter(x=>x.age>3).length;

    let table_rows = "";
    data.forEach((r,i)=>{
        let age_class = r.age > 3 ? "color:#dc2626;font-weight:700" : r.age > 1 ? "color:#d97706;font-weight:700" : "color:#15803d;font-weight:700";
        table_rows += `<tr data-company="${frappe.utils.escape_html(r.company||'')}" data-dept="${frappe.utils.escape_html(r.department||'')}" data-leave="${frappe.utils.escape_html(r.leave_type||'')}" style="background:${i%2===0?'#ffffff':'#f8fafc'}">
<td style="padding:14px 20px;font-size:13px;font-weight:500;color:#2563eb;border-bottom:1px solid #f0f0f0;cursor:pointer" class="app-link" data-name="${frappe.utils.escape_html(r.name)}">${frappe.utils.escape_html(r.name)}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${frappe.utils.escape_html(r.employee||'')}</td>
<td style="padding:14px 20px;font-size:14px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.employee_name||'')}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.department||'')}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.company||'')}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.leave_type||'')}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${frappe.datetime.str_to_user(r.from_date)}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${frappe.datetime.str_to_user(r.to_date)}</td>
<td style="padding:14px 20px;text-align:center;font-weight:600;font-size:14px;color:#1f2937;border-bottom:1px solid #f0f0f0">${r.total_leave_days||0}</td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0"><span style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;color:#2563eb;background:#eff6ff;border:1px solid #bfdbfe">${frappe.utils.escape_html(r.pending_level)}</span></td>
<td style="padding:14px 20px;font-size:13px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.current_approver)}</td>
<td style="padding:14px 20px;text-align:center;font-size:14px;font-weight:600;border-bottom:1px solid #f0f0f0;${age_class}">${r.age}</td>
</tr>`;
    });

    let html = `<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;padding:20px 24px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:10px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:20px 28px;display:flex;align-items:center;gap:16px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:32px;line-height:1">&#x1F46B;</div>
        <div style="flex:1">
            <div style="font-size:20px;font-weight:700;color:#fff;letter-spacing:-0.3px">Emergency Leave Approval Queue</div>
            <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:2px">HR Manager View — Emergency Leave Pending Approvals</div>
        </div>
        <div class="header-actions">
            <button id="openListBtn" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border:none;border-radius:8px;background:rgba(255,255,255,0.2);color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.15)">
                <i class="fa fa-external-link" style="font-size:12px"></i> Open List
            </button>
            <button id="refreshBtn" style="display:flex;align-items:center;gap:6px;padding:8px 18px;border:none;border-radius:8px;background:rgba(255,255,255,0.15);color:#fff;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:12px"></i> Refresh
            </button>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:20px;flex-shrink:0"><i class="fa fa-clock-o"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Total Pending</div>
                <div style="font-size:28px;font-weight:800;color:#d97706;line-height:1.1">${data.length}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">All Departments</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#fef2f2;border-radius:10px;border:1px solid #fecaca;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#fee2e2,#fef2f2);color:#ef4444;font-size:20px;flex-shrink:0"><i class="fa fa-exclamation-triangle"></i></div>
            <div>
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">Overdue</div>
                <div style="font-size:28px;font-weight:800;color:#dc2626;line-height:1.1">${overdue}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:2px">Pending > 3 Days</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:#f8fafc;border-radius:10px;border:1px solid #e5e7eb;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:20px;flex-shrink:0"><i class="fa fa-user-md"></i></div>
            <div style="overflow:hidden">
                <div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px">HR Manager</div>
                <div style="font-size:15px;font-weight:700;color:#1f2937;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${frappe.utils.escape_html(frappe.session.user_fullname||frappe.session.user)}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:1px">${frappe.utils.escape_html(frappe.session.user)}</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:14px 20px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:14px;font-weight:700;color:#374151;display:flex;align-items:center;gap:8px;margin-right:auto">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:13px"></i> Emergency Leave Approval Queue
                <span style="font-size:12px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:2px 10px;border-radius:12px;margin-left:4px">${data.length}</span>
            </div>
            <select id="companyFilter" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;background:#fff;cursor:pointer"><option value="">All Companies</option></select>
            <select id="deptFilter" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;background:#fff;cursor:pointer"><option value="">All Departments</option></select>
                        <button id="exportBtn" style="display:flex;align-items:center;gap:5px;padding:6px 14px;border:none;border-radius:6px;background:#16a34a;color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-download"></i> Export</button>
        </div>

        <div class="table-container" style="max-height:650px">
            <table style="width:100%;border-collapse:collapse;font-size:14px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave No</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Employee</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Name</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Department</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Company</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">From</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">To</th>
                        <th style="padding:12px 20px;text-align:center;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:60px">Days</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Pending Level</th>
                        <th style="padding:12px 20px;text-align:left;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Current Approver</th>
                        <th style="padding:12px 20px;text-align:center;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:60px">Age</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:10px 20px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#6b7280">
            <span>Showing ${data.length} pending application${data.length!==1?'s':''} across all departments</span>
            <span style="font-size:11px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

    root_element.innerHTML = html;

    function fill(id,key){
        let s=$(root_element).find(id);
        [...new Set(data.map(x=>x[key]).filter(Boolean))].sort().forEach(v=>s.append(`<option>${v}</option>`));
    }
    fill("#companyFilter","company");
    fill("#deptFilter","department");

    function apply(){
        const c=$("#companyFilter",root_element).val();
        const d=$("#deptFilter",root_element).val();
        $("tbody tr",root_element).each(function(){
            let ok=true;
            if(c && $(this).data("company")!=c) ok=false;
            if(d && $(this).data("dept")!=d) ok=false;
            $(this).toggle(ok);
        });
    }

    $(".app-link",root_element).on("click",function(e){
        e.stopPropagation();
        const name=$(this).data("name");
        if(name) frappe.set_route("Form","Leave Application",name);
    });

    $("#companyFilter,#deptFilter",root_element).on("change",apply);
    $("#refreshBtn",root_element).on("click",function(e){e.stopPropagation();location.reload();});
    $("#openListBtn",root_element).on("click",function(e){e.stopPropagation();frappe.set_route("List","Leave Application");});

    $("#exportBtn",root_element).on("click",function(){
        const csv=[];
        $("table tr:visible",root_element).each(function(){
            const row=[];
            $(this).find("th,td").each(function(){
                row.push('"'+$(this).text().trim().replace(/"/g,'""')+'"');
            });
            csv.push(row.join(","));
        });
        const blob=new Blob([csv.join("\n")],{type:"text/csv;charset=utf-8"});
        const a=document.createElement("a");
        a.href=URL.createObjectURL(blob);
        a.download="Emergency_Leave_Approval_Queue.csv";
        a.click();
    });

    frappe.dom.unfreeze();

}).catch(e=>{
    frappe.dom.unfreeze();
    console.error(e);
    frappe.msgprint(e.message||e);
});
