from django.urls import path, include
from .views import *

app_name = 'main'
urlpatterns = [
    path('', include([
        path('', RedirectToLoginView.as_view(), name ='redirect_to_login'),
        path('login/', LoginView.as_view(), name='login'),
        path('logout/', LogoutView.as_view(), name='logout'),
        path('profile/<str:nim>/', ProfileView.as_view(), name='user_profile'),
        path('profile/<str:nim>/ubah-password/', ProfileView.as_view(), name='user_profile_with_password_prompt'),
    ])),
]