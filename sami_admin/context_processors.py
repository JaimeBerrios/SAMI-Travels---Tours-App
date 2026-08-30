def administrative_permissions(request):
    user = request.user
    can_manage_users = False
    if user.is_authenticated and user.is_active and user.is_staff:
        can_manage_users = user.groups.filter(name="Administrador").exists()
    return {"can_manage_users": can_manage_users}
