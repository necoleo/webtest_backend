"""
URL configuration for back project.

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
# from django.contrib import admin
from django.urls import path

from api_auto_test.views.delete_api_document_view import DeleteApiDocumentView
from api_auto_test.views.get_api_document_list_view import GetApiDocumentListView
from api_auto_test.views.parse_api_document_view import ParseApiDocumentView
from api_auto_test.views.update_api_document_view import UpdateApiDocumentView
from api_auto_test.views.upload_api_document_view import UploadApiDocumentView
from projects.views.create_project_view import CreateProjectView
from projects.views.delete_project_view import DeleteProjectView
from projects.views.get_project_list_view import GetProjectListView
from projects.views.update_project_view import UpdateProjectView
from users.views.UserLoginView import UserLoginView

urlpatterns = [
       # path('admin/', admin.site.urls),
    # 用户账号相关接口
    path("api/user/login/", UserLoginView.as_view()),

    # 接口文档相关接口
    path("api/api_document/upload/", UploadApiDocumentView.as_view()),
    path("api/api_document/list/", GetApiDocumentListView.as_view()),
    path("api/api_document/delete/", DeleteApiDocumentView.as_view()),
    path("api/api_document/parse/", ParseApiDocumentView.as_view()),
    path("api/api_document/update/", UpdateApiDocumentView.as_view()),

    # 项目管理相关接口
    path("api/project/create/", CreateProjectView.as_view()),
    path("api/project/update/", UpdateProjectView.as_view()),
    path("api/project/delete/", DeleteProjectView.as_view()),
    path("api/project/list/", GetProjectListView.as_view()),
]
