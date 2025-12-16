from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Permission, Role, Employee

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['codename', 'description']

class RoleSerializer(serializers.ModelSerializer):
    # Shows codenames like ["can_print", "can_ship"] when reading
    permissions = serializers.SlugRelatedField(
        many=True, 
        slug_field='codename', 
        queryset=Permission.objects.all()
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']

class EmployeeSerializer(serializers.ModelSerializer):
    # Flatten fields from the linked User model
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    # Show the human-readable shift name ("First") instead of (1)
    shift_display = serializers.CharField(source='get_shift_display', read_only=True)
    
    # Calculated field to show the "Final" set of permissions this person has
    all_permissions = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 
            'employee_id', 
            'username', 'email', 'first_name', 'last_name', 
            'shift', 'shift_display', 
            'is_active', 
            'roles', 
            'extra_permissions',
            'all_permissions',
            'hired_at'
        ]

    def get_all_permissions(self, obj):
        """
        Aggregates permissions from both Roles and Extra Permissions.
        Useful for the frontend to decide which buttons to show/hide.
        """
        # Get permissions from roles
        role_perms = Permission.objects.filter(role__in=obj.roles.all())
        # Combine with extra permissions
        total_perms = (role_perms | obj.extra_permissions.all()).distinct()
        return [p.codename for p in total_perms]
    
class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    # Fields required for the User account
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Employee
        fields = [
            'username', 'password', 'email', 
            'employee_id', 'shift', 'roles', 'extra_permissions', 'hired_at'
        ]

    def create(self, validated_data):
        # 1. Extract User data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.get('email', ''),
        }
        password = validated_data.pop('password')
        
        # 2. Create the Django User
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()
        
        # 3. Handle ManyToMany fields separately (roles, extra_permissions)
        roles = validated_data.pop('roles', [])
        extra_perms = validated_data.pop('extra_permissions', [])
        
        # 4. Create the Employee
        employee = Employee.objects.create(user=user, **validated_data)
        employee.roles.set(roles)
        employee.extra_permissions.set(extra_perms)
        
        return employee