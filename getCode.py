#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信小程序登录Code获取模块
用于通过微信iPad协议接口获取小程序登录Code值
模块作者：3iXi
创建时间：2025/07/04
！！需要先搭建WeChatPadPro或iwechat才能使用此模块！！
环境变量：
    WECHAT_SERVER: 协议服务IP地址和端口
    ADMIN_KEY: 与搭建时设置的ADMIN_KEY一致
"""

import os
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class WeChatCodeGetter:
    """微信小程序Code获取模块"""
    
    def __init__(self):
        """初始化，获取环境变量"""
        self.wechat_server = os.getenv('WECHAT_SERVER')
        self.admin_key = os.getenv('ADMIN_KEY')
        
        if not self.wechat_server:
            raise ValueError("环境变量 WECHAT_SERVER 未设置")
        if not self.admin_key:
            raise ValueError("环境变量 ADMIN_KEY 未设置")
            
        if not self.wechat_server.startswith('http'):
            self.wechat_server = f"http://{self.wechat_server}"
    
    def _is_license_valid(self, expiry_date: str) -> bool:
        """检查授权码是否过期"""
        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
            return expiry.date() >= datetime.now().date()
        except ValueError:
            return False
    
    def get_auth_keys(self) -> List[Dict]:
        """获取授权码列表"""
        url = f"{self.wechat_server}/admin/GetAuthKey"
        params = {"key": self.admin_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            auth_data = response.json()
            if not isinstance(auth_data, list):
                raise ValueError("获取授权码响应格式错误")
            
            valid_accounts = []
            for account in auth_data:
                if self._is_license_valid(account.get('expiry_date', '')):
                    valid_accounts.append(account)
            
            return valid_accounts
            
        except requests.RequestException as e:
            raise Exception(f"获取授权码失败: {e}")
        except json.JSONDecodeError:
            raise Exception("授权码响应数据格式错误")
    
    def get_login_status(self, license: str) -> Dict:
        """获取登录状态"""
        url = f"{self.wechat_server}/login/GetLoginStatus"
        params = {"key": license}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            if status_data.get('Code') != 200:
                raise Exception(f"获取登录状态失败: {status_data.get('Text', '未知错误')}")
            
            return status_data.get('Data', {})
            
        except requests.RequestException as e:
            raise Exception(f"获取登录状态失败: {e}")
        except json.JSONDecodeError:
            raise Exception("登录状态响应数据格式错误")
    
    def get_online_accounts(self) -> List[Tuple[Dict, Dict]]:
        """获取在线账号列表"""
        accounts = self.get_auth_keys()
        online_accounts = []
        
        for account in accounts:
            license = account.get('license')
            if not license:
                continue
                
            try:
                login_status = self.get_login_status(license)
                if login_status.get('loginState') == 1:
                    online_accounts.append((account, login_status))
            except Exception as e:
                print(f"检查账号 {account.get('nick_name', '未知')} 登录状态失败: {e}")
                continue
        
        return online_accounts
    
    def print_online_status(self):
        """打印在线账号状态"""
        online_accounts = self.get_online_accounts()
        
        print(f"当前有{len(online_accounts)}个账号在线")
        for account, status in online_accounts:
            nick_name = account.get('nick_name', '未知昵称')
            online_time = status.get('onlineTime', '未知在线时间')
            print(f"{nick_name} {online_time}")
    
    def get_applet_code(self, app_id: str, license: str) -> str:
        """获取小程序登录Code"""
        url = f"{self.wechat_server}/applet/JsLogin"
        params = {"key": license}
        payload = {
            "AppId": app_id,
            "Data": "",
            "Opt": 1,
            "PackageName": "",
            "SdkName": ""
        }
        
        try:
            response = requests.post(url, params=params, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('Code') != 200:
                raise Exception(f"获取小程序Code失败: {result.get('Text', '未知错误')}")
            
            data = result.get('Data', {})
            code = data.get('Code')
            if not code:
                raise Exception("响应中未找到Code值")
            
            return code
            
        except requests.RequestException as e:
            raise Exception(f"请求小程序Code失败: {e}")
        except json.JSONDecodeError:
            raise Exception("小程序Code响应数据格式错误")
    
    def get_codes_for_all_online_accounts(self, app_id: str) -> Dict[str, str]:
        """为所有在线账号获取小程序Code"""
        online_accounts = self.get_online_accounts()
        codes = {}
        
        for account, _ in online_accounts:
            license = account.get('license')
            nick_name = account.get('nick_name', '未知昵称')
            
            try:
                code = self.get_applet_code(app_id, license)
                codes[nick_name] = code
                print(f"获取 {nick_name} 的Code成功: {code}")
            except Exception as e:
                print(f"获取 {nick_name} 的Code失败: {e}")
                continue
        
        return codes


def get_wechat_codes(app_id: str) -> Dict[str, str]:
    """
    获取所有在线微信账号的小程序登录Code
    
    Args:
        app_id (str): 小程序AppId
        
    Returns:
        Dict[str, str]: 账号昵称到Code的映射字典
        
    Raises:
        ValueError: 环境变量未设置
        Exception: 网络请求或数据处理错误
    """
    getter = WeChatCodeGetter()
    return getter.get_codes_for_all_online_accounts(app_id)


def print_online_status():
    """打印当前在线账号状态"""
    getter = WeChatCodeGetter()
    getter.print_online_status()


def get_single_code(app_id: str, license: str) -> str:
    """
    为指定授权码获取小程序登录Code
    
    Args:
        app_id (str): 小程序AppId
        license (str): 微信账号授权码
        
    Returns:
        str: 小程序登录Code
        
    Raises:
        ValueError: 环境变量未设置
        Exception: 网络请求或数据处理错误
    """
    getter = WeChatCodeGetter()
    return getter.get_applet_code(app_id, license)