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

# 接口文档相关视图
from api_auto_test.views.delete_api_document_view import DeleteApiDocumentView
from api_auto_test.views.get_api_document_list_view import GetApiDocumentListView
from api_auto_test.views.parse_api_document_view import ParseApiDocumentView
from api_auto_test.views.update_api_document_view import UpdateApiDocumentView
from api_auto_test.views.upload_api_document_view import UploadApiDocumentView

# 接口测试用例相关视图
from api_auto_test.views.upload_api_test_case_view import UploadApiTestCaseView
from api_auto_test.views.get_api_test_case_list_view import GetApiTestCaseListView
from api_auto_test.views.get_api_test_case_detail_view import GetApiTestCaseDetailView
from api_auto_test.views.get_api_test_case_yaml_view import GetApiTestCaseYamlView
from api_auto_test.views.delete_api_test_case_view import DeleteApiTestCaseView

# 接口测试环境配置相关视图
from api_auto_test.views.create_api_test_environment_view import CreateApiTestEnvironmentView
from api_auto_test.views.get_api_test_environment_list_view import GetApiTestEnvironmentListView
from api_auto_test.views.update_api_test_environment_view import UpdateApiTestEnvironmentView
from api_auto_test.views.delete_api_test_environment_view import DeleteApiTestEnvironmentView

# 接口测试执行相关视图
from api_auto_test.views.execute_api_test_case_view import ExecuteApiTestCaseView
from api_auto_test.views.get_api_test_execution_status_view import GetApiTestExecutionStatusView
from api_auto_test.views.get_api_test_execution_history_view import GetApiTestExecutionHistoryView
from api_auto_test.views.get_api_test_execution_detail_view import GetApiTestExecutionDetailView

# 接口测试定时任务相关视图
from api_auto_test.views.create_api_test_schedule_view import CreateApiTestScheduleView
from api_auto_test.views.get_api_test_schedule_list_view import GetApiTestScheduleListView
from api_auto_test.views.update_api_test_schedule_view import UpdateApiTestScheduleView
from api_auto_test.views.toggle_api_test_schedule_view import ToggleApiTestScheduleView
from api_auto_test.views.delete_api_test_schedule_view import DeleteApiTestScheduleView
from api_auto_test.views.trigger_api_test_schedule_view import TriggerApiTestScheduleView
from functional_test.views.create_functional_test_case_view import CreateFunctionalTestCaseView
from functional_test.views.delete_functional_test_case_view import DeleteFunctionalTestCaseView
from functional_test.views.get_functional_test_case_detail_view import GetFunctionalTestCaseDetailView
from functional_test.views.get_functional_test_case_list_view import GetFunctionalTestCaseListView
from functional_test.views.update_functional_test_case_view import UpdateFunctionalTestCaseView

# 项目管理相关视图
from projects.views.create_project_view import CreateProjectView
from projects.views.delete_project_view import DeleteProjectView
from projects.views.get_project_list_view import GetProjectListView
from projects.views.update_project_view import UpdateProjectView
from requirements.views.audit_requirement_view import AuditRequirementView

# 需求文档相关视图
from requirements.views.delete_requirement_document_view import DeleteRequirementDocumentView
from requirements.views.delete_requirement_view import DeleteRequirementView
from requirements.views.get_requirement_document_list_view import GetRequirementDocumentListView
from requirements.views.get_requirement_list_view import GetRequirementListView
from requirements.views.parse_requirement_document_view import ParseRequirementDocumentView
from requirements.views.update_requirement_document_view import UpdateRequirementDocumentView
from requirements.views.update_requirement_view import UpdateRequirementView
from requirements.views.upload_requirement_document_view import UploadRequirementDocumentView
from requirements.views.upload_requirement_view import UploadRequirementView

# 用户相关视图
from users.views.UserLoginView import UserLoginView
from users.views.UserRegisterView import UserRegisterView

urlpatterns = [
    # path('admin/', admin.site.urls),
    # 用户账号相关接口
    path("api/user/login/", UserLoginView.as_view()),
    path("api/user/register/", UserRegisterView.as_view()),

    # 需求文档相关接口
    path("api/requirement_document/upload/", UploadRequirementDocumentView.as_view()),
    path("api/requirement_document/update/", UpdateRequirementDocumentView.as_view()),
    path("api/requirement_document/delete/", DeleteRequirementDocumentView.as_view()),
    path("api/requirement_document/list/", GetRequirementDocumentListView.as_view()),
    path("api/requirement_document/parse/",ParseRequirementDocumentView.as_view()),

    # 需求项相关接口
    path("api/requirement/delete/", DeleteRequirementView.as_view()),
    path("api/requirement/update/", UpdateRequirementView.as_view()),
    path("api/requirement/list/", GetRequirementListView.as_view()),
    path("api/requirement/upload/", UploadRequirementView.as_view()),
    path("api/requirement/audit/", AuditRequirementView.as_view()),

    # 测试用例相关接口
    path("api/functional_test_case/create/", CreateFunctionalTestCaseView.as_view()),
    path("api/functional_test_case/list/", GetFunctionalTestCaseListView.as_view()),
    path("api/functional_test_case/detail/", GetFunctionalTestCaseDetailView.as_view()),
    path("api/functional_test_case/update/", UpdateFunctionalTestCaseView.as_view()),
    path("api/functional_test_case/delete/", DeleteFunctionalTestCaseView.as_view()),

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

    # 接口测试用例相关接口
    path("api/api_test_case/upload/", UploadApiTestCaseView.as_view()),
    path("api/api_test_case/list/", GetApiTestCaseListView.as_view()),
    path("api/api_test_case/detail/", GetApiTestCaseDetailView.as_view()),
    path("api/api_test_case/yaml/", GetApiTestCaseYamlView.as_view()),
    path("api/api_test_case/delete/", DeleteApiTestCaseView.as_view()),

    # 接口测试环境配置相关接口
    path("api/api_test_environment/create/", CreateApiTestEnvironmentView.as_view()),
    path("api/api_test_environment/list/", GetApiTestEnvironmentListView.as_view()),
    path("api/api_test_environment/update/", UpdateApiTestEnvironmentView.as_view()),
    path("api/api_test_environment/delete/", DeleteApiTestEnvironmentView.as_view()),

    # 接口测试执行相关接口
    path("api/api_test_execution/execute/", ExecuteApiTestCaseView.as_view()),
    path("api/api_test_execution/status/", GetApiTestExecutionStatusView.as_view()),
    path("api/api_test_execution/history/", GetApiTestExecutionHistoryView.as_view()),
    path("api/api_test_execution/detail/", GetApiTestExecutionDetailView.as_view()),

    # 接口测试定时任务相关接口
    path("api/api_test_schedule/create/", CreateApiTestScheduleView.as_view()),
    path("api/api_test_schedule/list/", GetApiTestScheduleListView.as_view()),
    path("api/api_test_schedule/update/", UpdateApiTestScheduleView.as_view()),
    path("api/api_test_schedule/toggle/", ToggleApiTestScheduleView.as_view()),
    path("api/api_test_schedule/delete/", DeleteApiTestScheduleView.as_view()),
    path("api/api_test_schedule/trigger/", TriggerApiTestScheduleView.as_view()),
]
