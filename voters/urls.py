from django.urls import path, include
from .views import *

app_name = 'voters'

urlpatterns = [
    path('', include([
        path('home/', home_views.HomeView.as_view(), name='home'),
        path('vote/<int:pemilihan_id>/', vote_views.VotePageView.as_view(), name='vote_page'),
        path('vote/<int:pemilihan_id>/send_token/', vote_views.SendTokenView.as_view(), name='send_token'),
        path('vote/<int:pemilihan_id>/submit/', vote_views.SubmitVoteView.as_view(), name='submit_vote'),
        path('hasil/<int:pemilihan_id>/', home_views.HomeView.as_view(), name='hasil_pemilihan'),
	])),
]