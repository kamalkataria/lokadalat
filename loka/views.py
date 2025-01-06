from django.contrib import messages
from django.contrib.auth import authenticate, logout  # add this
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, UpdateView
from .forms import NewUserForm
from .forms import SettlementForm, SettlementFormset1
from .models import SettlementRow, Profile, RegionalOffice, Bank, LokAdalat
from .utils import render_to_pdf


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


class SettlementListView(ListView):
    model = SettlementRow
    template_name = "settlement_list.html"

    def get_queryset(self, **kwargs):
        if self.request.user.is_authenticated:
            qs = super().get_queryset(**kwargs)

            return qs.filter(branch=self.request.user)

        else:
            print('User is not authenticated')

            return {'aunthenticated': False}

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:

            context = super(SettlementListView, self).get_context_data(**kwargs)
            context['contoutstanding'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('outstanding'))
            context['contunapplied_int'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('unapplied_int'))
            context['conttotalclosure'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('totalclosure'))
            context['contcompromise_amt'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('compromise_amt'))
            context['conttoken_money'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('token_money'))
            context['contpr_waived'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('pr_waived'))
            context['contint_waived'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('int_waived'))
            context['contrest_amount'] = SettlementRow.objects.filter(branch=self.request.user).aggregate(
                Sum('rest_amount'))
            context['authed'] = True
            return context
        else:
            context = super(SettlementListView, self).get_context_data(**kwargs)

            context['authed'] = False
            return context




class SettlementAddView(TemplateView):
    template_name = "add_settlement.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))
        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        qs = SettlementRow.objects.filter(loka__username=profile_user[0].bank.bank_id)
        print("QML is", str(qs))
        kwargs['queryset'] = lokax
        return kwargs

    def get(self, *args, **kwargs):

        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        print(profile_user[0].bank.bank_id)

        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))

        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        qs = SettlementRow.objects.filter(loka__username=profile_user[0].bank.bank_id)






        formset = SettlementFormset1(loka=lokax, branch=self.request.user.id, queryset=SettlementRow.objects.none(),
                                     initial=[{'branch': self.request.user.id, 'loka': lokax[0].id}])

        return self.render_to_response({'settlement_formset': formset})

    def post(self, *args, **kwargs):
        profile_user = Profile.objects.filter(Q(user__username__icontains=self.request.user.username))
        print(profile_user[0].bank.bank_id)

        bankid = Bank.objects.filter(Q(bank_id__username__icontains=profile_user[0].bank.bank_id))

        lokax = LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by(
            'lokadalatdate')
        formset = SettlementFormset1(loka=lokax, branch=self.request.user.id, data=self.request.POST)
        if (formset.is_valid()):
            formset.save()
            print('forset is vallid')


        else:

            print('form set is invalid ', formset.errors)

        return redirect(reverse_lazy("settlement_list"))


import django_tables2 as tables


class SimpleTable(tables.Table):
    class Meta:
        model = SettlementRow
        exclude = ('id', 'loka',)


def deleteset(request, id):
    settlerow = SettlementRow.objects.get(id=id)
    settlerow.delete()

    return redirect("settlement_list")


class SettlementUpdateView(UpdateView):
    model = SettlementRow

    form_class = SettlementForm

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None


    success_url = reverse_lazy("settlement_list")


def updaterec(request, id):
    mymember = SettlementRow.objects.get(id=id)
    template = loader.get_template('updaterec.html')
    context = {
        'setrow': mymember,
    }
    return HttpResponse(template.render(context, request))


def settopdf(request):
    context = {}
    qs1 = SettlementRow.objects.filter(branch=request.user)
    ros = RegionalOffice.objects.filter(branches__branch_alpha=request.user.username)
    bank_id = ros[0].bank_id
    print(bank_id)
    if (request.user.is_authenticated and qs1):

        qs1 = SettlementRow.objects.filter(branch=request.user)
        branchx = Profile.objects.filter(user=qs1[0].branch)
        bankid = Bank.objects.filter(Q(bank_id__username__icontains='bupb'))
        lokax = \
        LokAdalat.objects.all().filter(Q(username__username__icontains=bankid[0].bank_id)).order_by('lokadalatdate')[0]
        context['contoutstanding'] = SettlementRow.objects.filter(branch=request.user).aggregate(Sum('outstanding'))
        context['contunapplied_int'] = SettlementRow.objects.filter(branch=request.user).aggregate(
            Sum('unapplied_int'))
        context['conttotalclosure'] = SettlementRow.objects.filter(branch=request.user).aggregate(Sum('totalclosure'))
        context['contcompromise_amt'] = SettlementRow.objects.filter(branch=request.user).aggregate(
            Sum('compromise_amt'))
        context['conttoken_money'] = SettlementRow.objects.filter(branch=request.user).aggregate(Sum('token_money'))
        context['contpr_waived'] = SettlementRow.objects.filter(branch=request.user).aggregate(Sum('pr_waived'))
        context['contint_waived'] = SettlementRow.objects.filter(branch=request.user).aggregate(Sum('int_waived'))
        context['contrest_amount'] = SettlementRow.objects.filter(branch=request.user).aggregate(Sum('rest_amount'))
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

