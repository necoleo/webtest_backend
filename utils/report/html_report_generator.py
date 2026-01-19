# -*- coding: utf-8 -*-
"""
自制 HTML 测试报告生成器
生成单文件 HTML 报告，包含所有 CSS/JS，下载后可直接查看
"""
import html
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class HtmlReportGenerator:
    """HTML 测试报告生成器"""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.test_name: str = "API 自动化测试报告"
        self.environment: str = ""
        self.base_url: str = ""

    def set_test_info(self, name: str, environment: str = "", base_url: str = ""):
        """设置测试信息"""
        self.test_name = name
        self.environment = environment
        self.base_url = base_url

    def set_time(self, start_time: datetime, end_time: datetime):
        """设置执行时间"""
        self.start_time = start_time
        self.end_time = end_time

    def add_case_result(self, case_result: Dict[str, Any]):
        """
        添加用例执行结果
        case_result 格式：
        {
            "case_id": "LIST_001",
            "case_name": "[查询链接列表] 正向-默认参数查询成功",
            "status": "PASS" | "FAIL",
            "duration": 1.23,  # 秒
            "error_message": "",  # 失败时的错误信息
            "steps": [
                {
                    "name": "owner_login",
                    "request": {
                        "method": "POST",
                        "url": "https://xxx/v1/auth/login",
                        "headers": {...},
                        "body": {...}
                    },
                    "response": {
                        "status_code": 200,
                        "headers": {...},
                        "body": {...}
                    },
                    "status": "PASS" | "FAIL",
                    "error_message": ""
                }
            ]
        }
        """
        self.test_results.append(case_result)

    def generate(self) -> str:
        """生成 HTML 报告"""
        # 统计数据
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get('status') == 'PASS')
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        # 生成用例 HTML
        cases_html = self._generate_cases_html()

        # 生成完整 HTML
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(self.test_name)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e4e4e4;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 头部 */
        .header {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header .subtitle {{
            color: #888;
            font-size: 14px;
        }}
        
        /* 统计卡片 */
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        .stat-card .value {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .stat-card .label {{
            color: #888;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card.total .value {{ color: #00d9ff; }}
        .stat-card.passed .value {{ color: #00ff88; }}
        .stat-card.failed .value {{ color: #ff4757; }}
        .stat-card.rate .value {{ color: #ffa502; }}
        
        /* 进度条 */
        .progress-bar {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        
        .progress-bar .fill {{
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00d9ff);
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        
        /* 用例列表 */
        .cases {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
        }}
        
        .cases-header {{
            padding: 20px 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .cases-header h2 {{
            font-size: 18px;
            font-weight: 600;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 8px;
        }}
        
        .filter-btn {{
            padding: 6px 16px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: transparent;
            color: #e4e4e4;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: rgba(0, 217, 255, 0.2);
            border-color: #00d9ff;
            color: #00d9ff;
        }}
        
        /* 用例项 */
        .case-item {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .case-item:last-child {{
            border-bottom: none;
        }}
        
        .case-header {{
            padding: 16px 24px;
            display: flex;
            align-items: center;
            cursor: pointer;
            transition: background 0.2s;
        }}
        
        .case-header:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}
        
        .case-status {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            font-size: 16px;
        }}
        
        .case-status.pass {{
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
        }}
        
        .case-status.fail {{
            background: rgba(255, 71, 87, 0.2);
            color: #ff4757;
        }}
        
        .case-info {{
            flex: 1;
        }}
        
        .case-id {{
            font-weight: 600;
            color: #00d9ff;
            margin-right: 12px;
        }}
        
        .case-name {{
            color: #e4e4e4;
        }}
        
        .case-duration {{
            color: #888;
            font-size: 13px;
            margin-left: 16px;
        }}
        
        .case-expand {{
            color: #888;
            transition: transform 0.3s;
        }}
        
        .case-item.expanded .case-expand {{
            transform: rotate(180deg);
        }}
        
        /* 用例详情 */
        .case-detail {{
            display: none;
            padding: 0 24px 24px 72px;
        }}
        
        .case-item.expanded .case-detail {{
            display: block;
        }}
        
        .error-message {{
            background: rgba(255, 71, 87, 0.1);
            border: 1px solid rgba(255, 71, 87, 0.3);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            color: #ff4757;
        }}
        
        .error-message .label {{
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        /* 步骤 */
        .step {{
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
        }}
        
        .step-header {{
            padding: 12px 16px;
            display: flex;
            align-items: center;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.03);
        }}
        
        .step-header:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .step-status {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-size: 12px;
        }}
        
        .step-status.pass {{
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
        }}
        
        .step-status.fail {{
            background: rgba(255, 71, 87, 0.2);
            color: #ff4757;
        }}
        
        .step-name {{
            flex: 1;
            font-weight: 500;
        }}
        
        .step-method {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 12px;
        }}
        
        .step-method.GET {{ background: rgba(0, 217, 255, 0.2); color: #00d9ff; }}
        .step-method.POST {{ background: rgba(0, 255, 136, 0.2); color: #00ff88; }}
        .step-method.PUT {{ background: rgba(255, 165, 2, 0.2); color: #ffa502; }}
        .step-method.DELETE {{ background: rgba(255, 71, 87, 0.2); color: #ff4757; }}
        .step-method.PATCH {{ background: rgba(155, 89, 182, 0.2); color: #9b59b6; }}
        
        .step-detail {{
            display: none;
            padding: 16px;
        }}
        
        .step.expanded .step-detail {{
            display: block;
        }}
        
        .detail-section {{
            margin-bottom: 16px;
        }}
        
        .detail-section:last-child {{
            margin-bottom: 0;
        }}
        
        .detail-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        
        .detail-content {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 6px;
            padding: 12px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }}
        
        .detail-content.url {{
            color: #00d9ff;
        }}
        
        .status-code {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .status-code.success {{ background: rgba(0, 255, 136, 0.2); color: #00ff88; }}
        .status-code.error {{ background: rgba(255, 71, 87, 0.2); color: #ff4757; }}
        
        /* 底部 */
        .footer {{
            text-align: center;
            padding: 24px;
            color: #666;
            font-size: 13px;
        }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .case-detail {{
                padding-left: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>{html.escape(self.test_name)}</h1>
            <div class="subtitle">
                {f'环境: {html.escape(self.environment)} | ' if self.environment else ''}
                {f'Base URL: {html.escape(self.base_url)} | ' if self.base_url else ''}
                执行时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else '-'}
            </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="stats">
            <div class="stat-card total">
                <div class="value">{total}</div>
                <div class="label">总用例数</div>
            </div>
            <div class="stat-card passed">
                <div class="value">{passed}</div>
                <div class="label">通过</div>
            </div>
            <div class="stat-card failed">
                <div class="value">{failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="stat-card rate">
                <div class="value">{pass_rate:.1f}%</div>
                <div class="label">通过率</div>
            </div>
        </div>
        
        <!-- 进度条 -->
        <div class="progress-bar">
            <div class="fill" style="width: {pass_rate}%"></div>
        </div>
        
        <!-- 用例列表 -->
        <div class="cases">
            <div class="cases-header">
                <h2>测试用例详情</h2>
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterCases('all')">全部</button>
                    <button class="filter-btn" onclick="filterCases('pass')">通过</button>
                    <button class="filter-btn" onclick="filterCases('fail')">失败</button>
                </div>
            </div>
            {cases_html}
        </div>
        
        <!-- 底部 -->
        <div class="footer">
            Generated by API Auto Test Platform | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        // 切换用例展开/折叠
        function toggleCase(element) {{
            const caseItem = element.closest('.case-item');
            caseItem.classList.toggle('expanded');
        }}
        
        // 切换步骤展开/折叠
        function toggleStep(element) {{
            const step = element.closest('.step');
            step.classList.toggle('expanded');
        }}
        
        // 过滤用例
        function filterCases(type) {{
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const cases = document.querySelectorAll('.case-item');
            cases.forEach(item => {{
                if (type === 'all') {{
                    item.style.display = 'block';
                }} else if (type === 'pass') {{
                    item.style.display = item.dataset.status === 'pass' ? 'block' : 'none';
                }} else if (type === 'fail') {{
                    item.style.display = item.dataset.status === 'fail' ? 'block' : 'none';
                }}
            }});
        }}
        
        // 自动展开失败的用例
        document.addEventListener('DOMContentLoaded', function() {{
            const failedCases = document.querySelectorAll('.case-item[data-status="fail"]');
            failedCases.forEach(item => item.classList.add('expanded'));
        }});
    </script>
</body>
</html>'''
        return html_content

    def _generate_cases_html(self) -> str:
        """生成用例列表 HTML"""
        cases_html = ""
        for result in self.test_results:
            case_id = html.escape(result.get('case_id', ''))
            case_name = html.escape(result.get('case_name', ''))
            status = result.get('status', 'FAIL')
            duration = result.get('duration', 0)
            error_message = result.get('error_message', '')
            steps = result.get('steps', [])

            status_lower = 'pass' if status == 'PASS' else 'fail'
            status_icon = '✓' if status == 'PASS' else '✗'

            # 生成步骤 HTML
            steps_html = self._generate_steps_html(steps)

            # 错误信息
            error_html = ""
            if error_message:
                error_html = f'''
                <div class="error-message">
                    <div class="label">❌ 错误信息</div>
                    <div>{html.escape(error_message)}</div>
                </div>
                '''

            cases_html += f'''
            <div class="case-item" data-status="{status_lower}">
                <div class="case-header" onclick="toggleCase(this)">
                    <div class="case-status {status_lower}">{status_icon}</div>
                    <div class="case-info">
                        <span class="case-id">{case_id}</span>
                        <span class="case-name">{case_name}</span>
                    </div>
                    <div class="case-duration">{duration:.2f}s</div>
                    <div class="case-expand">▼</div>
                </div>
                <div class="case-detail">
                    {error_html}
                    {steps_html}
                </div>
            </div>
            '''
        return cases_html

    def _generate_steps_html(self, steps: List[Dict]) -> str:
        """生成步骤 HTML"""
        steps_html = ""
        for step in steps:
            step_name = html.escape(step.get('name', ''))
            step_status = step.get('status', 'PASS')
            request_data = step.get('request', {})
            response_data = step.get('response', {})
            step_error = step.get('error_message', '')

            status_lower = 'pass' if step_status == 'PASS' else 'fail'
            status_icon = '✓' if step_status == 'PASS' else '✗'

            method = request_data.get('method', 'GET')
            url = request_data.get('url', '')
            req_headers = request_data.get('headers', {})
            req_body = request_data.get('body', {})

            resp_status = response_data.get('status_code', 0)
            resp_body = response_data.get('body', {})

            status_class = 'success' if 200 <= resp_status < 400 else 'error'

            # 格式化 JSON
            req_headers_str = json.dumps(req_headers, ensure_ascii=False, indent=2) if req_headers else '{}'
            req_body_str = json.dumps(req_body, ensure_ascii=False, indent=2) if req_body else '{}'
            resp_body_str = json.dumps(resp_body, ensure_ascii=False, indent=2) if isinstance(resp_body, (dict, list)) else str(resp_body)

            # 步骤错误信息
            step_error_html = ""
            if step_error:
                step_error_html = f'''
                <div class="detail-section">
                    <div class="detail-label">错误信息</div>
                    <div class="detail-content" style="color: #ff4757;">{html.escape(step_error)}</div>
                </div>
                '''

            steps_html += f'''
            <div class="step">
                <div class="step-header" onclick="toggleStep(this)">
                    <div class="step-status {status_lower}">{status_icon}</div>
                    <div class="step-name">{step_name}</div>
                    <div class="step-method {method}">{method}</div>
                </div>
                <div class="step-detail">
                    <div class="detail-section">
                        <div class="detail-label">请求 URL</div>
                        <div class="detail-content url">{html.escape(url)}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-label">请求头</div>
                        <div class="detail-content">{html.escape(req_headers_str)}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-label">请求体</div>
                        <div class="detail-content">{html.escape(req_body_str)}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-label">响应 <span class="status-code {status_class}">{resp_status}</span></div>
                        <div class="detail-content">{html.escape(resp_body_str)}</div>
                    </div>
                    {step_error_html}
                </div>
            </div>
            '''
        return steps_html

    def save_to_file(self, file_path: str):
        """保存报告到文件"""
        html_content = self.generate()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return file_path
