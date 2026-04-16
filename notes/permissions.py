from users.permissions import AppModelPermissions


class NotePermission(AppModelPermissions):
    app_label = "notes"
    model_name = "note"

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
