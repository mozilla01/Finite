from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('profile', views.Profile.as_view(), name='profile'),
    path('login', views.login_user, name='login'),
    path('signup', views.signup, name='signup'),
    path('logout', views.logout_user, name='logout'),
    path('create-category', views.CreateCategory.as_view(), name='create-category'),
    path('add-source', views.AddSource.as_view(), name='add-source'),
    path('add-transaction', views.AddTransaction.as_view(), name='add-transaction'),
    path('update-transaction', views.UpdateTransaction.as_view(), name='update-transaction'),
    path('delete-transaction', views.DeleteTransaction.as_view(), name='delete-transaction'),
    path('update-profile', views.UpdateProfile.as_view(), name='update-profile'),
]
