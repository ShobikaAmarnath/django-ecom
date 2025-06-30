from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'date_joined', 'last_login', 'is_admin', 'is_staff', 'is_active', 'is_superadmin')
    list_display_links = ('email', 'username', 'first_name', 'last_name')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined',) #descending order by - (minus) sign
    
    # only for custom user model
    filter_horizontal = ()
    list_filter = ()
    
    fieldsets = ()
    
    add_fieldsets = ()
    
    ordering = ('-date_joined',)


admin.site.register(Account, AccountAdmin)