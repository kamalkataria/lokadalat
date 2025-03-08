from django.urls import path

from . import views
from django.views.generic import RedirectView

from .views import ChangePasswordView,LokAdalatAccountListView



urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),  # Point to your favicon


    path("", views.index, name="index"),
    path('add', views.SettlementAddView.as_view(), name="add_settlement"),
    path('loka/', views.getsettlementlist, name="selectsettlements"),
    path('loka/setlist/', views.SettlementListView.as_view(), name="settlement_list"),

    path('loka/setlist/deleteset/<int:id>', views.deleteset, name="deletesettlement"),
    # path('gotohome/', views.SettlementListView.as_view(), name="gotohome"),
    path("siriusisadogstar/", views.register_request, name="register"),
    path("editprofile/", views.BranchEditView.as_view(), name="editprofile"),

    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    path("regbranch/", views.regbranch, name="regbranch"),
    path("settopdf/<int:lokax_id>/", views.settopdf, name="settopdf"),
    path("getsettlements1/<int:lokax_id>/", views.getsettlements1, name="getsettlements1"),

    path("getladata/", views.getladata, name="getladata"),
    path("getladata1/", views.getladata1, name="getladata1"),

    path('loadregions/', views.load_regions, name='ajax_load_regions'),
    path('loka/setlist/update/<int:pk>', views.SettlementUpdateView.as_view(), name='updaterec'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('setcalc/', views.setcalc, name='setcalc'),
    path('generate-pdf/', views.generate_pdf, name='generate_pdf'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('account/', views.get_account_details, name='get_account_details'),
    path("laaccounts/", LokAdalatAccountListView.as_view(), name="account_list"),
    path('upload/success/', views.upload_success, name='upload_success'),
     path('lokadalat/upload/', views.upload_lokadalat_csv, name='upload_lokadalat_csv'),
    path('lokadalat/accounts/', views.view_lokadalat_accounts, name='view_lokadalat_accounts'),

]
