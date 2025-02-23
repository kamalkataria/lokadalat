from django.contrib import admin
from django.db.models import Sum
from django.http import HttpResponse
import csv
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from totalsum.admin import TotalsumAdmin

from django.utils.translation import gettext_lazy as _  # ✅ Import for translations
from .models import Branch, SettlementRow

from .models import Bank, RegionalOffice, Branch, Profile, LokAdalat, SettlementRow

# ==================== INLINE ADMIN CLASSES ====================

class BranchInline(admin.TabularInline):
    """Inline for adding branches under a Regional Office."""
    model = Branch
    extra = 1  # Allows adding new branches directly under RO

class ProfileInline(admin.TabularInline):
    """Inline for adding a user profile under a user."""
    model = Profile
    extra = 1

class SettlementInline(admin.TabularInline):
    """Inline for settlements under a Lok Adalat."""
    model = SettlementRow
    extra = 1

# ==================== MAIN ADMIN CLASSES ====================

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    """Admin for Banks (Only superusers can add banks)."""
    list_display = ('id', 'bank_name')
    search_fields = ('id', 'bank_name')

    def has_add_permission(self, request):
        return request.user.is_superuser  # Only superusers can add banks

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can edit banks

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(RegionalOffice)
class RegionalOfficeAdmin(admin.ModelAdmin):
    """Admin for Regional Offices with inline branches."""
    list_display = ('ro_name', 'bank_id')
    search_fields = ('ro_name',)
    inlines = [BranchInline]  # Add Branches under a Regional Office

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        try:
            user_profile = Profile.objects.get(user=request.user)
            if not user_profile.branch:
                return qs.none()
            return qs.filter(bank=user_profile.branch.ro.bank)
        except Profile.DoesNotExist:
            return qs.none()

from .models import Branch  # Import the Branch model

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_alpha', 'branch_name', 'regional_office', 'branch_district')
    search_fields = ('branch_name', 'branch_alpha')
    list_filter = ('regional_office', 'branch_district')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        if request.user.groups.filter(name="SuperBanker").exists():
            try:
                user_profile = Profile.objects.get(user=request.user)
                if not user_profile.branch:
                    return qs.none()
                return qs.filter(ro__bank=user_profile.branch.ro.bank)
            except Profile.DoesNotExist:
                return qs.none()

        return qs.filter(ro__bank=request.user.profile.branch.ro.bank)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin for user profiles (linked to branches)."""
    list_display = ('user', 'get_ro', 'get_branch_alpha', 'get_branch_name', 'get_branch_addr', 'get_branch_district')
    search_fields = ('branch__branch_addr', 'branch__branch_name')

    def get_ro(self, obj):
        return obj.branch.regional_office if obj.branch else "No RO Assigned"
    get_ro.short_description = "Regional Office"

    def get_branch_alpha(self, obj):
        return obj.branch.branch_alpha if obj.branch else "N/A"
    get_branch_alpha.short_description = "Branch Alpha"

    def get_branch_name(self, obj):
        return obj.branch.branch_name if obj.branch else "N/A"
    get_branch_name.short_description = "Branch Name"

    def get_branch_addr(self, obj):
        return obj.branch.branch_addr if obj.branch else "N/A"
    get_branch_addr.short_description = "Branch Address"

    def get_branch_district(self, obj):
        return obj.branch.get_branch_district_display() if obj.branch else "N/A"
    get_branch_district.short_description = "Branch District"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name="SuperBanker").exists():
            try:
                user_profile = Profile.objects.get(user=request.user)
                if not user_profile.branch:
                    return qs.none()
                return qs.filter(branch__regional_office__bank_id=user_profile.branch.regional_office.bank_id)
            except Profile.DoesNotExist:
                return qs.none()

        return qs.filter(user=request.user)
        # elif request.user.groups.filter(name="SuperBanker").exists():
        #     return qs.filter(branch__ro__bank_id=request.user.bank_set.first())
        # return qs.filter(user=request.user)

@admin.register(LokAdalat)
class LokadalatAdmin(admin.ModelAdmin):
    """Admin for Lok Adalats with settlement inlines."""
    inlines = [SettlementInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

# ==================== EXPORT CSV MIXIN ====================

class ExportCsvMixin:
    """Mixin to export selected objects as CSV."""
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}.csv'
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"

# ==================== Filters ====================


class RegionalOfficeFilter(admin.SimpleListFilter):
    title = _('Regional Office')
    parameter_name = 'ro'

    def lookups(self, request, model_admin):
        """Get list of available Regional Offices."""
        return [(ro.id, ro.ro_name) for ro in RegionalOffice.objects.all()]

    def queryset(self, request, queryset):
        """Filter settlement rows by selected Regional Office."""
        if self.value():
            return queryset.filter(ro__id=self.value())
        return queryset

class BranchDistrictFilter(admin.SimpleListFilter):
    title = _('Branch District')
    parameter_name = 'branch_district'

    def lookups(self, request, model_admin):
        """Fetch available district choices dynamically."""
        field = Branch._meta.get_field('branch_district')  # ✅ Get the field object
        return field.choices  # ✅ Return its choices

    def queryset(self, request, queryset):
        """Filters queryset based on selection."""
        if self.value():
            return queryset.filter(branch__branch_district=self.value())
        return queryset

# ==================== SETTLEMENT ROW ADMIN ====================

@admin.register(SettlementRow)
class SettlementRowAdmin(TotalsumAdmin, ExportCsvMixin):

    # def get_district(self, obj):
    #     return obj.branch.branch_district if obj.branch else "N/A"
    def get_district(self, obj):
        return obj.branch.branch.get_branch_district_display() if obj.branch.branch else "N/A"

    """Admin for settlement rows with filtering and CSV export."""
    list_display = ('loka', 'ro', 'branch', 'account_no', 'cust_name', 'totalclosure',
                    'outstanding', 'unapplied_int', 'pr_waived', 'int_waived',
                    'compromise_amt', 'token_money', 'rest_amount', 'loan_obj', 'irac', 'get_district')

    list_filter = (RegionalOfficeFilter, BranchDistrictFilter)
    search_fields = ['loka__lokadalatvenue', 'branch__branch_name']
    totalsum_list = ('totalclosure', 'compromise_amt', 'token_money', 'outstanding',
                     'pr_waived', 'int_waived', 'rest_amount', 'unapplied_int')
    actions = ["export_as_csv"]


    get_district.short_description = "Branch District"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            user_profile = Profile.objects.get(user=request.user)
            if not user_profile.branch:
                return qs.none()
            return qs.filter(branch__regional_office__bank_id=user_profile.branch.regional_office.bank_id)
        except Profile.DoesNotExist:
            return qs.none()

# ==================== CUSTOM USER ADMIN ====================

class CustomUserAdmin(UserAdmin):
    """Custom user admin with inline profile editing."""
    inlines = (ProfileInline,)
    list_select_related = ('profile',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        if request.user.groups.filter(name="SuperBanker").exists():
            try:
                user_profile = Profile.objects.get(user=request.user)
                if not user_profile.branch:
                    return qs.none()
                return qs.filter(profile__branch__ro__bank=user_profile.branch.ro.bank, is_superuser=False)
            except Profile.DoesNotExist:
                return qs.none()

        return qs.filter(username=request.user)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser:
            return False  # SuperBankers cannot delete superusers
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_superuser:
            return False  # SuperBankers cannot edit superusers
        return super().has_change_permission(request, obj)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

        # Unregister default User model and register CustomUserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
