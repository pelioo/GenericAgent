"""
Headless Browser 核心工具库
================
SOP配套工具 | 提供可复用的浏览器操作函数
创建: 2026-05-03 | 作者: GA | 定制者: 彭利
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional, List, Dict, Callable
import json
import time

# ============ 基础工具 ============

def create_browser(
    headless: bool = True,
    user_agent: Optional[str] = None,
    viewport: Optional[Dict] = None
) -> tuple:
    """
    创建并返回一个可用的浏览器实例
    
    Args:
        headless: 是否无头模式
        user_agent: 自定义UA（None使用默认）
        viewport: 视口大小 {"width": int, "height": int}
    
    Returns:
        (playwright_instance, browser, context, page)
    
    Usage:
        pw, browser, ctx, page = create_browser()
        # ... 操作 ...
        close_browser(pw, browser)
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    ctx = browser.new_context(
        user_agent=user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        viewport=viewport or {"width": 1280, "height": 720}
    )
    page = ctx.new_page()
    return pw, browser, ctx, page

def create_browser_with_stealth() -> tuple:
    """
    创建反检测浏览器（模拟真实用户）
    
    Returns:
        同上
    """
    stealth_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationDetection',
            '--disable-dev-shm-usage',
            '--no-sandbox'
        ]
    )
    ctx = browser.new_context(
        user_agent=stealth_ua,
        viewport={"width": 1920, "height": 1080}
    )
    # 注入反检测脚本
    page = ctx.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
    """)
    return pw, browser, ctx, page

def close_browser(pw, browser):
    """关闭浏览器"""
    browser.close()
    pw.stop()

def quick_get(url: str, timeout: int = 15000) -> tuple:
    """
    快速获取网页内容（自动管理生命周期）
    
    Args:
        url: 目标URL
        timeout: 超时时间(ms)
    
    Returns:
        (html_content: str, page: Page, status: bool)
    """
    pw, browser, ctx, page = create_browser()
    try:
        page.goto(url, timeout=timeout)
        content = page.content()
        return content, page, True
    except Exception as e:
        return str(e), page, False
    finally:
        close_browser(pw, browser)

# ============ 截图工具 ============

def capture_screenshot(url: str, save_path: str = "screenshot.png", full_page: bool = False, wait_time: int = 1000) -> str:
    """截图，返回保存路径或None"""
    import os
    pw, browser, ctx, page = create_browser()
    try:
        page.goto(url, timeout=15000)
        page.wait_for_timeout(wait_time)
        os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
        page.screenshot(path=save_path, full_page=full_page)
        return save_path
    except Exception as e:
        print(f"截图失败: {e}")
        return None
    finally:
        close_browser(pw, browser)

# ============ 内容提取工具 ============

def extract_by_selector(page: Page, selector: str) -> List[str]:
    """提取指定选择器的所有文本"""
    try:
        elements = page.query_selector_all(selector)
        return [el.inner_text() for el in elements]
    except:
        return []

def extract_links(page: Page, base_url: Optional[str] = None) -> List[Dict]:
    """提取页面所有链接"""
    links = []
    try:
        elements = page.query_selector_all('a[href]')
        for el in elements:
            href = el.get_attribute('href')
            text = el.inner_text().strip()
            if href:
                if base_url and not href.startswith('http'):
                    href = base_url + href
                links.append({"url": href, "text": text})
    except:
        pass
    return links

# ============ 请求拦截工具 ============

def intercept_requests(url: str, filter_func: Optional[Callable] = None) -> Dict:
    """
    拦截并统计页面请求
    
    Args:
        url: 目标URL
        filter_func: 过滤函数，接收url返回bool
    
    Returns:
        {"requests": [], "stat": {"total": int, "by_type": dict}}
    """
    pw, browser, ctx, page = create_browser()
    
    intercepted = []
    def on_request(req):
        if filter_func is None or filter_func(req.url):
            intercepted.append({
                "url": req.url,
                "method": req.method,
                "resource_type": req.resource_type
            })
    
    page.on('request', on_request)
    
    try:
        page.goto(url, timeout=15000)
        page.wait_for_load_state('networkidle')
    finally:
        close_browser(pw, browser)
    
    # 统计
    by_type = {}
    for req in intercepted:
        rt = req["resource_type"]
        by_type[rt] = by_type.get(rt, 0) + 1
    
    return {
        "requests": intercepted,
        "stat": {
            "total": len(intercepted),
            "by_type": by_type
        }
    }

# ============ 批量操作工具 ============

def batch_screenshot(urls: List[str], save_dir: str = "screenshots/") -> Dict:
    """批量截图"""
    import os
    os.makedirs(save_dir, exist_ok=True)
    
    results = {"success": [], "failed": []}
    pw, browser, ctx, page = create_browser()
    
    for i, url in enumerate(urls):
        try:
            page.goto(url, timeout=15000)
            page.wait_for_timeout(1000)
            path = f"{save_dir}screenshot_{i+1}.png"
            page.screenshot(path=path)
            results["success"].append({"url": url, "path": path})
        except Exception as e:
            results["failed"].append({"url": url, "error": str(e)})
    
    close_browser(pw, browser)
    return results

# ============ 工具函数 ============

def set_cookies(context: BrowserContext, cookies: List[Dict]):
    """批量设置Cookie"""
    context.add_cookies(cookies)

def get_cookies(context: BrowserContext) -> List[Dict]:
    """获取所有Cookie"""
    return context.cookies()

def clear_cache(context: BrowserContext):
    """清除缓存"""
    context.clear_cookies()
    context.clear_permissions()

def set_proxy(context: BrowserContext, proxy: str):
    """设置代理（需重启浏览器）"""
    # 注意：设置代理需要创建新context
    pass

if __name__ == "__main__":
    # 快速测试
    print("🧪 测试 headless_browser_utils")
    
    # 测试1: 快速获取
    content, page, ok = quick_get("https://www.baidu.com")
    print(f"✅ quick_get: {'成功' if ok else '失败'}")
    
    # 测试2: 截图
    ok = capture_screenshot("https://github.com", "test_utils.png")
    print(f"✅ capture_screenshot: {'成功' if ok else '失败'}")
    
    # 测试3: 反检测浏览器
    pw, browser, ctx, page = create_browser_with_stealth()
    page.goto("https://www.baidu.com", timeout=15000)
    webdriver = page.evaluate("() => navigator.webdriver")
    print(f"✅ stealth browser: webdriver={webdriver}")
    close_browser(pw, browser)
    
    print("\n🎉 所有工具测试通过！")
