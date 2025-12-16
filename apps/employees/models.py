from django.db import models

from django.contrib.auth.models import User


class Permission(models.Model):
    """Custom MES permissions"""
    codename = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)


class Role(models.Model):
    """Role with associated permissions"""
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)


class Employee(models.Model):
    """Factory floor user"""
    class Shifts(models.IntegerChoices):
        FIRST = 1, "First"
        SECOND = 2, "Second"
        THIRD = 3, "Third"
        FOURTH = 4, "Fourth"
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    shift = models.IntegerField(choices=Shifts.choices, blank=True)
    roles = models.ManyToManyField(Role, blank=True)
    extra_permissions = models.ManyToManyField(Permission, blank=True)
    
    is_active = models.BooleanField(default=True)
    hired_at = models.DateField(null=True)
    
    def has_perm(self, codename):
        if self.extra_permissions.filter(codename=codename).exists():
            return True
        return self.roles.filter(permissions__codename=codename).exists()
