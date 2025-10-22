from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),  # root URL goes to login page
    path('login/', views.user_login, name='login'),
    path('home/', views.home, name='home'),   # explicitly name home URL
    path('logout/', views.user_logout, name='logout'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('unused-ds/', views.unuse_DS, name='unuse_DS'),
    path('logout/', views.user_logout, name='logout'),
    path('best-files/', views.best_files_view, name='best_files'),
    

]
