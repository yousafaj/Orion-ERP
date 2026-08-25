frappe.ready(function () {
	var wf = frappe.web_form;
	if (!wf) return;

	var required = {{ recaptcha_required }};
	var site_key = "{{ recaptcha_site_key }}";
	if (!required || !site_key) return;

	var token = null;

	function mount_widget() {
		var container = document.createElement("div");
		container.id = "recaptcha-widget";
		container.style.margin = "12px 0";

		var submit_btn = document.querySelector(".web-form-footer .submit-btn, .submit-btn");
		if (submit_btn && submit_btn.parentNode) {
			submit_btn.parentNode.insertBefore(container, submit_btn);
		} else {
			var wrapper = document.querySelector(".web-form-wrapper") || document.body;
			wrapper.appendChild(container);
		}
	}

	window.orion_recaptcha_init = function () {
		if (!window.grecaptcha || !window.grecaptcha.render) return;
		window.grecaptcha.render("recaptcha-widget", {
			sitekey: site_key,
			callback: function (t) {
				token = t;
			},
			"expired-callback": function () {
				token = null;
			},
			"error-callback": function () {
				token = null;
			},
		});
	};

	mount_widget();

	var script = document.createElement("script");
	script.src = "https://www.google.com/recaptcha/api.js?onload=orion_recaptcha_init&render=explicit";
	script.async = true;
	script.defer = true;
	document.head.appendChild(script);

	var original_save = wf.save.bind(wf);
	wf.save = function () {
		if (!token) {
			frappe.msgprint(__("Please complete the verification check before submitting."));
			return false;
		}
		wf.doc.recaptcha_token = token;
		return original_save();
	};
});
