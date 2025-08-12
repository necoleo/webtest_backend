from urllib import response

from django.core.exceptions import ObjectDoesNotExist

from projects import models
from projects.models import Projects


class ProjectService:

    # 设置不可修改的字段
    ALLOWED_UPDATE_FIELDS = [
        'project_name',
        'description',
        'project_type',
        'status',
        'start_date',
        'end_date',
    ]

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

    def delete_project_by_code(self, project_code):
        """根据 project_code 删除项目"""
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

    def update_project_by_code(self, project_code, update_data):
        """根据 project_code 修改项目"""
        response = {
            'code': "",
            'message': "",
            'data': ""
        }

        try:

            target_project = Projects.objects.get(project_code=project_code)

            valid_update_data = {}
            # 过滤数据，只保留可以更新的数据
            for key, value in update_data:
                if value in self.ALLOWED_UPDATE_FIELDS:
                    valid_update_data[key] = update_data[value]

            # 更新数据
            for field, value in valid_update_data.items():
                # 动态设置字段
                setattr(target_project, field, value)
            target_project.save()

            response['code'] = "success"
            response['message'] = "更新成功"
            response['data'] = f"项目 {target_project.project_code} 更新成功"

        except ObjectDoesNotExist:
            # 项目不存在
            response['code'] = "error"
            response['message'] = f"更新失败：项目 {project_code} 不存在"
            response['data'] = ""

        except Exception as e:
            response['code'] = "error"
            response['message'] = "更新失败"
            response['data'] = str(e)
