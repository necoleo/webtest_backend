# -*- coding=utf-8
from dotenv import load_dotenv
from qcloud_cos import CosConfig, CosClientError, CosServiceError
from qcloud_cos import CosS3Client
import sys
import os
import logging

class CosClient:

    def __init__(self):
        # 正常情况日志级别使用 INFO，需要定位时可以修改为 DEBUG，此时 SDK 会打印和服务端的通信信息
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

        # 加载 .env文件
        load_dotenv("../config/.env")

        # 1. 设置用户属性
        secret_id = os.environ['COS_SECRET_ID']
        secret_key = os.environ['COS_SECRET_KEY']
        # 已创建桶归属的 region
        region = 'ap-guangzhou'
        token = None
        # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
        scheme = 'https'

        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
        self.bucket = "heypon-1347960590"
        self.client = CosS3Client(config)

    # 查询存储桶列表
    def get_cos_bucket_lists(self):
        response = self.client.list_buckets()
        logging.info(response)
        return response


    # 上传文件
    # 失败重试时不会上传已成功的分块(这里重试3次)
    def upload_file_to_cos_bucket(self, target_dir, file_name, file_path):
        """
        上传文件
        file_name
        file_path
        """
        response = {}
        file_name = os.path.join(target_dir, file_name)
        for i in range(0, 3):
            try:
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=file_name,
                    LocalFilePath= file_path
                )
                break
            except CosClientError or CosServiceError as e:
                print(e)
        return response

    def download_file_by_cos_bucket(self, target_dir, file_name, file_path):
        """
        下载文件
        :param target_dir:
        :param file_name:
        :param file_path: 文件下载的本地目的路径名
        :return:
        """
        response = {}
        file_name = os.path.join(target_dir, file_name)
        for i in range(0, 10):
            try:
                response = self.client.download_file(
                    Bucket=self.bucket,
                    Key=file_name,
                    DestFilePath=file_path
                )
                break
            except CosClientError or CosServiceError as e:
                print(e)
        return response

    def get_file_lists(self, prefix=None, delimiter=None):
        """
        列出指定目录下的对象和子目录
        Prefix='folder1/', Delimiter='/'
        :param prefix: 默认为空，对对象的对象键进行筛选，匹配 prefix 为前缀的对象
        :param delimiter: 默认为空，设置分隔符，例如设置 / 来模拟文件夹
        :return:
        """
        # 列举 folder1 目录下的文件和子目录
        # Prefix='folder1/', Delimiter='/'
        response = self.client.list_objects(
            Bucket=self.bucket, Prefix=prefix, Delimiter=delimiter)
        # 打印文件列表
        if 'Contents' in response:
            for content in response['Contents']:
                print(content['Key'])
        # 打印子目录
        if 'CommonPrefixes' in response:
            for folder in response['CommonPrefixes']:
                print(folder['Prefix'])
        return response

if __name__ == '__main__':
    cos_client = CosClient()
    res = cos_client.upload_file_to_cos_bucket("webtest_requirements_document/", "test_upload.txt", "C:/Users/92700/Desktop/test_upload.txt")
    res1 = cos_client.download_file_by_cos_bucket("webtest_requirements_document/", "test_upload.txt", "C:/Users/92700/Desktop/test_download.txt")
    print(res)
    print(res1)