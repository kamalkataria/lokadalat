from django.urls import path

from . import views
from .views import ChangePasswordView


urlpatterns = [

    path("", views.index, name="index"),
    path('add', views.SettlementAddView.as_view(), name="add_settlement"),
    path('loka/', views.getsettlementlist, name="selectsettlements"),
    path('loka/setlist/', views.SettlementListView.as_view(), name="settlement_list"),
    path('loka/setlist/deleteset/<int:id>', views.deleteset, name="deletesettlement"),
    # path('gotohome/', views.SettlementListView.as_view(), name="gotohome"),
    path("siriusisadogstar/", views.register_request, name="register"),
    path("editprofile/", views.UserEditView.as_view(), name="editprofile"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    path("regbranch/", views.regbranch, name="regbranch"),
    path("settopdf/", views.settopdf, name="settopdf"),
    path("getsettlements1/", views.getsettlements1, name="getsettlements1"),
    path("getladata/", views.getladata, name="getladata"),
    path("getladata1/", views.getladata1, name="getladata1"),
    path("getladata/", views.getladata, name="getladata"),
    path('loadregions/', views.load_regions, name='ajax_load_regions'),
    path('loka/setlist/update/<int:pk>', views.SettlementUpdateView.as_view(), name='updaterec'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('setcalc/', views.setcalc, name='setcalc'),
    path('generate-pdf/', views.generate_pdf, name='generate_pdf'),
]
