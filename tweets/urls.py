from django.urls import path

from . import views

urlpatterns = [
    path("", views.tweet_list, name="tweet-list"),
    path("create/", views.tweet_create, name="tweet-create"),
    path("sample/", views.tweet_sample, name="tweet-sample"),
]
