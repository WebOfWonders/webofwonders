from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('weather/', views.weather, name='weather'),
    path('ocr/', views.ocr, name='ocr'),
    path('md5/', views.md5, name='md5'),
    path('nearby/', views.nearby, name='nearby'),
    path('urlshortner', views.shorten_url, name='shorten_url'),
    # path('humanizer/', views.humanize_text, name='humanize_text'),
    path('<str:short_code>/', views.redirect_url, name='redirect_url'),  # Keep this at the end
]
