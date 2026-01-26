import yaml

class loadConfig():

    def __init__(self, config_path=None) -> None:
        # 如果config_path参数不为None，则使用用户指定的路径
        if config_path is not None:
            self.config_path = config_path
        else:
            # 否则，使用默认路径
            self.config_path = "../config/config.yaml"

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
