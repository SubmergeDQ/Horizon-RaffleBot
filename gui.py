"""
GUI界面模块
使用Tkinter构建轻量化图形界面，支持参数配置、日志输出、热键控制
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import threading
from pynput import keyboard
from config import config
from raffle_engine import raffle_engine
from image_recognizer import recognizer


class RaffleBotGUI:
    """抽奖机器人图形界面类"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("极限竞速地平线6 - 自动抽奖工具")
        self.root.geometry("720x680")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果存在）
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'Pictures', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # 热键监听器
        self._hotkey_listener = None
        
        # 构建界面
        self._build_ui()
        
        # 注册回调
        raffle_engine.add_log_callback(self._append_log)
        raffle_engine.set_state_callback(self._update_status)
        
        # 启动热键监听
        self._start_hotkey_listener()
        
        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _build_ui(self):
        """构建完整的用户界面"""
        # 主框架，带内边距
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重（使界面可伸缩）
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # ===== 标题区域 =====
        title_label = ttk.Label(
            main_frame, 
            text="🎮 地平线6自动抽奖工具",
            font=('Microsoft YaHei', 14, 'bold')
        )
        title_label.grid(row=current_row, column=0, columnspan=2, pady=(0, 10), sticky="w")
        current_row += 1
        
        # ===== 控制按钮区域 =====
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="8")
        control_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        current_row += 1
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill="x")
        
        self.start_btn = ttk.Button(
            btn_frame, 
            text="▶ 启动 (F1)",
            command=self._on_start,
            width=18
        )
        self.start_btn.pack(side="left", padx=(0, 8))
        
        self.stop_btn = ttk.Button(
            btn_frame, 
            text="⏹ 停止 (F2)",
            command=self._on_stop,
            width=18,
            state="disabled"
        )
        self.stop_btn.pack(side="left")
        
        # 状态显示
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill="x", pady=(8, 0))
        
        ttk.Label(status_frame, text="运行状态:").pack(side="left")
        self.status_var = tk.StringVar(value="● 已停止")
        self.status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            font=('Microsoft YaHei', 10, 'bold'),
            foreground='gray'
        )
        self.status_label.pack(side="left", padx=(8, 16))
        
        ttk.Label(status_frame, text="进度:").pack(side="left")
        self.progress_var = tk.StringVar(value="0 / 0")
        ttk.Label(status_frame, textvariable=self.progress_var).pack(side="left", padx=(4, 0))
        
        # ===== 参数设置区域 =====
        param_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="8")
        param_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        current_row += 1
        
        # 第一行参数
        row1 = ttk.Frame(param_frame)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="总抽奖次数:", width=12).pack(side="left")
        self.total_raffles_var = tk.IntVar(value=config.get('total_raffles'))
        total_spinbox = ttk.Spinbox(
            row1, from_=1, to=9999, 
            textvariable=self.total_raffles_var, width=8
        )
        total_spinbox.pack(side="left", padx=(4, 16))
        
        ttk.Label(row1, text="相似度阈值:", width=12).pack(side="left")
        self.similarity_var = tk.DoubleVar(value=config.get('similarity_threshold'))
        similarity_scale = ttk.Scale(
            row1, from_=0.5, to=1.0, 
            variable=self.similarity_var, 
            orient="horizontal",
            length=100
        )
        similarity_scale.pack(side="left", padx=(4, 4))
        self.similarity_label = ttk.Label(row1, text=f"{config.get('similarity_threshold'):.2f}", width=4)
        self.similarity_label.pack(side="left")
        similarity_scale.configure(command=lambda v: self.similarity_label.config(text=f"{float(v):.2f}"))
        
        # 第二行参数
        row2 = ttk.Frame(param_frame)
        row2.pack(fill="x", pady=2)
        
        ttk.Label(row2, text="扫描间隔(秒):", width=12).pack(side="left")
        self.interval_var = tk.DoubleVar(value=config.get('scan_interval'))
        interval_scale = ttk.Scale(
            row2, from_=0.1, to=1.0, 
            variable=self.interval_var, 
            orient="horizontal",
            length=100
        )
        interval_scale.pack(side="left", padx=(4, 4))
        self.interval_label = ttk.Label(row2, text=f"{config.get('scan_interval'):.2f}", width=4)
        self.interval_label.pack(side="left")
        interval_scale.configure(command=lambda v: self.interval_label.config(text=f"{float(v):.2f}"))
        
        ttk.Label(row2, text="动作冷却(秒):", width=14).pack(side="left", padx=(16, 0))
        self.cooldown_var = tk.DoubleVar(value=config.get('action_cooldown'))
        cooldown_scale = ttk.Scale(
            row2, from_=0.1, to=2.0, 
            variable=self.cooldown_var, 
            orient="horizontal",
            length=80
        )
        cooldown_scale.pack(side="left", padx=(4, 4))
        self.cooldown_label = ttk.Label(row2, text=f"{config.get('action_cooldown'):.2f}", width=4)
        self.cooldown_label.pack(side="left")
        cooldown_scale.configure(command=lambda v: self.cooldown_label.config(text=f"{float(v):.2f}"))
        
        # 应用参数按钮
        apply_btn = ttk.Button(param_frame, text="✓ 应用参数", command=self._apply_params)
        apply_btn.pack(pady=(8, 0))
        
        # ===== 识别区域坐标设置 =====
        region_frame = ttk.LabelFrame(main_frame, text="识别区域坐标", padding="8")
        region_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        current_row += 1
        
        region_grid = ttk.Frame(region_frame)
        region_grid.pack(fill="x")
        
        # 左下角区域
        bl_frame = ttk.LabelFrame(region_grid, text="左下角区域", padding="4")
        bl_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        
        self.bl_x = tk.IntVar(value=config.get('bottom_left_region.x'))
        self.bl_y = tk.IntVar(value=config.get('bottom_left_region.y'))
        self.bl_w = tk.IntVar(value=config.get('bottom_left_region.width'))
        self.bl_h = tk.IntVar(value=config.get('bottom_left_region.height'))
        
        self._create_coord_inputs(bl_frame, self.bl_x, self.bl_y, self.bl_w, self.bl_h)
        
        # 中间区域
        ct_frame = ttk.LabelFrame(region_grid, text="中间区域", padding="4")
        ct_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))
        
        self.ct_x = tk.IntVar(value=config.get('center_region.x'))
        self.ct_y = tk.IntVar(value=config.get('center_region.y'))
        self.ct_w = tk.IntVar(value=config.get('center_region.width'))
        self.ct_h = tk.IntVar(value=config.get('center_region.height'))
        
        self._create_coord_inputs(ct_frame, self.ct_x, self.ct_y, self.ct_w, self.ct_h)
        
        # ===== 模板图片路径设置 =====
        template_frame = ttk.LabelFrame(main_frame, text="模板图片路径", padding="8")
        template_frame.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        current_row += 1
        
        template_names = [
            ('enter_skip', 'Enter跳过'),
            ('enter_claim_and_raffle', 'Enter领取奖励并再次抽奖'),
            ('esc_claim', 'Esc领取奖励'),
            ('car_received', '获得车辆')
        ]
        
        self.template_vars = {}
        for key, name in template_names:
            row_t = ttk.Frame(template_frame)
            row_t.pack(fill="x", pady=1)
            
            ttk.Label(row_t, text=f"{name}:", width=24).pack(side="left")
            
            path_value = config.get(f'template_paths.{key}', '')
            var = tk.StringVar(value=path_value)
            self.template_vars[key] = var
            
            entry = ttk.Entry(row_t, textvariable=var, width=50)
            entry.pack(side="left", padx=(4, 4), fill="x", expand=True)
            
            browse_btn = ttk.Button(
                row_t, text="浏览...", 
                command=lambda k=key, v=var: self._browse_template(k, v),
                width=8
            )
            browse_btn.pack(side="right")
        
        # ===== 日志输出区域 =====
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="8")
        log_frame.grid(row=current_row, column=0, columnspan=2, sticky="nsew", pady=(0, 0))
        current_row += 1
        
        main_frame.rowconfigure(current_row - 1, weight=1)  # 让日志区域能够扩展
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=12, 
            font=('Consolas', 9),
            state='disabled',
            wrap='word'
        )
        self.log_text.pack(fill="both", expand=True)
        
        # 配置日志文本标签颜色
        self.log_text.tag_config('info', foreground='#333333')
        self.log_text.tag_config('success', foreground='#008800')
        self.log_text.tag_config('warning', foreground='#CC8800')
        self.log_text.tag_config('error', foreground='#CC0000')
        
        # 清除日志按钮
        clear_btn = ttk.Button(log_frame, text="清除日志", command=self._clear_log)
        clear_btn.pack(anchor="e", pady=(4, 0))
    
    def _create_coord_inputs(self, parent, x_var, y_var, w_var, h_var):
        """创建坐标输入框组"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x")
        
        coords = [('X:', x_var), ('Y:', y_var), ('宽:', w_var), ('高:', h_var)]
        for label_text, var in coords:
            f = ttk.Frame(frame)
            f.pack(side="left", padx=2)
            ttk.Label(f, text=label_text, width=3).pack(side="left")
            ttk.Entry(f, textvariable=var, width=5).pack(side="left")
    
    def _browse_template(self, key: str, var: tk.StringVar):
        """浏览选择模板图片"""
        file_path = filedialog.askopenfilename(
            title=f"选择 {key} 模板图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            var.set(file_path)
    
    def _apply_params(self):
        """应用用户修改的参数到配置系统"""
        try:
            # 基本参数
            config.set('total_raffles', int(self.total_raffles_var.get()))
            config.set('similarity_threshold', float(self.similarity_var.get()))
            config.set('scan_interval', float(self.interval_var.get()))
            config.set('action_cooldown', float(self.cooldown_var.get()))
            
            # 区域坐标
            config.set('bottom_left_region.x', int(self.bl_x.get()))
            config.set('bottom_left_region.y', int(self.bl_y.get()))
            config.set('bottom_left_region.width', int(self.bl_w.get()))
            config.set('bottom_left_region.height', int(self.bl_h.get()))
            
            config.set('center_region.x', int(self.ct_x.get()))
            config.set('center_region.y', int(self.ct_y.get()))
            config.set('center_region.width', int(self.ct_w.get()))
            config.set('center_region.height', int(self.ct_h.get()))
            
            # 模板路径
            for key, var in self.template_vars.items():
                path = var.get().strip()
                if path and os.path.exists(path):
                    config.set(f'template_paths.{key}', path)
                    recognizer.clear_cache()  # 清除缓存以重新加载
            
            self._append_log("[成功] 参数已应用 ✓", 'success')
            
        except Exception as e:
            messagebox.showerror("错误", f"参数应用失败: {e}")
    
    def _on_start(self):
        """处理启动按钮点击"""
        # 先应用当前参数
        self._apply_params()
        
        total = int(self.total_raffles_var.get())
        if raffle_engine.start(total):
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_label.configure(foreground='#008800')
    
    def _on_stop(self):
        """处理停止按钮点击"""
        if raffle_engine.stop():
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
    
    def _append_log(self, message: str, tag: str = 'info'):
        """
        追加日志消息（线程安全）
        通过after方法确保在主线程中更新UI
        """
        def append():
            self.log_text.configure(state='normal')
            self.log_text.insert('end', message + '\n', tag)
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
            
            # 限制日志行数，避免内存无限增长
            line_count = int(self.log_text.index('end-1c').split('.')[0])
            max_lines = config.get('log_max_lines', 1000)
            if line_count > max_lines:
                self.log_text.delete('1.0', f'{line_count - max_lines}.0')
        
        self.root.after(0, append)
    
    def _clear_log(self):
        """清除日志内容"""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')
    
    def _update_status(self, state: str, current: int, total: int):
        """
        更新运行状态显示（通过回调触发）
        state: 'stopped' | 'running' | 'stopping' | 'finished'
        """
        def update():
            if state == 'running':
                self.status_var.set("● 运行中...")
                self.status_label.configure(foreground='#008800')
                self.progress_var.set(f"{current} / {total}")
                self.start_btn.configure(state="disabled")
                self.stop_btn.configure(state="normal")
                
            elif state == 'stopping':
                self.status_var.set("● 正在停止...")
                self.status_label.configure(foreground='#CC8800')
                
            elif state == 'stopped':
                self.status_var.set(f"● 已停止 (完成 {current}/{total})")
                self.status_label.configure(foreground='#666666')
                self.progress_var.set(f"{current} / {total}")
                self.start_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
                
            elif state == 'finished':
                self.status_var.set("✓ 全部完成！")
                self.status_label.configure(foreground='#00AA00')
                self.progress_var.set(f"{current} / {total}")
                self.start_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
        
        self.root.after(0, update)
    
    def _start_hotkey_listener(self):
        """启动全局热键监听（F1启动/F2停止）"""
        def on_press(key):
            try:
                if key == keyboard.Key.f1:
                    self.root.after(0, self._on_start)
                elif key == keyboard.Key.f2:
                    self.root.after(0, self._on_stop)
            except Exception as e:
                print(f"[错误] 热键处理异常: {e}")
        
        try:
            self._hotkey_listener = keyboard.Listener(on_press=on_press)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
        except Exception as e:
            print(f"[警告] 热键监听启动失败: {e}")
    
    def _stop_hotkey_listener(self):
        """停止热键监听"""
        if self._hotkey_listener:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
    
    def _on_closing(self):
        """处理窗口关闭事件"""
        # 停止抽奖引擎
        if raffle_engine.is_running():
            raffle_engine.stop()
        
        # 停止热键监听
        self._stop_hotkey_listener()
        
        # 销毁窗口
        self.root.destroy()


def launch_gui():
    """启动GUI界面的入口函数"""
    root = tk.Tk()
    
    # 设置主题样式（如果可用）
    try:
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
    except:
        pass
    
    app = RaffleBotGUI(root)
    root.mainloop()


if __name__ == '__main__':
    launch_gui()
