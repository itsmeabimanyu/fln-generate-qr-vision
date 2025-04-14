from django.shortcuts import redirect
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', lambda request: redirect('generate_create_manual')),
    path('qrvision/create/manual/', views.CreateManualGeneratePageView.as_view(), name='generate_create_manual'),
    path('qrvision/key/create/', views.CreatePrivateKeyView.as_view(), name='key_create'),
    path('qrvision/key/delete/<int:pk>/', views.DeletePrivateKeyView.as_view(), name='key_delete'),
    # path('add-manual', views.GeneratePage2.as_view(), name='GeneratePage2'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

