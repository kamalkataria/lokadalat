from django.contrib import messages
from django.contrib.auth import authenticate, logout  # add this
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, UpdateView
from .forms import NewUserForm, LAForm
from .forms import SettlementForm, SettlementFormset1
from .models import SettlementRow, Profile, RegionalOffice, Bank, LokAdalat
from .utils import render_to_pdf
from django.http import Http404


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


def load_regions(request):
    region_id = request.GET.get('bank')
    print('loading regions')
    regions = RegionalOffice.objects.filter(bank_id_id=region_id).order_by('ro_name')
    return render(request, 'region_dropdown_list_options.html', {'regions': regions})


def regbranch(request):
    return HttpResponse('At REGISTRATION OF BRANCH')


def index(request):
    return redirect("settlement_list")


def gotohome(request):
    print('go man!!!!!!!')
    return redirect('settlement_list')


from django.contrib.auth.mixins import LoginRequiredMixin


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
            return qs.filter(branch=Profile.objects.get(user__id=self.request.user.id))

        else:
            print('User is not authenticated')
            return qs.filter(branch=None)

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:

            context = super(SettlementListView, self).get_context_data(**kwargs)
            if (self.request.user.is_superuser):
                context['userissu'] = True
            else:
                context['userissu'] = False

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


class SettlementAddView(LoginRequiredMixin, TemplateView):
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
            formset = SettlementFormset1(ros=ros, loka=lokax, branch=self.request.user.id,
                                         queryset=SettlementRow.objects.none(),
                                         initial=[{'branch': self.request.user.id, 'loka': lokax[0].id,
                                                   'ro': RegionalOffice.objects.filter(id=ros.id)[0].id}])

            return self.render_to_response({'settlement_formset': formset})

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
            formset.save()
            messages.success(self.request, "Record added successfully")
            return redirect(reverse_lazy("settlement_list"))


        else:

            messages.error(self.request, formset.errors)
            return redirect(reverse_lazy("add_settlement"))

        


import django_tables2 as tables


class SimpleTable(tables.Table):
    class Meta:
        model = SettlementRow
        exclude = ('id', 'loka',)


def deleteset(request, id):
    branchx = Profile.objects.filter(id=request.user.id)
    # print(request.POST,'getttttttt')
    setpk = SettlementRow.objects.filter(id=id)
    if request.user.is_authenticated and branchx[0].user == setpk[0].branch.user:
        # print('Trueeeeeeee')
        settlerow = SettlementRow.objects.get(id=id)
        settlerow.delete()
        return redirect("settlement_list")
    else:
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
        if self.request.user.is_authenticated and branchx[0].user == setpk[0].branch.user:
            context['passed'] = True
            print('yep passed')
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
        context = self.get_context_data(form=form)
        formset = context['formset']
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            messages.success(self.request, "Record Updated Suceesfully successfully")
            return response

        else:
            return super().form_invalid(form)
            messages.error(self.request, formset.errors)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = journal_entry_formset(self.request.POST, instance=self.object)
        print("form:", form.is_valid())  # True
        print("formset:", formset.is_valid())  # False
        print(formset.non_form_errors())  # No Entry
        print(formset.errors)  # {'id': ['This field is required.']}

        if (form.is_valid() and formset.is_valid()):
            return self.form_valid(form)

        else:
            return self.form_invalid(form)


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
            return render(request, "ladata.html", context)
        else:
            raise Http404()


def settopdf(request):
    context = {}
    QueryDict = request.GET
    predicted = QueryDict.get("lokadalat")
    print('request post is')
    print(predicted)
    print('ello world')
    # qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=Profile.objects.get(id=request.user.id)))
    qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))

    ros = RegionalOffice.objects.filter(branches__branch_alpha=request.user.username)
    bank_id = ros[0].bank_id
    print(bank_id)
    if (request.user.is_authenticated and qs1):

        qs1 = SettlementRow.objects.filter(branch=Profile.objects.get(id=request.user.id))
        branchx = Profile.objects.filter(id=request.user.id)
        # print('Bank id is',bankid)
        lokax = LokAdalat.objects.all().filter(id=predicted)[0]
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

    pdf = render_to_pdf('settlements_list2.html', context)
    return HttpResponse(pdf, content_type='application/pdf')
