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
    path('logout/', views.user_logout, name='logout'),
    path('applications/', views.user_applications, name='user_applications'),
    path('applications/create/', views.create_application, name='create_application'),
    path('applications/', views.user_applications, name='user_applications'),
    path('applications/create/', views.create_application, name='create_application'),
    path('applications/delete/<int:app_id>/', views.delete_application, name='delete_application'),
    path('superadmin/', views.admin_dashboard, name='admin_dashboard'),
    path('superadmin/application/<int:app_id>/update/', views.update_application_status, name='update_application_status'),
    path('superadmin/categories/manage/', views.manage_categories, name='manage_categories'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)