from email.policy import default

from django.contrib.auth.models import User
from django.db import models
from django.db.models import ManyToManyField, ForeignKey, AutoField
from django.db.models.fields import return_None
from django.utils.timezone import now
from django.utils.datetime_safe import datetime
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from pkg_resources import require



class LokAdalatAccount(models.Model):
    branch = models.CharField(max_length=255)
    account_no = models.CharField(max_length=50, unique=True)
    scheme_code = models.CharField(max_length=50)
    account_name = models.CharField(max_length=255)
    sanction_date = models.DateField(null=True, blank=True)
    sanction_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    address = models.TextField()
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2)
    demand_amount = models.DecimalField(max_digits=15, decimal_places=2)
    account_npa_date = models.DateField(null=True, blank=True)
    category_as_on_2024 = models.CharField(max_length=100)
    provision_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    mobile_no = models.CharField(max_length=15, null=True, blank=True)
    npa_expenses = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_dues = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.account_no} - {self.account_name}"

class ENRSAccounts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.CharField(max_length=255)
    account_no = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=20)
    acc_sanction_date = models.DateField(null=True,blank=True)
    total_dues = models.DecimalField(max_digits=10, decimal_places=2)
    outstanding_as_on = models.DecimalField(max_digits=10, decimal_places=2)
    min_comp_amt = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    minimum_compromise_amt = models.DecimalField(max_digits=10, decimal_places=2)
    npa_expenses = models.DecimalField(max_digits=10, decimal_places=2)



class Bank(models.Model):
    # bank_id=models.ForeignKey(User,on_delete=models.CASCADE)
    bank_name=models.CharField(max_length=50,default="",blank=True, null=True)
    bank_ho_address=models.CharField(max_length=200,default="",blank=True, null=True)
    def __str__(self):
        return f"{self.bank_name}"
#
# class SuperBanker(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="superbanker")
#     bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="superbankers", null=True, blank=True)
#     is_unrestricted = models.BooleanField(default=False)  # Flag for unrestricted access
#
#     def __str__(self):
#         return f"{self.user.username} - {self.bank.bank_name if self.bank else 'All Banks'}"

class SuperBankerAssignment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='superbanker_profile')
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='superbankers')

    def __str__(self):
        return f"{self.user.username} - {self.bank.bank_name}"

class RegionalOffice(models.Model):
    bank_id=models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="regions",null=True,blank=True)
    ro_name=models.CharField(max_length=100)
    ro_addr=models.CharField(max_length=500)
    def __str__(self):
        return f"{self.ro_name,self.bank_id.bank_name}"

class Branch(models.Model):
    DIST_CHOICES = (
        ('1', 'Agra'), ('2', 'Aligarh'), ('3', 'Allahabad'), ('4', 'Ambedkar Nagar'),
        ('5', 'Amethi (Chatrapati Sahuji Mahraj Nagar)'), ('6', 'Amroha (J.P. Nagar)'),
        ('7', 'Auraiya'), ('8', 'Azamgarh'), ('9', 'Baghpat'), ('10', 'Bahraich'),
        ('11', 'Ballia'), ('12', 'Balrampur'), ('13', 'Banda'), ('14', 'Barabanki'),
        ('15', 'Bareilly'), ('16', 'Basti'), ('17', 'Bhadohi'), ('18', 'Bijnor'),
        ('19', 'Budaun'), ('20', 'Bulandshahr'), ('21', 'Chandauli'), ('22', 'Chitrakoot'),
        ('23', 'Deoria'), ('24', 'Etah'), ('25', 'Etawah'), ('26', 'Faizabad'),
        ('27', 'Farrukhabad'), ('28', 'Fatehpur'), ('29', 'Firozabad'), ('30', 'Gautam Buddha Nagar'),
        ('31', 'Ghaziabad'), ('32', 'Ghazipur'), ('33', 'Gonda'), ('34', 'Gorakhpur'),
        ('35', 'Hamirpur'), ('36', 'Hapur (Panchsheel Nagar)'), ('37', 'Hardoi'),
        ('38', 'Hathras'), ('39', 'Jalaun'), ('40', 'Jaunpur'), ('41', 'Jhansi'),
        ('42', 'Kannauj'), ('43', 'Kanpur Dehat'), ('44', 'Kanpur Nagar'),
        ('45', 'Kanshiram Nagar (Kasganj)'), ('46', 'Kaushambi'), ('47', 'Kushinagar (Padrauna)'),
        ('48', 'Lakhimpur - Kheri'), ('49', 'Lalitpur'), ('50', 'Lucknow'),
        ('51', 'Maharajganj'), ('52', 'Mahoba'), ('53', 'Mainpuri'), ('54', 'Mathura'),
        ('55', 'Mau'), ('56', 'Meerut'), ('57', 'Mirzapur'), ('58', 'Moradabad'),
        ('59', 'Muzaffarnagar'), ('60', 'Pilibhit'), ('61', 'Pratapgarh'), ('62', 'RaeBareli'),
        ('63', 'Rampur'), ('64', 'Saharanpur'), ('65', 'Sambhal (Bhim Nagar)'),
        ('66', 'Sant Kabir Nagar'), ('67', 'Shahjahanpur'), ('68', 'Shamali (Prabuddh Nagar)'),
        ('69', 'Shravasti'), ('70', 'Siddharth Nagar'), ('71', 'Sitapur'), ('72', 'Sonbhadra'),
        ('73', 'Sultanpur'), ('74', 'Unnao'), ('75', 'Varanasi')
    )
    regional_office = models.ForeignKey(RegionalOffice, on_delete=models.CASCADE, related_name="branches")
    branch_alpha = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=50)
    branch_addr = models.CharField(max_length=500)
    branch_ifsc = models.CharField(max_length=20)
    branch_district = models.CharField(max_length=5, choices=DIST_CHOICES, default='25')
    branch_state = models.CharField(max_length=50, default="Uttar Pradesh")

    def __str__(self):
        return f"{self.regional_office.bank_id.bank_name},Branch - {self.branch_name},District-{dict(self.DIST_CHOICES).get(self.branch_district, 'Unknown District')}"

class LokAdalat(models.Model):
    # username=models.ForeignKey(User,on_delete=models.CASCADE,related_name="userx")
    bank=models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="banx")
    # ro=models.ForeignKey(RegionalOffice,on_delete=models.CASCADE,related_name="lokro")
    lokadalatvenue=models.CharField(max_length=50)
    lokadalatdate=models.DateField()

    def __str__(self):
        x=self.lokadalatdate.strftime("%d %B %Y")
        return f"{self.bank.bank_name,self.lokadalatvenue,x }"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')

    def __str__(self):
        return f"{self.user.username} - {self.branch.branch_name if self.branch else 'No Branch'}"

    def get_ro(self):
        return self.branch.regional_office if self.branch else None

    def get_bank(self):
        if self.branch:
            if self.branch.regional_office:
                print(
                    f"User: {self.user.username}, Branch: {self.branch}, RO: {self.branch.regional_office}, Bank: {self.branch.regional_office.bank_id}")
                return self.branch.regional_office.bank_id
            else:
                print(f"User: {self.user.username} has a branch but no regional office.")
                return None
        print(f"User: {self.user.username} has no branch.")
        return None
        # return self.branch.regional_office.bank_id if self.branch and self.branch.regional_office else None

    def get_district(self):
        return self.branch.branch_district if self.branch else "No Branch Assigned"


from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
#
# class CustomUser(AbstractUser):
#     is_superbanker = models.BooleanField(default=False)  # ✅ This replaces SuperBanker model
#     bank = models.ForeignKey(
#         "Bank",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="bank_users"  # ✅ Use a unique related_name to avoid conflict
#     )
#
#     groups = models.ManyToManyField("auth.Group", related_name="custom_users_groups", blank=True)
#     user_permissions = models.ManyToManyField("auth.Permission", related_name="custom_users_permissions", blank=True)
#
#     def __str__(self):
#         return self.username

class SettlementRow(models.Model):
    loka=models.ForeignKey(LokAdalat,on_delete=models.CASCADE,related_name="setrow")
    branch = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True,related_name='branchesset')
    ro=models.ForeignKey(RegionalOffice,on_delete=models.CASCADE,blank=True,null=True)
    account_no=models.CharField(blank=True,max_length=20)
    cust_name=models.CharField(max_length=50)
    outstanding=models.IntegerField(blank=True)
    totalclosure=models.IntegerField(blank=True)
    compromise_amt=models.IntegerField(blank=True)
    token_money=models.IntegerField(blank=True)
    loan_obj=models.CharField(max_length=20)
    irac=models.CharField(max_length=10)
    pr_waived=models.IntegerField(blank=True)
    int_waived=models.IntegerField(blank=True)
    rest_amount=models.IntegerField(blank=True)
    unapplied_int=models.IntegerField(blank=True)


    def save(self,*args,**kwargs):
        self.unapplied_int = (self.totalclosure or 0) - (self.outstanding or 0)
        self.rest_amount = (self.compromise_amt or 0) - (self.token_money or 0)

        if self.compromise_amt>self.outstanding:
            self.pr_waived=0
            self.int_waived=self.totalclosure-self.compromise_amt

        else:
            self.pr_waived=self.outstanding-self.compromise_amt
            self.int_waived=self.unapplied_int
        print(self.unapplied_int)
        print(self.compromise_amt)
        print(self.pr_waived)
        print(self.int_waived)


        super().save()

    def __str__(self):
        return f"{self.account_no,self.branch,self.cust_name}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        print('yes user is creaed')
        profile=Profile.objects.create(user=instance)
        profile.save()




@receiver(post_save, sender=SuperBankerAssignment)
def add_to_superbanker_group(sender, instance, created, **kwargs):
    if created:
        superbanker_group, _ = Group.objects.get_or_create(name="SuperBanker")
        instance.user.groups.add(superbanker_group)
