"""
多搜索引擎工具 - Multi-Search Engine Utility
================
SOP配套工具 | 支持多种搜索引擎智能切换
创建: 2026-05-03 | 作者: GA | 定制者: 彭利

策略: 必应 → 百度 → 搜狗 → 微信 → 哔哩哔哩
"""

from playwright.sync_api import sync_playwright
from typing import Optional, List, Dict, Tuple
import time
import json

# ============ 搜索引擎配置 ============

SEARCH_ENGINES = {
    # 中文搜索引擎（优先级顺序）
    "bing": {
        "url": "https://www.bing.com/search?q={query}",
        "result_selector": "li.b_algo",
        "title_selector": "h2",
        "snippet_selector": "div.b_caption p",
        "timeout": 15000
    },
    "baidu": {
        "url": "https://www.baidu.com/s?wd={query}",
        "result_selector": "div.result",
        "title_selector": "h3.t a",
        "snippet_selector": "div.c-abstract, div.result-info",
        "timeout": 15000
    },
    "sogou": {
        "url": "https://www.sogou.com/web?query={query}",
        "result_selector": "div.vrwrap, div.rb",
        "title_selector": "h3.pt a, h3.vr-title",
        "snippet_selector": "div.str_text, p.str_info",
        "timeout": 15000
    },
    
    # 垂直搜索
    "weixin": {
        "url": "https://weixin.sogou.com/weixin?type=2&s_from=input&query={query}&ie=utf8&_sug_=n&_sug_type_=",
        "result_selector": "div.news-box ul li",
        "title_selector": "div.txt-info h3 a",
        "snippet_selector": "div.txt-info p.txt-info",
        "timeout": 15000
    },
    "bilibili": {
        "url": "https://search.bilibili.com/all?keyword={query}",
        "result_selector": "li.video-item",
        "title_selector": "a.title",
        "snippet_selector": "span.description",
        "timeout": 20000
    }
}

# 搜索优先级（按效率和质量排序）
SEARCH_PRIORITY = ["bing", "baidu", "sogou", "weixin", "bilibili", "google"]


# ============ 核心搜索函数 ============

def search_with_engine(
    engine: str,
    query: str,
    max_results: int = 10,
    headless: bool = True,
    proxy: Optional[str] = None
) -> Dict:
    """
    使用指定搜索引擎搜索
    
    Args:
        engine: 搜索引擎名称 (bing/baidu/sogou/weixin/bilibili/google)
        query: 搜索关键词
        max_results: 最大结果数
        headless: 是否无头
        proxy: 代理地址（可选）
    
    Returns:
        {
            "engine": str,
            "query": str,
            "results": [{"title": str, "url": str, "snippet": str}],
            "count": int,
            "time": float,
            "success": bool,
            "error": str or None
        }
    """
    import urllib.parse
    
    if engine not in SEARCH_ENGINES:
        return {
            "engine": engine,
            "query": query,
            "results": [],
            "count": 0,
            "time": 0,
            "success": False,
            "error": f"Unknown engine: {engine}"
        }
    
    config = SEARCH_ENGINES[engine]
    url = config["url"].format(query=urllib.parse.quote(query))
    
    start_time = time.time()
    
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        viewport={"width": 1280, "height": 720}
    )
    page = context.new_page()
    
    results = []
    
    try:
        page.goto(url, timeout=config["timeout"])
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)  # 等待JS渲染
        
        # 提取结果
        result_elements = page.query_selector_all(config["result_selector"])
        
        for elem in result_elements[:max_results]:
            try:
                title_elem = elem.query_selector(config["title_selector"])
                title = title_elem.inner_text() if title_elem else ""
                
                # 获取链接
                link_elem = elem.query_selector("a")
                url_link = link_elem.get_attribute("href") if link_elem else ""
                
                # 获取摘要
                snippet = ""
                for sel in config["snippet_selector"].split(","):
                    snippet_elem = elem.query_selector(sel.strip())
                    if snippet_elem:
                        snippet = snippet_elem.inner_text()
                        break
                
                if title or url_link:
                    results.append({
                        "title": title.strip(),
                        "url": url_link,
                        "snippet": snippet.strip()[:200]
                    })
            except:
                continue
        
        success = True
        error = None
        
    except Exception as e:
        success = False
        error = str(e)
        results = []
        
    finally:
        browser.close()
        pw.stop()
    
    elapsed = time.time() - start_time
    
    return {
        "engine": engine,
        "query": query,
        "results": results,
        "count": len(results),
        "time": round(elapsed, 2),
        "success": success,
        "error": error
    }


def multi_engine_search(
    query: str,
    engines: Optional[List[str]] = None,
    max_results_per_engine: int = 10,
    stop_on_success: bool = True,
    min_results: int = 5
) -> Dict:
    """
    多引擎智能搜索（自动切换+聚合结果）
    
    Args:
        query: 搜索关键词
        engines: 指定引擎列表（None则按优先级）
        max_results_per_engine: 每个引擎最大结果数
        stop_on_success: 获得足够结果后停止
        min_results: 最小期望结果数
    
    Returns:
        {
            "query": str,
            "total_results": int,
            "all_results": [...],
            "engine_results": {...},
            "best_engine": str,
            "success_count": int,
            "failed_engines": [...]
        }
    """
    if engines is None:
        engines = SEARCH_PRIORITY
    
    all_results = []
    engine_results = {}
    best_engine = ""
    success_count = 0
    failed_engines = []
    
    print(f"🔍 开始多引擎搜索: {query}")
    print(f"   引擎顺序: {' → '.join(engines)}")
    print()
    
    for engine in engines:
        print(f"  [{engine}] ", end="", flush=True)
        
        result = search_with_engine(
            engine=engine,
            query=query,
            max_results=max_results_per_engine
        )
        
        engine_results[engine] = result
        
        if result["success"]:
            success_count += 1
            all_results.extend(result["results"])
            print(f"✅ {result['count']}条 ({result['time']}s)")
            
            if not best_engine and result["count"] >= min_results:
                best_engine = engine
                if stop_on_success:
                    print("   📌 已获得" + str(result["count"]) + "条结果，停止搜索")
                    break
        else:
            failed_engines.append(engine)
            print(f"❌ {result['error']}")
    
    # 去重（根据URL）
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)
    
    return {
        "query": query,
        "total_results": len(unique_results),
        "all_results": unique_results,
        "engine_results": engine_results,
        "best_engine": best_engine,
        "success_count": success_count,
        "failed_engines": failed_engines
    }


def quick_search(query: str, engine: str = "bing") -> List[Dict]:
    """
    快速单引擎搜索（简化接口）
    
    Args:
        query: 搜索关键词
        engine: 搜索引擎
    
    Returns:
        结果列表
    """
    result = search_with_engine(engine, query)
    return result["results"] if result["success"] else []


def save_search_results(results: Dict, save_path: str):
    """保存搜索结果到文件"""
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 结果已保存: {save_path}")


# ============ 测试 ============

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 测试多搜索引擎工具")
    print("=" * 60)
    
    # 测试1: 单引擎搜索
    print("\n📌 测试1: 百度搜索")
    r = search_with_engine("baidu", "Python教程")
    print(f"   结果: {r['count']}条, 耗时: {r['time']}s, 成功: {r['success']}")
    if r['results']:
        print(f"   标题: {r['results'][0]['title'][:50]}")
    
    # 测试2: 多引擎搜索
    print("\n📌 测试2: 多引擎搜索（中文）")
    multi = multi_engine_search(
        query="人工智能发展趋势",
        engines=["bing", "baidu"],
        min_results=3
    )
    print(f"\n   总结果: {multi['total_results']}条")
    print(f"   最佳引擎: {multi['best_engine'] or '无'}")
    print(f"   成功率: {multi['success_count']}/{len(multi['engine_results'])}")
    
    # 测试3: 快速搜索
    print("\n📌 测试3: 快速搜索")
    results = quick_search("数据分析", "bing")
    print(f"   获取: {len(results)}条")
    
    print("\n" + "=" * 60)
    print("🎉 多搜索引擎工具测试完成！")
    print("=" * 60)
