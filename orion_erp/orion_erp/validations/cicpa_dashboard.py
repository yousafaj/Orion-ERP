# Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.utils import today, add_days, date_diff
from frappe import _

@frappe.whitelist()
def get_expiring_cicpas():
    """
    Fetch all Driver and Vehicle CICPA passes that are expiring in the next 30 days
    or are already expired, sorted by closest expiry date first.
    """
    today_str = today()
    thirty_days = add_days(today_str, 30)

    # Fetch submitted and Active/Expired CICPAs
    cicpas = frappe.get_all(
        "CICPA",
        filters={
            "docstatus": 1,
            "cicpa_status": ["in", ["Active", "Expired"]],
            "expiry_date": ["<=", thirty_days]
        },
        fields=["name", "cicpa_no", "cicpa_type", "expiry_date", "loa", "driver", "vehicle", "cicpa_status"],
        order_by="expiry_date ASC"
    )

    drivers = []
    vehicles = []

    for c in cicpas:
        days_left = date_diff(c.expiry_date, today_str)

        if c.cicpa_type == "Driver" and c.driver:
            driver_name = frappe.db.get_value("Driver", c.driver, "driver_name")
            drivers.append({
                "name": c.name,
                "driver": c.driver,
                "driver_name": driver_name or c.driver,
                "cicpa_no": c.cicpa_no,
                "expiry_date": str(c.expiry_date),
                "loa": c.loa,
                "days_left": days_left,
                "status": c.cicpa_status
            })

        elif c.cicpa_type == "Vehicle" and c.vehicle:
            license_plate = frappe.db.get_value("Vehicle", c.vehicle, "license_plate")
            vehicles.append({
                "name": c.name,
                "vehicle": c.vehicle,
                "license_plate": license_plate or c.vehicle,
                "cicpa_no": c.cicpa_no,
                "expiry_date": str(c.expiry_date),
                "loa": c.loa,
                "days_left": days_left,
                "status": c.cicpa_status
            })

    return {
        "drivers": drivers,
        "vehicles": vehicles
    }

@frappe.whitelist()
def get_expiring_cicpas_count():
    """
    Returns count of CICPA passes expiring in the next 30 days.
    Used by 'CICPAs Expiring (30 Days)' Number Card.
    """
    today_str = today()
    thirty_days = add_days(today_str, 30)
    count = frappe.db.count("CICPA", filters={
        "docstatus": 1,
        "cicpa_status": "Active",
        "expiry_date": ["between", [today_str, thirty_days]]
    })
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "CICPA"],
        "route_options": {
            "docstatus": 1,
            "cicpa_status": "Active",
            "expiry_date": ["between", [today_str, thirty_days]]
        }
    }

@frappe.whitelist()
def get_expired_cicpas_count():
    """
    Returns count of Expired CICPA passes.
    Used by 'Expired CICPAs' Number Card.
    """
    count = frappe.db.count("CICPA", filters={
        "docstatus": 1,
        "cicpa_status": "Expired"
    })
    return {
        "value": count,
        "fieldtype": "Int",
        "route": ["List", "CICPA"],
        "route_options": {
            "docstatus": 1,
            "cicpa_status": "Expired"
        }
    }

def setup_cicpa_workspace_widgets():
    """
    Creates the Custom HTML Block and Number Cards, then dynamically integrates them
    into the 'Orion Fleet' Workspace database record if they aren't already.
    Executed safely during bench migrations.
    """
    try:
        # 1. Create Expiring CICPAs Number Card
        expiring_card_name = "CICPAs Expiring (30 Days)"
        if not frappe.db.exists("Number Card", expiring_card_name):
            frappe.get_doc({
                "doctype": "Number Card",
                "name": expiring_card_name,
                "label": _("CICPAs Expiring (30 Days)"),
                "is_standard": 1,
                "is_public": 1,
                "module": "Orion ERP",
                "type": "Custom",
                "method": "orion_erp.orion_erp.validations.cicpa_dashboard.get_expiring_cicpas_count"
            }).insert(ignore_permissions=True)

        # 2. Create Expired CICPAs Number Card
        expired_card_name = "Expired CICPAs"
        if not frappe.db.exists("Number Card", expired_card_name):
            frappe.get_doc({
                "doctype": "Number Card",
                "name": expired_card_name,
                "label": _("Expired CICPAs"),
                "is_standard": 1,
                "is_public": 1,
                "module": "Orion ERP",
                "type": "Custom",
                "method": "orion_erp.orion_erp.validations.cicpa_dashboard.get_expired_cicpas_count"
            }).insert(ignore_permissions=True)

        # 3. Create Custom HTML Block for dashboard widget
        html_block_name = "CICPA Expiry Dashboard Widget"

        # HTML Content (including styles and scripts)
        html_content = """
<div class="cicpa-expiry-widget">
  <div class="widget-header">
    <div class="widget-title">
      <i class="fa fa-id-card"></i> Upcoming CICPA Expiries (Next 30 Days)
    </div>
    <div class="widget-tabs">
      <button class="tab-btn active" onclick="switchCICPATab('drivers')">
        <i class="fa fa-user"></i> Driver Passes (<span id="driver-count">0</span>)
      </button>
      <button class="tab-btn" onclick="switchCICPATab('vehicles')">
        <i class="fa fa-car"></i> Vehicle Passes (<span id="vehicle-count">0</span>)
      </button>
    </div>
  </div>

  <div class="widget-body">
    <div id="drivers-tab" class="tab-content active">
      <div class="table-responsive">
        <table class="cicpa-table">
          <thead>
            <tr>
              <th>Driver</th>
              <th>CICPA No</th>
              <th>Expiry Date</th>
              <th>Days Left</th>
              <th>LOA</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="driver-expiries-body">
            <tr>
              <td colspan="6" class="text-center loading-text">Loading expiring passes...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div id="vehicles-tab" class="tab-content">
      <div class="table-responsive">
        <table class="cicpa-table">
          <thead>
            <tr>
              <th>Vehicle</th>
              <th>CICPA No</th>
              <th>Expiry Date</th>
              <th>Days Left</th>
              <th>LOA</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="vehicle-expiries-body">
            <tr>
              <td colspan="6" class="text-center loading-text">Loading expiring passes...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<style>
.cicpa-expiry-widget {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  padding: 20px;
  margin-top: 20px;
  font-family: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.cicpa-expiry-widget:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
}
.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid var(--bg-color, #f7fafc);
  padding-bottom: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.widget-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color, #1a202c);
  display: flex;
  align-items: center;
  gap: 8px;
}
.widget-title i {
  color: var(--primary-color, #2980b9);
}
.widget-tabs {
  display: flex;
  gap: 8px;
  background: var(--bg-color, #f7fafc);
  padding: 4px;
  border-radius: 8px;
}
.tab-btn {
  border: none;
  background: transparent;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted, #718096);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}
.tab-btn:hover {
  color: var(--text-color, #1a202c);
}
.tab-btn.active {
  background: var(--card-bg, #ffffff);
  color: var(--primary-color, #2980b9);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.tab-content {
  display: none;
}
.tab-content.active {
  display: block;
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.table-responsive {
  width: 100%;
  overflow-x: auto;
}
.cicpa-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.cicpa-table th {
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #718096);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}
.cicpa-table td {
  padding: 14px 16px;
  font-size: 13.5px;
  color: var(--text-color, #2d3748);
  border-bottom: 1px solid var(--bg-color, #f7fafc);
  vertical-align: middle;
}
.cicpa-table tbody tr:hover td {
  background: var(--bg-color, #f8fafc);
}
.cicpa-table tbody tr:last-child td {
  border-bottom: none;
}
.badge-expiry {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}
.badge-expiry.expired {
  background: #fff5f5;
  color: #e53e3e;
  border: 1px solid #fed7d7;
}
.badge-expiry.critical {
  background: #fffaf0;
  color: #dd6b20;
  border: 1px solid #feebc8;
}
.badge-expiry.warning {
  background: #fffdf5;
  color: #d69e2e;
  border: 1px solid #fef3c7;
}
.badge-expiry.safe {
  background: #f0fff4;
  color: #38a169;
  border: 1px solid #c6f6d5;
}
.btn-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--card-bg, #ffffff);
  color: var(--text-color, #2d3748);
  text-decoration: none !important;
  transition: all 0.2s ease;
}
.btn-action:hover {
  background: var(--bg-color, #f7fafc);
  border-color: var(--text-muted, #718096);
  color: var(--primary-color, #2980b9);
}
.loading-text {
  color: var(--text-muted, #718096);
  padding: 30px !important;
  font-style: italic;
}
.empty-text {
  color: var(--text-muted, #718096);
  padding: 30px !important;
  font-weight: 500;
  text-align: center;
}
</style>

<script>
window.switchCICPATab = function(tabName) {
  const container = document.querySelector('.cicpa-expiry-widget');
  if (!container) return;

  container.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  container.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  if (tabName === 'drivers') {
    container.querySelector('button[onclick*="drivers"]').classList.add('active');
    document.getElementById('drivers-tab').classList.add('active');
  } else {
    container.querySelector('button[onclick*="vehicles"]').classList.add('active');
    document.getElementById('vehicles-tab').classList.add('active');
  }
};

window.loadCICPAExpiries = function() {
  frappe.call({
    method: 'orion_erp.orion_erp.validations.cicpa_dashboard.get_expiring_cicpas',
    callback: function(r) {
      if (r.message) {
        const data = r.message;

        // Update tabs counts
        document.getElementById('driver-count').innerText = data.drivers.length;
        document.getElementById('vehicle-count').innerText = data.vehicles.length;

        // Render Drivers
        const driverBody = document.getElementById('driver-expiries-body');
        if (data.drivers.length === 0) {
          driverBody.innerHTML = '<tr><td colspan="6" class="empty-text">No Driver CICPA passes expiring in the next 30 days</td></tr>';
        } else {
          driverBody.innerHTML = data.drivers.map(d => {
            let badgeClass = 'safe';
            if (d.days_left < 0) badgeClass = 'expired';
            else if (d.days_left <= 10) badgeClass = 'critical';
            else if (d.days_left <= 30) badgeClass = 'warning';

            const daysText = d.days_left < 0 ? 'Expired' : `${d.days_left} Days Left`;

            return `
              <tr>
                <td><strong><a href="/app/driver/${d.driver}" style="color: var(--primary-color, #2980b9); font-weight: 600;">${d.driver_name || d.driver}</a></strong></td>
                <td><code style="font-size: 12px; color: var(--text-color, #2d3748);">${d.cicpa_no || 'N/A'}</code></td>
                <td>${frappe.datetime.str_to_user(d.expiry_date)}</td>
                <td><span class="badge-expiry ${badgeClass}">${daysText}</span></td>
                <td><a href="/app/loa/${d.loa}" style="color: var(--text-muted, #718096); font-weight: 500;">${d.loa}</a></td>
                <td><a class="btn-action" href="/app/cicpa/${d.name}"><i class="fa fa-eye"></i> View</a></td>
              </tr>
            `;
          }).join('');
        }

        // Render Vehicles
        const vehicleBody = document.getElementById('vehicle-expiries-body');
        if (data.vehicles.length === 0) {
          vehicleBody.innerHTML = '<tr><td colspan="6" class="empty-text">No Vehicle CICPA passes expiring in the next 30 days</td></tr>';
        } else {
          vehicleBody.innerHTML = data.vehicles.map(v => {
            let badgeClass = 'safe';
            if (v.days_left < 0) badgeClass = 'expired';
            else if (v.days_left <= 10) badgeClass = 'critical';
            else if (v.days_left <= 30) badgeClass = 'warning';

            const daysText = v.days_left < 0 ? 'Expired' : `${v.days_left} Days Left`;

            return `
              <tr>
                <td><strong><a href="/app/vehicle/${v.vehicle}" style="color: var(--primary-color, #2980b9); font-weight: 600;">${v.license_plate}</a></strong></td>
                <td><code style="font-size: 12px; color: var(--text-color, #2d3748);">${v.cicpa_no || 'N/A'}</code></td>
                <td>${frappe.datetime.str_to_user(v.expiry_date)}</td>
                <td><span class="badge-expiry ${badgeClass}">${daysText}</span></td>
                <td><a href="/app/loa/${v.loa}" style="color: var(--text-muted, #718096); font-weight: 500;">${v.loa}</a></td>
                <td><a class="btn-action" href="/app/cicpa/${v.name}"><i class="fa fa-eye"></i> View</a></td>
              </tr>
            `;
          }).join('');
        }
      }
    }
  });
};

// Initialise
setTimeout(window.loadCICPAExpiries, 150);
</script>
"""

        # Create or update Custom HTML Block
        if not frappe.db.exists("Custom HTML Block", html_block_name):
            frappe.get_doc({
                "doctype": "Custom HTML Block",
                "name": html_block_name,
                "html": html_content
            }).insert(ignore_permissions=True)
        else:
            block = frappe.get_doc("Custom HTML Block", html_block_name)
            block.html = html_content
            block.save(ignore_permissions=True)

        # 4. Safely integrate widgets into the Orion Fleet Workspace
        if frappe.db.exists("Workspace", "Orion Fleet"):
            workspace = frappe.get_doc("Workspace", "Orion Fleet")

            # Check if the block widget is already present in workspace content
            content_list = json.loads(workspace.content or "[]")
            has_widget = any(item.get("type") == "custom_block" and item.get("data", {}).get("custom_block_name") == html_block_name for item in content_list)

            if not has_widget:
                # Add dynamic content blocks
                content_list.append({
                    "id": "cicpa-expiry-spacer",
                    "type": "spacer",
                    "data": {"col": 12}
                })
                content_list.append({
                    "id": "cicpa-expiry-header",
                    "type": "header",
                    "data": {"text": "<span class=\"h4\">CICPA Pass Expiries</span>", "col": 12}
                })

                # Insert the two Number Cards side-by-side (each takes col size 6)
                content_list.append({
                    "id": "cicpa-expiring-card-block",
                    "type": "number_card",
                    "data": {
                        "number_card_name": expiring_card_name,
                        "col": 6
                    }
                })
                content_list.append({
                    "id": "cicpa-expired-card-block",
                    "type": "number_card",
                    "data": {
                        "number_card_name": expired_card_name,
                        "col": 6
                    }
                })

                # Add the tabbed HTML Widget (takes full col size 12)
                content_list.append({
                    "id": "cicpa-expiry-widget-block",
                    "type": "custom_block",
                    "data": {
                        "custom_block_name": html_block_name,
                        "col": 12
                    }
                })

                workspace.content = json.dumps(content_list)

                # Ensure child table entries are also inserted safely
                existing_cards = {c.number_card_name for c in workspace.number_cards}
                if expiring_card_name not in existing_cards:
                    workspace.append("number_cards", {
                        "number_card_name": expiring_card_name,
                        "label": expiring_card_name
                    })
                if expired_card_name not in existing_cards:
                    workspace.append("number_cards", {
                        "number_card_name": expired_card_name,
                        "label": expired_card_name
                    })

                # Append to workspace.custom_blocks child table
                existing_blocks = {b.custom_block_name for b in workspace.custom_blocks}
                if html_block_name not in existing_blocks:
                    workspace.append("custom_blocks", {
                        "custom_block_name": html_block_name,
                        "label": html_block_name
                    })

                workspace.save(ignore_permissions=True)
                frappe.db.commit()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "setup_cicpa_workspace_widgets failed")
