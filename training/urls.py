from django.urls import path
from . import views

urlpatterns = [
    path("", views.home),
    path("connect/", views.Connection.as_view()),
    path("move/", views.MoveView.as_view()),
    path("getTree/", views.GetTree.as_view())
]