from django.shortcuts import redirect
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: redirect('invoice_create_manual')),
    path('qrvision/invoice/create/manual/', views.CreateManualInvoiceView.as_view(), name='invoice_create_manual'),
    path('qrvision/invoice/create/delete/<int:pk>/', views.DeleteInvoiceView.as_view(), name='invoice_delete_manual'),
    path('qrvision/key/create/', views.CreatePrivateKeyView.as_view(), name='key_create'),
    path('qrvision/key/delete/<int:pk>/', views.DeletePrivateKeyView.as_view(), name='key_delete'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

