#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块 - 仅用于捕获脚本输出并转发给notify.py
创建日期：2025-09-17
模块作者：3iXi
项目主页：https://github.com/3ixi/CloudScripts
使用方法：访问青龙面板，打开“配置文件”页面，从44行开始，找到自己想要使用的推送方式，在双引号中填入对应的配置，脚本运行结束后会自动发送通知。
"""

import os
import sys
from datetime import datetime

# ==================== notify.py 集成 ====================
NOTIFY_PATHS = ['./notify.py', '../notify.py']
HAS_NOTIFY = False
notify_send = None

for path in NOTIFY_PATHS:
    if os.path.exists(path):
        try:
            sys.path.append(os.path.dirname(os.path.abspath(path)))
            from notify import send as notify_send
            HAS_NOTIFY = True
            break
        except ImportError:
            continue

if not HAS_NOTIFY:
    print("⚠️ 未找到青龙自带通知模块，请确保notify.py文件存在于当前目录或上级目录中")
    print("   访问青龙面板，打开“配置文件”页面，从44行开始，找到自己想要使用的推送方式，在双引号中填入对应的配置")

# ==================== 输出捕获类 ====================
class OutputCapture:
    
    def __init__(self):
        self.content = []
        self.original_stdout = sys.stdout
        self.capture_enabled = False
    
    def start_capture(self):
        if not self.capture_enabled:
            self.capture_enabled = True
            sys.stdout = self._DualOutput(self.original_stdout, self)
    
    def stop_capture(self):
        if self.capture_enabled:
            sys.stdout = self.original_stdout
            self.capture_enabled = False
    
    def add_content(self, content):
        if content:
            self.content.append(str(content))
    
    def get_content(self):
        return "\n".join(self.content)
    
    def clear(self):
        self.content.clear()
    
    def __enter__(self):
        self.start_capture()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_capture()
    
    class _DualOutput:
        
        def __init__(self, original_stdout, capture_instance):
            self.original_stdout = original_stdout
            self.capture_instance = capture_instance
        
        def write(self, text):
            self.original_stdout.write(text)
            if text.strip():
                self.capture_instance.add_content(text.strip())
        
        def flush(self):
            self.original_stdout.flush()
        
        def __getattr__(self, name):
            return getattr(self.original_stdout, name)

_global_output_capture = OutputCapture()

def capture_output(title="脚本运行结果"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global _global_output_capture
            
            _global_output_capture.clear()
            _global_output_capture.start_capture()
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                _global_output_capture.add_content(f"❌ 脚本运行错误: {e}")
                raise
            finally:
                _global_output_capture.stop_capture()
                
                captured_content = _global_output_capture.get_content()
                if captured_content:
                    SendNotify(title, captured_content)
        
        return wrapper
    return decorator


def start_capture():
    global _global_output_capture
    _global_output_capture.clear()
    _global_output_capture.start_capture()


def stop_capture_and_notify(title="脚本运行结果"):
    global _global_output_capture
    _global_output_capture.stop_capture()
    
    captured_content = _global_output_capture.get_content()
    if captured_content:
        SendNotify(title, captured_content)


def add_to_capture(content):
    global _global_output_capture
    _global_output_capture.add_content(content)


class NotificationSender:
    def __init__(self):
        pass

    def _truncate_title(self, content: str, max_length: int = 30) -> str:
        if not content:
            return "3iXi云函数脚本通知"
        
        title = content.replace('\n', ' ').replace('\r', ' ').strip()
        if len(title) > max_length:
            title = title[:max_length] + "..."
        
        return title or "3iXi云函数脚本通知"

    def _get_current_time(self) -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def send_notification(self, title: str = "", content: str = "") -> bool:
        if not content:
            print("⚠️ 通知内容为空，跳过推送")
            return False
        
        if not title:
            title = self._truncate_title(content)
        
        timestamp = self._get_current_time()
        content = f"发送时间: {timestamp}\n\n{content}"
        
        if HAS_NOTIFY and notify_send:
            try:
                notify_send(title, content)
                print("✅ 通知已通过notify.py发送")
                return True
            except Exception as e:
                print(f"❌ 通过notify.py发送通知失败: {e}")
                return False
        else:
            print("⚠️ 未找到notify.py模块，无法发送通知")
            print("   请确保notify.py文件存在于当前目录或上级目录中")
            print("   访问青龙面板，打开“配置文件”页面，找到自己想要使用的推送方式填入对应的配置")
            return False


_notification_sender = None

def SendNotify(title: str = "", content: str = "") -> bool:
    global _notification_sender
    
    if _notification_sender is None:
        _notification_sender = NotificationSender()
    
    return _notification_sender.send_notification(title, content)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("📱 SendNotify通知模块测试")
    print("=" * 30)
    
    # 测试通知
    test_title = "SendNotify测试通知"
    test_content = """这是一条测试通知消息。

测试内容包括：
✅ 通知模块正常工作
📱 仅通过notify.py推送功能测试成功

如果您收到此消息，说明通知配置正确"""
    
    result = SendNotify(test_title, test_content)
    
    if result:
        print("✅ 测试完成，通知发送成功")
    else:
        print("❌ 测试完成，但通知发送失败")