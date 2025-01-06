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
class LokAdalat(models.Model):
    username=models.ForeignKey(User,on_delete=models.CASCADE,related_name="userx")
    bank=models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="banx")
    lokadalatvenue=models.CharField(max_length=50)
    lokadalatdate=models.DateField()

    def __str__(self):
        x=self.lokadalatdate.strftime("%d %B %Y")
        return f"{self.lokadalatvenue,x }"

class SettlementRow(models.Model):
    loka=models.ForeignKey(LokAdalat,on_delete=models.CASCADE,related_name="setrow")
    branch = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,related_name='branches')
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


class RegionalOffice(models.Model):
    bank_id=models.ForeignKey(Bank,on_delete=models.CASCADE,related_name="regions",null=True,blank=True)
    ro_name=models.CharField(max_length=100)
    ro_addr=models.CharField(max_length=500)
    def __str__(self):
        return f"{self.ro_name}"

class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, null=True)
    ro=models.ForeignKey(RegionalOffice,on_delete=models.CASCADE,related_name='branches',null=True,blank=True)
    branch_alpha=models.CharField(max_length=100)
    branch_name=models.CharField(max_length=50)
    branch_addr=models.CharField(max_length=500)
    branch_ifsc=models.CharField(max_length=20)

    def __str__(self):
        return f"{self.branch_alpha,self.branch_name}"

    def save(self, *args, **kwargs):
        super().save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    user = instance
    if created:
        print('yes user is creaed')
        profile=Profile.objects.create(user=instance)
        profile.save()
