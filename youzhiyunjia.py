#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优智云家品牌商城小程序签到脚本
脚本作者：3iXi
创建时间：2025/07/10
！！此脚本需要配合iPad协议服务使用！！
小程序：优智云家品牌商城
--------------------
更新时间：2025/07/18
更新内容：新增使用brotli依赖用于解压响应数据
"""

import time
import json
from typing import Optional, Dict, Any

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

try:
    import brotli
except ImportError:
    print("错误: 需要安装 brotli 依赖")
    exit(1)

import getCode


class YouzhiyunjiaSignin:
    """优智云家品牌商城小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://xapi.weimob.com"
        self.app_id = "wxa61f98248d20178b"
        
        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)
        
        self.headers = {
            "host": "xapi.weimob.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2540611) XWEB/14199",
            "content-type": "application/json",
            "accept": "*/*",
            "referer": "https://servicewechat.com/wxa61f98248d20178b/81/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9"
        }
        
        self.token = None

    def login(self, code: str) -> bool:
        """
        用户登录
        
        Args:
            code (str): 微信小程序登录code
            
        Returns:
            bool: 登录是否成功
        """
        payload = {
            "appid": self.app_id,
            "basicInfo": {
                "bosId": "4022115200359",
                "cid": "821033359",
                "tcode": "weimob",
                "vid": "6016741943359"
            },
            "env": "production",
            "extendInfo": {
                "source": 1
            },
            "is_pre_fetch_open": True,
            "parentVid": 0,
            "pid": "",
            "storeId": "",
            "code": code,
            "queryAuthConfig": True
        }
        
        # 动态计算content-length
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        
        url = f"{self.base_url}/fe/mapi/user/loginX"
        
        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("errcode") == 0:
                token = data.get("data", {}).get("token")
                if token:
                    self.token = token
                    # 添加token到后续请求头
                    self.headers["x-wx-token"] = token
                    print("登录成功")
                    return True
                else:
                    print("登录失败：未获取到token")
                    return False
            else:
                print(f"登录失败：{data.get('errmsg', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"登录请求失败: {e}")
            return False

    def check_signin_status(self) -> Optional[bool]:
        """
        检查签到状态
        
        Returns:
            Optional[bool]: True=已签到, False=未签到, None=检查失败
        """
        payload = {
            "appid": self.app_id,
            "basicInfo": {
                "vid": 6016741943359,
                "vidType": 2,
                "bosId": 4022115200359,
                "productId": 146,
                "productInstanceId": 15532102359,
                "productVersionId": "10003",
                "merchantId": 2000230069359,
                "tcode": "weimob",
                "cid": 821033359
            },
            "extendInfo": {
                "wxTemplateId": 7930,
                "analysis": [],
                "bosTemplateId": 1000001998,
                "childTemplateIds": [
                    {"customId": 90004, "version": "crm@0.1.64"},
                    {"customId": 90002, "version": "ec@69.1"},
                    {"customId": 90006, "version": "hudong@0.0.229"},
                    {"customId": 90008, "version": "cms@0.0.506"}
                ],
                "quickdeliver": {"enable": True},
                "youshu": {"enable": False},
                "source": 1,
                "channelsource": 5,
                "refer": "onecrm-signgift",
                "mpScene": 1035
            },
            "queryParameter": None,
            "i18n": {
                "language": "zh",
                "timezone": "8"
            },
            "pid": "",
            "storeId": "",
            "customInfo": {
                "source": 0,
                "wid": 11659047914
            }
        }
        
        # 动态计算content-length
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        
        url = f"{self.base_url}/api3/onecrm/mactivity/sign/misc/sign/activity/c/signMainInfo"
        
        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("errcode") == "0":
                has_sign = data.get("data", {}).get("hasSign", False)
                print(f"签到状态: {'已签到' if has_sign else '未签到'}")
                return has_sign
            else:
                print(f"检查签到状态失败：{data.get('errmsg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"检查签到状态请求失败: {e}")
            return None

    def submit_signin(self) -> Optional[Dict[str, Any]]:
        """
        提交签到
        
        Returns:
            Optional[Dict[str, Any]]: 签到奖励信息，None表示签到失败
        """
        payload = {
            "appid": self.app_id,
            "basicInfo": {
                "vid": 6016741943359,
                "vidType": 2,
                "bosId": 4022115200359,
                "productId": 146,
                "productInstanceId": 15532102359,
                "productVersionId": "10003",
                "merchantId": 2000230069359,
                "tcode": "weimob",
                "cid": 821033359
            },
            "extendInfo": {
                "wxTemplateId": 7930,
                "analysis": [],
                "bosTemplateId": 1000001998,
                "childTemplateIds": [
                    {"customId": 90004, "version": "crm@0.1.64"},
                    {"customId": 90002, "version": "ec@69.1"},
                    {"customId": 90006, "version": "hudong@0.0.229"},
                    {"customId": 90008, "version": "cms@0.0.506"}
                ],
                "quickdeliver": {"enable": True},
                "youshu": {"enable": False},
                "source": 1,
                "channelsource": 5,
                "refer": "onecrm-signgift",
                "mpScene": 1035
            },
            "queryParameter": None,
            "i18n": {
                "language": "zh",
                "timezone": "8"
            },
            "pid": "",
            "storeId": "",
            "customInfo": {
                "source": 0,
                "wid": 11659047914
            }
        }
        
        # 动态计算content-length
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        
        url = f"{self.base_url}/api3/onecrm/mactivity/sign/misc/sign/activity/core/c/sign"
        
        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("errcode") == "0":
                reward_data = data.get("data", {})
                return reward_data
            else:
                print(f"签到失败：{data.get('errmsg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"签到请求失败: {e}")
            return None

    def print_signin_rewards(self, reward_data: Dict[str, Any]):
        """
        打印签到奖励信息
        
        Args:
            reward_data (Dict[str, Any]): 签到奖励数据
        """
        fixed_reward = reward_data.get("fixedReward", {})
        extra_reward = reward_data.get("extraReward", {})
        
        reward_messages = []
        
        # 处理固定奖励
        fixed_parts = []
        if fixed_reward.get("points", 0) > 0:
            fixed_parts.append(f"{fixed_reward['points']}积分")
        if fixed_reward.get("growth", 0) > 0:
            fixed_parts.append(f"{fixed_reward['growth']}成长值")
        if fixed_reward.get("amount", 0) > 0:
            fixed_parts.append(f"{fixed_reward['amount']}余额")
        
        if fixed_parts:
            reward_messages.append(f"固定奖励{','.join(fixed_parts)}")
        
        # 处理额外奖励
        extra_parts = []
        if extra_reward.get("points", 0) > 0:
            extra_parts.append(f"{extra_reward['points']}积分")
        if extra_reward.get("growth", 0) > 0:
            extra_parts.append(f"{extra_reward['growth']}成长值")
        if extra_reward.get("amount", 0) > 0:
            extra_parts.append(f"{extra_reward['amount']}余额")
        
        if extra_parts:
            reward_messages.append(f"额外奖励{','.join(extra_parts)}")
        
        if reward_messages:
            print(f"签到成功，获得{','.join(reward_messages)}")
        else:
            print("签到成功")

    def get_account_info(self) -> Optional[int]:
        """
        获取账号积分信息
        
        Returns:
            Optional[int]: 当前积分，None表示获取失败
        """
        payload = {
            "appid": self.app_id,
            "basicInfo": {
                "vid": 6016741943359,
                "vidType": 2,
                "bosId": 4022115200359,
                "productId": 1,
                "productInstanceId": 15532140359,
                "productVersionId": "32049",
                "merchantId": 2000230069359,
                "tcode": "weimob",
                "cid": 821033359
            },
            "extendInfo": {
                "wxTemplateId": 7930,
                "analysis": [],
                "bosTemplateId": 1000001998,
                "childTemplateIds": [
                    {"customId": 90004, "version": "crm@0.1.64"},
                    {"customId": 90002, "version": "ec@69.1"},
                    {"customId": 90006, "version": "hudong@0.0.229"},
                    {"customId": 90008, "version": "cms@0.0.506"}
                ],
                "quickdeliver": {"enable": True},
                "youshu": {"enable": False},
                "source": 1,
                "channelsource": 5,
                "refer": "cms-usercenter",
                "mpScene": 1035
            },
            "queryParameter": None,
            "i18n": {
                "language": "zh",
                "timezone": "8"
            },
            "pid": "",
            "storeId": "",
            "targetBasicInfo": {
                "productInstanceId": 15532102359
            },
            "request": {}
        }
        
        # 动态计算content-length
        payload_str = json.dumps(payload, separators=(',', ':'))
        content_length = len(payload_str.encode('utf-8'))
        
        headers = self.headers.copy()
        headers["content-length"] = str(content_length)
        
        url = f"{self.base_url}/api3/onecrm/point/myPoint/getSimpleAccountInfo"
        
        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("errcode") == "0":
                points = data.get("data", {}).get("sumAvailablePoint", 0)
                print(f"当前账号有{points}积分")
                return points
            else:
                print(f"获取账号信息失败：{data.get('errmsg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"获取账号信息请求失败: {e}")
            return None

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
            return False

        # 2. 检查签到状态
        sign_status = self.check_signin_status()
        if sign_status is None:
            print(f"账号 {nick_name} 检查签到状态失败")
            return False

        if sign_status:
            print("今日已签到")
        else:
            print("未签到，开始签到")
            # 3. 提交签到
            reward_data = self.submit_signin()
            if reward_data is None:
                print(f"账号 {nick_name} 签到失败")
                return False

            # 4. 打印签到奖励
            self.print_signin_rewards(reward_data)

        # 5. 获取账号信息
        self.get_account_info()

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wxa61f98248d20178b"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = YouzhiyunjiaSignin()

        try:
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

        finally:
            signin.close()

        print("\n所有账号处理完成")

    except Exception as e:
        print(f"脚本执行失败: {e}")


if __name__ == "__main__":
    main()
