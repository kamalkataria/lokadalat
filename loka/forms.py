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


class LAForm(forms.Form):
    lokadalat = forms.ModelChoiceField(queryset=LokAdalat.objects.filter(),widget=forms.Select(attrs={'class':'form-control input-sm maxwidth300'}))

    class Meta:
        model = LokAdalat
        fields = ['lokadalat']

    def __init__(self, *args, lokax=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lokax = lokax
        self.fields['lokadalat'].queryset=self.lokax




class NewUserForm(UserCreationForm):
    DIST_CHOICES = (('1', 'Agra'), ('2', 'Aligarh'), ('3', 'Allahabad'), ('4', 'Ambedkar Nagar'),
                    ('5', 'Amethi (Chatrapati Sahuji Mahraj Nagar)'), \
                    ('6', 'Amroha (J.P. Nagar)'), ('7', 'Auraiya'), ('8', 'Azamgarh'), ('9', 'Baghpat'),
                    ('10', 'Bahraich'), \
                    ('11', 'Ballia'), ('12', 'Balrampur'), ('13', 'Banda'), ('14', 'Barabanki'), ('15', 'Bareilly'), \
                    ('16', 'Basti'), ('17', 'Bhadohi'), ('18', 'Bijnor'), ('19', 'Budaun'), ('20', 'Bulandshahr'), \
                    ('21', 'Chandauli'), ('22', 'Chitrakoot'), ('23', 'Deoria'), ('24', 'Etah'), ('25', 'Etawah'),
                    ('26', 'Faizabad'), \
                    ('27', 'Farrukhabad'), ('28', 'Fatehpur'), ('29', 'Firozabad'), ('30', 'Gautam Buddha Nagar'),
                    ('31', 'Ghaziabad'), \
                    ('32', 'Ghazipur'), ('33', 'Gonda'), ('34', 'Gorakhpur'), ('35', 'Hamirpur'),
                    ('36', 'Hapur (Panchsheel Nagar)'),
                    ('37', 'Hardoi'), ('38', 'Hathras'), ('39', 'Jalaun'), ('40', 'Jaunpur'), ('41', 'Jhansi'),
                    ('42', 'Kannauj'), \
                    ('43', 'Kanpur Dehat'), ('44', 'Kanpur Nagar'), ('45', 'Kanshiram Nagar (Kasganj)'),
                    ('46', 'Kaushambi'), \
                    ('47', 'Kushinagar (Padrauna)'), ('48', 'Lakhimpur - Kheri'), ('49', 'Lalitpur'), ('50', 'Lucknow'), \
                    ('51', 'Maharajganj'), ('52', 'Mahoba'), ('53', 'Mainpuri'), ('54', 'Mathura'), ('55', 'Mau'), \
                    ('56', 'Meerut'), ('57', 'Mirzapur'), ('58', 'Moradabad'), ('59', 'Muzaffarnagar'),
                    ('60', 'Pilibhit'), \
                    ('61', 'Pratapgarh'), ('62', 'RaeBareli'), ('63', 'Rampur'), ('64', 'Saharanpur'),
                    ('65', 'Sambhal (Bhim Nagar)'), \
                    ('66', 'Sant Kabir Nagar'), ('67', 'Shahjahanpur'), ('68', 'Shamali (Prabuddh Nagar)'), \
                    ('69', 'Shravasti'), ('70', 'Siddharth Nagar'), \
                    ('71', 'Sitapur'), ('72', 'Sonbhadra'), ('73', 'Sultanpur'), \
                    ('74', 'Unnao'), ('75', 'Varanasi'))
    email = forms.EmailField(required=True)
    branch_alpha = forms.CharField(max_length=100)
    branch_name = forms.CharField(max_length=50)
    branch_addr = forms.CharField(max_length=500)
    branch_ifsc = forms.CharField(max_length=20)
    bank= forms.ModelChoiceField(Bank.objects.all())
    branch_district=forms.ChoiceField(choices=DIST_CHOICES)
    branch_state=forms.CharField(max_length=50)
    qs = RegionalOffice.objects.all()
    ro = forms.ModelChoiceField(qs)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2","branch_alpha","branch_name","branch_addr","branch_ifsc","bank","ro",'branch_district','branch_state')




    def save(self, commit=True):
        user = super(NewUserForm, self).save()
        user.email = self.cleaned_data['email']
        user.profile.ro=self.cleaned_data['ro']
        user.profile.bank=self.cleaned_data['bank']
        user.profile.branch_district = self.cleaned_data['branch_district']
        user.profile.branch_state = self.cleaned_data['branch_state']

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
                # print(self.fields['ro'].queryset )

            except (ValueError, TypeError):
                print('ERRRRRRRRRRRRRRR')
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['ro'].queryset = self.instance.bank.regionaloffice_set.order_by('ro_name')

        self.fields['password1'].help_text = ''


class SettlementForm(forms.ModelForm):
    # qs2=LokAdalat.objects.all()
    # qs3=User.objects.all()
    # loka=forms.ModelChoiceField(qs2)
    # branch=forms.ModelChoiceField(qs3)
    ro=forms.ModelChoiceField(None)

    class Meta:
        model=SettlementRow

        fields=['loka','ro','branch','account_no','cust_name','totalclosure','outstanding','compromise_amt','token_money','loan_obj','irac']
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
        self.loka=qs
        self.branch=kwargs.pop('branch',None)
        self.roset=kwargs.pop('ros',None)
        rosetx=self.roset

        self.myros=RegionalOffice.objects.filter(id=self.roset.id)



        self.maker = Profile.objects.filter(id=self.branch)
        super(SettlementForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control input-sm maxwidth300'

        self.fields['loka'].queryset=self.loka
        self.fields['branch'].queryset=self.maker
        self.fields['ro'].queryset=self.myros
        self.fields['account_no'].label = ""
        self.fields['loka'].label = ""
        self.fields['branch'].label = ""
        self.fields['cust_name'].label = ""
        self.fields['outstanding'].label = ""
        self.fields['totalclosure'].label = ""
        self.fields['compromise_amt'].label = ""
        self.fields['token_money'].label = ""
        self.fields['loan_obj'].label = ""
        self.fields['ro'].label = ""
        self.fields['irac'].label = ""



SettlementFormset=forms.modelformset_factory(SettlementRow,SettlementForm)

class SettlementFormset1(SettlementFormset):

    def __init__(self, *args, **kwargs):
        self.loka = kwargs.pop('loka')
        self.branch = kwargs.pop('branch')
        self.roset = kwargs.pop('ros')


        super(SettlementFormset, self).__init__(*args, **kwargs)


    def _construct_form(self, *args, **kwargs):
        kwargs['loka'] = self.loka
        kwargs['branch'] = self.branch
        kwargs['ros']=self.roset

        return super(SettlementFormset, self)._construct_form(*args, **kwargs)


class LokadalatForm(ModelForm):
    class Meta:
        model   = LokAdalat
        fields  = ['lokadalatvenue','lokadalatdate']





