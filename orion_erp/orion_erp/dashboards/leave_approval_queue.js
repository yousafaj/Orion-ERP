frappe.dom.freeze("Loading Leave Approval Queue...");

const CURRENT_USER = frappe.session.user;
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
        "custom_leave_approver_5","status","custom_status_approver1","custom_status_approver2","custom_status_approver4","custom_status_approver5","modified"
    ],
    filters:{
        docstatus:0,
        custom_approval_status:["in",APPROVAL_STATES]
    },
    limit:2000,
    order_by:"modified desc"
}).then(data=>{

    function pendingLevel(r){

        const flow=[
            {level:"Approver 1",user:r.leave_approver,status:r.status},
            {level:"Approver 2",user:r.custom_leave_approver_1,status:r.custom_status_approver1},
            {level:"Approver 3",user:r.custom_leave_approver_2,status:r.custom_status_approver2},
            {level:"Approver 4",user:r.custom_leave_approver_4,status:r.custom_status_approver4},
            {level:"Approver 5",user:r.custom_leave_approver_5,status:r.custom_status_approver5}
        ];

        for(const row of flow){
            if(row.user===CURRENT_USER && row.status==="Open"){
                return row.level;
            }
            if(row.status==="Open"){
                break;
            }
        }

        return "";
    }

    data=data.filter(d=>{
        d.pending_level=pendingLevel(d);
        return d.pending_level;
    });

    data.forEach(d=>{
        d.age=frappe.datetime.get_day_diff(frappe.datetime.get_today(),d.posting_date);
    });

    let overdue=data.filter(x=>x.age>3).length;

    let table_rows = "";
    data.forEach((r,i)=>{
        let age_class = r.age > 3 ? "color:#dc2626;font-weight:700" : r.age > 1 ? "color:#d97706;font-weight:700" : "color:#15803d;font-weight:700";
        table_rows += `<tr data-company="${frappe.utils.escape_html(r.company||'')}" data-dept="${frappe.utils.escape_html(r.department||'')}" data-leave="${frappe.utils.escape_html(r.leave_type||'')}" style="background:${i%2===0?'#ffffff':'#f8fafc'}">
<td style="padding:8px 16px;font-size:12px;font-weight:500;color:#2563eb;border-bottom:1px solid #f0f0f0;cursor:pointer" class="app-link" data-name="${frappe.utils.escape_html(r.name)}">${frappe.utils.escape_html(r.name)}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${frappe.utils.escape_html(r.employee||'')}</td>
<td style="padding:8px 16px;font-size:13px;font-weight:500;color:#1f2937;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.employee_name||'')}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.department||'')}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.company||'')}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.leave_type||'')}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${frappe.datetime.str_to_user(r.from_date)}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${frappe.datetime.str_to_user(r.to_date)}</td>
<td style="padding:8px 16px;text-align:center;font-weight:600;font-size:13px;color:#1f2937;border-bottom:1px solid #f0f0f0">${r.total_leave_days||0}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0"><span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;color:#2563eb;background:#eff6ff;border:1px solid #bfdbfe">${frappe.utils.escape_html(r.pending_level)}</span></td>
<td style="padding:8px 16px;text-align:center;font-size:13px;font-weight:600;border-bottom:1px solid #f0f0f0;${age_class}">${r.age}</td>
</tr>`;
    });

    let html = `<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;padding:10px 20px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:8px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:12px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:24px;line-height:1">&#x1F4CB;</div>
        <div style="flex:1">
            <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px">Leave Application Approval Queue</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:0">Applications Awaiting Your Approval</div>
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
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:15px;flex-shrink:0"><i class="fa fa-clock-o"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Pending Approvals</div>
                <div style="font-size:22px;font-weight:800;color:#d97706;line-height:1">${data.length}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Awaiting Your Decision</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fef2f2;border-radius:10px;border:1px solid #fecaca;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fee2e2,#fef2f2);color:#ef4444;font-size:15px;flex-shrink:0"><i class="fa fa-exclamation-triangle"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Overdue</div>
                <div style="font-size:22px;font-weight:800;color:#dc2626;line-height:1">${overdue}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Pending > 3 Days</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f8fafc;border-radius:10px;border:1px solid #e5e7eb;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#dbeafe,#eff6ff);color:#2563eb;font-size:15px;flex-shrink:0"><i class="fa fa-user"></i></div>
            <div style="overflow:hidden">
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Leave Approver</div>
                <div style="font-size:13px;font-weight:700;color:#1f2937;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${frappe.utils.escape_html(frappe.session.user_fullname||frappe.session.user)}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">${frappe.utils.escape_html(frappe.session.user)}</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 16px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:13px;font-weight:700;color:#374151;display:flex;align-items:center;gap:6px;margin-right:auto">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:12px"></i> Approval Queue
                <span style="font-size:11px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:1px 8px;border-radius:10px;margin-left:4px">${data.length}</span>
            </div>
            <select id="companyFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Companies</option></select>
            <select id="deptFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Departments</option></select>
            <select id="leaveFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Leave Types</option></select>
            <button id="exportBtn" style="display:flex;align-items:center;gap:4px;padding:4px 10px;border:none;border-radius:5px;background:#16a34a;color:#fff;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-download" style="font-size:10px"></i> Export</button>
        </div>

        <div class="table-container" style="max-height:450px">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave No</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Employee</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Name</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Department</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Company</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">From</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">To</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:50px">Days</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Pending</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:50px">Age</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:6px 16px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#6b7280">
            <span>Showing ${data.length} application${data.length!==1?'s':''} pending your approval</span>
            <span style="font-size:10px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
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
    fill("#leaveFilter","leave_type");

    function apply(){
        let c=$("#companyFilter",root_element).val();
        let d=$("#deptFilter",root_element).val();
        let l=$("#leaveFilter",root_element).val();
        $("tbody tr",root_element).each(function(){
            let ok=true;
            if(c && $(this).data("company")!=c) ok=false;
            if(d && $(this).data("dept")!=d) ok=false;
            if(l && $(this).data("leave")!=l) ok=false;
            $(this).toggle(ok);
        });
    }

    $(".app-link",root_element).on("click",function(e){
        e.stopPropagation();
        const name=$(this).data("name");
        if(name) frappe.set_route("Form","Leave Application",name);
    });

    $("#companyFilter,#deptFilter,#leaveFilter",root_element).on("change",apply);
    $("#refreshBtn",root_element).on("click",function(e){e.stopPropagation();location.reload();});
    $("#openListBtn",root_element).on("click",function(e){e.stopPropagation();frappe.set_route("List","Leave Application");});

    $("#exportBtn",root_element).on("click",function(){
        let company=$("#companyFilter",root_element).val()||"All Companies";
        let department=$("#deptFilter",root_element).val()||"All Departments";
        let leave_type=$("#leaveFilter",root_element).val()||"All Leave Types";
        let today=frappe.datetime.get_today();
        let csv=[];
        csv.push('"LEAVE APPLICATION APPROVAL QUEUE"');
        csv.push("");
        csv.push('"Export Date","'+frappe.datetime.str_to_user(today)+'"');
        csv.push('"Company","'+company+'"');
        csv.push('"Department","'+department+'"');
        csv.push('"Leave Type","'+leave_type+'"');
        csv.push("");
        csv.push('"Pending Applications","'+data.length+'","Overdue Applications","'+overdue+'"');
        csv.push("");
        csv.push("");
        let headers=[];
        $("table thead th",root_element).each(function(){headers.push('"'+$(this).text().trim().replace(/"/g,'""')+'"');});
        csv.push(headers.join(","));
        $("table tbody tr:visible",root_element).each(function(){
            let row=[];
            $(this).find("td").each(function(index){
                let t=index===0?$(this).find("a").text().trim():$(this).text().replace(/\n/g," ").trim();
                row.push('"'+t.replace(/"/g,'""')+'"');
            });
            csv.push(row.join(","));
        });
        let blob=new Blob([csv.join("\n")],{type:"text/csv;charset=utf-8;"});
        let link=document.createElement("a");
        link.href=URL.createObjectURL(blob);
        link.download="Leave_Approval_Queue_"+today+".csv";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    frappe.dom.unfreeze();

}).catch(e=>{
    frappe.dom.unfreeze();
    console.error(e);
    frappe.msgprint(e.message||e);
});
