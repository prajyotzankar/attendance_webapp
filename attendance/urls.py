from django.contrib import admin
from django.urls import path, include
from attendance import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

handler500 = views.error_500
handler404 = views.error_404
handler403 = views.error_403
handler400 = views.error_400

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # add these to configure our home page (default view) and result web page
    path('home/', views.home, name='home'),
    path('attendance/', views.attendance, name='attendance'),
    path('defaulter', views.defaulter, name='defaulter'),
    path('defaulter_list', views.defaulter_list, name='defaulter_list'),
    path('profile/', views.profile, name='profile'),
    path("register/", views.register, name='register'),
    path("",auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path("logout/", views.logout_view, name = 'logout'),
    path('upload',views.upload_file, name='upload'),

]

#if settings.DEBUG:
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
