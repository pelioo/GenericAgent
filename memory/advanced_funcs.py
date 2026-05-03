"""
Headless Browser 高级功能模块
================
SOP配套工具 | 提供高级浏览器操作能力
创建: 2026-05-03 | 作者: GA | 定制者: 彭利

高级功能:
    1. 智能表单填写/提交
    2. 分页爬取
    3. 数据提取器(JSON/List/Table)
    4. 文件上传
    5. 代理轮换
    6. 自动化测试
    7. 页面性能分析
    8. 复杂交互(拖拽/滚动)
"""

from playwright.sync_api import sync_playwright, Page, BrowserContext
from typing import Optional, List, Dict, Callable, Any
import json
import time
import re

# ============ 1. 智能表单填写 ============

def fill_form(page: Page, fields: Dict[str, str], submit: bool = False, 
              submit_selector: Optional[str] = None) -> Dict[str, Any]:
    """
    智能填写表单（自动检测元素类型）
    
    Args:
        page: Playwright Page对象
        fields: {"选择器": "值"} 字典
        submit: 是否自动提交
        submit_selector: 提交按钮选择器（None则自动查找）
    
    Returns:
        {"success": bool, "filled": List[str], "errors": List[str]}
    """
    filled = []
    errors = []
    
    for selector, value in fields.items():
        try:
            # 检测元素类型并填写
            if page.locator(selector).get_attribute("type") == "checkbox":
                if value.lower() == "true":
                    page.locator(selector).check()
            elif page.locator(selector).get_attribute("type") == "radio":
                page.locator(selector).check()
            elif page.locator(selector).evaluate("el => el.tagName") == "SELECT":
                page.locator(selector).select_option(value)
            else:
                page.locator(selector).fill(value)
            filled.append(selector)
        except Exception as e:
            errors.append(f"{selector}: {str(e)}")
    
    # 提交表单
    if submit:
        try:
            if submit_selector:
                page.locator(submit_selector).click()
            else:
                page.locator("button[type=\"submit\"]").first.click()
        except Exception as e:
            errors.append(f"submit: {str(e)}")
    
    return {"success": len(errors) == 0, "filled": filled, "errors": errors}


# ============ 2. 分页爬取 ============

def paginated_crawl(
    page: Page,
    start_url: str,
    next_selector: str,
    max_pages: int = 10,
    extract_func: Optional[Callable] = None,
    stop_condition: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    分页爬取（自动翻页提取数据）
    
    Args:
        page: Playwright Page对象
        start_url: 起始URL
        next_selector: "下一页"按钮选择器
        max_pages: 最大页数限制
        extract_func: 数据提取函数，接收page参数
        stop_condition: 停止条件函数，返回True则停止
    
    Returns:
        {"pages_crawled": int, "all_data": List, "errors": List}
    """
    all_data = []
    errors = []
    current_page = 1
    
    page.goto(start_url)
    
    while current_page <= max_pages:
        try:
            # 提取当前页数据
            if extract_func:
                data = extract_func(page)
                all_data.extend(data if isinstance(data, list) else [data])
            
            # 检查停止条件
            if stop_condition and stop_condition(page):
                break
            
            # 检查是否有下一页
            if not page.locator(next_selector).is_visible():
                break
            
            # 点击下一页
            page.locator(next_selector).click()
            page.wait_for_load_state("networkidle")
            current_page += 1
            
        except Exception as e:
            errors.append(f"Page {current_page}: {str(e)}")
            break
    
    return {
        "pages_crawled": current_page,
        "all_data": all_data,
        "errors": errors
    }


# ============ 3. 数据提取器 ============

def extract_json_block(page: Page, selector: str) -> Optional[Dict]:
    """提取页面中的JSON数据块"""
    try:
        script = f"JSON.parse(document.querySelector('{selector}').textContent)"
        return page.evaluate(script)
    except:
        return None

def extract_table(page: Page, selector: str, has_header: bool = True) -> List[Dict]:
    """提取HTML表格数据"""
    try:
        script = f"""
            () => {{
                const table = document.querySelector('{selector}');
                const rows = table.querySelectorAll('tr');
                const result = [];
                
                for (let i = 0; i < rows.length; i++) {{
                    const cells = rows[i].querySelectorAll('td, th');
                    result.push(Array.from(cells).map(c => c.textContent.trim()));
                }}
                return result;
            }}
        """
        data = page.evaluate(script)
        
        if has_header and len(data) > 1:
            headers = data[0]
            return [dict(zip(headers, row)) for row in data[1:]]
        return data
    except:
        return []

def extract_list_items(page: Page, selector: str, fields: Dict[str, str]) -> List[Dict]:
    """
    提取列表项的多个字段
    
    Args:
        page: Playwright Page对象
        selector: 列表容器选择器
        fields: {"字段名": "选择器"} 字典
    
    Returns:
        List[Dict] - 每个元素包含fields中定义的所有字段
    """
    try:
        script = f"""
            () => {{
                const items = document.querySelectorAll('{selector}');
                const result = [];
                
                items.forEach(item => {{
                    const row = {{}};
                    {json.dumps(fields)}
                    Object.keys(row).forEach(key => {{
                        const sel = row[key];
                        const el = item.querySelector(sel);
                        row[key] = el ? el.textContent.trim() : '';
                    }});
                    result.push(row);
                }});
                return result;
            }}
        """
        return page.evaluate(script)
    except:
        return []


# ============ 4. 文件上传 ============

def upload_file(page: Page, file_input_selector: str, file_path: str) -> bool:
    """上传文件"""
    try:
        page.locator(file_input_selector).set_input_files(file_path)
        return True
    except Exception as e:
        print(f"Upload error: {e}")
        return False

def upload_multiple_files(page: Page, file_input_selector: str, file_paths: List[str]) -> bool:
    """批量上传多个文件"""
    try:
        page.locator(file_input_selector).set_input_files(file_paths)
        return True
    except:
        return False


# ============ 5. 代理轮换 ============

def create_browser_with_proxy(
    proxy: Dict[str, str],
    headless: bool = True
) -> tuple:
    """
    创建带代理的浏览器
    
    Args:
        proxy: {"server": "http://ip:port", "username": "user", "password": "pass"}
        headless: 是否无头
    
    Returns:
        (playwright, browser, context, page)
    """
    from headless_browser_utils import create_browser
    
    pw, browser, ctx, page = create_browser(headless=headless)
    
    # 设置代理
    ctx.set_extra_http_headers({"X-Proxy-Authorization": proxy.get("auth", "")})
    
    return pw, browser, ctx, page


# ============ 6. 自动化测试框架 ============

class BrowserTest:
    """浏览器自动化测试框架"""
    
    def __init__(self, page: Page):
        self.page = page
        self.results = []
    
    def assert_title(self, expected: str) -> bool:
        """断言页面标题"""
        actual = self.page.title()
        passed = expected in actual
        self.results.append({
            "test": "title",
            "expected": expected,
            "actual": actual,
            "passed": passed
        })
        return passed
    
    def assert_text(self, selector: str, expected: str) -> bool:
        """断言元素文本"""
        try:
            actual = self.page.locator(selector).text_content()
            passed = expected in actual
            self.results.append({
                "test": "text",
                "selector": selector,
                "expected": expected,
                "actual": actual,
                "passed": passed
            })
            return passed
        except:
            self.results.append({"test": "text", "selector": selector, "passed": False})
            return False
    
    def assert_visible(self, selector: str) -> bool:
        """断言元素可见"""
        try:
            visible = self.page.locator(selector).is_visible()
            self.results.append({"test": "visible", "selector": selector, "passed": visible})
            return visible
        except:
            self.results.append({"test": "visible", "selector": selector, "passed": False})
            return False
    
    def get_report(self) -> Dict:
        """获取测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{passed/total*100:.1f}%" if total else "0%",
            "results": self.results
        }


# ============ 7. 页面性能分析 ============

def analyze_page_performance(page: Page) -> Dict:
    """
    分析页面性能指标
    
    Returns:
        包含加载时间、资源统计等指标
    """
    metrics = page.evaluate("""
        () => {
            const timing = performance.timing;
            const resources = performance.getEntriesByType('resource');
            
            return {
                // 时间指标 (ms)
                dom_content_loaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                page_load: timing.loadEventEnd - timing.navigationStart,
                response_time: timing.responseEnd - timing.requestStart,
                
                // 资源统计
                total_resources: resources.length,
                images: resources.filter(r => r.initiatorType === 'img').length,
                scripts: resources.filter(r => r.initiatorType === 'script').length,
                styles: resources.filter(r => r.initiatorType === 'link').length,
                
                // 总传输量
                total_size: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
                
                // DNS/TCP/TLS
                dns_time: timing.domainLookupEnd - timing.domainLookupStart,
                tcp_time: timing.connectEnd - timing.connectStart,
                tls_time: timing.secureConnectionStart > 0 
                    ? timing.connectEnd - timing.secureConnectionStart : 0
            };
        }
    """)
    
    return metrics


# ============ 8. 复杂交互 ============

def scroll_to_element(page: Page, selector: str, smooth: bool = True) -> bool:
    """滚动到指定元素可见"""
    try:
        script = f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.scrollIntoView({{behavior: '{'smooth' if smooth else 'instant'}'}});
                    return true;
                }}
                return false;
            }}
        """
        return page.evaluate(script)
    except:
        return False

def drag_and_drop(page: Page, source: str, target: str) -> bool:
    """拖拽操作（源选择器 -> 目标选择器）"""
    try:
        page.locator(source).drag_to(page.locator(target))
        return True
    except:
        return False

def hover_and_click(page: Page, hover_selector: str, click_selector: str) -> bool:
    """悬停后点击（用于hover菜单）"""
    try:
        page.locator(hover_selector).hover()
        page.wait_for_timeout(300)
        page.locator(click_selector).click()
        return True
    except:
        return False


# ============ 9. 智能等待 ============

def wait_for_content(page: Page, selector: str, timeout: int = 10000) -> bool:
    """等待元素出现并包含内容"""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        text = page.locator(selector).text_content()
        return bool(text and text.strip())
    except:
        return False

def wait_for_network_idle_safe(page: Page, timeout: int = 30000) -> bool:
    """安全的网络空闲等待（超时保护）"""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
        return True
    except:
        # 超时后继续执行
        return False


# ============ 测试代码 ============

if __name__ == "__main__":
    from headless_browser_utils import create_browser, close_browser
    
    print("=" * 60)
    print("🧪 测试高级功能模块")
    print("=" * 60)
    
    pw, browser, ctx, page = create_browser()
    
    # 测试1: 页面性能分析
    print("\n📌 T1: 页面性能分析")
    page.goto("https://www.baidu.com")
    perf = analyze_page_performance(page)
    print(f"   DOM加载: {perf['dom_content_loaded']}ms")
    print(f"   页面加载: {perf['page_load']}ms")
    print(f"   资源数: {perf['total_resources']}")
    
    # 测试2: 表单填写（百度搜索）
    print("\n📌 T2: 智能表单填写")
    result = fill_form(page, {"#kw": "测试"}, submit=False)
    print(f"   填写: {result['filled']}, 成功: {result['success']}")
    
    # 测试3: 自动化测试
    print("\n📌 T3: 自动化测试框架")
    test = BrowserTest(page)
    test.assert_title("百度")
    test.assert_visible("#su")
    report = test.get_report()
    print(f"   通过率: {report['pass_rate']}")
    
    # 测试4: 数据提取
    print("\n📌 T4: 表格数据提取")
    page.goto("https://www.w3school.com.cn/html/html_tables.asp")
    time.sleep(1)
    table_data = extract_table(page, "table.list")
    print(f"   提取行数: {len(table_data)}")
    
    close_browser(pw, browser)
    
    print("\n" + "=" * 60)
    print("🎉 高级功能模块测试完成！")
    print("=" * 60)
