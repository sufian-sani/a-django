from users.permissions import AppModelPermissions


class NotePermission(AppModelPermissions):
    app_label = "notes"
    model_name = "note"
