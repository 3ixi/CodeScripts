#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信小程序登录Code获取模块
用于通过微信iPad协议接口获取小程序登录Code值
模块作者：3iXi
创建时间：2025/07/04
修改时间：2025/07/09
！！需要先搭建WeChatPadPro或iwechat才能使用此模块！！
环境变量：
    WECHAT_SERVER: 协议服务IP地址和端口
    ADMIN_KEY: 与搭建时设置的ADMIN_KEY一致
    WX_ID: 可选，指定要获取Code的微信账号ID，多个用&分隔
           对应iwechat接口的wx_id字段或WeChatPadPro接口的deviceId字段
           如果不设置则获取所有有效账号的Code
"""

import os
import requests
import json
from typing import List, Dict, Tuple


class WeChatCodeGetter:
    """微信小程序Code获取模块"""
    
    def __init__(self):
        """初始化，获取环境变量"""
        self.wechat_server = os.getenv('WECHAT_SERVER')
        self.admin_key = os.getenv('ADMIN_KEY')
        self.wx_id_filter = os.getenv('WX_ID')  # 新增：WX_ID环境变量

        if not self.wechat_server:
            raise ValueError("环境变量 WECHAT_SERVER 未设置")
        if not self.admin_key:
            raise ValueError("环境变量 ADMIN_KEY 未设置")

        if not self.wechat_server.startswith('http'):
            self.wechat_server = f"http://{self.wechat_server}"

        # 解析WX_ID环境变量
        self.target_wx_ids = []
        if self.wx_id_filter:
            self.target_wx_ids = [wx_id.strip() for wx_id in self.wx_id_filter.split('&') if wx_id.strip()]
            print(f"检测到WX_ID环境变量，将筛选指定账号: {', '.join(self.target_wx_ids)}")
    
    def _is_account_valid(self, account: Dict) -> bool:
        """检查账号是否有效（基于status字段）"""
        status = account.get('status', 0)
        return status == 1

    def _filter_accounts_by_wx_id(self, accounts: List[Dict]) -> List[Dict]:
        """根据WX_ID环境变量筛选账号"""
        if not self.target_wx_ids:
            return accounts

        filtered_accounts = []
        for account in accounts:
            # 获取微信ID，支持两种接口的不同字段名
            wx_id = account.get('wx_id') or account.get('deviceId', '')
            if wx_id in self.target_wx_ids:
                filtered_accounts.append(account)

        if filtered_accounts:
            print(f"根据WX_ID筛选后获得{len(filtered_accounts)}个账号")
        else:
            print(f"警告：根据WX_ID筛选后没有找到匹配的账号")

        return filtered_accounts
    
    def get_auth_keys(self) -> List[Dict]:
        """获取授权码列表（iwechat）"""
        url = f"{self.wechat_server}/admin/GetAuthKey"
        params = {"key": self.admin_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            auth_data = response.json()
            if not isinstance(auth_data, list):
                raise ValueError("获取授权码响应格式错误")

            # 只获取status=1的有效账号
            valid_accounts = []
            for account in auth_data:
                if self._is_account_valid(account):
                    valid_accounts.append(account)

            # 根据WX_ID环境变量筛选账号
            filtered_accounts = self._filter_accounts_by_wx_id(valid_accounts)
            return filtered_accounts

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("检测到协议服务不支持GetAuthKey接口，切换到GetAllDevices接口...")
                return self._get_devices_auth_keys()
            else:
                raise Exception(f"获取授权码失败: {e}")
        except requests.RequestException as e:
            raise Exception(f"获取授权码失败: {e}")
        except json.JSONDecodeError:
            raise Exception("授权码响应数据格式错误")

    def _get_devices_auth_keys(self) -> List[Dict]:
        """获取授权码列表（WeChatPadPro）"""
        url = f"{self.wechat_server}/admin/GetAllDevices"
        params = {"key": self.admin_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            devices_data = response.json()

            if isinstance(devices_data, dict) and 'Data' in devices_data:
                data_section = devices_data['Data']
                if 'devices' in data_section:
                    auth_data = data_section['devices']
                else:
                    raise ValueError("GetAllDevices响应中Data部分缺少devices字段")
            elif isinstance(devices_data, list):
                auth_data = devices_data
            elif isinstance(devices_data, dict):
                if 'data' in devices_data:
                    auth_data = devices_data['data']
                elif 'devices' in devices_data:
                    auth_data = devices_data['devices']
                else:
                    auth_data = [devices_data]
            else:
                raise ValueError("GetAllDevices响应格式错误")

            if not isinstance(auth_data, list):
                raise ValueError("GetAllDevices响应格式错误")

            # 只获取status=1的有效账号
            valid_accounts = []
            for account in auth_data:
                if self._is_account_valid(account):
                    valid_accounts.append(account)

            print(f"通过GetAllDevices接口获取到{len(valid_accounts)}个有效账号")

            # 根据WX_ID环境变量筛选账号
            filtered_accounts = self._filter_accounts_by_wx_id(valid_accounts)
            return filtered_accounts

        except requests.RequestException as e:
            raise Exception(f"通过GetAllDevices获取授权码失败: {e}")
        except json.JSONDecodeError:
            raise Exception("GetAllDevices响应数据格式错误")

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
            license = account.get('license') or account.get('authKey')
            if not license:
                continue

            try:
                login_status = self.get_login_status(license)
                if login_status.get('loginState') == 1:
                    online_accounts.append((account, login_status))
            except Exception as e:
                nick_name = account.get('nick_name') or account.get('deviceName') or '未知'
                print(f"检查账号 {nick_name} 登录状态失败: {e}")
                continue

        return online_accounts
    
    def print_online_status(self):
        """打印在线账号状态"""
        online_accounts = self.get_online_accounts()

        print(f"当前有{len(online_accounts)}个账号在线")
        for account, status in online_accounts:
            nick_name = account.get('nick_name') or account.get('deviceName') or '未知昵称'
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

        for i, (account, _) in enumerate(online_accounts, 1):
            license = account.get('license') or account.get('authKey')
            base_nick_name = account.get('nick_name') or account.get('deviceName') or '未知昵称'

            device_id = account.get('deviceId', '')
            if not base_nick_name.strip() or base_nick_name.strip() == 'ㅤ':
                if device_id:
                    nick_name = f"设备_{device_id[-6:]}"
                else:
                    nick_name = f"账号_{i}"
            else:
                nick_name = base_nick_name

            original_nick_name = nick_name
            counter = 1
            while nick_name in codes:
                nick_name = f"{original_nick_name}_{counter}"
                counter += 1

            if not license:
                print(f"账号 {nick_name} 缺少license/authKey，跳过")
                continue

            try:
                code = self.get_applet_code(app_id, license)
                codes[nick_name] = code
                print(f"获取 {nick_name} 的Code成功: {code}")
            except Exception as e:
                print(f"获取 {nick_name} 的Code失败: {e}")
                print(f"提示：如果持续获取失败，账号 {nick_name} 可能需要重新登录")
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
    try:
        return getter.get_applet_code(app_id, license)
    except Exception as e:
        print(f"提示：如果持续获取失败，该账号可能需要重新登录")
        raise e