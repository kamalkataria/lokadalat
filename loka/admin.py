from django.contrib import admin
from django.db.models import Sum
from django.http import HttpResponse
import csv
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from totalsum.admin import TotalsumAdmin

from django.utils.translation import gettext_lazy as _  # ✅ Import for translations
from .models import Branch, SettlementRow

from .models import Bank, RegionalOffice, Branch, Profile, LokAdalat, SettlementRow,SuperBankerAssignment

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

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            try:
                if hasattr(request.user, 'superbanker_profile'):
                    bank = request.user.superbanker_profile.bank.id
                    return qs.filter(id=bank)
            except AttributeError:
                return qs.none()
            return qs  # God-Level SuperUser sees all



class RegionalOfficeAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict bank selection for SuperBankers and block access for normal users."""
        if db_field.name == "bank_id":
            if request.user.is_superuser:
                if hasattr(request.user, 'superbanker_profile'):
                    kwargs["queryset"] = Bank.objects.filter(id=request.user.superbanker_profile.bank_id)

                else:
                    kwargs["queryset"] = Bank.objects.all()  # SuperUser sees all banks
           # SuperBanker sees only their bank
            else:
                kwargs["queryset"] = Bank.objects.none()
        else:
            print('noname')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



    def has_add_permission(self, request):
        """Only SuperUsers and SuperBankers can add ROs."""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'superbanker_profile'):
            return True  # SuperBankers can add ROs (but only for their bank)
        return False  # General users cannot add ROs

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            if hasattr(request.user, 'superbanker_profile'):
                bank = request.user.superbanker_profile.bank
                return qs.filter(bank_id=bank)
            return qs  # God-Level SuperUser sees all

        return qs.none()

class BranchAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:

            if hasattr(request.user, 'superbanker_profile'):
                bank = request.user.superbanker_profile.bank
                return qs.filter(regional_office__bank_id=bank)
            return qs

        try:
            superbanker_profile = request.user.superbanker_profile
            return qs.filter(regional_office__bank_id=superbanker_profile.bank_id)
        except AttributeError:
            return qs.none()
#
# class ProfileAdmin(admin.ModelAdmin):
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         print('humor seting 0%')
#
#         if request.user.is_superuser:
#
#             if hasattr(request.user, 'superbanker_profile'):
#                 bank = request.user.superbanker_profile.bank
#                 return qs.filter(branch__regional_office__bank_id=bank)
#
#                 # return qs.filter(branch__branch__regional_office__bank=bank)
#             return qs
#
#         try:
#             superbanker_profile = request.user.superbanker_profile
#             return qs.filter(branch__regional_office__bank_id=superbanker_profile.bank_id)
#         except AttributeError:
#             return qs.none()
#
# class SettlementRowAdmin(admin.ModelAdmin):
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#
#         if request.user.is_superuser:
#             return qs  # God-Level SuperUser sees everything
#
#         try:
#             superbanker_profile = request.user.superbanker_profile
#             # print(qs.filter(branch__regional_office__bank_id=superbanker_profile.bank_id))
#             return qs.filter(branch__regional_office__bank_id=superbanker_profile.bank_id)
#         except AttributeError:
#             return qs.none()
# #
# @admin.register(RegionalOffice)
# class RegionalOfficeAdmin(admin.ModelAdmin):
#     """Admin for Regional Offices with inline branches."""
#     list_display = ('ro_name', 'bank_id')
#     search_fields = ('ro_name',)
#     inlines = [BranchInline]  # Add Branches under a Regional Office
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if request.user.is_superuser:
#             try:
#                 superbanker = request.user.superbanker
#                 if superbanker.is_unrestricted:
#                     return qs  # Show all banks if unrestricted
#                 return qs.filter(bank_id=superbanker.bank)  # Filter Regional Offices by this bank
#             except:
#                 return qs.none()  # If no bank   is assigned, show nothing
#             return qs  # Normal users see all data
#
#             # return qs
#
#         try:
#             user_profile = Profile.objects.get(user=request.user)
#             if not user_profile.branch:
#                 return qs.none()
#             return qs.filter(bank=user_profile.branch.ro.bank)
#         except Profile.DoesNotExist:
#             return qs.none()

from .models import Branch  # Import the Branch model
#
# class SuperBankerAdmin(admin.ModelAdmin):
#     list_display = ("user", "bank", "is_unrestricted")  # Show is_unrestricted status
#     list_filter = ("is_unrestricted", "bank")  # Filter by restriction
#     search_fields = ("user__username", "bank__bank_name") # Search by username or bank name

# @admin.register(Branch)
# class BranchAdmin(admin.ModelAdmin):
#     list_display = ('branch_alpha', 'branch_name', 'regional_office', 'branch_district')
#     search_fields = ('branch_name', 'branch_alpha')
#     list_filter = ('regional_office', 'branch_district')
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if request.user.is_superuser:
#             try:
#                 superbanker = request.user.superbanker
#                 if superbanker.is_unrestricted:
#                     return qs  # Show all data
#                 return qs.filter(regional_office__bank=superbanker.bank)  # ✅ Correct
#             except:
#                 return qs.none()
#             return qs
#
#         # if request.user.groups.filter(name="SuperBanker").exists():
#         #     try:
#         #         user_profile = Profile.objects.get(user=request.user)
#         #         if not user_profile.branch:
#         #             return qs.none()
#         #         return qs.filter(ro__bank=user_profile.branch.ro.bank)
#         #     except Profile.DoesNotExist:
#         #         return qs.none()
#         #
#         # return qs.filter(ro__bank=request.user.profile.branch.ro.bank)

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

            if hasattr(request.user, 'superbanker_profile'):
                bank = request.user.superbanker_profile.bank
                return qs.filter(branch__regional_office__bank_id=bank)
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
            try:
                if hasattr(request.user, 'superbanker_profile'):
                    bank = request.user.superbanker_profile.bank
                    return qs.filter(bank=bank)
            except:
                return qs.none()
        return qs


# ==================== EXPORT CSV MIXIN ====================

class ExportCsvMixin:
    """Mixin to export selected objects as CSV."""
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.model_name}.csv'
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
            return queryset.filter(branch__branch__regional_office__id=self.value())  # ✅ Correct reference
        return queryset

class BranchDistrictFilter(admin.SimpleListFilter):
    title = _('Branch District')
    parameter_name = 'branch_district'

    def lookups(self, request, model_admin):
        """Fetch available district choices dynamically."""
        field = Branch._meta.get_field('branch_district')
        # choices = list(field.choices)
        # print("District Choices:", choices)
        # districts = Branch.objects.all().values_list("branch_district", flat=True).distinct()
        # print("Districts:", list(districts))
        #
        # x= [(d,d) for d in districts if d]
        # return x

        # print('my district is',x)
        # ✅ Get the field object
        # print(field.choices/)
        return field.choices  # ✅ Return its choices

    def queryset(self, request, queryset):
        """Filters queryset based on selection."""
        if self.value():
            return queryset.filter(branch__branch__branch_district__iexact=self.value())
        print('why empty qs')
        return queryset

    # template = "admin/dropdown_filter.html"

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

        # SuperUser can see everything
        if request.user.is_superuser:
            # print('okay i came here')
            if hasattr(request.user, 'superbanker_profile'):
                # print('okay i came here also')

                bank = request.user.superbanker_profile.bank
                # print(type(bank))# Ensure this is a Bank instance
                print()
                return qs.filter(branch__branch__regional_office__bank_id=bank)
            # print('okay i came here then')

            return qs



            # SuperBanker can only see their own bank's data




        # return qs.filter(branch__regional_office__bank_id=user_bank)  # F
# ==================== CUSTOM USER ADMIN ====================

class CustomUserAdmin(UserAdmin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        # Check if 'is_superuser' is already included before adding it
        if not any('is_superuser' in fields for _, fields in fieldsets):
            fieldsets += (('Superuser Settings', {'fields': ('is_superuser',)}),)
        if not request.user.is_superuser:
            fieldsets = tuple(f for f in fieldsets if 'is_superuser' not in f[1]['fields'])

        return fieldsets

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            if hasattr(request.user, 'superbanker_profile'):
                print('ists a si')
                bank = request.user.superbanker_profile.bank
                return qs.filter(profile__branch__regional_office__bank_id=bank)
            return qs
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
from django.contrib import admin
from .models import SuperBankerAssignment

@admin.register(SuperBankerAssignment)
class SuperBankerAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "bank")
    search_fields = ("user__username", "bank__name")

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# admin.site.register(Bank)  # Only SuperUsers can add Banks
admin.site.register(RegionalOffice, RegionalOfficeAdmin)
admin.site.register(Branch, BranchAdmin)
# admin.site.register(Profile, ProfileAdmin)
# admin.site.register(SettlementRow, SettlementRowAdmin)
# admin.site.register(SuperBankerAssignment, SuperBankerAdmin)

