#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蓝氏宠物小程序签到脚本
脚本作者：3iXi
创建时间：2025/07/16
！！此脚本需要配合iPad协议服务使用！！
小程序：蓝氏宠物
"""

import time
import json
import random
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 依赖")
    exit(1)

import getCode


class LanshiSignin:
    """蓝氏宠物小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://api.vshop.hchiv.cn"
        self.app_id = "wxb7a9c0dd9a2fcc53"
        
        self.session = requests.Session()
        #self.session.verify = False
        
        self.headers = {
            "Host": "api.vshop.hchiv.cn",
            "Connection": "keep-alive",
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61(0x18003d2a) NetType/WIFI Language/zh_CN",
            "Referer": "https://servicewechat.com/wxb7a9c0dd9a2fcc53/30/page-frame.html"
        }
        
        self.activity_id: Optional[str] = None
        self.client_token: Optional[str] = None

    def get_activity_list(self) -> Optional[str]:
        """
        获取签到活动ID
        
        Returns:
            Optional[str]: 签到活动ID，获取失败返回None
        """
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "interfaceSource": 0,
            "pageNumber": 1,
            "pageSize": 20,
            "decoActStatus": []
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["Content-Length"] = str(content_length)
        
        url = f"{self.base_url}/jfmb/cloud/activity/activity/activityList"
        params = {
            "sideType": "3",
            "appId": self.app_id,
            "shopNick": self.app_id
        }
        
        try:
            response = self.session.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data", {}).get("code") == 200:
                activity_data = data.get("data", {}).get("data", {})
                data_list = activity_data.get("dataList", [])
                
                for activity in data_list:
                    activity_name = activity.get("name", "")
                    if "签到" in activity_name:
                        activity_id = str(activity.get("id"))
                        print(f"获取到签到活动: {activity_name} (ID: {activity_id})")
                        return activity_id
                
                print("未找到包含'签到'的活动")
                return None
            else:
                print(f"获取活动列表失败：{data.get('message', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"获取活动列表请求失败: {e}")
            return None

    def login(self, code: str) -> bool:
        """
        用户登录

        Args:
            code (str): 微信小程序登录code

        Returns:
            bool: 登录是否成功
        """
        timestamp = int(time.time() * 1000)

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "wxInfo": code,
            "extend": "{\"sourcePage\":\"/packageA/pages/integral-index/integral-index\",\"activityId\":\"\",\"sourceShopId\":\"\",\"guideNo\":\"\",\"way\":\"member\",\"linkType\":\"2001\"}",
            "sessionIdForWxShop": ""
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))

        headers = self.headers.copy()
        if "Authorization" in headers:
            del headers["Authorization"]
        headers["Content-Length"] = str(content_length)
        
        url = f"{self.base_url}/jfmb/cloud/member/wechatlogin/authLoginApplet"
        params = {
            "sideType": "3",
            "mob": "",
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp,
            "guideNo": ""
        }
        
        try:
            response = self.session.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data", {}).get("code") == 200:
                login_data = data.get("data", {}).get("data", {})
                client_token = login_data.get("clientToken")
                
                if client_token:
                    self.client_token = client_token
                    self.headers["Authorization"] = f"Bearer {client_token}"
                    print("账号登录成功")
                    return True
                else:
                    print("账号登录失败，请登录小程序手动签到一次授权手机号后再运行脚本")
                    return False
            else:
                print("账号登录失败，请登录小程序手动签到一次授权手机号后再运行脚本")
                return False
                
        except Exception as e:
            print(f"登录请求失败: {e}")
            return False

    def get_client_info(self) -> Optional[Dict[str, Any]]:
        """
        获取账号信息
        
        Returns:
            Optional[Dict[str, Any]]: 账号信息，获取失败返回None
        """
        timestamp = int(time.time() * 1000)
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["Content-Length"] = str(content_length)
        
        url = f"{self.base_url}/jfmb/cloud/member/tblogin/getClientInfo"
        params = {
            "sideType": "3",
            "shopNick": self.app_id
        }
        
        try:
            response = self.session.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            data_code = data.get("data", {}).get("code")
            if data_code == 200:
                client_data = data.get("data", {}).get("data", {})
                user_mob = client_data.get("user_mob")
                client_name = client_data.get("client_name")
                residual_integral = client_data.get("residualIntegral")

                print(f"账号{client_name}信息获取成功，当前积分{residual_integral}")
                return client_data
            elif data_code == 204:
                print("账号未授权，请手动登录小程序进行授权")
                return None
            else:
                message = data.get("data", {}).get("message", "未知错误")
                print(f"获取账号信息失败：{message}")
                return None
                
        except Exception as e:
            print(f"获取账号信息请求失败: {e}")
            return None

    def submit_signin(self, user_mob: str) -> bool:
        """
        提交签到
        
        Args:
            user_mob (str): 用户手机号
            
        Returns:
            bool: 签到是否成功
        """
        timestamp = int(time.time() * 1000)
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": self.activity_id
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["Content-Length"] = str(content_length)
        
        url = f"{self.base_url}/jfmb/api/play-default/sign/add-sign-new.do"
        params = {
            "sideType": "3",
            "mob": user_mob,
            "shopNick": self.app_id
        }
        
        try:
            response = self.session.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                sign_data = data.get("data", {})
                integral = sign_data.get("integral")
                integral_alias = sign_data.get("integralAlias")
                message = sign_data.get("message", "")

                if integral is not None and integral_alias:
                    print(f"签到成功，获得{integral}{integral_alias}")
                    return True
                elif message == "已签到":
                    print("今日已签到")
                    return True
                else:
                    print(f"签到失败：{message}")
                    return False
            else:
                message = data.get("message", "签到失败")
                print(f"签到失败：{message}")
                return False
                
        except Exception as e:
            print(f"签到请求失败: {e}")
            return False

    def get_final_integral(self) -> Optional[int]:
        """
        获取最新积分信息
        
        Returns:
            Optional[int]: 当前积分，获取失败返回None
        """
        timestamp = int(time.time() * 1000)
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["Content-Length"] = str(content_length)
        
        url = f"{self.base_url}/jfmb/cloud/member/tblogin/getClientInfo"
        params = {
            "sideType": "3",
            "shopNick": self.app_id
        }
        
        try:
            response = self.session.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            data_code = data.get("data", {}).get("code")
            if data_code == 200:
                client_data = data.get("data", {}).get("data", {})
                residual_integral = client_data.get("residualIntegral")

                random_phrases = [
                    "两半鸽肉配粮，猫咪练习干饭强！",
                    "吃鸽粮，猫爪无需篮球场！",
                    "鸽肉含量高，猫生练习不划水！",
                    "喵界顶流粮，鸽鸽是主食担当！",
                    "两半鸽肉配比，猫碗里唱跳RAP！",
                    "蓝氏鸽粮，唱跳RAP必备！",
                    "两半鸽肉，猫碗里打篮球！",
                    "喵咪尝鸽，直呼太美！"
                ]
                random_phrase = random.choice(random_phrases)

                print(f"当前积分{residual_integral}，{random_phrase}")
                return residual_integral
            elif data_code == 204:
                print("账号未授权，无法获取最新积分")
                return None
            else:
                message = data.get("data", {}).get("message", "未知错误")
                print(f"获取最新积分失败：{message}")
                return None
                
        except Exception as e:
            print(f"获取最新积分请求失败: {e}")
            return None

    def clear_session(self):
        """清理会话数据"""
        self.session.close()
        self.session = requests.Session()
        #self.session.verify = False
        self.client_token = None
        if "Authorization" in self.headers:
            del self.headers["Authorization"]
        self.headers["Authorization"] = "Bearer "

    def process_account(self, nick_name: str, code: str) -> bool:
        """
        处理单个账号的签到流程
        
        Args:
            nick_name (str): 账号昵称
            code (str): 微信小程序登录code
            
        Returns:
            bool: 是否处理成功
        """
        print(f"\n开始处理账号: {nick_name}")
        
        # 1. 登录
        if not self.login(code):
            print(f"账号 {nick_name} 登录失败")
            self.clear_session()
            return False
        
        # 2. 获取账号信息
        client_info = self.get_client_info()
        if not client_info:
            print(f"账号 {nick_name} 获取信息失败")
            self.clear_session()
            return False
        
        user_mob = client_info.get("user_mob")
        if not user_mob:
            print(f"账号 {nick_name} 未获取到手机号")
            self.clear_session()
            return False
        
        # 3. 提交签到
        if not self.submit_signin(user_mob):
            print(f"账号 {nick_name} 签到失败")
            self.clear_session()
            return False
        
        # 4. 获取最新积分
        self.get_final_integral()
        
        # 5. 清理会话数据
        self.clear_session()
        
        return True


def main():
    """主函数"""
    try:
        signin = LanshiSignin()
        
        print("正在获取签到活动ID...")
        activity_id = signin.get_activity_list()
        if not activity_id:
            print("获取签到活动ID失败，脚本退出")
            return
        
        signin.activity_id = activity_id
        
        print("正在获取登录Code...")
        codes = getCode.get_wechat_codes(signin.app_id)
        
        if not codes:
            print("未获取到任何在线账号的Code")
            return
        
        print(f"获取到 {len(codes)} 个账号的Code")
        
        for i, (nick_name, code) in enumerate(codes.items(), 1):
            print(f"\n{'='*50}")
            print(f"处理第 {i}/{len(codes)} 个账号")
            print(f"{'='*50}")
            
            try:
                signin.process_account(nick_name, code)
            except Exception as e:
                print(f"处理账号 {nick_name} 时发生错误: {e}")
            
            if i < len(codes):
                print(f"等待2秒后处理下一个账号...")
                time.sleep(2)
        
        print("\n所有账号处理完成")
        
    except Exception as e:
        print(f"脚本执行失败: {e}")


if __name__ == "__main__":
    main()
