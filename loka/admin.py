from importlib import reload

from django.contrib import admin
from django.db.models import Avg,Sum

from .models import SettlementRow,Bank,RegionalOffice,Profile,LokAdalat
from django.contrib.admin.options import StackedInline,TabularInline
from totalsum.admin import TotalsumAdmin
from django.http import HttpResponse
import csv
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.admin import ModelAdmin

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

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"

class SettlementRowAdmin(TotalsumAdmin,ExportCsvMixin):
    def get_district(self, obj):
        return obj.branch.get_branch_district_display()

    list_display = ('loka','ro','branch','account_no','cust_name','totalclosure','outstanding','unapplied_int','pr_waived','int_waived','compromise_amt','token_money','rest_amount','loan_obj','irac','get_district')
    list_filter=('ro','branch__branch_district')
    search_fields = ['loka__lokadalatvenue','branch__branch_district']
    totalsum_list = ( 'totalclosure', 'compromise_amt','token_money','outstanding','pr_waived','int_waived','rest_amount','unapplied_int')
    actions = ["export_as_csv"]



    # def changelist_view(self, request):
    #     cl = super().get_changelist_instance(request)
    #     q = cl.get_queryset(request).aggregate(totalclosure_sum=Sum('totalclosure'))
    #     cl.totalclosure = q['totalclosure_sum']
    #     return cl
    #

    # def show_sum(self, obj):
    #
    #     result = SettlementRow.objects.filter(settlementrow=obj).aggregate(Sum("outstanding"))
    #     return result["ossum"]
    # #
    # def get_author(self, obj):
    #     return obj.ro.ro_name

    def get_queryset(self, request):
        qs=super(SettlementRowAdmin,self).get_queryset(request)
        if request.user.is_superuser:
            return qs

        # return qs.filter(branch=request.user,**request.GET.dict())
        return qs.filter(branch=request.user)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user','ro','branch_alpha','branch_name','branch_addr','branch_district')


    def get_queryset(self, request):
        qs = super(ProfileAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    search_fields = ('branch_addr', 'branch_name',)

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    list_select_related = ('profile',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.register(RegionalOffice, RegionalOfficeAdmin)
admin.site.register(Bank)

admin.site.register(LokAdalat,LokadalatAdmin)
admin.site.register(SettlementRow,SettlementRowAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile,ProfileAdmin)



