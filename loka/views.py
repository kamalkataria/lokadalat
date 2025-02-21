from django.contrib import messages
from django.contrib.auth import authenticate, logout  # add this
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, UpdateView, DeleteView
from .forms import NewUserForm,LAForm,ProfileForm
from .forms import SettlementForm, SettlementFormset1
from .models import SettlementRow, Profile, RegionalOffice, Bank, LokAdalat
from .utils import render_to_pdf
from django.http import Http404
from io import BytesIO
from django.views import generic
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.template.loader import get_template
import asyncio
# from StringIO import StringIO
from xhtml2pdf import pisa
import io

from xhtml2pdf import pisa
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.views.decorators.csrf import csrf_exempt



def setcalc(request):
    visit_count = request.session.get('visit_count', 0)

    # If the user has exceeded 10 visits, redirect to signup page
    if visit_count >= 500 and not request.user.is_authenticated:
        messages.warning(request, "Request limits exceeded. Please contact us for using pro features")
        return redirect('login')  # Replace with your signup URL name

    # Increase visit count
    request.session['visit_count'] = visit_count + 1

    return render(request, 'settlementcalc.html')




class ChangePasswordView(LoginRequiredMixin,PasswordChangeView):
    login_url='/login/'
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
        ros = RegionalOffice.objects.filter(branches__user__username=self.request.user.username)
        bank_id = ros[0].bank_id
        context['bankid'] = bank_id

        if (len(Profile.objects.filter(user__id=self.request.user.id)) == 0):
            context['branch_name'] = self.request.user.username

        else:
            context['branch_name'] = Profile.objects.filter(user__id=self.request.user.id)[0].branch_name
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
                messages.success(request, f"You are now logged in as {username}.")
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
            user = form.save()

            user.refresh_from_db()
            print('Ro is')
            print(user.profile.ro)

            user.profile.branch_name = form.cleaned_data.get('branch_name')
            user.profile.ro = form.cleaned_data.get('ro')
            user.profile.bank = form.cleaned_data.get('bank')

            user.profile.branch_alpha = form.cleaned_data.get('branch_alpha')
            user.profile.branch_addr = form.cleaned_data.get('branch_addr')
            user.profile.branch_ifsc = form.cleaned_data.get('branch_ifsc')
            user.profile.branch_district = form.cleaned_data.get('branch_district')
            user.profile.branch_state = form.cleaned_data.get('branch_state')
            user.profile.save()
            user.is_staff = True
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect("index")
        else:

            print(form.errors)
    form = NewUserForm()
    return render(request=request, template_name="register.html", context={"register_form": form})


class UserEditView(LoginRequiredMixin,UpdateView):
    login_url = '/login/'

    form_class = ProfileForm
    template_name = 'editprofile.html'
    success_url = reverse_lazy('index')

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return Profile.objects.get(user=self.request.user)
        else:
            return Profile.objects.get(user=None)

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
        return super(UserEditView, self).get(*args, **kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        if self.request.user.is_authenticated:
            return qs.filter(id=Profile.objects.get(user__id=self.request.user.id))

        else:
            print('User is not authenticated')
            return qs.filter(branch=None)

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:


            context = super(UserEditView, self).get_context_data(**kwargs)
            if(self.request.user.is_superuser):
                context['userissu']=True
            else:
                context['userissu'] = False
            ros = RegionalOffice.objects.filter(branches__user__username=self.request.user.username)
            bank_id = ros[0].bank_id
            context['authed'] = True
            context['bankid'] = bank_id
            context['user']=self.request.user


            if(len(Profile.objects.filter(user__id=self.request.user.id))==0):
                context['branch_name']=self.request.user.username

            else:
                context['branch_name']=Profile.objects.filter(user__id=self.request.user.id)[0].branch_name

            return context
        else:
            context = super(UserEditView, self).get_context_data(**kwargs)
            context['user']=self.request.user
            print('hey this is coming unauthenticated')
            context['authed'] = False

            return context


def load_regions(request):
    region_id = request.GET.get('bank')
    print('loading regions')
    regions = RegionalOffice.objects.filter(bank_id_id=region_id).order_by('ro_name')
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
    if (request.user.is_superuser):
        raise Http404()
    else:
        profile_user = Profile.objects.filter(Q(user__username__icontains=User.objects.get(id=request.user.id)))
        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        if profile_user:
            if request.method == "POST":
                form = LAForm(request.POST, lokax=lokax)
                if form.is_valid():
                    selected_lokax_id = form.cleaned_data['lokax'].id  # Assuming form has a LokAdalat field

                    context['lokax_id']=selected_lokax_id
                    context['form'] = form
                    context['branch_name'] = profile_user[0].branch_name
                    context['bankid'] = bankid[0]
                    return redirect('settlement_list', lokax_id=selected_lokax_id)  # Pass LokAdalat ID

            else:
                form = LAForm(lokax=lokax)
                context['form'] = form
                context['branch_name'] = profile_user[0].branch_name
                context['bankid'] = bankid[0]
                context['lokax']=lokax
            return render(request, "getsetlist.html", context)
        else:
            raise Http404()
    # return render(request,"getsetlist.html",{})


class SettlementListView(LoginRequiredMixin, ListView):
    login_url = '/login/'
    model = SettlementRow
    template_name = "settlement_list.html"

    def shouldBeRedirectedToAdmin(self):
        isSU = self.request.user.is_superuser
        thisUser = User.objects.get(username=self.request.user)
        isASuperBanker = thisUser.groups.filter(name="SuperBanker").exists()
        shdBRedctd = isSU or isASuperBanker
        return shdBRedctd

    def get(self, *args, **kwargs):
        shdBRedctd = self.shouldBeRedirectedToAdmin()
        # print(self.request.user.is_superuser)
        if (shdBRedctd):
            return redirect('admin:index')
        return super(SettlementListView, self).get(*args, **kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        if self.request.user.is_authenticated:
            # lokax_id = self.kwargs.get("lokax_id")
            lokax_id = self.request.GET.get("lokadalat")# Get LokAdalat ID from URL
            if not lokax_id:
                raise Http404("LokAdalat not selected.")

            try:
                lokax = LokAdalat.objects.get(id=lokax_id)

            except LokAdalat.DoesNotExist:
                raise Http404("Invalid LokAdalat selected.")
            return qs.filter(branch=Profile.objects.get(user__id=self.request.user.id),loka=lokax)


        else:
            print('User is not authenticated')
            return qs.filter(branch=None)

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:

            context = super(SettlementListView, self).get_context_data(**kwargs)
            # lokax_id = self.kwargs.get("lokax_id")
            lokax_id = self.request.GET.get("lokadalat")
            try:
                lokax = LokAdalat.objects.get(id=lokax_id)
                context["lokax"] = lokax
            except LokAdalat.DoesNotExist:
                raise Http404("Invalid LokAdalat selected.")

            if(self.request.user.is_superuser):
                context['userissu']=True
            else:
                context['userissu'] = False
            ros = RegionalOffice.objects.filter(branches__user__username=self.request.user.username)
            bank_id = ros[0].bank_id


            context['contoutstanding'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('outstanding'))
            context['contunapplied_int'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('unapplied_int'))
            context['conttotalclosure'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('totalclosure'))
            context['contcompromise_amt'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('compromise_amt'))
            context['conttoken_money'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('token_money'))
            context['contpr_waived'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('pr_waived'))
            context['contint_waived'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('int_waived'))
            context['contrest_amount'] = SettlementRow.objects.filter(
                branch=Profile.objects.get(user__id=self.request.user.id)).aggregate(
                Sum('rest_amount'))
            context['authed'] = True
            context['bankid'] = bank_id
            print(Profile.objects.filter(user__id=self.request.user.id))
            if (len(Profile.objects.filter(user__id=self.request.user.id)) == 0):
                context['branch_name'] = self.request.user.username

            else:
                context['branch_name'] = Profile.objects.filter(user__id=self.request.user.id)[0].branch_name

            return context
        else:
            context = super(SettlementListView, self).get_context_data(**kwargs)

            context['authed'] = False
            return context


class SettlementDelete(DeleteView):
    model = SettlementRow
    context_object_name = 'settlement'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        messages.success(self.request, "The settlement was deleted successfully.")
        return super(SettlementDelete, self).form_valid(form)

class SettlementAddView(LoginRequiredMixin,TemplateView):
    login_url = '/login/'
    template_name = "add_settlement.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
        # ros=RegionalOffice.objects.all()

        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')

        qs = SettlementRow.objects.filter(loka__username=profile_user[0].bank.bank_id)
        print("QML is", str(qs))
        kwargs['queryset'] = lokax
        kwargs['bankid']=bankid
        return kwargs

    def get(self, *args, **kwargs):
        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        # print(profile_user[0], "profinonesx")

        if profile_user[0].bank is None:
            return render(self.request, "loka/unauthorised.html", {})

            # return HttpResponse("You are not authorised",status=401)
        else:
            bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
            lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by( \
                'lokadalatdate')
            qs = SettlementRow.objects.filter(loka__username=profile_user[0].bank.bank_id)
            ros = profile_user[0].ro
            formset = SettlementFormset1(ros=ros,loka=lokax, branch=self.request.user.id, queryset=SettlementRow.objects.none(),
                                     initial=[{'branch': self.request.user.id, 'loka': lokax[0].id,'ro':RegionalOffice.objects.filter(id=ros.id)[0].id}])
            branchx = Profile.objects.filter(id=self.request.user.id)
            profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
            bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
            context={}
            context['settlement_formset']=formset
            context['bankid']=bankid[0]
            context['branch_name']=profile_user[0].branch_name

            return self.render_to_response(context)

    def post(self, *args, **kwargs):
        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        print(profile_user[0].bank.bank_id)

        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))

        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        # ros = RegionalOffice.objects.all().filter(bank_id=bankid[0])
        ros = profile_user[0].ro

        formset = SettlementFormset1(ros=ros, loka=lokax, branch=Profile.objects.get(id=profile_user[0].id).id,
                                     data=self.request.POST)
        if (formset.is_valid()):
            instances = formset.save(commit=False)
            # account_numbers = ", ".join([instance.account_no for instance in instances])  # Extract account numbers
            account_numbers = ", ".join([instance.account_no for instance in instances])  # Extract account numbers

            lokax_id = None
            if instances:
                lokax_id = instances[0].loka.id
            for instance in instances:
                instance.save()
            if lokax_id:
                messages.success(self.request, f"Added successfully for Account No(s): {account_numbers}")

                return redirect(f"{reverse_lazy('settlement_list')}?lokadalat={lokax_id}")
            else:
                messages.error(self.request, "Something went wrong because it seems there exist no lokadaat.Contact Admin.")
                return redirect(reverse_lazy("add_settlement"))

            print('Formset is vallid')


        else:

            messages.error(self.request, "Invalid data. Please check the form fields.")
            print('Formset is invalid ', formset.errors)

        return redirect(reverse_lazy("add_settlement"))

        


import django_tables2 as tables


class SimpleTable(tables.Table):
    class Meta:
        model = SettlementRow
        exclude = ('id', 'loka',)


def deleteset(request, id):
    from django.urls import reverse

    branchx = Profile.objects.filter(id=request.user.id)
    settlerow = SettlementRow.objects.filter(id=id).first()
    if not settlerow:
        raise Http404("Settlement not found.")


    lokax_id = settlerow.loka.id
    # print(request.POST,'getttttttt')
    setpk = SettlementRow.objects.filter(id=id)
    if request.user.is_authenticated and branchx[0].user == setpk[0].branch.user:
        # print('Trueeeeeeee')
        settlerow = SettlementRow.objects.get(id=id)
        settlerow.delete()
        messages.success(request, f"Deleted successfully for Account No(s): {settlerow.account_no}")

        return redirect(f"{reverse('settlement_list')}?lokadalat={lokax_id}")
    else:
        messages.error(request, "Some problem occurred")
        raise Http404()


class SettlementUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    model = SettlementRow
    fields = (
    'cust_name', 'account_no', 'outstanding', 'totalclosure', 'compromise_amt', 'token_money', 'loan_obj', 'irac')
    exclude = ('loka', 'ro', 'branch', 'pr_waived', 'int_waived', 'unapplied_int', 'rest_amount')
    success_url = reverse_lazy("settlement_list")

    

    def get_context_data(self, **kwargs):
        context = super(SettlementUpdateView, self).get_context_data(**kwargs)
        branchx = Profile.objects.filter(id=self.request.user.id)
        setpk = SettlementRow.objects.filter(id=self.kwargs['pk'])
        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
        if self.request.user.is_authenticated and branchx[0].user == setpk[0].branch.user:
            context['passed'] = True
            context['branch_name']=branchx[0].branch_name
            context['bankid']=bankid[0].bank_name
            
        else:
            context['passed'] = False
        return context

    def get_queryset(self):
        base_qs = super(SettlementUpdateView, self).get_queryset()
        branchx = Profile.objects.filter(id=self.request.user.id)
        setpk = SettlementRow.objects.filter(id=self.kwargs['pk'])
        if (branchx[0].user == setpk[0].branch.user):
            return base_qs.filter(branch=Profile.objects.filter(id=self.request.user.id)[0])
        else:
            # return None
            return base_qs.filter(branch=None)

    def form_valid(self, form):
        if not (form.data['cust_name'] and form.data['account_no'] and form.data['outstanding'] \
                and form.data['totalclosure'] and\
                form.data['compromise_amt'] and\
                form.data['token_money'] and\
             form.data['loan_obj']  and form.data[ 'irac']):
            messages.warning(self.request, "Empty fields not allowed")
            return redirect(reverse_lazy("settlement_list"))

        else:
            form.save()
            messages.success(self.request, "Updated")
            return redirect(reverse_lazy("settlement_list"))
        


    def form_invalid(self, form):
        messages.info(self.request, form.errors)
        return redirect(reverse_lazy("settlement_list"))






def updaterec(request, id):
    mymember = SettlementRow.objects.get(id=id)
    template = loader.get_template('settlementrow_form.html')
    context = {
        'setrow': mymember,
    }
    return HttpResponse(template.render(context, request))


def getladata(request):
    context = {}
    if (request.user.is_superuser):
        raise Http404()
    else:
        profile_user = Profile.objects.filter(Q(user__username__icontains=User.objects.get(id=request.user.id)))
        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        if profile_user:
            context['form'] = LAForm(lokax=lokax)
            context['branch_name']=profile_user[0].branch_name
            context['bankid']=bankid[0]
            context['lokax']=lokax

            return render(request, "ladata.html", context)
        else:
            raise Http404()

def getladata1(request):
    context = {}
    if (request.user.is_superuser):
        raise Http404()
    else:
        profile_user = Profile.objects.filter(Q(user__username__icontains=User.objects.get(id=request.user.id)))
        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        if profile_user:
            context['form'] = LAForm(lokax=lokax)
            context['branch_name']=profile_user[0].branch_name
            context['bankid']=bankid[0]
            context['lokax']=lokax
            return render(request, "ladata1.html", context)
        else:
            raise Http404()


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def settopdf(request,lokax_id):
    context = {}
    QueryDict = request.GET
    predicted = QueryDict.get("lokadalat")
    print('request post is')
    print(predicted)
    print('ello world')
    # qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=Profile.objects.get(id=request.user.id)))
    qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))

    ros = RegionalOffice.objects.filter(branches__user__username=request.user.username)
    bank_id = ros[0].bank_id
    print(bank_id)
    if (request.user.is_authenticated and qs1):

        qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
        branchx = Profile.objects.filter(id=request.user.id)
        # print('Bank id is',bankid)
        # lokax = LokAdalat.objects.all().filter(id=predicted)[0]
        lokax = LokAdalat.objects.all().filter(id=lokax_id).first()

        # print(str(lokax))
        context['contoutstanding'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('outstanding'))
        context['contunapplied_int'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(
            Sum('unapplied_int'))
        context['conttotalclosure'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('totalclosure'))
        context['contcompromise_amt'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(
            Sum('compromise_amt'))
        context['conttoken_money'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('token_money'))
        context['contpr_waived'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('pr_waived'))
        context['contint_waived'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('int_waived'))
        context['contrest_amount'] = SettlementRow.objects.filter(
            branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('rest_amount'))
        context['branch'] = branchx[0].branch_name
        context['object_list'] = qs1
        context['venue'] = lokax.lokadalatvenue
        context['ladate'] = lokax.lokadalatdate
        context['emptyset'] = False
        context['regiono'] = ros[0].ro_name
        context['bankid'] = bank_id
    else:

        context['emptyset'] = True
    # return render(request,"settlements_list2.html",context)
    return  render_to_pdf("loka/summary.html",context)



def getsettlements1(request,lokax_id):
    context = {}
    QueryDict = request.GET
    predicted = QueryDict.get("lokadalat")
    # print('request post is')
    print(predicted)
    # print('ello world')
    # qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=Profile.objects.get(id=request.user.id)))
    qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))

    ros = RegionalOffice.objects.filter(branches__user__username=request.user.username)
    bank_id = ros[0].bank_id
    print(bank_id)
    if (request.user.is_authenticated and qs1):

        qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
        branchx = Profile.objects.filter(id=request.user.id)
        # print('Bank id is',bankid)
        # lokax = LokAdalat.objects.all().filter(id=predicted)[0]
        lokax = LokAdalat.objects.all().filter(id=lokax_id).first()
        # print(str(lokax))
        context['contoutstanding'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('outstanding'))
        context['contunapplied_int'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(
            Sum('unapplied_int'))
        context['conttotalclosure'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('totalclosure'))
        context['contcompromise_amt'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(
            Sum('compromise_amt'))
        context['conttoken_money'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('token_money'))
        context['contpr_waived'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('pr_waived'))
        context['contint_waived'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('int_waived'))
        context['contrest_amount'] = SettlementRow.objects.filter(branch=Profile.objects.get(user__id=request.user.id)).aggregate(Sum('rest_amount'))
        context['branch'] = branchx[0].branch_name
        context['object_list'] = qs1
        context['venue'] = lokax.lokadalatvenue
        context['ladate'] = lokax.lokadalatdate
        context['emptyset'] = False
        context['regiono'] = ros[0].ro_name
        context['bankid'] = bank_id
    else:

        context['emptyset'] = True




    return  render_to_pdf("loka/settled.html",context)






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
        response['Content-Disposition'] = 'attachment; filename="Settlement_Report.pdf"'
        return response
    return JsonResponse({'error': 'Invalid request'}, status=400)
