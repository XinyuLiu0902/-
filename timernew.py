import tkinter as tk
from tkinter import messagebox
import time
import threading
import winsound  # Windows系统音效
from datetime import datetime
import os
from pathlib import Path
import subprocess
import platform

class FloatingTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("计时器")
        self.root.overrideredirect(True)  # 移除窗口边框
        self.root.attributes("-topmost", True)  # 窗口置顶
        self.root.attributes("-alpha", 0.75)  # 设置透明度
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("300x240")
        
        # 初始化变量
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False
        self.is_paused = False
        self.is_minimized = False
        self.is_always_top = True
        self.timer_finished_triggered = False
        
        # 时间记录相关
        self.start_time = None
        self.end_time = None
        self.pause_start_time = None
        self.total_pause_seconds = 0
        self.current_pause_start = None  # 当前暂停开始时间
        
        # 精确计时相关
        self.target_end_time = None  # 目标结束时间
        self.last_update_time = None  # 最后更新时间
        
        # 拖拽相关变量
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # 字体大小相关
        self.base_font_size = 24  # 基础字号
        self.min_font_size = 16   # 最小字号
        self.max_font_size = 48   # 最大字号
        
        # 线程控制
        self.timer_thread = None
        self.stop_thread = False
        
        # 文件路径
        self.desktop_path = Path.home() / "Desktop"
        self.file_path = self.desktop_path / "timer.txt"

        # 创建说明和版权信息
        self.help_text = "1. 在上方输入框设置时分秒。\n2. 点击[开始]按钮启动倒计时。\n3. 点击[暂停]可暂停计时，再次点击继续。\n4. 点击[重置]可恢复初始设置。\n提示：窗口可拖拽、可调整大小。\nCopyright: This toolkit is jointly developed by Han Chaoliang from the School of Economics, Harbin University of Commerce, and Xue Jianpo from the Wang Yanan Institute for Studies in Economics, Xiamen University."
        
        # 创建UI
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        # 初始位置
        self.root.geometry("+100+100")
        
    def create_widgets(self):
        # 主框架
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e", bd=1, relief="solid")
        self.main_frame.pack(fill="both", expand=True)
        
        # 标题栏
        self.header_frame = tk.Frame(self.main_frame, bg="black", height=30)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        
        self.title_label = tk.Label(self.header_frame, text="计时器", 
                                   bg="black", fg="#f0f0f0", font=("Arial", 10, "bold"))
        self.title_label.pack(side="left", padx=10)
        
        self.controls_frame = tk.Frame(self.header_frame, bg="black")
        self.controls_frame.pack(side="right", padx=5)
        
        # 将取消置顶按钮移到标题栏
        self.always_top_btn = tk.Button(self.controls_frame, text="⊤", 
                                       bg="#3498db", fg="white", font=("Arial", 8, "bold"),
                                       width=2, height=1, bd=0,
                                       command=self.toggle_always_top)
        self.always_top_btn.pack(side="left", padx=2)
        
        self.minimize_btn = tk.Button(self.controls_frame, text="−", 
                                     bg="#f39c12", fg="white", font=("Arial", 8),
                                     width=2, height=1, bd=0,
                                     command=self.toggle_minimize)
        self.minimize_btn.pack(side="left", padx=2)
        
        self.close_btn = tk.Button(self.controls_frame, text="×", 
                                  bg="#e74c3c", fg="white", font=("Arial", 8),
                                  width=2, height=1, bd=0,
                                  command=self.close_app)
        self.close_btn.pack(side="left", padx=2)
        
        # 内容区域 - 使用pack布局但添加居中容器
        self.content_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 第一行：时间显示 - 使用可调整的字号
        self.time_display = tk.Label(self.content_frame, text="00:00:00", 
                                    bg="#1e1e1e", fg="white", 
                                    font=("Arial", self.base_font_size, "bold"))
        self.time_display.pack(expand=True, fill="both")
        
        # 第二行：控制按钮（放在输入框上面）
        self.buttons_container = tk.Frame(self.content_frame, bg="#1e1e1e")
        self.buttons_container.pack(pady=5)
        
        self.start_btn = tk.Button(self.buttons_container, text="开始", 
                                  bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                                  width=5, height=1, bd=0,
                                  command=self.start_timer)
        self.start_btn.pack(side="left", padx=8)
        
        self.pause_btn = tk.Button(self.buttons_container, text="暂停", 
                                  bg="#f39c12", fg="white", font=("Arial", 10, "bold"),
                                  width=5, height=1, bd=0,
                                  state="disabled",
                                  command=self.pause_timer)
        self.pause_btn.pack(side="left", padx=8)
        
        self.reset_btn = tk.Button(self.buttons_container, text="重置", 
                                  bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                                  width=5, height=1, bd=0,
                                  command=self.reset_timer)
        self.reset_btn.pack(side="left", padx=8)
        # --- 添加第四个按钮 ---
        self.info_btn = tk.Button(self.buttons_container, 
                                  text="说明",  # 按钮文字
                                  bg="#9b59b6",  # 按钮颜色
                                  fg="white", 
                                  font=("Arial", 10, "bold"), 
                                  width=5, 
                                  height=1, 
                                  bd=0, 
                                  command=self.show_info_dialog) # 绑定点击事件
        self.info_btn.pack(side="left", padx=8) # 紧挨着前面的按钮排列
        
        # 第三行：时间输入框 - 添加居中容器
        self.input_container = tk.Frame(self.content_frame, bg="#1e1e1e")
        self.input_container.pack(pady=8)
        
        # 小时设置
        self.hours_input = tk.Spinbox(self.input_container, from_=0, to=23, 
                                     width=3, font=("Arial", 10),
                                     validate="key", 
                                     validatecommand=(self.root.register(self.validate_input), '%P'))
        self.hours_input.delete(0, "end")
        self.hours_input.insert(0, "0")
        self.hours_input.pack(side="left", padx=2)
        
        self.hours_label = tk.Label(self.input_container, text="时", bg="#1e1e1e", fg="white")
        self.hours_label.pack(side="left", padx=2)
        
        # 分钟设置
        self.minutes_input = tk.Spinbox(self.input_container, from_=0, to=59, 
                                       width=3, font=("Arial", 10),
                                       validate="key", 
                                       validatecommand=(self.root.register(self.validate_input), '%P'))
        self.minutes_input.delete(0, "end")
        self.minutes_input.insert(0, "5")
        self.minutes_input.pack(side="left", padx=8)
        
        self.minutes_label = tk.Label(self.input_container, text="分", bg="#1e1e1e", fg="white")
        self.minutes_label.pack(side="left", padx=2)
        
        # 秒钟设置
        self.seconds_input = tk.Spinbox(self.input_container, from_=0, to=59, 
                                       width=3, font=("Arial", 10),
                                       validate="key", 
                                       validatecommand=(self.root.register(self.validate_input), '%P'))
        self.seconds_input.delete(0, "end")
        self.seconds_input.insert(0, "0")
        self.seconds_input.pack(side="left", padx=8)
        
        self.seconds_label = tk.Label(self.input_container, text="秒", bg="#1e1e1e", fg="white")
        self.seconds_label.pack(side="left", padx=2)
        
        # 第四行：状态显示
        self.status_label = tk.Label(self.content_frame, text="准备就绪", 
                                    bg="#1e1e1e", fg="#bbb", font=("Arial", 9))
        self.status_label.pack(pady=5)
        
        # 底部栏
        self.footer_frame = tk.Frame(self.main_frame, bg="black", height=20)
        self.footer_frame.pack(fill="x")
        self.footer_frame.pack_propagate(False)
        
        self.drag_label = tk.Label(self.footer_frame, text="拖拽移动 • 右下角调整大小", 
                                  bg="black", fg="#aaa", font=("Arial", 8))
        self.drag_label.pack(side="left", padx=10)
        
        # 添加调整大小的控制点
        self.create_resize_handle()
        
    def create_resize_handle(self):
        """创建调整大小的控制点"""
        # 右下角调整大小控制点
        self.resize_handle = tk.Frame(self.main_frame, bg="#3498db", width=10, height=10)
        self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
        
        # 绑定调整大小事件
        self.resize_handle.bind("<ButtonPress-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.on_resize)
        self.resize_handle.bind("<ButtonRelease-1>", self.stop_resize)
        
    def start_resize(self, event):
        """开始调整大小"""
        self.is_resizing = True
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.initial_width = self.root.winfo_width()
        self.initial_height = self.root.winfo_height()
        
    def on_resize(self, event):
        """调整大小过程中"""
        if hasattr(self, 'is_resizing') and self.is_resizing:
            # 计算新的宽度和高度
            delta_x = event.x_root - self.resize_start_x
            delta_y = event.y_root - self.resize_start_y
            
            # 根据是否最小化设置不同的最小尺寸
            if self.is_minimized:
                min_width = 300
                min_height = 180
            else:
                min_width = 300
                min_height = 240
                
            new_width = max(min_width, self.initial_width + delta_x)
            new_height = max(min_height, self.initial_height + delta_y)
            
            self.root.geometry(f"{int(new_width)}x{int(new_height)}")
            
            # 根据窗口大小调整字号
            self.adjust_font_size(new_width, new_height)
            
    def adjust_font_size(self, width, height):
        """根据窗口大小调整时间显示的字号"""
        # 基于窗口面积计算字号
        if self.is_minimized:
            base_area = 240 * 144  # 最小化模式的基础面积
        else:
            base_area = 300 * 240  # 正常模式的基础面积
            
        current_area = width * height
        
        # 计算字号缩放比例
        scale_factor = max(1.0, min(8.0, current_area / base_area))
        
        # 计算新字号
        new_font_size = max(self.min_font_size, 
                           min(144, 
                               int(self.base_font_size * scale_factor)))
        
        # 更新时间显示的字体
        self.time_display.config(font=("Arial", new_font_size, "bold"))
        
    def stop_resize(self, event):
        """停止调整大小"""
        self.is_resizing = False
        
    def bind_events(self):
        # 拖拽事件
        self.header_frame.bind("<ButtonPress-1>", self.start_drag)
        self.header_frame.bind("<B1-Motion>", self.drag)
        self.header_frame.bind("<ButtonRelease-1>", self.stop_drag)
        
        # 点击事件传递
        self.title_label.bind("<ButtonPress-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.drag)
        self.title_label.bind("<ButtonRelease-1>", self.stop_drag)
        
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self.on_window_configure)
        
    def on_window_configure(self, event):
        """窗口大小变化时的回调"""
        if event.widget == self.root:
            # 只有在主窗口大小变化时才调整字号
            self.adjust_font_size(event.width, event.height)
        
    def validate_input(self, value):
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
        
    def format_time(self, seconds):
        """格式化时间显示为 时:分:秒"""
        is_negative = seconds < 0
        abs_seconds = abs(seconds)
        
        hours = abs_seconds // 3600
        minutes = (abs_seconds % 3600) // 60
        secs = abs_seconds % 60
        
        sign = "-" if is_negative else ""
        return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def format_duration(self, seconds):
        """格式化持续时间"""
        if seconds is None:
            return "--"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def update_display(self):
        self.time_display.config(text=self.format_time(self.remaining_seconds))
        
        # 如果倒计时结束，显示红色
        if self.remaining_seconds <= 0 and self.is_running:
            self.time_display.config(fg="#ff6b6b")
            # 更新状态显示超时时间
            if self.remaining_seconds < 0:
                self.status_label.config(text=f"超时 {self.format_time(abs(self.remaining_seconds))}")
            else:
                self.status_label.config(text="时间到！")
        else:
            self.time_display.config(fg="white")
    
    def start_timer(self):
        if self.is_running and not self.is_paused:
            return
        
        # 重置完成触发标志
        self.timer_finished_triggered = False
        self.stop_thread = False
        
        if not self.is_running:
            # 从输入框获取时间
            try:
                hours = int(self.hours_input.get())
                minutes = int(self.minutes_input.get())
                seconds = int(self.seconds_input.get())
            except ValueError:
                self.status_label.config(text="请输入有效时间")
                return
                
            self.total_seconds = hours * 3600 + minutes * 60 + seconds
            self.remaining_seconds = self.total_seconds
            
            if self.total_seconds <= 0:
                self.status_label.config(text="请输入有效时间")
                return
            
            self.is_running = True
            self.is_paused = False
            
            # 记录开始时间和目标结束时间
            self.start_time = datetime.now()
            self.target_end_time = time.time() + self.total_seconds
            self.total_pause_seconds = 0
            self.current_pause_start = None
            self.last_update_time = time.time()
            
        elif self.is_paused:
            # 从暂停状态恢复
            self.is_paused = False
            self.pause_btn.config(text="暂停")
            
            # 计算本次暂停时长并累加，同时调整目标结束时间
            if self.current_pause_start:
                pause_duration = time.time() - self.current_pause_start
                self.total_pause_seconds += pause_duration
                self.target_end_time += pause_duration  # 延长目标结束时间
                self.current_pause_start = None
        
        self.update_display()
        self.status_label.config(text="倒计时进行中...")
        
        # 禁用输入和开始按钮
        self.hours_input.config(state="disabled")
        self.minutes_input.config(state="disabled")
        self.seconds_input.config(state="disabled")
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        
        # 启动倒计时线程
        self.timer_thread = threading.Thread(target=self.countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()
    
    def countdown(self):
        last_update_time = time.time()
        
        while self.is_running and not self.stop_thread:
            current_time = time.time()
            if not self.is_paused:
                # 精确计时，避免累积误差
                if current_time - last_update_time >= 1.0:
                    self.remaining_seconds -= 1
                    self.root.after(0, self.update_display)
                    last_update_time = current_time
                    
                    # 检查是否刚刚到达0秒（只触发一次）
                    if self.remaining_seconds == 0 and not self.timer_finished_triggered:
                        self.timer_finished_triggered = True
                        self.root.after(0, self.timer_finished)
                
                time.sleep(0.05)  # 减少CPU占用，提高响应性
            else:
                last_update_time = current_time
                time.sleep(0.05)
       
    def timer_finished(self):
        self.root.update_idletasks()
        self.status_label.config(text="时间到！")
        #self.play_beep()播放提示音
    
    def pause_timer(self):
        if not self.is_running:
            return
        
        if not self.is_paused:
            # 开始暂停
            self.is_paused = True
            self.current_pause_start = time.time()  # 记录暂停开始时间
            self.pause_btn.config(text="继续")
            self.status_label.config(text="已暂停")
        else:
            # 继续计时
            self.is_paused = False
            # 计算本次暂停时长并累加，同时调整目标结束时间
            if self.current_pause_start:
                pause_duration = time.time() - self.current_pause_start
                self.total_pause_seconds += pause_duration
                self.target_end_time += pause_duration  # 延长目标结束时间
                self.current_pause_start = None
            self.pause_btn.config(text="暂停")
            self.status_label.config(text="倒计时进行中...")
    
    def reset_timer(self):
        # 先停止线程
        self.stop_thread = True
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
        
        # 如果计时器正在运行，保存记录
        if self.is_running and self.start_time:
            self.end_time = datetime.now()
            total_duration = (self.end_time - self.start_time).total_seconds()
            
            # 如果当前处于暂停状态，需要加上当前的暂停时长
            if self.is_paused and self.current_pause_start:
                current_pause_duration = time.time() - self.current_pause_start
                self.total_pause_seconds += current_pause_duration
            
            # 计算超时时间（如果计时器超时）
            overtime = 0
            if self.remaining_seconds < 0:
                overtime = abs(self.remaining_seconds)
            
            # 实际运行时间 = 总时长 - 暂停时长
            actual_running_duration = total_duration - self.total_pause_seconds
            
            # 保存记录到文件
            self.save_record(total_duration, actual_running_duration, overtime)
        
        # 重置所有状态
        self.is_running = False
        self.is_paused = False
        try:
            hours = int(self.hours_input.get())
            minutes = int(self.minutes_input.get())
            seconds = int(self.seconds_input.get())
            self.remaining_seconds = hours * 3600 + minutes * 60 + seconds
        except ValueError:
            self.remaining_seconds = 0
        self.timer_finished_triggered = False
        self.start_time = None
        self.end_time = None
        self.target_end_time = None
        self.total_pause_seconds = 0
        self.current_pause_start = None
        
        self.update_display()
        
        # 启用输入和开始按钮
        self.hours_input.config(state="normal")
        self.minutes_input.config(state="normal")
        self.seconds_input.config(state="normal")
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.pause_btn.config(text="暂停")
        
        self.time_display.config(fg="white")
        self.status_label.config(text="已重置")
    
    def save_record(self, total_duration, actual_duration, overtime):
        """保存记录到桌面timer.txt文件"""
        try:
            # 实际运行时间 = 实际运行时长 + 超时时间
            actual_running_with_overtime = actual_duration + overtime
            
            record = (
                f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"程序总计用时（从开始到结束）: {self.format_duration(int(total_duration))}\n"
                f"暂停时长: {self.format_duration(int(self.total_pause_seconds))}\n"
                f"*预设时间: {self.format_duration(self.total_seconds)}\n"
                f"*超时时间（与预设时间超出用时）: {self.format_duration(int(overtime))}\n"
                f"*实际运行时间（实际总用时）: {self.format_duration(int(actual_duration))}\n"
                f"{'='*50}\n"
            )
            
            # 追加模式写入文件
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(record)
            
            print(f"记录已保存: 预设时间={self.total_seconds}秒,暂停时长={self.total_pause_seconds:.2f}秒, 超时时间={overtime}秒")
            
        except Exception as e:
            print(f"保存记录失败: {e}")
    
    def open_timer_file(self):
        """打开timer.txt文件"""
        try:
            if self.file_path.exists():
                if platform.system() == "Windows":
                    os.startfile(self.file_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(self.file_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(self.file_path)])
            else:
                # 如果文件不存在，创建一个空文件再打开
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write("计时器记录文件\n" + "="*50 + "\n")
                self.open_timer_file()
        except Exception as e:
            print(f"打开文件失败: {e}")
    
    # def play_beep(self):
        # try:
            # Windows系统音效
            # winsound.Beep(1000, 1000)  # 频率1000Hz，持续1秒
        # except:
            # 如果winsound不可用，尝试其他方法
            # print("\a")  # 系统提示音
    
    def toggle_minimize(self):
        self.is_minimized = not self.is_minimized
        
        if self.is_minimized:
            # 隐藏输入框和状态显示，保留按钮和时间显示
            self.input_container.pack_forget()
            self.status_label.pack_forget(pady=5, fill='x')
            self.footer_frame.pack_forget()
            # 注意：不隐藏调整大小按钮，让最小化模式也能调整大小
            self.minimize_btn.config(text="+")
            # 设置最小化模式的最小尺寸
            self.root.geometry("300x180")
        else:
            # 恢复显示
            self.input_container.pack(pady=8)
            self.status_label.pack(pady=5)
            self.footer_frame.pack(fill="x")
            self.minimize_btn.config(text="−")
            self.root.geometry("300x240")

    def show_info_dialog(self):
        """
       弹出一个显示指定文本的对话框
        """
        # 创建顶级窗口 (Toplevel) 作为弹窗
        dialog = tk.Toplevel(self.root)
        dialog.title("版权信息") # 弹窗标题
    
        # 设置弹窗属性
        dialog.geometry("400x200") # 设置弹窗大小
        dialog.configure(bg="white") # 与主界面一致的背景色
        dialog.transient(self.root)  # 设置为临时窗口（跟随主窗口）
        dialog.grab_set()            # 模态：点击弹窗外无效
    
        # 计算居中位置
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 6)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
        # 创建文本标签
        text_widget = tk.Text(dialog, 
                              bg="#ffffff", 
                              fg="black", 
                              font=("Arial", 10),
                              wrap="word", # 自动换行
                              padx=10,
                              pady=10)
        text_widget.insert("1.0", self.help_text) # 插入定义好的文本
        text_widget.config(state="disabled") # 设置为只读
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)
    
        # 创建关闭按钮
        close_btn = tk.Button(dialog, 
                              text="关闭", 
                              command=dialog.destroy,
                              bg="#e74c3c",
                              fg="white")
        close_btn.pack(pady=5)
    
    def close_app(self):
        # 先询问用户是否确认关闭
        if messagebox.askokcancel("关闭", "确定要关闭计时器吗？所有已经重置的结果将被保存在桌面的timer.txt文件内！"):
            # 只有在用户确认关闭时才停止线程
            self.stop_thread = True
            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread.join(timeout=1.0)
            
            # 退出前打开timer.txt文件
            self.open_timer_file()
            
            self.root.destroy()
        else:
            # 用户取消关闭，不执行任何操作，计时器继续运行
            pass
    
    def toggle_always_top(self):
        self.is_always_top = not self.is_always_top
        self.root.attributes("-topmost", self.is_always_top)
        self.always_top_btn.config(text="⊤" if self.is_always_top else "⬇")
        # 更新按钮颜色提示状态
        if self.is_always_top:
            self.always_top_btn.config(bg="#3498db", fg="white")
        else:
            self.always_top_btn.config(bg="#95a5a6", fg="white")
    
    def start_drag(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
    
    def drag(self, event):
        if self.is_dragging:
            x = self.root.winfo_x() + (event.x_root - self.drag_start_x)
            y = self.root.winfo_y() + (event.y_root - self.drag_start_y)
            self.root.geometry(f"+{x}+{y}")
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
    
    def stop_drag(self, event):
        self.is_dragging = False
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    timer = FloatingTimer()
    timer.run()
