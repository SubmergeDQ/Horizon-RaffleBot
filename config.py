"""
配置管理模块
统一管理所有运行参数，支持自定义修改
"""

import os

# 获取当前脚本所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 默认配置字典
DEFAULT_CONFIG = {
    # 图像识别参数
    'similarity_threshold': 0.7,  # 模板匹配相似度阈值（0.0-1.0）
    'scan_interval': 0.3,         # 识别循环间隔（秒），默认0.3秒
    'action_cooldown': 0.5,       # 动作冷却时间（秒），防止重复触发
    
    # 抽奖参数
    'total_raffles': 10,          # 总抽奖次数
    
    # 屏幕识别区域坐标（基于屏幕分辨率的比例或绝对坐标）
    # 左下角区域 - 用于识别Enter跳过、领取奖励等按钮
    'bottom_left_region': {
        'x': 0,
        'y': 0, 
        'width': 400,
        'height': 150
    },
    
    # 中间区域 - 用于识别添加至车库、送礼等按钮组合
    'center_region': {
        'x': 600,
        'y': 300,
        'width': 700,
        'height': 200
    },
    
    # 模板图片路径配置
    'template_paths': {
        'enter_skip': os.path.join(BASE_DIR, 'Pictures', 'Examples', 'Enter跳过.png'),
        'enter_claim_and_raffle': os.path.join(BASE_DIR, 'Pictures', 'Examples', 'Enter领取奖励并再次抽奖.png'),
        'esc_claim': os.path.join(BASE_DIR, 'Pictures', 'Examples', 'Esc领取奖励.png'),
        'car_received': os.path.join(BASE_DIR, 'Pictures', 'Examples', '获得车辆.png')
    },
    
    # 热键配置
    'hotkeys': {
        'start': 'f1',   # F1启动
        'stop': 'f2'     # F2停止
    },
    
    # 日志配置
    'log_max_lines': 1000,  # 日志最大行数
}


class Config:
    """配置管理类，支持动态修改参数"""
    
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        # 深拷贝嵌套字典
        self._config['bottom_left_region'] = DEFAULT_CONFIG['bottom_left_region'].copy()
        self._config['center_region'] = DEFAULT_CONFIG['center_region'].copy()
        self._config['template_paths'] = DEFAULT_CONFIG['template_paths'].copy()
        self._config['hotkeys'] = DEFAULT_CONFIG['hotkeys'].copy()
    
    def get(self, key_path: str, default=None):
        """
        获取配置值，支持点号分隔的嵌套键
        例如: config.get('template_paths.enter_skip')
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path: str, value):
        """
        设置配置值，支持点号分隔的嵌套键
        """
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def get_all(self) -> dict:
        """获取所有配置的深拷贝"""
        import copy
        return copy.deepcopy(self._config)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.__init__()


# 全局配置实例
config = Config()
