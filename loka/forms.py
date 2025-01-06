from dataclasses import fields

from django import forms
from django.forms import ModelForm
from django.views.generic import ListView

from loka.models import SettlementRow, Profile, RegionalOffice,LokAdalat
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Bank,RegionalOffice,Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model=Profile
        fields='__all__'


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    branch_alpha = forms.CharField(max_length=100)
    branch_name = forms.CharField(max_length=50)
    branch_addr = forms.CharField(max_length=500)
    branch_ifsc = forms.CharField(max_length=20)
    bank= forms.ModelChoiceField(Bank.objects.all())
    qs = RegionalOffice.objects.all()
    ro = forms.ModelChoiceField(qs)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2","branch_alpha","branch_name","branch_addr","branch_ifsc","bank","ro")




    def save(self, commit=True):
        user = super(NewUserForm, self).save()
        user.email = self.cleaned_data['email']
        user.profile.ro=self.cleaned_data['ro']
        user.profile.bank=self.cleaned_data['bank']

        user.save()
        if commit:
            user.save()

        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ro'].queryset = RegionalOffice.objects.none()

        if 'bank' in self.data:
            try:
                print('okay bank is there')
                bank_id = int(self.data.get('bank'))
                self.fields['ro'].queryset = RegionalOffice.objects.filter(bank_id=bank_id).order_by('ro_name')
                print(self.fields['ro'].queryset )

            except (ValueError, TypeError):
                print('ERRRRRRRRRRRRRRR')
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['ro'].queryset = self.instance.bank.regionaloffice_set.order_by('ro_name')

        self.fields['password1'].help_text = ''


class SettlementForm(forms.ModelForm):
    loka=forms.ModelChoiceField(None)
    branch=forms.ModelChoiceField(None)

    class Meta:
        model=SettlementRow

        fields=['loka','branch','account_no','cust_name','totalclosure','outstanding','compromise_amt','token_money','loan_obj','irac']
        widgets = {
            'account_no': forms.TextInput(attrs={'placeholder': 'Account No'}),
            'cust_name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'totalclosure': forms.TextInput(attrs={'placeholder': 'Total closure'}),
            'outstanding': forms.TextInput(attrs={'placeholder': 'Outstanding'}),
            'compromise_amt': forms.TextInput(attrs={'placeholder': 'Compromise Amount'}),
            'token_money': forms.TextInput(attrs={'placeholder': 'Token Money'}),
            'loan_obj': forms.TextInput(attrs={'placeholder': 'Loan Obj'}),
            'irac': forms.TextInput(attrs={'placeholder': 'IRAC'}),

        }
        __name__ = 'SettlementForm'




    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('loka', None)
        print('atpcell', qs)
        self.loka=qs
        self.branch=kwargs.pop('branch',None)
        print('branch is',self.branch)

        self.maker = User.objects.filter(id=self.branch)
        super(SettlementForm, self).__init__(*args, **kwargs)
        self.fields['loka'].queryset=self.loka
        self.fields['branch'].queryset=self.maker
        self.fields['account_no'].label = ""
        self.fields['loka'].label = ""
        self.fields['branch'].label = ""
        self.fields['cust_name'].label = ""
        self.fields['outstanding'].label = ""
        self.fields['totalclosure'].label = ""
        self.fields['compromise_amt'].label = ""
        self.fields['token_money'].label = ""
        self.fields['loan_obj'].label = ""
        self.fields['irac'].label = ""











        print('printing kwargspop')
        print(qs)









SettlementFormset=forms.modelformset_factory(SettlementRow,SettlementForm)

class SettlementFormset1(SettlementFormset):

    def __init__(self, *args, **kwargs):
        self.loka = kwargs.pop('loka')
        self.branch = kwargs.pop('branch')

        super(SettlementFormset, self).__init__(*args, **kwargs)


    def _construct_form(self, *args, **kwargs):
        kwargs['loka'] = self.loka
        kwargs['branch'] = self.branch

        return super(SettlementFormset, self)._construct_form(*args, **kwargs)


class LokadalatForm(ModelForm):
    class Meta:
        model   = LokAdalat
        fields  = ['lokadalatvenue','lokadalatdate']





