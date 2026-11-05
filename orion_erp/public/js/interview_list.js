frappe.listview_settings['Interview'] = {
    refresh: function (listview) {
        show_interviewers(listview);
    }
};

function show_interviewers(listview) {
    const names = (listview.data || []).map(d => d.name);
    if (!names.length) return;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Interview Detail',   // child doctype of interview_details
            parent: 'Interview',
            fields: ['parent', 'interviewer'],
            filters: { parent: ['in', names] },
            limit_page_length: 0
        },
        callback: function (r) {
            // Group interviewers by Interview ID
            const map = {};
            (r.message || []).forEach(row => {
                if (row.interviewer) {
                    (map[row.parent] = map[row.parent] || []).push(row.interviewer);
                }
            });

            const col_style = 'flex: 1.5; min-width: 160px;';

            // Header cell
            listview.$result.find('.list-row-head .interviewers-col').remove();
            listview.$result.find('.list-row-head .list-subject').after(
                `<div class="list-row-col ellipsis hidden-xs interviewers-col" style="${col_style}">
                    <span>Interviewers</span>
                </div>`
            );

            // Row cells
            listview.$result.find('.list-row-container').each(function () {
                const $row = $(this);
                const name = $row.find('.list-row-checkbox').data('name');
                const text = (map[name] || []).join(', ');

                $row.find('.interviewers-col').remove();
                $row.find('.list-subject').after(
                    `<div class="list-row-col ellipsis hidden-xs interviewers-col"
                          style="${col_style}"
                          title="${frappe.utils.escape_html(text)}">
                        <span>${frappe.utils.escape_html(text)}</span>
                    </div>`
                );
            });
        }
    });
}