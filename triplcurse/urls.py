from . import views
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('superadmin/', admin.site.urls),
    path('catalog/', RedirectView.as_view(pattern_name='home'), name='catalog-redirect'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)