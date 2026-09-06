"""
核心抽奖引擎模块
实现完整的抽奖流程控制，包括常规抽奖和最后一次专属收尾流程
"""

import time
import threading
from datetime import datetime
from config import config
from image_recognizer import recognizer
from key_controller import key_controller


class RaffleEngine:
    """抽奖引擎类，负责整个抽奖流程的控制"""
    
    def __init__(self):
        self._running = False  # 运行状态标志
        self._paused = False   # 暂停标志（保留扩展）
        self._current_raffle = 0  # 当前第几次抽奖（从1开始）
        self._total_raffles = config.get('total_raffles', 10)
        self._thread = None  # 抽奖线程
        self._lock = threading.Lock()  # 线程锁
        
        # 日志回调函数列表（支持多个监听器）
        self._log_callbacks = []
        
        # 状态回调函数
        self._state_callback = None
    
    def add_log_callback(self, callback):
        """添加日志回调函数"""
        if callback not in self._log_callbacks:
            self._log_callbacks.append(callback)
    
    def remove_log_callback(self, callback):
        """移除日志回调函数"""
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)
    
    def set_state_callback(self, callback):
        """设置状态变化回调函数"""
        self._state_callback = callback
    
    def _emit_log(self, message: str):
        """
        发送日志消息到所有注册的回调
        带时间戳格式化
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        for callback in self._log_callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                print(f"[错误] 日志回调异常: {e}")
    
    def _emit_state(self, state: str, current: int = 0, total: int = 0):
        """
        发送状态更新消息
        state: 'stopped' | 'running' | 'finished'
        """
        if self._state_callback:
            try:
                self._state_callback(state, current, total)
            except Exception as e:
                print(f"[错误] 状态回调异常: {e}")
    
    def _get_scan_interval(self) -> float:
        """获取当前配置的扫描间隔"""
        return config.get('scan_interval', 0.3)
    
    def _is_last_raffle(self) -> bool:
        """判断是否为最后一次抽奖"""
        with self._lock:
            return self._current_raffle >= self._total_raffles
    
    def _execute_normal_raffle_loop(self):
        """
        执行常规抽奖循环（前N-1次）
        按照优先级顺序检测并响应：
        1. Enter跳过 -> 按Enter
        2. Enter领取奖励并再次抽奖 -> 按Enter
        3. 添加至车库/送礼按钮组合 -> 按Enter
        """
        self._emit_log(f"开始常规抽奖流程 (第 {self._current_raffle}/{self._total_raffles} 次)")
        
        while self._running and not self._is_last_raffle():
            try:
                # 检测1: Enter跳过（左下角区域）
                matched, confidence = recognizer.check_enter_skip()
                if matched:
                    self._emit_log(f"检测到 [Enter跳过] (匹配度: {confidence:.2f})")
                    if key_controller.press_enter():
                        self._emit_log("执行: 按下 Enter")
                
                # 检测2: Enter领取奖励并再次抽奖（左下角区域）
                matched, confidence = recognizer.check_enter_claim_and_raffle()
                if matched:
                    self._emit_log(f"检测到 [Enter领取奖励并再次抽奖] (匹配度: {confidence:.2f})")
                    if key_controller.press_enter():
                        self._emit_log(f"执行: 按下 Enter，完成第 {self._current_raffle} 次抽奖")
                        with self._lock:
                            self._current_raffle += 1
                        self._emit_state('running', self._current_raffle, self._total_raffles)
                        
                        # 如果已经达到最后一次，退出常规循环
                        if self._is_last_raffle():
                            break
                
                # 检测3: 获得车辆界面 - 添加至车库/送礼按钮（中间区域）
                matched, confidence = recognizer.check_car_received()
                if matched:
                    self._emit_log(f"检测到 [获得车辆-添加至车库/送礼] (匹配度: {confidence:.2f})")
                    if key_controller.press_enter():
                        self._emit_log("执行: 按下 Enter 确认")
                
                # 等待下一次扫描
                time.sleep(self._get_scan_interval())
                
            except Exception as e:
                self._emit_log(f"[错误] 常规抽奖循环异常: {e}")
                time.sleep(1.0)
    
    def _execute_final_raffle(self):
        """
        执行最后一次专属抽奖流程
        规则：将"Enter领取奖励并再次抽奖"替换为按Esc键领取奖励，
              然后等待识别到车辆获取界面即完成
        """
        self._emit_log("=" * 50)
        self._emit_log(f"开始最后一次专属抽奖流程 (第 {self._current_raffle}/{self._total_raffles} 次)")
        self._emit_log("规则变更: 使用 Esc 键领取奖励（不再继续抽奖）")
        
        final_completed = False
        
        while self._running and not final_completed:
            try:
                # 检测1: Enter跳过 -> 按Enter（正常处理）
                matched, confidence = recognizer.check_enter_skip()
                if matched:
                    self._emit_log(f"检测到 [Enter跳过] (匹配度: {confidence:.2f})")
                    if key_controller.press_enter():
                        self._emit_log("执行: 按下 Enter")
                
                # 检测2: 领取奖励相关按钮（左下角区域）
                # 优先检测"Esc领取奖励"
                matched_esc, conf_esc = recognizer.check_esc_claim()
                matched_enter, conf_enter = recognizer.check_enter_claim_and_raffle()
                
                if matched_esc or matched_enter:
                    if matched_esc:
                        self._emit_log(f"检测到 [Esc领取奖励] (匹配度: {conf_esc:.2f})")
                    else:
                        self._emit_log(f"检测到 [领取奖励按钮] (匹配度: {conf_enter:.2f})，使用Esc键")
                    
                    if key_controller.press_esc():
                        self._emit_log("执行: 按下 Esc 领取奖励（不继续抽奖）")
                
                # 检测3: 获得车辆界面 - 表示本轮抽奖完成
                matched, confidence = recognizer.check_car_received()
                if matched:
                    self._emit_log(f"检测到 [获得车辆界面] (匹配度: {confidence:.2f})")
                    self._emit_log("✓ 最后一次抽奖完成！已成功领取最终奖励")
                    final_completed = True
                
                time.sleep(self._get_scan_interval())
                
            except Exception as e:
                self._emit_log(f"[错误] 最后一次抽奖循环异常: {e}")
                time.sleep(1.0)
    
    def _raffle_worker(self):
        """抽奖工作线程的主函数"""
        try:
            self._emit_log("抽奖引擎启动")
            self._emit_log(f"目标抽奖次数: {self._total_raffles}")
            self._emit_log(f"相似度阈值: {config.get('similarity_threshold')}")
            self._emit_log(f"扫描间隔: {config.get('scan_interval')}秒")
            self._emit_log("-" * 50)
            
            # 执行常规抽奖（前N-1次）
            self._execute_normal_raffle_loop()
            
            # 如果仍在运行且需要执行最后一次
            if self._running and self._is_last_raffle() and self._current_raffle <= self._total_raffles:
                self._execute_final_raffle()
            
            # 抽奖完成
            self._emit_log("=" * 50)
            self._emit_log(f"🎉 全部抽奖完成！共执行 {self._total_raffles} 次")
            self._emit_log("=" * 50)
            
            self._running = False
            self._emit_state('finished', self._total_raffles, self._total_raffles)
            
        except Exception as e:
            self._emit_log(f"[严重错误] 抽奖引擎异常终止: {e}")
            self._running = False
            self._emit_state('stopped', self._current_raffle, self._total_raffles)
    
    def start(self, total_raffles: int = None):
        """
        启动抽奖引擎
        total_raffles: 总抽奖次数（可选，不传则使用配置值）
        返回: 是否成功启动
        """
        with self._lock:
            if self._running:
                self._emit_log("[警告] 抽奖已在运行中")
                return False
            
            self._running = True
            self._current_raffle = 1
            
            if total_raffles is not None:
                self._total_raffles = max(1, total_raffles)
            else:
                self._total_raffles = config.get('total_raffles', 10)
        
        # 创建并启动工作线程
        self._thread = threading.Thread(target=self._raffle_worker, daemon=True)
        self._thread.start()
        
        self._emit_state('running', 0, self._total_raffles)
        return True
    
    def stop(self):
        """
        停止抽奖引擎
        返回: 是否成功停止
        """
        with self._lock:
            if not self._running:
                return False
            
            self._running = False
        
        self._emit_log("正在停止抽奖引擎...")
        self._emit_state('stopping', self._current_raffle, self._total_raffles)
        
        # 等待线程结束（最多5秒）
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        self._emit_log(f"抽奖已停止 (已完成 {self._current_raffle - 1}/{self._total_raffles} 次)")
        self._emit_state('stopped', self._current_raffle - 1, self._total_raffles)
        return True
    
    def is_running(self) -> bool:
        """获取当前运行状态"""
        with self._lock:
            return self._running
    
    def get_progress(self) -> tuple[int, int]:
        """
        获取当前进度
        返回: (当前次数, 总次数)
        """
        with self._lock:
            return self._current_raffle - 1, self._total_raffles


# 全局抽奖引擎实例
raffle_engine = RaffleEngine()
