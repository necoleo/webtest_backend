"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from projects.views.add_project_view import AddProjectView
from projects.views.delete_project_view import DeleteProjectView
from projects.views.edit_project_view import EditProjectView
from projects.views.show_project_view import ShowProjectView
from users.views.UserRegisterView import UserRegisterView
from users.views.UserLoginView import UserLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/login', UserLoginView.as_view()),
    path('api/user/register', UserRegisterView.as_view()),
    path('api/project/add', AddProjectView.as_view()),
    path('api/project/show', ShowProjectView.as_view()),
    path('api/project/delete', DeleteProjectView.as_view()),
    path('api/project/edit', EditProjectView.as_view()),
]
