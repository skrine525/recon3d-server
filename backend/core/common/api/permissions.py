from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    """
    Разрешает доступ только суперпользователям.
    """
    message = "У вас нет прав"

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class IsStaff(BasePermission):
    """
    Разрешает доступ только персоналу (staff).
    """
    message = "У вас нет прав"

    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class CanChangePassword(BasePermission):
    """
    Позволяет суперпользователям менять пароль кому угодно,
    а персоналу — только обычным пользователям.
    """
    message = "У вас нет прав"

    def has_object_permission(self, request, view, obj):
        # Суперпользователь может менять пароль любому.
        if request.user.is_superuser:
            return True
        
        # Персонал (staff) может менять пароль только обычным пользователям 
        # (не другим сотрудникам и не суперпользователям).
        if request.user.is_staff and not obj.is_staff and not obj.is_superuser:
            return True
            
        return False

class CanChangeIsActive(BasePermission):
    """
    Позволяет суперпользователям менять is_active кому угодно,
    а персоналу — только обычным пользователям.
    """
    message = "У вас нет прав"

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if request.user.is_staff and not obj.is_staff and not obj.is_superuser:
            return True
            
        return False 