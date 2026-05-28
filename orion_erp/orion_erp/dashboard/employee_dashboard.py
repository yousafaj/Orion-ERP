from frappe import _

def get_data(data):

    data.setdefault("transactions", [])

    data["transactions"].append(
        {
            "label": _("Documents"),
            "items": ["Asset Handover"]
        }
    )

    return data