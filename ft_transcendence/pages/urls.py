from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view),
    path('inactive/', views.inactive_view),
    path('users/', views.users_view),
    path('users/<int:id>', views.user_view),
    path('best/', views.best_view),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)