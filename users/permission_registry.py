PERMISSION_REGISTRY = {
    "task": {
        "app_label": "todo",
        "model_name": "task",
        "fields": {
            "add": "can_add_task",
            "change": "can_change_task",
            "delete": "can_delete_task",
            "view": "can_view_task",
        },
    },
    "project": {
        "app_label": "project",
        "model_name": "project",
        "fields": {
            "add": "can_add_project",
            "change": "can_change_project",
            "delete": "can_delete_project",
            "view": "can_view_project",
        },
    },
    "note": {
        "app_label": "notes",
        "model_name": "note",
        "fields": {
            "add": "can_add_note",
            "change": "can_change_note",
            "delete": "can_delete_note",
            "view": "can_view_note",
        },
    },
}