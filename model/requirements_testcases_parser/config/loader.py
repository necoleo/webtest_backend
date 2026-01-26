import yaml

class LoadConfig:

    def __init__(self, config_path):
        """配置加载器，需要指定配置文件路径"""
        self.config_path = config_path
        self.configs = {}

    def load_config(self):
        # 从环境变量加载配置

        # self.configs = dict(os.environ)

        # 打开配置文件
        with open(self.config_path, "r", encoding='utf-8') as file:
            # 使用yaml.safe_load方法加载配置文件
            yaml_data = yaml.safe_load(file)
        # 将配置文件中的键值对添加到self.configs字典中
        self.configs.update(yaml_data)

        return self.configs
