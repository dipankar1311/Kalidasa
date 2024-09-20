from django.urls import path, include
from pii.detector import views

urlpatterns = [
    path('/', view=views.index, name="index"),
]