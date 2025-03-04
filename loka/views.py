from django.contrib import messages
from django.contrib.auth import authenticate, logout  # add this
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render,redirect, get_object_or_404
from django.template import loader
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, UpdateView, DeleteView
from .forms import NewUserForm,LAForm,ProfileForm
from .forms import SettlementForm, SettlementFormset1
from .models import SettlementRow, Profile, RegionalOffice, Bank, LokAdalat,Branch,ENRSAccounts
from django.core.files.storage import default_storage
from datetime import datetime

import csv
from datetime import datetime
from .utils import render_to_pdf
from django.http import Http404
from io import BytesIO
from django.views import generic
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from django.template.loader import get_template
# import asyncio
# from StringIO import StringIO
from xhtml2pdf import pisa
# from PyPDF2 import PdfMerger,PdfReader
# from pyppeteer import launch
import io

from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView


def upload_success(request):
    return render(request, 'upload_success.html')

def setcalc(request):
    visit_count = request.session.get('visit_count', 0)

    # If the user has exceeded 10 visits, redirect to signup page
    if visit_count >= 5 and not request.user.is_authenticated:
        messages.warning(request, "Request limits(5) exceeded. Please contact us for using pro features")
        return redirect('login')  # Replace with your signup URL name

    # Increase visit count
    request.session['visit_count'] = visit_count + 1

    return render(request, 'settlementcalc.html')


def upload_lokadalat_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not a CSV')
            return redirect('upload_lokadalat_csv')

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file,delimiter='|')
        next(reader)  # Skip header

        for row in reader:
            cleaned_row = [col.strip("'") for col in row]
            print('row is')
            print(cleaned_row)
            LokAdalatAccount.objects.update_or_create(
                account_no=cleaned_row[1],
                defaults={
                    'branch': cleaned_row[0],
                    'scheme_code': cleaned_row[2],
                    'account_name': cleaned_row[3],
                    'sanction_date': datetime.strptime(cleaned_row[4], '%d/%m/%Y').date() if cleaned_row[4] else None,
                    'sanction_amount': cleaned_row[5] or 0,
                    'address': cleaned_row[6][:20],  # Truncate address to first 20 characters
                    'balance_amount': cleaned_row[7] or 0,
                    'demand_amount': cleaned_row[8] or 0,
                    'account_npa_date': datetime.strptime(cleaned_row[9], '%d/%m/%Y').date() if cleaned_row[
                        9] else None,
                    'category_as_on_2024': cleaned_row[10],
                    'provision_amount': cleaned_row[11] or 0,
                    'mobile_no': cleaned_row[12],
                    'npa_expenses': cleaned_row[13] or 0,
                    'total_dues': cleaned_row[14] or 0,
                }
            )

        messages.success(request, 'CSV uploaded successfully!')
        return redirect('upload_lokadalat_csv')

    return render(request, 'upload_lokadalat.html')


def view_lokadalat_accounts(request):
    query = request.GET.get('account_no', '')
    account = None

    if query:
        account = LokAdalatAccount.objects.filter(account_no=query)

    return render(request, 'view_lokadalat.html', {'account': account})



class ChangePasswordView(LoginRequiredMixin,PasswordChangeView):
    login_url = '/login/'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('index')
    template_name = 'change_password.html'

    def form_valid(self, form):
        messages.success(self.request, "Password Changed successfully")
        super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())

    def shouldBeRedirectedToAdmin(self):
        isSU=self.request.user.is_superuser
        thisUser=User.objects.get(username=self.request.user)
        isASuperBanker=thisUser.groups.filter(name="SuperBanker").exists()
        shdBRedctd=isSU or isASuperBanker
        return shdBRedctd


    def get(self, *args, **kwargs):
        shdBRedctd=self.shouldBeRedirectedToAdmin()
        # print(self.request.user.is_superuser)
        if(shdBRedctd):
            return redirect('admin:index')
        return super(PasswordChangeView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ChangePasswordView, self).get_context_data(**kwargs)

        # Fetch the Profile of the current user
        profile = Profile.objects.filter(user=self.request.user).first()

        if profile and profile.branch:
            regional_office = profile.branch.regional_office  # Get the RegionalOffice
            if regional_office:
                context['bankid'] = regional_office.bank_id  # Get bank_id from RegionalOffice
            context['branch_name'] = profile.branch.branch_name
        else:
            context['branch_name'] = self.request.user.username
            context['bankid'] = ""

        return context



def width(string, font, size, charspace):
    width = stringWidth(string, font, size)
    width += (len(string) - 1) * charspace
    return width

def handler404(request, exception):
   return render(request, '404handler.html')


# def handler500(request, exception):
#     response = render_to_response("500handler.html")
#     response.status_code = 500
#     return response

def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('index')


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("index")
            else:
                print('invalidform')
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="login.html", context={"login_form": form})





def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()  # Creates the user

            # Make sure the Profile gets created
            profile, created = Profile.objects.get_or_create(user=user)

            # Get form data for branch
            branch_name = form.cleaned_data.get('branch_name')
            branch_alpha = form.cleaned_data.get('branch_alpha')
            branch_addr = form.cleaned_data.get('branch_addr')
            branch_ifsc = form.cleaned_data.get('branch_ifsc')
            branch_district = form.cleaned_data.get('branch_district')
            branch_state = form.cleaned_data.get('branch_state')
            ro = form.cleaned_data.get('ro')  # Regional Office
            bank = form.cleaned_data.get('bank')  # Bank

            # Ensure RO and Bank exist
            if not ro or not bank:
                return HttpResponse("Error: Regional Office and Bank must be selected!", status=400)

            # Create Branch and associate with Profile
            branch, created = Branch.objects.get_or_create(
                branch_name=branch_name,
                regional_office=ro,
                defaults={  # Only set these values if branch is newly created
                    'branch_alpha': branch_alpha,
                    'branch_addr': branch_addr,
                    'branch_ifsc': branch_ifsc,
                    'branch_district': branch_district,
                    'branch_state': branch_state,
                }
            )

            # Assign Branch and Bank to Profile
            profile.branch = branch
            profile.bank = bank
            profile.save()

            # Grant user staff status
            user.is_staff = True
            user.save()

            # Authenticate and login
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)

            return redirect("index")

        else:
            print(form.errors)

    form = NewUserForm()
    return render(request, "register.html", {"register_form": form})



# class UserEditView(LoginRequiredMixin,UpdateView):
#     login_url = '/login/'
#
#     form_class = ProfileForm
#     template_name = 'editprofile.html'
#     success_url = reverse_lazy('index')
#
#     def get_object(self, queryset=None):
#         return Profile.objects.get(user=self.request.user)
#
#     def shouldBeRedirectedToAdmin(self):
#         isSU=self.request.user.is_superuser
#         thisUser=User.objects.get(username=self.request.user)
#         isASuperBanker=thisUser.groups.filter(name="SuperBanker").exists()
#         shdBRedctd=isSU or isASuperBanker
#         return shdBRedctd
#
#
#     def get(self, *args, **kwargs):
#         shdBRedctd=self.shouldBeRedirectedToAdmin()
#         # print(self.request.user.is_superuser)
#         if(shdBRedctd):
#             return redirect('admin:index')
#         return super(UserEditView, self).get(*args, **kwargs)
#
#     def get_queryset(self, **kwargs):
#         qs = super().get_queryset(**kwargs)
#         if self.request.user.is_authenticated:
#             return qs.filter(id=Profile.objects.get(user__id=self.request.user.id))
#
#         else:
#             print('User is not authenticated')
#             return qs.filter(branch=None)
#
#     def get_context_data(self, **kwargs):
#         if self.request.user.is_authenticated:
#             context = super(UserEditView, self).get_context_data(**kwargs)
#             if(self.request.user.is_superuser):
#                 context['userissu']=True
#             else:
#                 context['userissu'] = False
#             ros = RegionalOffice.objects.filter(branches__user__username=self.request.user.username)
#             bank_id = ros[0].bank_id
#             context['authed'] = True
#             context['bankid'] = bank_id
#             context['user']=self.request.user
#
#
#             if(len(Profile.objects.filter(user__id=self.request.user.id))==0):
#                 context['branch_name']=self.request.user.username
#
#             else:
#                 context['branch_name']=Profile.objects.filter(user__id=self.request.user.id)[0].branch_name
#
#             return context
#         else:
#             context = super(UserEditView, self).get_context_data(**kwargs)
#             context['user']=self.request.user
#             print('hey this is coming unauthenticated')
#             context['authed'] = False
#
#             return context
from .forms import BranchEditForm

class BranchEditView(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    model = Branch
    form_class = BranchEditForm
    template_name = 'edit_branch.html'
    success_url = reverse_lazy('index')

    def get_object(self, queryset=None):
        if self.request.user.is_superuser:
            # If superuser, allow editing of any branch (or redirect if needed)
            return get_object_or_404(Branch, id=self.kwargs.get("pk"))

            # For regular users, fetch their branch through Profile
        profile = get_object_or_404(Profile, user=self.request.user)
        return get_object_or_404(Branch, id=profile.branch.id)

    def get_form_kwargs(self):
        """Pass the User instance to the form for additional fields."""
        kwargs = super().get_form_kwargs()
        kwargs["user_instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save both Branch and User model fields."""
        response = super().form_valid(form)  # Save the Branch model first

        # Update the User model email if changed
        email = form.cleaned_data.get("email")  # Get the updated email
        user = self.request.user  # Get the logged-in user
        if email and user.email != email:  # Check if email is updated
            user.email = email
            user.save()  # Save the User model

        return response  # Return the original response


class UserEditView(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    form_class = ProfileForm
    template_name = 'editprofile.html'
    success_url = reverse_lazy('index')

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def shouldBeRedirectedToAdmin(self):
        thisUser = self.request.user
        return thisUser.is_superuser or thisUser.groups.filter(name="SuperBanker").exists()

    def get(self, *args, **kwargs):
        if self.shouldBeRedirectedToAdmin():
            return redirect('admin:index')
        return super().get(*args, **kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        if self.request.user.is_authenticated:
            return qs.filter(user=self.request.user)  # ✅ Corrected filter
        return qs.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['userissu'] = self.request.user.is_superuser
            context['authed'] = True
            context['user'] = self.request.user

            # ✅ Get Profile for the logged-in user
            profile = Profile.objects.filter(user=self.request.user).first()
            if profile:
                context['branch_name'] = profile.branch.branch_name if profile.branch else "No Branch"
                context['bankid'] = profile.branch.regional_office.bank_id if profile.branch and profile.branch.regional_office else None
            else:
                context['branch_name'] = self.request.user.username

        else:
            context['authed'] = False
            context['user'] = self.request.user

        return context

def load_regions(request):
    region_id = request.GET.get('bank')
    print('loading regions',region_id)
    regions = RegionalOffice.objects.filter(bank_id_id=region_id).order_by('ro_name')
    # html = ''.join(f'<option value="{region.pk}">{region.ro_name}</option>' for region in regions)
    # return HttpResponse(html)
    print(regions[0].ro_name)
    return render(request, 'region_dropdown_list_options.html', {'regions': regions})


def regbranch(request):
    return HttpResponse('At REGISTRATION OF BRANCH')


def index(request):
    return redirect("selectsettlements")



def gotohome(request):
    print('go man!!!!!!!')
    return redirect('selectsettlements')

@login_required(login_url='/login/')
def getsettlementlist(request):
    context = {}
    if request.user.is_superuser:
        raise Http404()

    profile_user = Profile.objects.filter(user=request.user).first()

    if not profile_user or not profile_user.branch:
        raise Http404("No profile or branch associated with this user.")

    bank = profile_user.branch.regional_office.bank_id


    if not bank:
        raise Http404("No bank associated with this user.")

    lokax = LokAdalat.objects.filter(bank=profile_user.branch.regional_office.bank_id).order_by('lokadalatdate')

    if request.method == "POST":
        form = LAForm(request.POST, lokax=lokax)
        if form.is_valid():
            selected_lokax_id = form.cleaned_data['lokax'].id
            return redirect('settlement_list', lokax_id=selected_lokax_id)  # Redirect with ID

    else:
        form = LAForm(lokax=lokax)

    context.update({
        'form': form,
        'branch_name': profile_user.branch.branch_name if profile_user.branch else "No Branch",
        'bankid': bank,
        'lokax': lokax
    })

    return render(request, "getsetlist.html", context)



class SettlementListView(LoginRequiredMixin, ListView):
    login_url = "/login/"
    model = SettlementRow
    template_name = "settlement_list.html"

    def should_be_redirected_to_admin(self):
        """Redirect Superuser and SuperBanker to Admin Panel"""
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="SuperBanker").exists()

    def get(self, *args, **kwargs):
        """Redirects Superusers & SuperBankers to the Admin Panel"""
        if self.should_be_redirected_to_admin():
            return redirect("admin:index")
        return super().get(*args, **kwargs)

    def get_queryset(self):
        """Fetches the Settlement Rows for the User's Branch"""
        if not self.request.user.is_authenticated:
            return SettlementRow.objects.none()  # Return an empty queryset

        # Fetch the profile of the logged-in user
        profile = get_object_or_404(Profile, user=self.request.user)

        # Fetch the LokAdalat ID from request
        lokax_id = self.request.GET.get("lokadalat")
        print(lokax_id, "Tamerind")
        if not lokax_id:
            raise Http404("LokAdalat not selected.")

        # Fetch the corresponding LokAdalat
        lokax = get_object_or_404(LokAdalat, id=lokax_id)

        # Filter Settlement Rows by the user's branch and selected LokAdalat
        return SettlementRow.objects.filter(branch=profile, loka=lokax)

    def get_context_data(self, **kwargs):
        """Provides Additional Context Data for the Template"""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_authenticated:
            context["authed"] = False
            return context

        # Fetch the user's profile
        profile = get_object_or_404(Profile, user=user)

        # Fetch Regional Office of the Branch
        ros = RegionalOffice.objects.filter(branches=profile.branch).first()
        if not ros:
            raise Http404("Regional Office not found for this branch.")

        # Fetch Bank ID from the Regional Office
        bank_id = ros.bank_id if ros else None

        # Get the selected LokAdalat
        lokax_id = self.request.GET.get("lokadalat")
        lokax = get_object_or_404(LokAdalat, id=lokax_id)

        # Aggregates for settlement amounts
        aggregates = SettlementRow.objects.filter(branch=profile).aggregate(
            total_outstanding=Sum("outstanding"),
            total_unapplied_int=Sum("unapplied_int"),
            total_closure=Sum("totalclosure"),
            total_compromise_amt=Sum("compromise_amt"),
            total_token_money=Sum("token_money"),
            total_pr_waived=Sum("pr_waived"),
            total_int_waived=Sum("int_waived"),
            total_rest_amount=Sum("rest_amount"),
        )
        print(aggregates)

        # Add data to context
        context.update({
            "lokax": lokax,
            "bankid": bank_id,
            "branch_name": profile.branch.branch_name,
            "userissu": user.is_superuser,
            "authed": True,
            "aggregates": aggregates,
        })

        return context



class SettlementDelete(DeleteView):
    model = SettlementRow
    context_object_name = 'settlement'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        messages.success(self.request, "The settlement was deleted successfully.")
        return super(SettlementDelete, self).form_valid(form)

# class SettlementAddView(LoginRequiredMixin,TemplateView):
#     login_url = '/login/'
#     template_name = "add_settlement.html"
#
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
#         bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#         # ros=RegionalOffice.objects.all()
#
#         lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
#             'lokadalatdate')
#
#         qs = SettlementRow.objects.filter(loka__username=profile_user[0].bank.bank_id)
#         print("QML is", str(qs))
#         kwargs['queryset'] = lokax
#         kwargs['bankid']=bankid
#         return kwargs
#
#     def get(self, *args, **kwargs):
#         profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
#         # print(profile_user[0], "profinonesx")
#
#         if profile_user[0].bank is None:
#             return render(self.request, "loka/unauthorised.html", {})
#
#             # return HttpResponse("You are not authorised",status=401)
#         else:
#             bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#             lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(\
#             'lokadalatdate')
#             qs = SettlementRow.objects.filter(loka__username=profile_user[0].bank.bank_id)
#             ros = profile_user[0].ro
#             formset = SettlementFormset1(ros=ros,loka=lokax, branch=self.request.user.id, queryset=SettlementRow.objects.none(),
#                                      initial=[{'branch': self.request.user.id, 'loka': lokax[0].id,'ro':RegionalOffice.objects.filter(id=ros.id)[0].id}])
#             branchx = Profile.objects.filter(id=self.request.user.id)
#             profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
#             bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#             context={}
#             context['settlement_formset']=formset
#             context['bankid']=bankid[0]
#             context['branch_name']=profile_user[0].branch_name
#
#             return self.render_to_response(context)
#
#     def post(self, *args, **kwargs):
#         profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
#         print(profile_user[0].bank.bank_id)
#
#         bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#
#         lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
#             'lokadalatdate')
#         # ros = RegionalOffice.objects.all().filter(bank_id=bankid[0])
#         ros=profile_user[0].ro
#
#         formset = SettlementFormset1(ros=ros,loka=lokax, branch=Profile.objects.get(id=profile_user[0].id).id, data=self.request.POST)
#         print(self.request.POST)
#         if (formset.is_valid()):
#             instances = formset.save(commit=False)
#             # account_numbers = ", ".join([instance.account_no for instance in instances])  # Extract account numbers
#             account_numbers = ", ".join([instance.account_no for instance in instances])  # Extract account numbers
#
#             lokax_id = None
#             if instances:
#                 lokax_id = instances[0].loka.id
#             for instance in instances:
#                 instance.save()
#             if lokax_id:
#                 messages.success(self.request, f"Added successfully for Account No(s): {account_numbers}")
#
#                 return redirect(f"{reverse_lazy('settlement_list')}?lokadalat={lokax_id}")
#             else:
#                 messages.error(self.request, "Something went wrong because it seems there exist no lokadaat.Contact Admin.")
#                 return redirect(reverse_lazy("add_settlement"))
#
#             print('Formset is vallid')
#
#
#         else:
#
#             messages.error(self.request, "Invalid data. Please check the form fields.")
#             print('Formset is invalid ', formset.errors)
#
#         return redirect(reverse_lazy("add_settlement"))


from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, LokAdalat, SettlementRow
from .forms import SettlementFormset1

class SettlementAddView(LoginRequiredMixin, TemplateView):
    login_url = "/login/"
    template_name = "add_settlement.html"

    def get_user_profile(self):
        """Fetch the logged-in user's profile and ensure it has a valid branch."""
        try:
            profile = Profile.objects.get(user=self.request.user)
            return profile if profile.branch else None
        except Profile.DoesNotExist:
            return None

    def get_lokadalats(self, bank):
        """Fetch all LokAdalats for the given bank."""
        return LokAdalat.objects.filter(bank=bank).order_by("lokadalatdate")

    def get_form_kwargs(self):
        """Pass additional arguments to the form."""
        kwargs = super().get_form_kwargs()
        profile = self.get_user_profile()
        if not profile:
            return kwargs  # Return empty kwargs if no valid profile

        bank = profile.branch.regional_office.bank_id
        kwargs["queryset"] = self.get_lokadalats(bank)
        kwargs["bankid"] = bank
        return kwargs

    def get(self, *args, **kwargs):
        """Handle GET request - Show the Settlement Formset"""
        profile = self.get_user_profile()
        if not profile:
            return render(self.request, "loka/unauthorised.html", {})

        bank = profile.branch.regional_office.bank_id
        lokax = self.get_lokadalats(bank)
        ros = profile.branch.regional_office

        if not lokax.exists():
            messages.error(self.request, "No LokAdalat found. Contact Admin.")
            return redirect("index")

        formset = SettlementFormset1(
            ros=ros,
            loka=lokax,
            branch=profile,
            queryset=SettlementRow.objects.none(),
            # initial=[{"branch": profile.branch.id, "loka": lokax.first().id, "ro": ros.id}],
            initial=[{"branch": profile.id, "loka": lokax.first().id, "ro": ros.id}],
        )

        context = {
            "settlement_formset": formset,
            "bankid": bank,
            "branch_name": profile.branch.branch_name,
        }
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        """Handle POST request - Process and save Settlement Formset"""
        profile = self.get_user_profile()
        if not profile:
            messages.error(self.request, "Unauthorized access.")
            return redirect("index")

        bank = profile.branch.regional_office.bank_id
        lokax = self.get_lokadalats(bank)
        ros = profile.branch.regional_office
        print(profile)
        print('metamorphoss')

        # formset = SettlementFormset1(
        #     ros=ros, loka=lokax, branch=profile.branch, data=self.request.POST
        # )
        formset = SettlementFormset1(
            ros=ros, loka=lokax, branch=profile, data=self.request.POST  # Pass Profile, not Branch
        )


        if formset.is_valid():
            instances = formset.save(commit=False)
            if not instances:
                messages.error(self.request, "No valid settlements provided.")
                return redirect("add_settlement")

            lokax_id = instances[0].loka.id
            account_numbers = ", ".join([instance.account_no for instance in instances])

            for instance in instances:
                instance.save()

            messages.success(
                self.request, f"Added successfully for Account No(s): {account_numbers}"
            )
            return redirect(f"{reverse_lazy('settlement_list')}?lokadalat={lokax_id}")

        messages.error(self.request, "Invalid data. Please check the form fields.")
        print("Formset errors:", formset.errors)

        return redirect("add_settlement")




import django_tables2 as tables


class SimpleTable(tables.Table):
    class Meta:
        model = SettlementRow
        exclude = ('id', 'loka',)


# def deleteset(request, id):
#     from django.urls import reverse
#
#     branchx = Profile.objects.filter(id=request.user.id)
#     settlerow = SettlementRow.objects.filter(id=id).first()
#     if not settlerow:
#         raise Http404("Settlement not found.")
#
#
#     lokax_id = settlerow.loka.id
#     # print(request.POST,'getttttttt')
#     setpk = SettlementRow.objects.filter(id=id)
#     if request.user.is_authenticated and branchx[0].user == setpk[0].branch.user:
#         # print('Trueeeeeeee')
#         settlerow = SettlementRow.objects.get(id=id)
#         settlerow.delete()
#         return redirect(f"{reverse('settlement_list')}?lokadalat={lokax_id}")
#     else:
#         raise Http404()




from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404
from django.contrib import messages

def deleteset(request, id):
    """Deletes a settlement row only if the user is authorized."""
    if not request.user.is_authenticated:
        raise Http404("Unauthorized access.")

    # Get user profile
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.branch:
            raise Http404("User profile is not linked to a branch.")
    except Profile.DoesNotExist:
        raise Http404("User profile not found.")

    # Fetch settlement row
    settlerow = get_object_or_404(SettlementRow, id=id)

    # Debugging: Check instance types
    print(f"Logged-in User: {request.user.username}")
    print(f"User's Profile: {profile} (Type: {type(profile)})")
    print(f"Settlement's Branch (Profile): {settlerow.branch} (Type: {type(settlerow.branch)})")

    # Ensure the settlement is linked to the correct profile, not branch
    if settlerow.branch != profile:
        raise Http404("You do not have permission to delete this settlement.")

    # Get LokAdalat ID for redirect
    lokax_id = settlerow.loka.id if settlerow.loka else None

    # Delete settlement row
    settlerow.delete()
    messages.success(request, "Settlement deleted successfully.")

    # Redirect with lokadalat ID
    return redirect(f"{reverse('settlement_list')}?lokadalat={lokax_id}" if lokax_id else "settlement_list")



# class SettlementUpdateView(LoginRequiredMixin,UpdateView):
#     login_url = '/login/'
#     model = SettlementRow
#     fields=('cust_name','account_no','outstanding','totalclosure','compromise_amt','token_money','loan_obj','irac')
#     exclude=('loka','ro','branch','pr_waived','int_waived','unapplied_int','rest_amount')
#     success_url = reverse_lazy("settlement_list")
#
#     def get_context_data(self, **kwargs):
#         context = super(SettlementUpdateView, self).get_context_data(**kwargs)
#         branchx = Profile.objects.filter(id=self.request.user.id)
#         setpk = SettlementRow.objects.filter(id=self.kwargs['pk'])
#         profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
#         bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#         if self.request.user.is_authenticated and branchx[0].user == setpk[0].branch.user:
#             context['passed'] = True
#             context['branch_name']=branchx[0].branch_name
#             context['bankid']=bankid[0].bank_name
#             print('yep passed')
#         else:
#             context['passed'] = False
#         return context
#
#     def get_queryset(self):
#         base_qs = super(SettlementUpdateView, self).get_queryset()
#         branchx = Profile.objects.filter(id=self.request.user.id)
#         setpk = SettlementRow.objects.filter(id=self.kwargs['pk'])
#         if (branchx[0].user==setpk[0].branch.user):
#             return base_qs.filter(branch=Profile.objects.filter(id=self.request.user.id)[0])
#         else:
#             # return None
#             return base_qs.filter(branch=None)
#
#     def form_valid(self, form):
#         if not (form.data['cust_name'] and form.data['account_no'] and form.data['outstanding'] \
#                 and form.data['totalclosure'] and\
#                 form.data['compromise_amt'] and\
#                 form.data['token_money'] and\
#              form.data['loan_obj']  and form.data[ 'irac']):
#             messages.warning(self.request, "Empty fields not allowed")
#             return redirect(reverse_lazy("settlement_list"))
#
#         else:
#             form.save()
#             messages.success(self.request, "Updated")
#             return redirect(reverse_lazy("settlement_list"))
#
#
#     def form_invalid(self, form):
#         messages.info(self.request, form.errors)
#         return redirect(reverse_lazy("settlement_list"))


class SettlementUpdateView(LoginRequiredMixin, UpdateView):
    login_url = "/login/"
    model = SettlementRow
    fields = (
        "cust_name",
        "account_no",
        "outstanding",
        "totalclosure",
        "compromise_amt",
        "token_money",
        "loan_obj",
        "irac",
    )
    exclude = (
        "loka",
        "ro",
        "branch",
        "pr_waived",
        "int_waived",
        "unapplied_int",
        "rest_amount",
    )
    success_url = reverse_lazy("settlement_list")

    def get_context_data(self, **kwargs):
        """Provide additional context for the template."""
        context = super().get_context_data(**kwargs)

        try:
            profile_user = Profile.objects.get(user=self.request.user)  # Get Profile instance
            settlement_instance = SettlementRow.objects.get(id=self.kwargs["pk"])  # Get SettlementRow instance

            # Check if the profile's branch matches the settlement's branch
            if profile_user == settlement_instance.branch:
                context["passed"] = True
                context["branch_name"] = profile_user.branch.branch_name
                context["bankid"] = profile_user.branch.regional_office.bank_id  # bank_id is used instead of bank
                print("Access granted to update settlement.")
            else:
                context["passed"] = False
                messages.error(self.request, "Unauthorized access.")
        except (Profile.DoesNotExist, SettlementRow.DoesNotExist):
            context["passed"] = False
            messages.error(self.request, "Invalid profile or settlement.")

        return context

    def get_queryset(self):
        """Filter settlements by the logged-in user's branch (Profile instance)."""
        profile_user = Profile.objects.get(user=self.request.user)  # Get Profile instance
        return SettlementRow.objects.filter(branch=profile_user)  # Ensure branch is a Profile

    def form_valid(self, form):
        """Validate and save form data."""
        required_fields = [
            "cust_name",
            "account_no",
            "outstanding",
            "totalclosure",
            "compromise_amt",
            "token_money",
            "loan_obj",
            "irac",
        ]
        settlement = form.instance  # Get the instance being updated

        if not (settlement.loka and settlement.loka.id):
            messages.error(self.request, "LokAdalat ID missing. Cannot proceed.")
            return redirect(reverse_lazy("settlement_list"))

        lokadalat_id = settlement.loka.id


        if any(not form.cleaned_data[field] for field in required_fields):
            messages.warning(self.request, "Empty fields are not allowed.")
            return redirect(reverse_lazy("settlement_list"))

        form.save()
        messages.success(self.request, "Settlement updated successfully.")
        # return redirect(reverse_lazy("settlement_list"))
        return redirect(f"{reverse_lazy('settlement_list')}?lokadalat={lokadalat_id}")

    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(self.request, "Invalid data. Please check your inputs.")
        return self.render_to_response(self.get_context_data(form=form))




def updaterec(request, id):
    mymember = SettlementRow.objects.get(id=id)
    template = loader.get_template('settlementrow_form.html')
    context = {
        'setrow': mymember,
    }
    return HttpResponse(template.render(context, request))


# def getladata(request):
#     context = {}
#     if (request.user.is_superuser):
#         raise Http404()
#     else:
#         profile_user = Profile.objects.filter(Q(user__username__icontains=User.objects.get(id=request.user.id)))
#         bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#         lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
#             'lokadalatdate')
#         if profile_user:
#             context['form'] = LAForm(lokax=lokax)
#             context['branch_name'] = profile_user[0].branch_name
#             context['bankid'] = bankid[0]
#             context['lokax']=lokax
#             return render(request, "ladata.html", context)
#         else:
#             raise Http404()


from django.shortcuts import render
from django.http import Http404
from django.db.models import Q
from .models import Profile, Bank, LokAdalat, RegionalOffice
from .forms import LAForm


def getladata(request):
    """Fetch LokAdalat data for the user's bank."""
    context = {}

    if request.user.is_superuser:
        raise Http404("Superusers are not allowed to access this page.")

    try:
        # Get the logged-in user's profile
        profile_user = Profile.objects.get(user=request.user)

        # Ensure the profile is linked to a RegionalOffice
        if not profile_user.branch.regional_office:
            raise Http404("Profile is not linked to a Regional Office.")

        # Get the user's bank from RegionalOffice (via bank_id)
        bank = profile_user.branch.regional_office.bank_id  # ✅ Corrected lookup
        if not bank:
            raise Http404("No bank found for the associated Regional Office.")

        # Fetch LokAdalat records linked to the user's bank
        # lokax = LokAdalat.objects.filter(username__username__icontains=bank.id).order_by('lokadalatdate')
        lokax = LokAdalat.objects.filter(bank=bank).order_by('lokadalatdate')

        # Set context data
        context["form"] = LAForm(lokax=lokax)
        context["branch_name"] = profile_user.branch.branch_name
        context["bankid"] = bank
        context["lokax"] = lokax

        return render(request, "ladata.html", context)

    except Profile.DoesNotExist:
        raise Http404("User profile not found.")


# def getladata1(request):
#     context = {}
#     if (request.user.is_superuser):
#         raise Http404()
#     else:
#         profile_user = Profile.objects.filter(Q(user__username__icontains=User.objects.get(id=request.user.id)))
#         bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
#         lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
#             'lokadalatdate')
#         if profile_user:
#             context['form'] = LAForm(lokax=lokax)
#             context['branch_name']=profile_user[0].branch_name
#             context['bankid']=bankid[0]
#             context['lokax']=lokax
#             return render(request, "ladata1.html", context)
#         else:
#             raise Http404()


def getladata1(request):
    if request.user.is_superuser:
        raise Http404()

    profile_user = Profile.objects.get(user=request.user)  # Get Profile instance
    # bank = profile_user.branch.bank  # Fix: Access Bank through Branch
    bank = profile_user.branch.regional_office.bank_id  # ✅ Corrected lookup

    lokax = LokAdalat.objects.filter(bank_id=bank).order_by('lokadalatdate')  # Query LokAdalat using Bank

    context = {
        'form': LAForm(lokax=lokax),
        'branch_name': profile_user.branch.branch_name,  # Fix: Access Branch Name
        'bankid': bank.bank_name,  # Fix: Access Bank Name
        'lokax': lokax
    }
    return render(request, "ladata1.html", context)




def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

# def settopdf(request,lokax_id):
#     context = {}
#     QueryDict = request.GET
#     predicted = QueryDict.get("lokadalat")
#     # print('request post is')
#     print(predicted)
#     # print('ello world')
#     # qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=Profile.objects.get(id=request.user.id)))
#     qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
#
#     ros = RegionalOffice.objects.filter(branches__user__username=request.user.username)
#     bank_id = ros[0].bank_id
#     print(bank_id)
#     if (request.user.is_authenticated and qs1):
#
#         qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
#         branchx = Profile.objects.filter(id=request.user.id)
#         # print('Bank id is',bankid)
#         lokax = LokAdalat.objects.all().filter(id=lokax_id).first()
#         # print(str(lokax))
#         context['contoutstanding'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('outstanding'))
#         context['contunapplied_int'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(
#             Sum('unapplied_int'))
#         context['conttotalclosure'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('totalclosure'))
#         context['contcompromise_amt'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(
#             Sum('compromise_amt'))
#         context['conttoken_money'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('token_money'))
#         context['contpr_waived'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('pr_waived'))
#         context['contint_waived'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('int_waived'))
#         context['contrest_amount'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('rest_amount'))
#         context['branch'] = branchx[0].branch_name
#         context['object_list'] = qs1
#         context['venue'] = lokax.lokadalatvenue
#         context['ladate'] = lokax.lokadalatdate
#         context['emptyset'] = False
#         context['regiono'] = ros[0].ro_name
#         context['bankid'] = bank_id
#     else:
#
#         context['emptyset'] = True
#
#
#
#     # return render(request,"loka/summary.html",context)
#     # y=render_to_pdf("settlements_list2.html",context)
#
#     x=render_to_pdf("loka/summary.html",context)
#     # z=render_to_pdf("loka/settled.html",context)
#     return x
#

def settopdf(request, lokax_id):
    context = {}
    profile = Profile.objects.get(user=request.user)  # Fix: Get Profile instance
    qs1 = SettlementRow.objects.filter(branch=profile)  # Fix: Use Profile instance, not ID

    ros = RegionalOffice.objects.filter(branches=profile.branch).first()  # Fix: Get RO linked to the Branch
    lokax = LokAdalat.objects.get(id=lokax_id)  # Fix: Get LokAdalat instance

    if request.user.is_authenticated and qs1.exists():
        context.update({
            'contoutstanding': qs1.aggregate(Sum('outstanding')),
            'contunapplied_int': qs1.aggregate(Sum('unapplied_int')),
            'conttotalclosure': qs1.aggregate(Sum('totalclosure')),
            'contcompromise_amt': qs1.aggregate(Sum('compromise_amt')),
            'conttoken_money': qs1.aggregate(Sum('token_money')),
            'contpr_waived': qs1.aggregate(Sum('pr_waived')),
            'contint_waived': qs1.aggregate(Sum('int_waived')),
            'contrest_amount': qs1.aggregate(Sum('rest_amount')),
            'branch': profile.branch.branch_name,
            'object_list': qs1,
            'venue': lokax.lokadalatvenue,
            'ladate': lokax.lokadalatdate,
            'emptyset': False,
            'regiono': ros.ro_name if ros else "N/A",
            'bankid': profile.branch.regional_office.bank_id.bank_name
        })
    else:
        context['emptyset'] = True

    return render_to_pdf("loka/summary.html", context)


def getsettlements1(request, lokax_id):
    context = {}
    profile = Profile.objects.get(user=request.user)  # Fix: Get Profile instance
    qs1 = SettlementRow.objects.filter(branch=profile)  # Fix: Use Profile instance

    ros = RegionalOffice.objects.filter(branches=profile.branch).first()  # Fix: Get RO linked to the Branch
    # bank = profile.branch.bank  # Fix: Access Bank through Branch
    bank = profile.branch.regional_office.bank_id  # ✅ Corrected lookup

    lokax = LokAdalat.objects.get(id=lokax_id)  # Fix: Get LokAdalat instance

    if request.user.is_authenticated and qs1.exists():
        context.update({
            'contoutstanding': qs1.aggregate(Sum('outstanding')),
            'contunapplied_int': qs1.aggregate(Sum('unapplied_int')),
            'conttotalclosure': qs1.aggregate(Sum('totalclosure')),
            'contcompromise_amt': qs1.aggregate(Sum('compromise_amt')),
            'conttoken_money': qs1.aggregate(Sum('token_money')),
            'contpr_waived': qs1.aggregate(Sum('pr_waived')),
            'contint_waived': qs1.aggregate(Sum('int_waived')),
            'contrest_amount': qs1.aggregate(Sum('rest_amount')),
            'branch': profile.branch.branch_name,  # Fix: Access Branch Name
            'object_list': qs1,
            'venue': lokax.lokadalatvenue,
            'ladate': lokax.lokadalatdate,
            'emptyset': False,
            'regiono': ros.ro_name if ros else "N/A",
            'bankid': bank.bank_name  # Fix: Access Bank Name
        })
    else:
        context['emptyset'] = True

    return render_to_pdf("loka/settled.html", context)


# def getsettlements1(request,lokax_id):
#     context = {}
#     QueryDict = request.GET
#     predicted = QueryDict.get("lokadalat")
#     # print('request post is')
#     print(predicted)
#     # print('ello world')
#     # qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=Profile.objects.get(id=request.user.id)))
#     qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
#
#     ros = RegionalOffice.objects.filter(branches__user__username=request.user.username)
#     bank_id = ros[0].bank_id
#     print(bank_id)
#     if (request.user.is_authenticated and qs1):
#
#         qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
#         branchx = Profile.objects.filter(id=request.user.id)
#         # print('Bank id is',bankid)
#         lokax = LokAdalat.objects.all().filter(id=lokax_id).first()
#         # print(str(lokax))
#         context['contoutstanding'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('outstanding'))
#         context['contunapplied_int'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(
#             Sum('unapplied_int'))
#         context['conttotalclosure'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('totalclosure'))
#         context['contcompromise_amt'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(
#             Sum('compromise_amt'))
#         context['conttoken_money'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('token_money'))
#         context['contpr_waived'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('pr_waived'))
#         context['contint_waived'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('int_waived'))
#         context['contrest_amount'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('rest_amount'))
#         context['branch'] = branchx[0].branch_name
#         context['object_list'] = qs1
#         context['venue'] = lokax.lokadalatvenue
#         context['ladate'] = lokax.lokadalatdate
#         context['emptyset'] = False
#         context['regiono'] = ros[0].ro_name
#         context['bankid'] = bank_id
#     else:
#
#         context['emptyset'] = True
#
#
#
#
#     return  render_to_pdf("loka/settled.html",context)
#     # return z


from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponse


def generate_sets(bank_name, regional_office, branch, lok_adalat_date, place, settlements):
    context = {
        'bankid': bank_name,
        'branch': branch,
        'venue': place,
        'object_list': settlements,
    }

    # Render the HTML content with the context
    html_content = render_to_string('loka/settled1.html', context)

    # Generate the PDF from the HTML
    pdf = HTML(string=html_content).write_pdf()

    # Return the generated PDF in an HTTP response for download
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="lok_adalat_settlement.pdf"'
    return response

@csrf_exempt  # Use this only if you're handling CSRF token manually in JavaScript
def generate_pdf(request):
    if request.method == 'POST':
        # Parse JSON data from the request
        import json
        data = json.loads(request.body)

        # Extract data from the request
        bank_name = data['bankName']
        regional_office = data['regionalOffice']
        branch = data['branch']
        lok_adalat_date = data['lokAdalatDate']
        place = data['place']
        settlements = data['settlements']
        for settlement in settlements:
            # Calculate the amount waived (totalclosure - compromiseAmount)
            totalClosure = settlement.get('totalClosure', 0)
            compromiseAmount = settlement.get('compromiseAmount', 0)

            # Calculate the amount waived and add it to the settlement object
            amount_waived = totalClosure - compromiseAmount
            print("total closure:",totalClosure,"minus",compromiseAmount,"=",amount_waived)
            settlement['amount_waived'] = amount_waived


        # Generate the PDF from the data
        pdf = generate_sets(bank_name, regional_office, branch, lok_adalat_date, place, settlements)

        # Return the PDF as an HttpResponse
        response = HttpResponse(pdf, content_type='application/pdf')
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Generates timestamp like 20250221153045
        filename = f"Settlement_Report_{timestamp}.pdf"
        print(filename)

        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        # response['Content-Disposition'] = 'attachment; filename="Settlement_Report.pdf"'
        return response
    return JsonResponse({'error': 'Invalid request'}, status=400)




@login_required
def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        file_path = default_storage.save(file.name, file)

        # Open file in binary mode and decode manually
        with default_storage.open(file_path, 'rb') as f:
            decoded_file = f.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file,delimiter='|')
            print("CSV Headers:", reader.fieldnames)

            for row in reader:
                print("Row Read from CSV:", row)
                row = {
                    key.strip().strip("'").strip('"'): value.strip().strip("'").strip('"') if value else ''
                    for key, value in row.items()
                }
                print("Row Read from CSV:", row)

                try:
                    def clean_value(value):
                        """ Ensure value is a string and strip whitespace safely """
                        return value.strip() if isinstance(value, str) else ''

                    def parse_date(date_str):
                        """ Convert date string to Python date object, handling different formats """
                        try:
                            date_str = clean_value(date_str)
                            return datetime.strptime(date_str, '%d-%m-%Y').date() if date_str else None
                        except ValueError:
                            return None  # Handle invalid date formats

                    def get_decimal(value):
                        """ Convert string to decimal, handling empty and improperly formatted values """
                        try:
                            return float(value.replace(',', '')) if value else 0.0
                        except ValueError:
                            return 0.0
                    # Ensure keys are stripped of extra spaces
                    row = {key.strip(): (value.strip() if value else '') for key, value in row.items() if key}


                    # print("Processing Row:", row)
                    account_no = clean_value(row.get('Account no', ''))
                    branch = clean_value(row.get('Branch', ''))
                    name = clean_value(row.get('Account Name', ''))
                    address = clean_value(row.get('Village', ''))[:20]
                    mobile_no = clean_value(row.get('Mobile No.', ''))
                    acc_sanction_date = row.get('Sanction Date', '').strip()
                    print('my date is',acc_sanction_date)

                    if acc_sanction_date:
                        try:
                            # 🔥 Allow both '18.10.2017' and '18-10-2017'
                            acc_sanction_date = datetime.strptime(acc_sanction_date, '%d.%m.%Y').date()

                        except ValueError:
                            try:
                                acc_sanction_date = datetime.strptime(acc_sanction_date, '%d-%m-%Y').date()
                            except ValueError:
                                acc_sanction_date = None
                    else:
                        acc_sanction_date = None

                    def get_decimal(value):
                        try:
                            return float(value.replace(',', '')) if value else 0.0
                        except ValueError:
                            return 0.0

                    print(f"Saving: {account_no}, {branch}, {name}, {acc_sanction_date}")

                    # Debugging to check CSV structure



                    ENRSAccounts.objects.update_or_create(
                        account_no=clean_value(row.get('Account no', '')),
                        defaults={
                            'user': request.user,
                            'branch': branch,
                            'name': name,
                            'address': address,
                            'mobile_no': mobile_no,
                            'acc_sanction_date': acc_sanction_date,
                            'total_dues': get_decimal(row.get('TOTAL DUES', '0')),
                            'outstanding_as_on': get_decimal(row.get('Bal as on current 30.12.2024', '0')),
                            'min_comp_amt': get_decimal(row.get('MINIMUM COMP AMOUNT', '0')),
                            'category': clean_value(row.get('Post audit category', '')),
                            'minimum_compromise_amt': get_decimal(row.get('MINIMUM COMP AMOUNT', '0')),
                            'npa_expenses': get_decimal(row.get('NPA EXPENSES', '0')),
                        }
                    )
                except Exception as e:
                    return JsonResponse({'error': f'Row processing failed: {str(e)}'}, status=400)

        return redirect('upload_success')

    return render(request, 'upload_csv.html')

# View to retrieve account details
def get_account_details(request):
    if request.method == 'GET' and 'account_no' in request.GET:
        if request.method == 'GET' and 'account_no' in request.GET:
            account_no = request.GET['account_no']
            try:
                account = ENRSAccounts.objects.get(account_no=account_no)
                context = {
                    'account': account  # Pass the account object directly to the template
                }
                return render(request, 'account_details.html', context)
            except ENRSAccounts.DoesNotExist:
                return render(request, 'account_details.html', {'error': 'Account not found'})
    return render(request, 'account_details.html')

