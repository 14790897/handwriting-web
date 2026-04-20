"""
Locust 压测脚本 - handwriting-web 后端并发测试
用法:
    locust -f locustfile.py --host=http://127.0.0.1:5005
    # 或命令行模式（无 UI）
    locust -f locustfile.py --host=http://127.0.0.1:5005 --headless -u 20 -r 5 --run-time 60s
"""

import random
import os
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


class HandwritingUser(HttpUser):
    """模拟一个用户提交手写生成任务并等待完成"""

    wait_time = between(0.5, 2.0)

    def on_start(self):
        """获取可用字体"""
        with self.client.get("/api/fonts_info", catch_response=True) as resp:
            if resp.status_code == 200:
                fonts = resp.json()
                if fonts:
                    self.font_option = fonts[0]
                    return
            resp.failure("获取字体列表失败")
            self.font_option = "STXingkai"

    def _build_form(self):
        text_lines = random.randint(5, 15)
        text = "测试并发压测 ABC 123 xyz.\n" * text_lines
        return {
            "text": text,
            "font_size": "120",
            "line_spacing": "180",
            "fill": "(0, 0, 0, 255)",
            "left_margin": "80",
            "top_margin": "80",
            "right_margin": "80",
            "bottom_margin": "80",
            "word_spacing": "1",
            "line_spacing_sigma": "0",
            "font_size_sigma": "2",
            "word_spacing_sigma": "2",
            "perturb_x_sigma": "2",
            "perturb_y_sigma": "2",
            "perturb_theta_sigma": "0.05",
            "preview": "true",
            "strikethrough_probability": "0",
            "strikethrough_length_sigma": "0",
            "strikethrough_width_sigma": "0",
            "strikethrough_angle_sigma": "0",
            "strikethrough_width": "0",
            "ink_depth_sigma": "10",
            "width": "2481",
            "height": "3507",
            "isUnderlined": "false",
            "enableEnglishSpacing": "false",
            "font_option": self.font_option,
            "pdf_save": "false",
            "full_preview": "false",
        }

    @task
    def submit_and_poll(self):
        """提交任务 -> 轮询等待完成 -> 获取结果"""
        form = self._build_form()

        # Step 1: 提交任务
        with self.client.post("/api/generate_handwriting", data=form, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"提交失败: {resp.status_code}")
                return
            json_data = resp.json()
            if json_data.get("status") != "accepted":
                resp.failure(f"状态异常: {json_data}")
                return
            task_id = json_data.get("task_id")

        # Step 2: 轮询任务状态
        import time
        deadline = time.time() + 120
        poll_interval = 1.0
        task_status = None

        while time.time() < deadline:
            with self.client.get(f"/api/generate_handwriting/task/{task_id}", catch_response=True) as poll_resp:
                if poll_resp.status_code != 200:
                    poll_resp.failure(f"轮询失败: {poll_resp.status_code}")
                    return
                poll_json = poll_resp.json()
                task_status = poll_json.get("task_status")
                if task_status == "completed":
                    break
                if task_status == "failed":
                    poll_resp.failure(f"任务失败: {poll_json.get('error_message')}")
                    return

            time.sleep(poll_interval)
        else:
            # 超时
            self.environment.events.request.fire(
                request_type="GET",
                name="/api/generate_handwriting/task/{task_id} [TIMEOUT]",
                response_time=0,
                response_length=0,
                exception=Exception("任务轮询超时"),
            )
            return

        # Step 3: 获取结果
        with self.client.get(f"/api/generate_handwriting/task/{task_id}/result", catch_response=True) as result_resp:
            if result_resp.status_code >= 400:
                result_resp.failure(f"获取结果失败: {result_resp.status_code}")
            elif len(result_resp.content) == 0:
                result_resp.failure("结果为空")
            else:
                result_resp.success()


# ==================== 轻量级测试（只测提交接口） ====================
class HandwritingSubmitOnly(HttpUser):
    """只测提交接口，不等待任务完成（测接口吞吐量）"""

    wait_time = between(0.1, 0.5)

    def on_start(self):
        with self.client.get("/api/fonts_info", catch_response=True) as resp:
            if resp.status_code == 200:
                fonts = resp.json()
                self.font_option = fonts[0] if fonts else "STXingkai"
            else:
                self.font_option = "STXingkai"

    @task(10)
    def submit_only(self):
        """只提交任务，不等待，用于测试接口极限吞吐量"""
        form = {
            "text": "快速压测文本" * 10,
            "font_size": "120",
            "line_spacing": "180",
            "fill": "(0, 0, 0, 255)",
            "left_margin": "80",
            "top_margin": "80",
            "right_margin": "80",
            "bottom_margin": "80",
            "word_spacing": "1",
            "line_spacing_sigma": "0",
            "font_size_sigma": "2",
            "word_spacing_sigma": "2",
            "perturb_x_sigma": "2",
            "perturb_y_sigma": "2",
            "perturb_theta_sigma": "0.05",
            "preview": "true",
            "strikethrough_probability": "0",
            "strikethrough_length_sigma": "0",
            "strikethrough_width_sigma": "0",
            "strikethrough_angle_sigma": "0",
            "strikethrough_width": "0",
            "ink_depth_sigma": "10",
            "width": "2481",
            "height": "3507",
            "isUnderlined": "false",
            "enableEnglishSpacing": "false",
            "font_option": self.font_option,
            "pdf_save": "false",
            "full_preview": "false",
        }
        self.client.post("/api/generate_handwriting", data=form)
