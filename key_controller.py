"""
按键模拟模块
使用PyAutoGUI进行后台按键模拟，支持冷却机制防止重复触发
"""

import time
import threading
import pyautogui
from config import config


class KeyController:
    """按键控制器类，负责按键输入和冷却管理"""
    
    def __init__(self):
        self._last_action_time = {}  # 记录各动作的最后执行时间
        self._lock = threading.Lock()  # 线程锁，保证线程安全
        
        # 禁用PyAutoGUI的安全暂停（避免每次按键都等待）
        pyautogui.PAUSE = 0.01
    
    def _get_cooldown(self) -> float:
        """获取当前配置的动作冷却时间"""
        return config.get('action_cooldown', 0.5)
    
    def _can_execute(self, action_name: str) -> bool:
        """
        检查是否可以执行动作（冷却时间已过）
        使用锁确保线程安全
        """
        with self._lock:
            cooldown = self._get_cooldown()
            last_time = self._last_action_time.get(action_name, 0)
            current_time = time.time()
            
            if current_time - last_time >= cooldown:
                return True
            return False
    
    def _record_action(self, action_name: str):
        """记录动作执行时间"""
        with self._lock:
            self._last_action_time[action_name] = time.time()
    
    def press_enter(self) -> bool:
        """
        按下回车键（Enter）
        返回: 是否成功执行
        """
        if not self._can_execute('enter'):
            return False
        
        try:
            pyautogui.press('enter')
            self._record_action('enter')
            return True
        except Exception as e:
            print(f"[错误] 按键失败 (Enter): {e}")
            return False
    
    def press_esc(self) -> bool:
        """
        按下Esc键
        返回: 是否成功执行
        """
        if not self._can_execute('esc'):
            return False
        
        try:
            pyautogui.press('escape')
            self._record_action('esc')
            return True
        except Exception as e:
            print(f"[错误] 按键失败 (Esc): {e}")
            return False
    
    def reset_cooldown(self):
        """重置所有冷却时间（用于测试或特殊情况）"""
        with self._lock:
            self._last_action_time.clear()
    
    def set_cooldown(self, cooldown: float):
        """动态设置冷却时间（通过修改配置）"""
        config.set('action_cooldown', max(0.1, min(5.0, cooldown)))


# 全局按键控制器实例
key_controller = KeyController()
