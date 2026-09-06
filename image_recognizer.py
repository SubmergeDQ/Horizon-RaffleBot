"""
图像识别模块
使用OpenCV进行模板匹配，支持自定义识别区域和相似度阈值
"""

import cv2
import numpy as np
import os
import pyautogui
from PIL import Image
import io
from config import config


class ImageRecognizer:
    """图像识别器类，负责屏幕截图和模板匹配"""
    
    def __init__(self):
        self._template_cache = {}  # 模板图片缓存，避免重复读取
    
    def _load_template(self, template_name: str) -> np.ndarray | None:
        """
        加载模板图片（带缓存）
        返回OpenCV格式的图片数组，加载失败返回None
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        template_path = config.get(f'template_paths.{template_name}')
        if not template_path or not os.path.exists(template_path):
            print(f"[错误] 模板图片不存在: {template_path}")
            return None
        
        # 使用cv2.imread读取图片（BGR格式）
        template = cv2.imread(template_path)
        if template is None:
            print(f"[错误] 无法读取模板图片: {template_path}")
            return None
        
        self._template_cache[template_name] = template
        return template
    
    def capture_screen_region(self, region_key: str) -> np.ndarray | None:
        """
        截取指定区域的屏幕截图
        region_key: 'bottom_left_region' 或 'center_region'
        返回OpenCV格式的图片数组（BGR）
        """
        region = config.get(region_key)
        if not region:
            print(f"[错误] 未找到区域配置: {region_key}")
            return None
        
        try:
            # 使用pyautogui截取区域截图（PIL格式）
            screenshot = pyautogui.screenshot(
                region=(region['x'], region['y'], region['width'], region['height'])
            )
            
            # 转换为OpenCV格式（BGR）
            opencv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return opencv_image
            
        except Exception as e:
            print(f"[错误] 截屏失败: {e}")
            return None
    
    def match_template(self, screen_region: np.ndarray, template_name: str, 
                       threshold: float = None) -> tuple[bool, float, tuple]:
        """
        在屏幕区域中匹配模板图片
        返回: (是否匹配成功, 最大匹配度, 匹配位置(x,y))
        """
        if threshold is None:
            threshold = config.get('similarity_threshold', 0.7)
        
        template = self._load_template(template_name)
        if template is None or screen_region is None:
            return False, 0.0, (0, 0)
        
        # 确保模板尺寸不超过屏幕区域
        if template.shape[0] > screen_region.shape[0] or template.shape[1] > screen_region.shape[1]:
            return False, 0.0, (0, 0)
        
        try:
            # 执行模板匹配（归一化相关系数匹配方法，效果最好但较慢）
            result = cv2.matchTemplate(screen_region, template, cv2.TM_CCOEFF_NORMED)
            
            # 获取最大匹配值及其位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 判断是否超过阈值
            matched = max_val >= threshold
            return matched, float(max_val), max_loc
            
        except Exception as e:
            print(f"[错误] 模板匹配失败 ({template_name}): {e}")
            return False, 0.0, (0, 0)
    
    def check_enter_skip(self) -> tuple[bool, float]:
        """
        检查左下角区域是否有"Enter跳过"按钮
        返回: (是否检测到, 匹配度)
        """
        screen = self.capture_screen_region('bottom_left_region')
        matched, confidence, _ = self.match_template(screen, 'enter_skip')
        return matched, confidence
    
    def check_enter_claim_and_raffle(self) -> tuple[bool, float]:
        """
        检查左下角区域是否有"Enter领取奖励并再次抽奖"按钮
        返回: (是否检测到, 匹配度)
        """
        screen = self.capture_screen_region('bottom_left_region')
        matched, confidence, _ = self.match_template(screen, 'enter_claim_and_raffle')
        return matched, confidence
    
    def check_esc_claim(self) -> tuple[bool, float]:
        """
        检查左下角区域是否有"Esc领取奖励"按钮
        返回: (是否检测到, 匹配度)
        """
        screen = self.capture_screen_region('bottom_left_region')
        matched, confidence, _ = self.match_template(screen, 'esc_claim')
        return matched, confidence
    
    def check_car_received(self) -> tuple[bool, float]:
        """
        检查中间区域是否有"添加至车库/送礼"按钮组合（获得车辆界面）
        返回: (是否检测到, 匹配度)
        """
        screen = self.capture_screen_region('center_region')
        matched, confidence, _ = self.match_template(screen, 'car_received')
        return matched, confidence
    
    def clear_cache(self):
        """清除模板缓存，用于重新加载修改后的图片"""
        self._template_cache.clear()


# 全局识别器实例
recognizer = ImageRecognizer()
