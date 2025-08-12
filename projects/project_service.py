from urllib import response

from django.core.exceptions import ObjectDoesNotExist

from projects import models
from projects.models import Projects


class ProjectService:

    def add_project(self, request_data):
        """添加项目"""
        response = {}
        try:
            project, created = Projects.objects.get_or_create(
                project_code=request_data['project_code'],
                defaults={
                    'project_name': request_data['project_name'],
                    'description': request_data.get('description', ''),  # 处理可选字段
                    'project_type': request_data['project_type'],
                    'project_status': request_data['project_status'],
                    'start_date': request_data.get('start_date'),
                    'end_date': request_data.get('end_date'),
                }
            )
            if created:
                response['code'] = "success"
                response['message'] = "项目创建成功"
                response['data'] = ""
            else:
                response['code'] = "error"
                response['message'] = "该项目已存在"
                response['data'] = ""
        except Exception as e:
            response['code'] = "error"
            response['message'] = "创建过程发生错误"
            response['data'] = str(e)

        return response

    def get_projects_list(self):
        """获取项目列表"""
        response = {}
        projects_list = []
        try:
            projects_obj = models.Projects.objects.all()
            if projects_obj:
                for project in projects_obj:
                    project_dict = {
                        'code': project.project_code,
                        'name': project.project_name,
                        'description': project.description,
                        'type': project.project_type,
                        'status': project.project_status,
                        'start_date': project.start_date,
                        'end_date': project.end_date
                    }
                    projects_list.append(project_dict)

                response['code'] = "success"
                response['message'] = "查询成功"
                response['data'] = projects_list
            else:
                response['code'] = "error"
                response['message'] = "查询对象不存在"
                response['data'] = ""

        except Exception as e:
            response['code'] = "error"
            response['message'] = "查询过程发生错误"
            response['data'] = str(e)

        return response

    def delete_project(self, project_code):
        response = {
            'code': "",
            'message': "",
            'data': ""
        }
        try:
            target_project = Projects.objects.get(project_code=project_code)
            target_project.delete()
            response['code'] = "success"
            response['message'] = f"项目 {project_code} 删除成功"
            response['data'] = ""

        except ObjectDoesNotExist:
            response['code'] = "error"
            response['message'] = f"项目 {project_code} 不存在，删除失败"
            response['data'] = ""

        except Exception as e:
            response['code'] = "error"
            response['message'] = "删除失败"
            response['data'] = str(e)

        return response