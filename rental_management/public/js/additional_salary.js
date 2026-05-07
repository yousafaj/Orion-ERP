
frappe.ui.form.on('Additional Salary', {
    onload(frm) {
        frm.set_df_property('naming_series', 'options', [
            'HR-ADS-.YY.-.MM.-',
            'HR-ADA-.YY.-.MM.-'
        ]);
    }
});


