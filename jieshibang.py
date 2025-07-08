#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
杰士邦会员中心小程序签到脚本
脚本作者：3iXi
创建时间：2025/07/07
！！此脚本需要配合iPad协议服务使用！！
小程序：杰士邦会员中心
---------------
更新时间：2025/07/08（新增阅读签到活动，但是活动获取有点问题，9号修复）
"""

import json
import time
import re
from datetime import datetime
from typing import Dict, Optional

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode


class JieshibangSignin:
    """杰士邦小程序签到"""
    
    def __init__(self):
        self.base_url = "https://api.vshop.hchiv.cn"
        self.app_id = "wx5966681b4a895dee"
        self.base_headers = {
            "host": "api.vshop.hchiv.cn",
            "xweb_xhr": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF",
            "appenv": "test",
            "content-type": "application/json",
            "accept": "*/*",
            "referer": "https://servicewechat.com/wx5966681b4a895dee/47/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9"
        }
        self.headers = self.base_headers.copy()
        self.client = httpx.Client(http2=True, verify=False)
    
    def get_timestamp(self) -> int:
        """获取13位时间戳"""
        return int(time.time() * 1000)

    def clear_session(self):
        """清理会话数据，防止cookie污染"""
        self.headers = self.base_headers.copy()

        self.client.cookies.clear()

        print("会话数据已清理")
    
    def login(self, wx_info: str) -> Optional[str]:
        """登录获取token"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/member/wechatlogin/authLoginApplet"
        params = {
            "sideType": "3",
            "mob": "",
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "wxInfo": wx_info,
            "extend": "{\"sourcePage\":\"/packageA/pages/integral-index/integral-index\",\"activityId\":\"\",\"sourceShopId\":\"\",\"guideNo\":\"\",\"way\":\"member\",\"linkType\":\"2001\"}",
            "sessionIdForWxShop": ""
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))
        
        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success") and data.get("data", {}).get("success"):
                client_token = data["data"]["data"].get("clientToken")
                if client_token:
                    self.headers["authorization"] = f"Bearer {client_token}"
                    return client_token
            else:
                if data.get("data", {}).get("code") == 1012:
                    return "CODE_EXPIRED"
                
        except Exception as e:
            print(f"登录请求失败: {e}")
        
        return None
    
    def get_client_info(self) -> Optional[Dict]:
        """获取客户信息"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/member/tblogin/getClientInfo"
        params = {
            "sideType": "3",
            "mob": "",
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))
        
        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success") and data.get("data", {}).get("success"):
                return data["data"]["data"]
                
        except Exception as e:
            print(f"获取客户信息失败: {e}")
        
        return None
    
    def get_signin_activity_id(self, mob: str) -> Optional[str]:
        """获取签到活动ID"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/common/common/get-customer-page"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "pageId": 102999,
            "pageType": 2
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))
        
        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                page_json_str = data.get("data", {}).get("result", {}).get("pageJson", "")
                if page_json_str:
                    try:
                        page_json = json.loads(page_json_str)
                        
                        for module in page_json.get('moduleList', []):
                            if module.get('type') == 'iconNav':
                                if 'detail' in module and 'linkList' in module['detail']:
                                    for link in module['detail']['linkList']:
                                        if link.get('text') == '签到':
                                            return link.get('id')
                    except json.JSONDecodeError:
                        print("解析pageJson失败")
                        
        except Exception as e:
            print(f"获取签到活动ID失败: {e}")
        
        return None
    
    def signin(self, mob: str, activity_id: str) -> bool:
        """提交签到"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/api/play-default/sign/add-sign-new.do"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": activity_id
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))
        
        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                integral = data.get("data", {}).get("integral", 0)
                integral_alias = data.get("data", {}).get("integralAlias", "积分")
                print(f"签到成功，获得{integral}{integral_alias}")
                return True
            else:
                print(f"签到失败: {data.get('errorMessage', '未知错误')}")
                
        except Exception as e:
            print(f"签到请求失败: {e}")
        
        return False
    
    def get_lottery_activity_id(self, mob: str):
        """获取抽奖活动ID和名称"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/common/common/get-customer-page"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }
        
        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "pageId": 111079,
            "pageType": 2
        }
        
        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))
        
        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                page_json_str = data.get("data", {}).get("result", {}).get("pageJson", "")
                if page_json_str:
                    try:
                        page_json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', page_json_str)
                        page_json = json.loads(page_json_str)
                        
                        for module in page_json.get('moduleList', []):
                            if module.get('type') == 'imgAd':
                                detail = module.get('detail', {})
                                link_list = detail.get('linkList', [])
                                for link in link_list:
                                    zones = link.get('zones', [])
                                    for zone in zones:
                                        link_url = zone.get('linkUrl', '')
                                        if '抽奖' in link_url:
                                            return zone.get('id'), link_url
                    except json.JSONDecodeError as e:
                        print(f"解析抽奖pageJson失败: {e}")
                        
        except Exception as e:
            print(f"获取抽奖活动ID失败: {e}")
        
        return None, None

    def get_lottery_times(self, mob: str, activity_id: str) -> int:
        """获取抽奖次数"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/activity/draw/child/receiveFreeTimes"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": activity_id
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("success") and data.get("data", {}).get("success"):
                total_times = data["data"]["data"].get("totalTimes", 0)
                return total_times

        except Exception as e:
            print(f"获取抽奖次数失败: {e}")

        return 0

    def lottery(self, mob: str, activity_id: str) -> bool:
        """提交抽奖"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/activity/draw/startTurntable"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": activity_id
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("success") and data.get("data", {}).get("success"):
                prize_result = data["data"]["data"].get("prizeResult", {})
                prize_name = prize_result.get("prizeName", "未知奖品")
                print(f"抽奖成功，获得{prize_name}")
                return True
            else:
                print(f"抽奖失败: {data.get('errorMessage', '未知错误')}")

        except Exception as e:
            print(f"抽奖请求失败: {e}")

        return False

    def get_activity_list(self, mob: str) -> Optional[str]:
        """获取活动列表，查找包含"签到"的活动"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/activity/activity/activityList"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "pageNumber": 1,
            "pageSize": 20,
            "decoActStatus": ["1"]
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("success") and data.get("data", {}).get("success"):
                data_list = data["data"]["data"].get("dataList", [])
                for activity in data_list:
                    name = activity.get("name", "")
                    if "签到" in name:
                        activity_id = str(activity.get("id", ""))
                        print(f"获取到{name}")
                        return activity_id

        except Exception as e:
            print(f"获取活动列表失败: {e}")

        return None

    def get_sign_prize(self, mob: str, activity_id: str) -> Optional[str]:
        """获取签到活动奖励详情"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/cloud/activity/sign/getSignPrize"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": activity_id
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                response_list = data.get("data", {}).get("responseList", [])
                if response_list:
                    prize_name = response_list[0].get("prizeName", "未知奖品")
                    return prize_name

        except Exception as e:
            print(f"获取签到奖励详情失败: {e}")

        return None

    def add_sign_new(self, mob: str, activity_id: str) -> Optional[Dict]:
        """提交签到活动"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/api/play-default/sign/add-sign-new.do"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": activity_id
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                result_data = data.get("data", {})
                integral = result_data.get("integral", 0)
                integral_alias = result_data.get("integralAlias", "积分")
                return {"integral": integral, "integralAlias": integral_alias}

        except Exception as e:
            print(f"提交签到活动失败: {e}")

        return None

    def get_continuous_sign_days(self, mob: str, activity_id: str) -> Optional[int]:
        """获取连续签到天数"""
        timestamp = self.get_timestamp()
        url = f"{self.base_url}/jfmb/api/play-default/sign/current-month-signdays-new.do"
        params = {
            "sideType": "3",
            "mob": mob,
            "appId": self.app_id,
            "shopNick": self.app_id,
            "timestamp": timestamp
        }

        # 获取当前年月，格式为 YYYY-MM
        current_time = datetime.now().strftime("%Y-%m")

        payload = {
            "appId": self.app_id,
            "openId": True,
            "shopNick": "",
            "timestamp": timestamp,
            "interfaceSource": 0,
            "activityId": activity_id,
            "time": current_time
        }

        payload_str = json.dumps(payload, separators=(',', ':'))
        self.headers["content-length"] = str(len(payload_str.encode('utf-8')))

        try:
            response = self.client.post(url, params=params, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                result_data = data.get("data", {})
                continuous_sign_day = result_data.get("continuousSignDay", 0)
                return continuous_sign_day

        except Exception as e:
            print(f"获取连续签到天数失败: {e}")

        return None

    def process_account(self, nick_name: str, wx_info: str, license: Optional[str] = None) -> bool:
        """处理单个账号的签到和抽奖"""
        print(f"\n开始处理账号: {nick_name}")

        token = self.login(wx_info)
        if token == "CODE_EXPIRED":
            print(f"Code已过期，重新获取...")
            if license:
                try:
                    new_code = getCode.get_single_code(self.app_id, license)
                    print(f"重新获取到Code: {new_code}")
                    token = self.login(new_code)
                except Exception as e:
                    print(f"重新获取Code失败: {e}")
                    return False
            else:
                print("无法重新获取Code，跳过此账号")
                return False

        if not token:
            print(f"账号 {nick_name} 登录失败")
            self.clear_session()
            return False

        client_info = self.get_client_info()
        if not client_info:
            print(f"获取账号 {nick_name} 信息失败")
            return False

        client_name = client_info.get("client_name", nick_name)
        residual_integral = client_info.get("residualIntegral", 0)
        user_mob = client_info.get("user_mob", "")

        print(f"{client_name}登录成功，当前积分{residual_integral}")

        # 第一个签到活动
        print("\n--- 每日签到 ---")
        signin_id = self.get_signin_activity_id(user_mob)
        if signin_id:
            self.signin(user_mob, signin_id)
        else:
            print("获取签到活动ID失败")

        # 第二个签到活动流程
        print("\n--- 签到活动 ---")
        try:
            activity_id = self.get_activity_list(user_mob)
            if activity_id:
                # 获取签到奖励详情
                prize_name = self.get_sign_prize(user_mob, activity_id)
                if prize_name:
                    print(f"签到奖励：{prize_name}")

                # 提交签到
                sign_result = self.add_sign_new(user_mob, activity_id)
                if sign_result:
                    integral = sign_result.get("integral", 0)
                    integral_alias = sign_result.get("integralAlias", "积分")
                    print(f"签到成功，获得{integral}{integral_alias}")

                    # 获取连续签到天数
                    continuous_days = self.get_continuous_sign_days(user_mob, activity_id)
                    if continuous_days is not None:
                        print(f"已连续签到{continuous_days}天")
                else:
                    print("签到活动提交失败")
        except Exception as e:
            print(f"签到活动处理失败，跳过: {e}")

        # 抽奖活动
        print("\n--- 抽奖活动 ---")
        lottery_id, lottery_name = self.get_lottery_activity_id(user_mob)
        if lottery_id:
            lottery_times = self.get_lottery_times(user_mob, lottery_id)
            print(f"抽奖活动\"{lottery_name}\"可免费抽奖{lottery_times}次")

            if lottery_times > 0:
                self.lottery(user_mob, lottery_id)
            else:
                print("没有免费抽奖次数")
        else:
            print("获取抽奖活动ID失败")

        self.clear_session()

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()

    def reset_client(self):
        """重置HTTP客户端，创建新的连接"""
        self.client.close()
        self.client = httpx.Client(http2=True, verify=False)


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wx5966681b4a895dee"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = JieshibangSignin()

        try:
            for i, (nick_name, code) in enumerate(codes.items(), 1):
                print(f"\n{'='*50}")
                print(f"处理第 {i}/{len(codes)} 个账号")
                print(f"{'='*50}")

                try:
                    signin.process_account(nick_name, code)
                except Exception as e:
                    print(f"处理账号 {nick_name} 时发生错误: {e}")
                    signin.clear_session()

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
