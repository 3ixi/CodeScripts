#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零食有鸣小程序签到脚本
脚本作者：3iXi
创建时间：2025/09/04
！！此脚本需要配合iPad协议服务使用！！
小程序：零食有鸣
"""

import time
import json
import re
from typing import Optional, Dict, List

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

import getCode

# 可以在这里指定门店ID，如果为空则自动获取注册时的门店ID
STORE_ID = ""


class LsymSignin:
    """零食有鸣小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://api-pub.lsym.cn"
        self.app_id = "wx295a967684523cdd"
        
        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)
        
        self.headers = {
            "host": "api-pub.lsym.cn",
            "appid": "wx295a967684523cdd",
            "authorization": "",
            "tenantid": "1001",
            "xweb_xhr": "1",
            "devicelanguage": "zh-cn",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254101e) XWEB/16389",
            "accept": "*/*",
            "content-type": "application/json",
            "version": "3.1.0",
            "devicemodel": "android",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://servicewechat.com/wx295a967684523cdd/73/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i"
        }
        
        self.access_token = None
        self.member_id = None
        self.lottery_activity_id = None
        self.store_id = STORE_ID

    def check_response(self, data: dict, operation: str) -> bool:
        """
        检查响应是否成功
        
        Args:
            data (dict): 响应数据
            operation (str): 操作名称
            
        Returns:
            bool: 是否成功
        """
        if data.get("code") != 200:
            print(f"{operation}失败：{data.get('msg', '未知错误')}")
            return False
        return True

    def login(self, code: str) -> bool:
        """
        用户登录
        
        Args:
            code (str): 微信小程序登录code
            
        Returns:
            bool: 登录是否成功
        """
        url = f"{self.base_url}/scrm/member-identity/front/miniapp/silentLogin"
        payload = {"loginType":0,"code":code}
        
        try:
            json_payload = json.dumps(payload, separators=(',', ':'))

            headers = self.headers.copy()
            headers["Content-Length"] = str(len(json_payload))
    
            response = self.client.post(url, content=json_payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not self.check_response(data, "登录"):
                return False
                
            login_data = data.get("data", {})
            self.access_token = login_data.get("accessToken")
            self.member_id = login_data.get("memberId")
            mobile = login_data.get("mobile", "")
            
            if self.access_token and self.member_id:
                self.headers["authorization"] = self.access_token
                print("登录成功")
                return True
            else:
                print("登录失败：未获取到token或memberId")
                return False
                
        except Exception as e:
            print(f"登录请求失败: {e}")
            return False

    def get_task_list(self) -> Optional[List[Dict]]:
        """
        获取任务列表
        
        Returns:
            Optional[List[Dict]]: 任务列表，None表示获取失败
        """
        url = f"{self.base_url}/scrm/marketing/front/task/batchGetTaskList"
        
        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if not self.check_response(data, "获取任务列表"):
                return None
                
            tasks = data.get("data", [])
            filtered_tasks = []
            for task in tasks:
                join_detail = task.get("joinDetailVO", {})
                task_state = join_detail.get("taskState")
                task_type = task.get("taskType")
                
                if task_type == 8 and task_state in [1, 2]:
                    filtered_tasks.append(task)
                    
            return filtered_tasks
            
        except Exception as e:
            print(f"获取任务列表请求失败: {e}")
            return None

    def register_task(self, activity_id: str, activity_name: str) -> bool:
        """
        领取任务
        
        Args:
            activity_id (str): 活动ID
            activity_name (str): 活动名称
            
        Returns:
            bool: 是否成功
        """
        url = f"{self.base_url}/scrm/marketing/front/task/registerJoin"
        params = {"activityId": activity_id}
        
        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if self.check_response(data, f"领取任务【{activity_name}】"):
                print(f"任务【{activity_name}】领取成功")
                return True
            return False
            
        except Exception as e:
            print(f"领取任务【{activity_name}】请求失败: {e}")
            return False

    def visit_page(self, activity_id: str, activity_name: str) -> bool:
        """
        提交任务浏览记录
        
        Args:
            activity_id (str): 活动ID
            activity_name (str): 活动名称
            
        Returns:
            bool: 是否成功
        """
        url = f"{self.base_url}/scrm/marketing/front/task/visitPage"
        payload = {
            "activityId": activity_id,
            "taskType": 8
        }
        
        try:
            json_payload = json.dumps(payload, separators=(',', ':'))
                
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(json_payload))
    
            response = self.client.post(url, content=json_payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if self.check_response(data, f"浏览任务【{activity_name}】"):
                print(f"任务【{activity_name}】浏览成功")
                return True
            return False
            
        except Exception as e:
            print(f"浏览任务【{activity_name}】请求失败: {e}")
            return False

    def receive_prize(self, activity_id: str, activity_name: str) -> bool:
        """
        领取任务奖励
        
        Args:
            activity_id (str): 活动ID
            activity_name (str): 活动名称
            
        Returns:
            bool: 是否成功
        """
        url = f"{self.base_url}/scrm/marketing/front/task/receivePrize"
        params = {"activityId": activity_id}
        
        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if self.check_response(data, f"领取奖励【{activity_name}】"):
                print(f"任务【{activity_name}】奖励领取成功")
                return True
            return False
            
        except Exception as e:
            print(f"领取奖励【{activity_name}】请求失败: {e}")
            return False

    def get_lottery_activity_id(self) -> Optional[str]:
        """
        获取抽奖活动ID
        
        Returns:
            Optional[str]: 抽奖活动ID，None表示获取失败
        """
        if self.lottery_activity_id:
            return self.lottery_activity_id
            
        url = f"{self.base_url}/scrm/cms/front/page/redirect/all"
        payload = {}
        
        try:
            json_payload = json.dumps(payload, separators=(',', ':'))
                
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(json_payload))
    
            response = self.client.post(url, content=json_payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if not self.check_response(data, "获取抽奖活动ID"):
                return None
                
            activities = data.get("data", [])
            for activity in activities:
                original_title = activity.get("originalTitle", "")
                if "抽" in original_title and "停用" not in original_title:
                    redirect_url = activity.get("redirectUrl", "")
                    try:
                        redirect_data = json.loads(redirect_url)
                        params = redirect_data.get("params", {})
                        activity_id = params.get("id")
                        if activity_id:
                            self.lottery_activity_id = activity_id
                            return activity_id
                    except json.JSONDecodeError:
                        continue
                        
            print("未找到有效的抽奖活动")
            return None
            
        except Exception as e:
            print(f"获取抽奖活动ID请求失败: {e}")
            return None

    def get_lottery_quota_rules(self, activity_id: str) -> Optional[Dict]:
        """
        获取抽奖任务规则

        Args:
            activity_id (str): 抽奖活动ID

        Returns:
            Optional[Dict]: 抽奖任务规则，None表示获取失败
        """
        url = f"{self.base_url}/scrm/marketing/front/activity/lottery-wheel/get-user-exchange-quota-rule-list"
        params = {"activityId": activity_id}

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if not self.check_response(data, "获取抽奖任务规则"):
                return None

            return data.get("data", {})

        except Exception as e:
            print(f"获取抽奖任务规则请求失败: {e}")
            return None

    def add_browse_record(self, activity_id: str, link_path: str, second: int, title: str) -> bool:
        """
        添加浏览记录

        Args:
            activity_id (str): 抽奖活动ID
            link_path (str): 链接路径
            second (int): 浏览秒数
            title (str): 页面标题

        Returns:
            bool: 是否成功
        """
        url = f"{self.base_url}/scrm/marketing/front/activity/lottery-wheel/add-browse-record"
        payload = {
            "activityId": activity_id,
            "memberId": self.member_id,
            "linkPath": link_path,
            "second": second
        }

        try:
            json_payload = json.dumps(payload, separators=(',', ':'))
                
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(json_payload))
    
            response = self.client.post(url, content=json_payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if self.check_response(data, f"浏览【{title}】{second}秒"):
                print("任务完成")
                return True
            return False

        except Exception as e:
            print(f"添加浏览记录请求失败: {e}")
            return False

    def submit_share_task(self, activity_id: str) -> bool:
        """
        提交分享任务

        Args:
            activity_id (str): 抽奖活动ID

        Returns:
            bool: 是否成功
        """
        url = f"{self.base_url}/scrm/marketing/front/activity/lottery-wheel/user-exchange-quota-operate"
        payload = {
            "activityId": activity_id,
            "type": 2,
            "versionId": "7"
        }

        try:
            json_payload = json.dumps(payload, separators=(',', ':'))
                
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(json_payload))
    
            response = self.client.post(url, content=json_payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if self.check_response(data, "分享任务"):
                print("分享任务完成")
                return True
            return False

        except Exception as e:
            print(f"提交分享任务请求失败: {e}")
            return False

    def get_lottery_quota(self, activity_id: str) -> Optional[int]:
        """
        查询抽奖次数

        Args:
            activity_id (str): 抽奖活动ID

        Returns:
            Optional[int]: 抽奖次数，None表示获取失败
        """
        url = f"{self.base_url}/scrm/marketing/front/activity/lottery-wheel/get-user-lottery-quota"
        params = {"activityId": activity_id}

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if not self.check_response(data, "查询抽奖次数"):
                return None

            quota = data.get("data", 0)
            print(f"可用抽奖次数{quota}次")
            return quota

        except Exception as e:
            print(f"查询抽奖次数请求失败: {e}")
            return None

    def ensure_store_id(self) -> bool:
        """
        确保门店ID已设置，如未设置则从会员信息中获取
        
        Returns:
            bool: 是否成功获取门店ID
        """
        if self.store_id:
            return True
            
        member_info = self.get_member_info()
        if not member_info:
            print("获取会员信息失败，无法获取门店ID")
            return False
            
        register_store_id = member_info.get("registerStoreId")
        register_store_name = member_info.get("registerStoreName", "")
        
        if not register_store_id:
            print("会员信息中未找到注册门店ID")
            return False
            
        self.store_id = register_store_id
        print(f"获取到注册门店信息：{register_store_name}({register_store_id})")
        return True

    def draw_lottery(self, activity_id: str) -> Optional[Dict]:
        """
        抽奖

        Args:
            activity_id (str): 抽奖活动ID

        Returns:
            Optional[Dict]: 抽奖结果，None表示抽奖失败
        """
        if not self.ensure_store_id():
            print("门店ID获取失败，无法进行抽奖")
            return None
        
        url = f"{self.base_url}/scrm/marketing/front/activity/lottery-wheel/prize-draw"
        payload = {
            "activityId": activity_id,
            "versionId": "7"
        }

        try:
            json_payload = json.dumps(payload, separators=(',', ':'))
                
            headers = self.headers.copy()
            headers["Content-Length"] = str(len(json_payload))
            headers["storeid"] = self.store_id
    
            response = self.client.post(url, content=json_payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if not self.check_response(data, "抽奖"):
                return None

            return data.get("data", {})

        except Exception as e:
            print(f"抽奖请求失败: {e}")
            return None

    def get_member_info(self) -> Optional[Dict]:
        """
        获取会员信息

        Returns:
            Optional[Dict]: 会员信息，None表示获取失败
        """
        url = f"{self.base_url}/scrm/member/front/getCurrentMember"

        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if not self.check_response(data, "获取会员信息"):
                return None

            return data.get("data", {})

        except Exception as e:
            print(f"获取会员信息请求失败: {e}")
            return None

    def get_coupons(self) -> Optional[List[Dict]]:
        """
        获取未使用的优惠券

        Returns:
            Optional[List[Dict]]: 优惠券列表，None表示获取失败
        """
        url = f"{self.base_url}/scrm/marketing/front/memberCoupon/page"
        params = {
            "currPage": 1,
            "pageSize": 20,
            "couponState": 2
        }

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if not self.check_response(data, "获取优惠券"):
                return None

            records = data.get("data", {}).get("records", [])
            return records

        except Exception as e:
            print(f"获取优惠券请求失败: {e}")
            return None

    def process_tasks(self) -> bool:
        """
        处理任务流程

        Returns:
            bool: 是否处理成功
        """
        # 1. 获取任务列表
        tasks = self.get_task_list()
        if not tasks:
            print("未获取到有效任务")
            return False

        # 2. 处理任务
        for task in tasks:
            activity_id = task.get("activityId")
            activity_name = task.get("activityName")
            join_detail = task.get("joinDetailVO", {})
            task_state = join_detail.get("taskState")

            # 检查必要字段
            if not activity_id or not activity_name:
                continue

            if task_state == 1:  # 未领取
                if not self.register_task(activity_id, activity_name):
                    continue

            if task_state in [1, 2]:  # 未领取或待完成
                # 提交浏览记录
                if not self.visit_page(activity_id, activity_name):
                    continue

                # 领取奖励
                if not self.receive_prize(activity_id, activity_name):
                    continue

            elif task_state == 3:  # 已完成，直接领取奖励
                self.receive_prize(activity_id, activity_name)

        return True

    def process_lottery(self) -> bool:
        """
        处理抽奖流程

        Returns:
            bool: 是否处理成功
        """
        # 1. 获取抽奖活动ID
        activity_id = self.get_lottery_activity_id()
        if not activity_id:
            return False

        # 2. 获取抽奖任务规则
        quota_rules = self.get_lottery_quota_rules(activity_id)
        if not quota_rules:
            return False

        # 3. 处理浏览任务
        browse_task = quota_rules.get("browseDesignatedPage", {})
        if browse_task.get("valid") and browse_task.get("state") == 1:
            thresholds = browse_task.get("thresholds", [])
            for threshold in thresholds:
                if threshold.get("valid"):
                    link_url = threshold.get("linkUrl", "")
                    second = threshold.get("second", 10)

                    try:
                        link_data = json.loads(link_url)
                        title = link_data.get("title", "")
                        path = link_data.get("path", "")

                        print(f"可做任务：浏览【{title}】{second}秒")
                        self.add_browse_record(activity_id, path, second, title)
                    except json.JSONDecodeError:
                        continue

        # 4. 处理分享任务
        share_task = quota_rules.get("share", {})
        if share_task.get("valid") and share_task.get("state") == 1:
            self.submit_share_task(activity_id)

        # 5. 查询抽奖次数并抽奖
        time.sleep(2)
        quota = self.get_lottery_quota(activity_id)
        if quota and quota > 0:
            for i in range(quota):
                draw_result = self.draw_lottery(activity_id)
                if draw_result:
                    state = draw_result.get("state", 1)
                    if state == 0:  # 中奖
                        prize = draw_result.get("prize", {})
                        prize_name = prize.get("prizeName", "")
                        prize_object = prize.get("prizeObject", {})
                        coupons = prize_object.get("coupons", [])
                        if coupons:
                            count = coupons[0].get("count", 1)
                            print(f"第{i+1}次抽奖抽中了{prize_name}x{count}")
                        else:
                            print(f"第{i+1}次抽奖抽中了{prize_name}")
                    if i < quota - 1:
                        time.sleep(1)

        return True

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

        # 2. 处理任务
        self.process_tasks()

        # 3. 处理抽奖
        self.process_lottery()

        # 4. 获取会员信息和积分
        member_info = self.get_member_info()
        if member_info:
            mobile = member_info.get("mobile", "")
            balance = member_info.get("balance", "0")

            # 手机号打码
            if len(mobile) >= 7:
                masked_mobile = mobile[:3] + "****" + mobile[7:]
            else:
                masked_mobile = mobile

            print(f"{masked_mobile}当前有{balance}积分")

        # 5. 获取优惠券信息
        coupons = self.get_coupons()
        if coupons:
            print("未使用优惠券：")
            for coupon in coupons:
                coupon_name = coupon.get("couponName", "")
                effective_time_end = coupon.get("effectiveTimeEnd", "")
                print(f"{coupon_name}({effective_time_end}过期)")
        else:
            print("暂无未使用优惠券")

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()

    def reset_session(self):
        """
        重置/清理会话数据
        """
        try:
            self.client.close()
        except Exception:
            pass

        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)

        self.access_token = None
        self.member_id = None
        self.headers["authorization"] = ""
        self.store_id = STORE_ID

        print("已清理会话数据，准备下一个账号...")


def main():
    """主函数"""
    try:
        print("正在获取登录Code...")
        app_id = "wx295a967684523cdd"
        codes = getCode.get_wechat_codes(app_id)

        if not codes:
            print("未获取到任何在线账号的Code")
            return

        print(f"获取到 {len(codes)} 个账号的Code")

        signin = LsymSignin()

        try:
            for i, (nick_name, code) in enumerate(codes.items(), 1):
                print(f"\n{'='*50}")
                print(f"处理第 {i}/{len(codes)} 个账号")
                print(f"{'='*50}")

                try:
                    signin.process_account(nick_name, code)
                except Exception as e:
                    print(f"处理账号 {nick_name} 时发生错误: {e}")

                signin.reset_session()

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
