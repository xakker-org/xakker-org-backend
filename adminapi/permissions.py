from rest_framework.permissions import BasePermission

ADMIN_TOKEN_SCOPE = "admin"


def _has_admin_scope(request):
    """A valid admin-panel JWT carries scope="admin". Client tokens don't,
    so they can never satisfy admin permission checks even if the user
    happens to be staff."""
    auth = getattr(request, "auth", None)
    if auth is None:
        return False
    try:
        return auth.get("scope") == ADMIN_TOKEN_SCOPE
    except AttributeError:
        return False


class IsStaffUser(BasePermission):
    """Default permission for the admin API: authenticated staff member
    holding an admin-scoped token."""

    message = "Bu əməliyyat üçün admin panelinə giriş tələb olunur."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_staff
            and _has_admin_scope(request)
        )


class IsSuperUser(IsStaffUser):
    """Superuser-only actions (granting/revoking staff, destructive user ops)."""

    message = "Bu əməliyyat üçün superuser hüququ tələb olunur."

    def has_permission(self, request, view):
        return bool(super().has_permission(request, view) and request.user.is_superuser)
