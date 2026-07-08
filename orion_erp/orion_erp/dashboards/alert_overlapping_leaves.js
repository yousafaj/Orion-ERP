frappe.dom.freeze("Loading Team Leave Overlap Alerts...");

if (!(frappe.user_roles || []).includes("HR Manager")) {
    root_element.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;padding:60px 40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.06);font-family:Inter,system-ui,sans-serif">
    <h3 style="margin:0 0 8px;color:#374151;font-weight:600;font-size:20px">You are not assigned the HR Manager role.</h3></div>`;
    frappe.dom.unfreeze();
    return;
}

frappe.db.get_list("Leave Application",{
    fields:["name","employee","employee_name","department","company","leave_type","from_date","to_date"],
    filters:{docstatus:1},
    limit:5000,
    order_by:"from_date asc"
}).then(data=>{

    const overlaps={};

    data.forEach(r=>{
        let d=frappe.datetime.str_to_obj(r.from_date);
        const end=frappe.datetime.str_to_obj(r.to_date);

        while(d<=end){
            const key=[frappe.datetime.obj_to_str(d),r.company||"",r.department||""].join("||");

            if(!overlaps[key]){
                overlaps[key]={
                    date:frappe.datetime.obj_to_str(d),
                    company:r.company||"",
                    department:r.department||"",
                    employees:[],
                    leave_types:new Set(),
                    applications:[]
                };
            }

            overlaps[key].employees.push(r.employee_name||r.employee);
            overlaps[key].leave_types.add(r.leave_type);
            overlaps[key].applications.push(r.name);
            d.setDate(d.getDate()+1);
        }
    });

    const rows=Object.values(overlaps).filter(x=>x.employees.length>1).map(x=>{
        x.count=x.employees.length;
        x.employee_names=x.employees.join(", ");
        x.leave_types=[...x.leave_types].join(", ");
        x.severity=x.count>=4?"Critical":x.count===3?"High":"Medium";
        return x;
    });

    const today=frappe.datetime.get_today();
    const critical=rows.filter(r=>r.severity==="Critical").length;
    const upcoming=rows.filter(r=>r.date>=today).length;
    const todayCnt=rows.filter(r=>r.date===today).length;

    let table_rows = "";
    rows.forEach(r=>{
        const bg=r.severity==="Critical"?"#fef2f2":r.severity==="High"?"#fffbeb":"#ffffff";
        const applicationLinks=r.applications.map(app=>`<a href="#" onclick="frappe.set_route('Form','Leave Application','${app}');return false;" style="color:#2563eb;font-weight:600;text-decoration:none;">${app}</a>`).join("<br>");
        table_rows += `<tr data-company="${frappe.utils.escape_html(r.company)}" data-dept="${frappe.utils.escape_html(r.department)}" style="background:${bg}">
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0;white-space:nowrap">${r.date}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.department)}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.company)}</td>
<td style="padding:8px 16px;font-size:12px;color:#1f2937;border-bottom:1px solid #f0f0f0;font-weight:500">${frappe.utils.escape_html(r.employee_names)}</td>
<td style="padding:8px 16px;text-align:center;font-size:13px;font-weight:600;color:#1f2937;border-bottom:1px solid #f0f0f0">${r.count}</td>
<td style="padding:8px 16px;font-size:12px;color:#6b7280;border-bottom:1px solid #f0f0f0">${frappe.utils.escape_html(r.leave_types)}</td>
<td style="padding:8px 16px;text-align:center;border-bottom:1px solid #f0f0f0">
<span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;color:${r.severity==="Critical"?"#dc2626":r.severity==="High"?"#d97706":"#6b7280"};background:${r.severity==="Critical"?"#fee2e2":r.severity==="High"?"#fef3c7":"#f3f4f6"}">${r.severity}</span>
</td>
<td style="padding:8px 16px;font-size:12px;border-bottom:1px solid #f0f0f0">${applicationLinks}</td>
</tr>`;
    });

    let html = `<style>.dashboard-body{font-family:Inter,system-ui,sans-serif;color:#1f2937}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;padding:10px 20px;background:#fff;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;min-width:0}.kpi-card{min-width:0;overflow:hidden}.header-actions{display:flex;gap:8px;flex-wrap:wrap;flex-shrink:0}.table-container{overflow-y:auto;overflow-x:auto}.table-container::-webkit-scrollbar{width:8px;height:8px}.table-container::-webkit-scrollbar-track{background:transparent}.table-container::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:10px}.table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}</style>
<div class="dashboard-body">
    <div style="background:linear-gradient(135deg,#1e40af,#2563eb,#3b82f6);border-radius:12px 12px 0 0;padding:12px 20px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 16px rgba(37,99,235,0.25)">
        <div style="font-size:24px;line-height:1">&#x26A0;&#xFE0F;</div>
        <div style="flex:1">
            <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px">Team Leave Overlap Alerts</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:0">Detected Overlapping Leave Dates</div>
        </div>
        <div class="header-actions">
            <button id="refreshBtn" style="display:flex;align-items:center;gap:5px;padding:5px 14px;border:none;border-radius:6px;background:rgba(255,255,255,0.15);color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.1)">
                <i class="fa fa-refresh" style="font-size:11px"></i> Refresh
            </button>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fffbeb;border-radius:10px;border:1px solid #fde68a;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#fef3c7,#fffbeb);color:#f59e0b;font-size:15px;flex-shrink:0"><i class="fa fa-calendar"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Upcoming Conflicts</div>
                <div style="font-size:22px;font-weight:800;color:#d97706;line-height:1">${upcoming}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Future Overlaps</div>
            </div>
        </div>
        <div class="kpi-card" style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f0fdf4;border-radius:10px;border:1px solid #bbf7d0;transition:all 0.25s">
            <div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#dcfce7,#f0fdf4);color:#16a34a;font-size:15px;flex-shrink:0"><i class="fa fa-calendar-check-o"></i></div>
            <div>
                <div style="font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:1px">Today's Conflicts</div>
                <div style="font-size:22px;font-weight:800;color:#15803d;line-height:1">${todayCnt}</div>
                <div style="font-size:11px;color:#6b7280;margin-top:0">Active Overlaps</div>
            </div>
        </div>
    </div>

    <div style="background:#fff;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.04)">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 16px;background:#f8fafc;border-bottom:1px solid #e5e7eb">
            <div style="font-size:13px;font-weight:700;color:#374151;display:flex;align-items:center;gap:6px;margin-right:auto">
                <i class="fa fa-list-alt" style="color:#2563eb;font-size:12px"></i> Overlap Details
                <span style="font-size:11px;font-weight:500;color:#6b7280;background:#e5e7eb;padding:1px 8px;border-radius:10px;margin-left:4px">${rows.length}</span>
            </div>
            <select id="companyFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Companies</option></select>
            <select id="deptFilter" style="padding:4px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:11px;background:#fff;cursor:pointer"><option value="">All Departments</option></select>
            <button id="exportBtn" style="display:flex;align-items:center;gap:4px;padding:4px 10px;border:none;border-radius:5px;background:#16a34a;color:#fff;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s"><i class="fa fa-download" style="font-size:10px"></i> Export</button>
        </div>

        <div class="table-container" style="max-height:450px">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead>
                    <tr style="background:#f1f5f9;position:sticky;top:0;z-index:10">
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Date</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Department</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Company</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Employees</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:50px">Count</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Leave Type</th>
                        <th style="padding:10px 16px;text-align:center;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0;width:70px">Severity</th>
                        <th style="padding:10px 16px;text-align:left;font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #e2e8f0">Applications</th>
                    </tr>
                </thead>
                <tbody id="tableBody">${table_rows}</tbody>
            </table>
        </div>

        <div style="padding:6px 16px;background:#f8fafc;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#6b7280">
            <span>Showing ${rows.length} overlap day${rows.length!==1?'s':''} — ${critical} critical, ${todayCnt} active today</span>
            <span style="font-size:10px">Last refreshed: ${frappe.datetime.str_to_user(frappe.datetime.now_datetime())}</span>
        </div>
    </div>
</div>`;

    root_element.innerHTML = html;

    function fill(id,key){
        const s=$(root_element).find(id);
        [...new Set(rows.map(r=>r[key]).filter(Boolean))].sort().forEach(v=>s.append(`<option>${v}</option>`));
    }
    fill("#companyFilter","company");
    fill("#deptFilter","department");

    function apply(){
        const c=$("#companyFilter",root_element).val();
        const d=$("#deptFilter",root_element).val();
        $("tbody tr",root_element).each(function(){
            $(this).toggle((!c||$(this).data("company")==c)&&(!d||$(this).data("dept")==d));
        });
    }

    $("#companyFilter,#deptFilter",root_element).on("change",apply);
    $("#refreshBtn",root_element).on("click",function(e){e.stopPropagation();location.reload();});

    $("#exportBtn", root_element).on("click",function(){
        let company=$("#companyFilter",root_element).val()||"All Companies";
        let department=$("#deptFilter",root_element).val()||"All Departments";
        let today=frappe.datetime.get_today();
        let csv=[];
        csv.push('"TEAM LEAVE OVERLAP ALERTS REPORT"');
        csv.push("");
        csv.push('"Export Date","'+frappe.datetime.str_to_user(today)+'"');
        csv.push('"Company","'+company+'"');
        csv.push('"Department","'+department+'"');
        csv.push("");
        csv.push('"Critical Conflicts","'+critical+'","Upcoming Conflicts","'+upcoming+'","Today Conflicts","'+todayCnt+'"');
        csv.push("");
        csv.push("");
        csv.push(['"Date"','"Department"','"Company"','"Employee"','"Employee Count"','"Leave Type"','"Severity"','"Leave Application"'].join(","));
        rows.forEach(r=>{
            if(company!=="All Companies"&&r.company!==company)return;
            if(department!=="All Departments"&&r.department!==department)return;
            const employees=r.employee_names.split(/\s*,\s*/);
            const applications=r.applications;
            const leaveTypes=r.leave_types.split(/\s*,\s*/);
            applications.forEach((app,index)=>{
                csv.push(['"'+r.date+'"','"'+r.department+'"','"'+r.company+'"','"'+(employees[index]||"")+'"','"'+r.count+'"','"'+(leaveTypes[index]||r.leave_types)+'"','"'+r.severity+'"','"'+app+'"'].join(","));
            });
        });
        let blob=new Blob([csv.join("\n")],{type:"text/csv;charset=utf-8;"});
        let link=document.createElement("a");
        link.href=URL.createObjectURL(blob);
        link.download="Team_Leave_Overlap_Alerts_"+today+".csv";
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
