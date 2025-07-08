#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1点点小程序签到脚本
脚本作者：3iXi
创建时间：2025/07/07
！！此脚本需要配合iPad协议服务使用！！
小程序：1点点alittleTea+
---------------
更新时间：2025/07/08（修复是否签到的判断逻辑，但是还需要修复签到积分获取逻辑，9号修复）
"""

import time
import hashlib
from collections import OrderedDict
from typing import Optional, Tuple
from datetime import datetime

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode


class YidiandianSignin:
    """1点点小程序签到类"""

    DEFAULT_KEY = "4645f747025858aa92bdf966eb3d3abc"  # n=1时使用
    SPECIAL_KEY = "11829b37265314822e26f5425e64e1f4"  # n=2时使用

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://crmapi.alittle-group.cn"
        self.app_id = "202201129689"

        self.client = httpx.Client(http2=True, timeout=30.0)

        self.headers = {
            "host": "crmapi.alittle-group.cn",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B)",
            "content-type": "application/json",
            "accept": "*/*",
            "referer": "https://servicewechat.com/wxe87f500c8cef4c8a/255/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9"
        }

    def generate_sign(self, params, sign_type=1):
        """
        生成签名

        Args:
            params (dict): 请求参数字典
            sign_type (int): 签名类型，1=默认密钥，2=特殊密钥

        Returns:
            str: MD5签名值
        """
        # 1. 复制参数（避免修改原参数）
        sign_params = params.copy()

        # 2. 移除sign参数（如果存在）
        if 'sign' in sign_params:
            del sign_params['sign']

        # 3. 按键名排序
        sorted_params = OrderedDict(sorted(sign_params.items()))

        # 4. 添加密钥
        if sign_type == 2:
            sorted_params['key'] = self.SPECIAL_KEY
        else:
            sorted_params['key'] = self.DEFAULT_KEY

        # 5. 拼接参数字符串
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])

        # 6. MD5加密
        sign = hashlib.md5(param_string.encode('utf-8')).hexdigest()

        return sign
    
    def get_openid_unionid(self, js_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取openid和unionid
        
        Args:
            js_code (str): 微信小程序登录code
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (openid, unionid)
        """
        params = {
            "method": "crm.wechat.openid",
            "js_code": js_code,
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }
        
        sign = self.generate_sign(params)
        params["sign"] = sign
        
        url = f"{self.base_url}/open"
        
        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("errCode") == 10000:
                result_data = data.get("data", {})
                openid = result_data.get("openid")
                unionid = result_data.get("unionid")
                
                if openid and unionid:
                    print("登录成功")
                    return openid, unionid
                else:
                    print("登录失败：未获取到openid或unionid")
                    return None, None
            else:
                print(f"登录失败：{data.get('errMsg', '未知错误')}")
                return None, None
                
        except Exception as e:
            print(f"登录请求失败: {e}")
            return None, None
    
    def get_token(self, openid: str, unionid: str) -> Tuple[Optional[str], Optional[str]]:
        """
        换取Token
        
        Args:
            openid (str): 微信openid
            unionid (str): 微信unionid
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (token, nickname)
        """
        params = {
            "method": "crm.member.wechat.user.login",
            "openid": openid,
            "unionid": unionid,
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }
        
        sign = self.generate_sign(params)
        params["sign"] = sign
        
        url = f"{self.base_url}/open"
        
        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("errCode") == 10000:
                result_data = data.get("data", {})
                token = result_data.get("token")
                nickname = result_data.get("nickname")
                
                if token:
                    print(f"{nickname}的Token换取成功")
                    return token, nickname
                else:
                    print("Token换取失败：未获取到token")
                    return None, None
            else:
                print(f"Token换取失败：{data.get('errMsg', '未知错误')}")
                return None, None
                
        except Exception as e:
            print(f"Token换取请求失败: {e}")
            return None, None
    
    def check_signin_status(self, token: str, openid: str) -> Optional[int]:
        """
        检查今日签到状态

        Args:
            token (str): 用户token
            openid (str): 微信openid

        Returns:
            Optional[int]: 0表示未签到，1表示已签到，None表示请求失败
        """
        params = {
            "method": "crm.activity.sign.in.config",
            "token": token,
            "openid": openid,
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }

        sign = self.generate_sign(params)
        params["sign"] = sign

        url = f"{self.base_url}/open"

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("errCode") == 10000:
                result_data = data.get("data", {})

                today = datetime.now().strftime("%Y%m%d")

                sign_list = result_data.get("list", [])

                for day_info in sign_list:
                    if day_info.get("day") == today:
                        is_sign = day_info.get("is_sgin", 0)
                        print(f"今日签到状态: {'已签到' if is_sign == 1 else '未签到'}")
                        return is_sign

                print("未找到今日签到记录，默认为未签到")
                return 0
            else:
                print(f"检查签到状态失败：{data.get('errMsg', '未知错误')}")
                return None

        except Exception as e:
            print(f"检查签到状态请求失败: {e}")
            return None

    def submit_signin(self, token: str, openid: str) -> Optional[int]:
        """
        提交签到

        Args:
            token (str): 用户token
            openid (str): 微信openid

        Returns:
            Optional[int]: 签到获得的积分，None表示签到失败
        """
        params = {
            "method": "crm.activity.sign.in.sign",
            "token": token,
            "openid": openid,
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }

        # 生成签名
        sign = self.generate_sign(params)
        params["sign"] = sign

        url = f"{self.base_url}/open"

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("errCode") == 10000:
                result_data = data.get("data", {})
                sign_d = result_data.get("sign_d", 0)
                print(f"签到成功，获得{sign_d}积分")
                return sign_d
            else:
                print(f"签到失败：{data.get('errMsg', '未知错误')}")
                return None

        except Exception as e:
            print(f"签到请求失败: {e}")
            return None

    def get_member_detail(self, token: str, unionid: str, openid: str) -> Optional[int]:
        """
        获取会员详情（积分余额）

        Args:
            token (str): 用户token
            unionid (str): 微信unionid
            openid (str): 微信openid

        Returns:
            Optional[int]: 当前积分余额，None表示获取失败
        """
        params = {
            "method": "crm.member.detail",
            "token": token,
            "platform": "WECHAT",
            "thirdparty_type": "unionid",
            "thirdparty_id": unionid,
            "openid": openid,
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }

        sign = self.generate_sign(params)
        params["sign"] = sign

        url = f"{self.base_url}/open"

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("errCode") == 10000:
                result_data = data.get("data", {})
                bonus = result_data.get("bonus", 0)
                print(f"当前积分{bonus}")
                return bonus
            else:
                print(f"获取积分余额失败：{data.get('errMsg', '未知错误')}")
                return None

        except Exception as e:
            print(f"获取积分余额请求失败: {e}")
            return None

    def get_coupon_activities(self, token: str, openid: str) -> list:
        """
        查询可领取的优惠券活动

        Args:
            token (str): 用户token
            openid (str): 微信openid

        Returns:
            list: 可领取的优惠券活动列表
        """
        params = {
            "method": "crm.coupon.activity.list",
            "token": token,
            "openid": openid,
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }

        sign = self.generate_sign(params)
        params["sign"] = sign

        url = f"{self.base_url}/open"

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("errCode") == 10000:
                activities = data.get("data", [])
                return activities if activities else []
            else:
                print(f"查询优惠券活动失败：{data.get('errMsg', '未知错误')}")
                return []

        except Exception as e:
            print(f"查询优惠券活动请求失败: {e}")
            return []

    def claim_coupon(self, token: str, openid: str, activity_id: int) -> bool:
        """
        领取优惠券

        Args:
            token (str): 用户token
            openid (str): 微信openid
            activity_id (int): 活动ID

        Returns:
            bool: 是否领取成功
        """
        params = {
            "method": "crm.coupon.activity.receive",
            "token": token,
            "openid": openid,
            "activity_id": str(activity_id),
            "app_id": self.app_id,
            "sign_type": "MD5",
            "version": "1.0.0"
        }

        sign = self.generate_sign(params)
        params["sign"] = sign

        url = f"{self.base_url}/open"

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("errCode") == 10000:
                return True
            else:
                print(f"领取优惠券失败：{data.get('errMsg', '未知错误')}")
                return False

        except Exception as e:
            print(f"领取优惠券请求失败: {e}")
            return False

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

        # 1. 获取openid和unionid
        openid, unionid = self.get_openid_unionid(code)
        if not openid or not unionid:
            print(f"账号 {nick_name} 登录失败")
            return False

        # 2. 换取Token
        token, _ = self.get_token(openid, unionid)
        if not token:
            print(f"账号 {nick_name} Token换取失败")
            return False

        # 3. 检查签到状态
        sign_status = self.check_signin_status(token, openid)
        if sign_status is None:
            print(f"账号 {nick_name} 检查签到状态失败")
            return False

        if sign_status == 1:
            print("今日已签到")
        else:
            # 4. 提交签到
            signin_result = self.submit_signin(token, openid)
            if signin_result is None:
                print(f"账号 {nick_name} 签到失败")
                return False

        # 5. 获取积分余额
        self.get_member_detail(token, unionid, openid)

        # 6. 查询并领取优惠券
        coupon_activities = self.get_coupon_activities(token, openid)
        if coupon_activities:
            for activity in coupon_activities:
                activity_id = activity.get("activity_id")
                activity_name = activity.get("name")
                if activity_id and activity_name:
                    success = self.claim_coupon(token, openid, activity_id)
                    if success:
                        print(f"领取优惠券【{activity_name}】成功")
                    else:
                        print(f"领取优惠券【{activity_name}】失败")

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wxe87f500c8cef4c8a"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = YidiandianSignin()

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
