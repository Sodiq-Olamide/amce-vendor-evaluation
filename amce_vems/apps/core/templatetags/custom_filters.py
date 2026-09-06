from django import template

register = template.Library()

@register.filter(name='dict_get')
def dict_get(h, key):
    if isinstance(h, dict):
        return h.get(key)
    return None

@register.filter(name='has_user_perm')
def has_user_perm(user, perm_codename):
    """
    Checks if a user has a specific permission, either directly assigned
    to the user or inherited through groups or superuser status.
    """
    if not user:
        return False
    if user.is_superuser:
        return True
    return user.user_permissions.filter(codename=perm_codename).exists() or user.has_perm(f"analytics.{perm_codename}")

@register.filter(name='has_direct_user_perm')
def has_direct_user_perm(user, perm_codename):
    """
    Checks if a user has the permission specifically assigned directly to their account.
    """
    if not user:
        return False
    return user.user_permissions.filter(codename=perm_codename).exists()

@register.filter(name='has_group_perm')
def has_group_perm(group, perm_codename):
    """
    Checks if a group has a specific permission assigned.
    """
    if not group:
        return False
    return group.permissions.filter(codename=perm_codename).exists()
