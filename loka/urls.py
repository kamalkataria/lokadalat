from django.urls import path

from . import views

urlpatterns = [

    path("", views.index, name="index"),
    path('add', views.SettlementAddView.as_view(), name="add_settlement"),
    path('loka/', views.SettlementListView.as_view(), name="settlement_list"),
    path('loka/deleteset/<int:id>', views.deleteset, name="deletesettlement"),
    # path('gotohome/', views.SettlementListView.as_view(), name="gotohome"),
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    path("regbranch/", views.regbranch, name="regbranch"),
    path("^settopdf/", views.settopdf, name="settopdf"),
    path("getladata/", views.getladata, name="getladata"),
    path('loadregions/', views.load_regions, name='ajax_load_regions'),
    path('loka/update/<int:pk>', views.SettlementUpdateView.as_view(), name='updaterec')

]