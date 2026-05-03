# Playwright 无头浏览器 SOP
> 用途：JS渲染快速抓取，补充TMWebDriver | 依赖：playwright>=1.59.0

## 定位
| 工具 | 特点 | 场景 |
|------|------|------|
| TMWebDriver | 保留登录态 | 需Cookie/复杂交互 |
| Playwright | 无头高速 | 快速抓取/反爬/批量 |

## 模板
```python
from playwright.sync_api import sync_playwright as pw
with pw() as p:
 b=p.chromium.launch(headless=True); pg=b.new_page()
 pg.goto(url, wait_until='networkidle', timeout=15000)
 html=pg.content(); pg.screenshot(path='x.png',full_page=True); b.close()
```

## 参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| wait_until | networkidle | 可选：domcontentloaded/commit |
| timeout | 15000 | ms |
| headless | True | |

## 常用
| 操作 | 代码 |
|------|------|
| 等待元素 | pg.wait_for_selector('css',timeout=5000) |
| 执行JS | pg.evaluate('()=>{...}') |
| 滚动懒加载 | pg.evaluate('window.scrollTo(0,document.body.scrollHeight)') |
| 拦截请求 | pg.route('**/*',lambda r:r.abort() if 'ads' in r.url else r.continue_()) |
| 多标签 | pg2=b.new_page() |
| 反检测 | args=['--disable-blink-features=AutomationDetection'] |

## 协同
- web_scan失败 → Playwright兜底
- 大规模采集 → 批量任务
- 登录态复杂 → TMWebDriver

## 配套工具（`../memory/`）
| 文件 | 导出 | 说明 |
|------|------|------|
| headless_browser_utils.py | create_browser, quick_get, capture_screenshot, extract_links, block_requests, stealth_browser, batch_open | 核心工具 |
| multi_search_engine.py | search_with_engine, multi_engine_search, quick_search | 搜索引擎，engines=['bing','baidu','sogou','weixin','bilibili'] |
| advanced_funcs.py | fill_form, paginated_crawl, extract_table, upload_file, BrowserTest, analyze_page_performance, scroll_to_element, drag_and_drop | 高级功能 |

使用：`from multi_search_engine import multi_engine_search; r=multi_engine_search('query')`

更新：2026-05-03 | 彭利
