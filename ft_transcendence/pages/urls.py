from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view),
    path('users/', views.users_view),
    path('users/<int:id>/', views.user_view),
    path('users/<int:id>/friends/', views.friends_view),
    path('inactive/', views.inactive_view),
    path('tournaments/', views.tournaments_view),
    path('best/', views.best_view),
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),
    path('delete_friend/<int:user_id>/', views.delete_friend, name='delete_friend'),
    path('accept_friend/<int:user_id>/', views.accept_friend, name='accept_friend'),
    path('cancel_friend/<int:user_id>/', views.cancel_friend, name='cancel_friend'),
    #for test modsecurity
    path('vulnerable/', views.vulnerable_view),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)