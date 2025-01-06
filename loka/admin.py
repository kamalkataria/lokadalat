from imp import reload

from django.contrib import admin

from .models import SettlementRow,Bank,RegionalOffice,Profile,LokAdalat
from django.contrib.admin.options import StackedInline,TabularInline


class ProfileInline(admin.TabularInline):
    model = Profile

class RegionalOfficeInline(admin.TabularInline):
    model = RegionalOffice

class RegionalOfficeAdmin(admin.ModelAdmin):
    inlines = [
        ProfileInline,
    ]
    def get_queryset(self, request):
        qs=super(RegionalOfficeAdmin,self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(bank_id__bank_id__username=request.user)

class BankAdmin(admin.TabularInline):
    inlines=[
        RegionalOfficeInline,
    ]
    search_fields = ('bank_id', 'bank_name',)

class SettlementInline(admin.TabularInline):
    model = SettlementRow
    
class LokadalatAdmin(admin.ModelAdmin):
    inlines = [SettlementInline,]
    def get_queryset(self, request):
        qs=super(LokadalatAdmin,self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(username=request.user)


class SettlementRowAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs=super(SettlementRowAdmin,self).get_queryset(request)
        if request.user.is_superuser:
            return qs


        return qs.filter(branch=request.user)

class ProfileAdmin(admin.TabularInline):

    def get_queryset(self, request):
        qs = super(ProfileAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    search_fields = ('bank', 'bank_name',)


admin.site.register(RegionalOffice, RegionalOfficeAdmin)
admin.site.register(Bank)
admin.site.register(Profile)
admin.site.register(LokAdalat,LokadalatAdmin)
admin.site.register(SettlementRow,SettlementRowAdmin)



