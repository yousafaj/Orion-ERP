function handle_eligibility_warnings_badge(frm) {
    $(".eligibility-warning-flag").remove();

    if (frm.doc.custom_eligibility_warnings) {
        let badge = `
        <span
            class="eligibility-warning-flag indicator-pill orange"
            style="
                margin-left:8px;
                white-space:nowrap;
                display:inline-flex;
                align-items:center;
                cursor: pointer;
            "
            title="${__(frm.doc.custom_eligibility_warnings)}"
        >
            ${__("Eligibility Warning")}
        </span>
    `;
        function tryInsertBadge() {
            if ($(".eligibility-warning-flag").length) return;
            let indicator = $(frm.page.wrapper)
                .find(".indicator-pill")
                .not(".medical-cert-flag")
                .not(".eligibility-warning-flag")
                .first();
            if (indicator.length) {
                indicator.after(badge);
                $(".eligibility-warning-flag").on("click", function() {
                    frappe.msgprint({
                        title: __("Eligibility Warnings"),
                        indicator: "orange",
                        message: frm.doc.custom_eligibility_warnings
                    });
                });
            }
        }
        tryInsertBadge();
    }
}


function handle_medical_certificate_flag(frm) {

    $(".medical-cert-flag").remove();

    if (!frm.doc.leave_type) return;

    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Leave Type",
            filters: {
                name: frm.doc.leave_type
            },
            fieldname: [
                "custom_medical_certificate_required",
                "custom_medical_certificate_required_by"
            ]
        },
        callback: function (r) {

            if (!r.message) return;

            update_medical_certificate_badge(
                frm,
                r.message.custom_medical_certificate_required,
                r.message.custom_medical_certificate_required_by
            );
        }
    });
}


function update_medical_certificate_badge(frm, required, hrs) {

    $(".medical-cert-flag").remove();

    if (
        !required ||
        frm.doc.custom_medical_certificate
    ) {
        return;
    }

    let label = __("Med. Cert Pending");

    let badge = `
    <span
        class="medical-cert-flag indicator-pill orange"
        style="
            margin-left:8px;
            white-space:nowrap;
            display:inline-flex;
            align-items:center;
        "
    >
        ${label}
    </span>
`;

    function tryInsertBadge() {

        if ($(".medical-cert-flag").length) return;

        let indicator = $(frm.page.wrapper)
            .find(".indicator-pill")
            .not(".medical-cert-flag")
            .first();

        if (indicator.length) {
            indicator.after(badge);
        }
    }

    tryInsertBadge();
}


function get_indicator_color(status) {

    if (
        status === "Approved" ||
        status === "Fully Approved"
    ) {

        return "green";
    }

    if (
        status === "Rejected"
    ) {

        return "red";
    }

    if (
        status === "Cancelled"
    ) {

        return "red";
    }

    if (
        status === "Open" ||
        status.startsWith("Pending Approval") ||
        status === "Submit Pending"
    ) {

        return "orange";
    }

    return "blue";
}

function apply_custom_status_indicator(frm) {

    let status =
        frm.doc.custom_approval_status || "Open";

    frm.page.set_indicator(
        status,
        get_indicator_color(status)
    );

    let field = frm.get_field("custom_approval_status");
    if (field && field.$wrapper) {
        field.$wrapper.find(".control-value, .like-disabled-input")
            .removeClass("green red orange blue")
            .addClass("indicator-pill " + get_indicator_color(status));
    }
}

function set_leave_balance_after(frm) {
    let balance = flt(frm.doc.leave_balance);
    let days = flt(frm.doc.total_leave_days);
    if (balance && days) {
        frm.set_value("custom_leave_balance_after", balance - days);
    } else if (balance) {
        frm.set_value("custom_leave_balance_after", balance);
    } else {
        frm.set_value("custom_leave_balance_after", 0);
    }
}
