// Copyright (c) 2026, osama.ahmed@deliverydevs.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Warning Letter", {
	refresh(frm) {
        frm.page.remove_inner_button(__('Print'));
        frm.page.remove_inner_button(__('PDF'));
        $("button[data-original-title=Print]").hide();
        set_print_format_default(frm);
	},

    setup: function(frm) {
        frm.set_query("employee", function() {
            return {
                filters: {
                    status: "Active"
                }
            };
        });
        frm.set_query("hr_manager", function() {
            return {
                query: "frappe.core.doctype.user.user.user_query",
                filters: {
                    role: "HR Manager"
                }
            };
        });

        frm.set_query("warning_template", function() {
            return {
                filters: {
                    title: frm.doc.title
                }
            };
        });

    },

    title: function(frm) {
        set_print_format_default(frm);
        frm.set_value("warning_template", "");

        frm.set_query("warning_template", function() {
            return {
                filters: {
                    title: frm.doc.title
                }
            };
        });

    }

});

function set_print_format_default(frm) {

    if (!frm.doc.title) return;

    // remove existing button to prevent duplicates
    frm.page.remove_inner_button("Print");

    frm.add_custom_button(__('Print'), function () {

        const print_doc = () => {
            const print_format = frm.doc.title;

            const url = `/printview?doctype=${encodeURIComponent(frm.doc.doctype)}`
                + `&name=${encodeURIComponent(frm.doc.name)}`
                + `&format=${encodeURIComponent(print_format)}`
                + `&no_letterhead=0`;

            window.open(url, "_blank");
        };

        // If document is new or unsaved
        if (frm.is_dirty()) {
            frm.save().then(() => {
                print_doc();
            });
        } else {
            print_doc();
        }

    });

}