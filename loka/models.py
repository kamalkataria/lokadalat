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




class Bank(models.Model):
    bank_id=models.ForeignKey(User,on_delete=models.CASCADE)
    bank_name=models.CharField(max_length=50,default="",blank=True, null=True)
    bank_ho_address=models.CharField(max_length=200,default="",blank=True, null=True)
    def __str__(self):
        return f"{self.bank_name}"



class RegionalOffice(models.Model):
    bank_id=models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="regions",null=True,blank=True)
    ro_name=models.CharField(max_length=100)
    ro_addr=models.CharField(max_length=500)
    def __str__(self):
        return f"{self.ro_name}"

class LokAdalat(models.Model):
    username=models.ForeignKey(User,on_delete=models.CASCADE,related_name="userx")
    bank=models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="banx")
    # ro=models.ForeignKey(RegionalOffice,on_delete=models.CASCADE,related_name="lokro")
    lokadalatvenue=models.CharField(max_length=50)
    lokadalatdate=models.DateField()

    def __str__(self):
        x=self.lokadalatdate.strftime("%d %B %Y")
        return f"{self.lokadalatvenue,x }"

class Profile(models.Model):
    DIST_CHOICES=(('1', 'Agra'), ('2', 'Aligarh'), ('3', 'Allahabad'), ('4', 'Ambedkar Nagar'), ('5', 'Amethi (Chatrapati Sahuji Mahraj Nagar)'), \
                  ('6', 'Amroha (J.P. Nagar)'), ('7', 'Auraiya'), ('8', 'Azamgarh'), ('9', 'Baghpat'), ('10', 'Bahraich'), \
                  ('11', 'Ballia'), ('12', 'Balrampur'), ('13', 'Banda'), ('14', 'Barabanki'), ('15', 'Bareilly'),\
                  ('16', 'Basti'), ('17', 'Bhadohi'), ('18', 'Bijnor'), ('19', 'Budaun'), ('20', 'Bulandshahr'), \
                  ('21', 'Chandauli'), ('22', 'Chitrakoot'), ('23', 'Deoria'), ('24', 'Etah'), ('25', 'Etawah'), ('26', 'Faizabad'), \
                  ('27', 'Farrukhabad'), ('28', 'Fatehpur'), ('29', 'Firozabad'), ('30', 'Gautam Buddha Nagar'), ('31', 'Ghaziabad'),\
                  ('32', 'Ghazipur'), ('33', 'Gonda'), ('34', 'Gorakhpur'), ('35', 'Hamirpur'), ('36', 'Hapur (Panchsheel Nagar)'),
                  ('37', 'Hardoi'), ('38', 'Hathras'), ('39', 'Jalaun'), ('40', 'Jaunpur'), ('41', 'Jhansi'), ('42', 'Kannauj'), \
                  ('43', 'Kanpur Dehat'), ('44', 'Kanpur Nagar'), ('45', 'Kanshiram Nagar (Kasganj)'), ('46', 'Kaushambi'), \
                  ('47', 'Kushinagar (Padrauna)'), ('48', 'Lakhimpur - Kheri'), ('49', 'Lalitpur'), ('50', 'Lucknow'), \
                  ('51', 'Maharajganj'), ('52', 'Mahoba'), ('53', 'Mainpuri'), ('54', 'Mathura'), ('55', 'Mau'), \
                  ('56', 'Meerut'), ('57', 'Mirzapur'), ('58', 'Moradabad'), ('59', 'Muzaffarnagar'), ('60', 'Pilibhit'), \
                  ('61', 'Pratapgarh'), ('62', 'RaeBareli'), ('63', 'Rampur'), ('64', 'Saharanpur'), ('65', 'Sambhal (Bhim Nagar)'),\
                  ('66', 'Sant Kabir Nagar'), ('67', 'Shahjahanpur'), ('68', 'Shamali (Prabuddh Nagar)'),\
                  ('69', 'Shravasti'), ('70', 'Siddharth Nagar'),\
                  ('71', 'Sitapur'), ('72', 'Sonbhadra'), ('73', 'Sultanpur'), \
                  ('74', 'Unnao'), ('75', 'Varanasi'))
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True)
    ro=models.ForeignKey(RegionalOffice,on_delete=models.CASCADE,related_name='branches',null=True,blank=True)
    branch_alpha=models.CharField(max_length=100)
    branch_name=models.CharField(max_length=50)
    branch_addr=models.CharField(max_length=500)
    branch_ifsc=models.CharField(max_length=20)
    branch_district=models.CharField(max_length=5,choices=DIST_CHOICES,default='25')
    branch_state=models.CharField(max_length=50,default="Uttar Pradesh")

    def __str__(self):
        return f"{self.branch_alpha,self.branch_name}"

    def save(self, *args, **kwargs):
        super().save()



class SettlementRow(models.Model):
    loka=models.ForeignKey(LokAdalat,on_delete=models.CASCADE,related_name="setrow")
    branch = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True,related_name='branches')
    ro=models.ForeignKey(RegionalOffice,on_delete=models.CASCADE,blank=True,null=True)
    account_no=models.IntegerField(blank=True)
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
        self.unapplied_int= self.totalclosure - self.outstanding
        self.rest_amount=self.compromise_amt-self.token_money

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
