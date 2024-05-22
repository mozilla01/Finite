from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('profile', views.Profile.as_view(), name='profile'),
    path('login', views.login_user, name='login'),
    path('signup', views.signup, name='signup'),
    path('logout', views.logout_user, name='logout'),
    path('bills', views.Bills.as_view(), name='bills'),
    path('pay-bill/<str:pk>', views.PayBill.as_view(), name='pay-bill'),
    path('delete-bill/<str:pk>', views.DeleteBill.as_view(), name='delete-bill'),
    path('create-category', views.CreateCategory.as_view(), name='create-category'),
    path('add-source', views.AddSource.as_view(), name='add-source'),
    path('add-transaction', views.AddTransaction.as_view(), name='add-transaction'),
    path('update-transaction', views.UpdateTransaction.as_view(), name='update-transaction'),
    path('delete-transaction', views.DeleteTransaction.as_view(), name='delete-transaction'),
    path('update-profile', views.UpdateProfile.as_view(), name='update-profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
