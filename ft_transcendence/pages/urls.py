from django.urls import path
from . import views
from .views import EmptyPath
from django.conf.urls.static import static
from django.conf import settings
print('asdasdas')
urlpatterns = [
    path('users/', views.users_view),
    path('users/<int:id>/', views.user_view),
    path('users/<int:id>/friends/', views.friends_view),
    path('tournaments/', views.tournaments_view),
    path('best/', views.best_view),
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),
    path('delete_friend/<int:user_id>/', views.delete_friend, name='delete_friend'),
    path('accept_friend/<int:user_id>/', views.accept_friend, name='accept_friend'),
    path('cancel_friend/<int:user_id>/', views.cancel_friend, name='cancel_friend'),
    path("add_invite/<int:user_id>/", views.add_invite, name="add_invite"),
    path('accept_invite/<int:user_id>/', views.accept_invite, name='accept_invite'),
    path('play_invite/<int:user_id>/', views.play_invite, name="play_invite"),
    path('cancel_invite/<int:user_id>/', views.cancel_invite, name="cancel_invite"),
    #for test modsecurity
	path('vulnerable/', views.vulnerable_view),
    path('', EmptyPath.as_view(), name='empty'),
	path('home/', EmptyPath.as_view(), name='empty'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
