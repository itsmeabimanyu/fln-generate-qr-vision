from django.shortcuts import redirect
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

handler404 = views.Template404View.as_view()

urlpatterns = [
    path('403/', views.Template403View.as_view(), name='403_view'),
    # Chapter: Login/Logout
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # Register
    # path('register/', views.RegisterAccount.as_view(), name='register'), # *Untuk testing non ldap (disable saat produksi)
    path('', lambda request: redirect('invoice_create_manual')),
    path('qrvision/invoice/create/manual/', views.CreateManualInvoiceView.as_view(), name='invoice_create_manual'),
    path('qrvision/invoice/create/delete/<int:pk>/', views.DeleteInvoiceView.as_view(), name='invoice_delete_manual'),
    path('qrvision/invoice/key/create/', views.CreatePrivateKeyView.as_view(), name='key_create'),
    path('qrvision/invoice/key/delete/<int:pk>/', views.DeletePrivateKeyView.as_view(), name='key_delete'),

    path('account/view/', views.AccountListView.as_view(), name='account_list'),
    path('account/register/<int:pk>/', views.RegisterMarkStatusView.as_view(), name='account_mark_register'),
    path('account/superuser/<int:pk>/', views.SuperuserMarkStatusView.as_view(), name='account_mark_superuser'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

