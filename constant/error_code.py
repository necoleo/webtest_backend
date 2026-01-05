

class ErrorCode:
    """业务异常码"""

    # 成功
    SUCCESS = "000000"

    # 通用错误 (1xxxxx)
    ERROR = "100000"

    # 参数相关错误 (4xxxxx)
    # 参数为空
    PARAM_BLANK = "400001"

    # 参数无效
    PARAM_INVALID = "400002"

    # 参数缺失
    PARAM_MISSING = "400003"

    # 认证授权错误 (4xxxxx)
    # 未授权
    UNAUTHORIZED = "401000"

    # 无权限
    FORBIDDEN = "403000"

    # 业务逻辑错误 (5xxxxx)
    # 用户不存在
    USER_NOT_FOUND = "500001"

    # 用户已存在
    USER_EXISTS = "500002"

    # 登录失败
    LOGIN_FAILED = "500003"

    # 文件保存失败
    FILE_SAVE_FAILED = "500004"

    # 服务器错误
    SERVER_ERROR = "500005"