"""
Everything 联动工具
支持两种模式：
1. CLI 模式：使用内嵌 es.exe（推荐，无需 Everything GUI 运行）
2. HTTP 模式：使用 Everything HTTP API（需要端口 8025）
"""
import os, subprocess, requests
from bs4 import BeautifulSoup

# CLI 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ES_EXE = os.path.join(SCRIPT_DIR, "es.exe")

# HTTP 配置
EVERYTHING_URL = "http://localhost:8025/"

def everything_search(query, max_results=20):
    """
    搜索 Everything 索引的文件
    
    自动模式优先级：
    1. CLI 模式 - 内嵌 es.exe，无需用户安装
    2. HTTP 模式 - 需要 Everything GUI + HTTP 服务器
    
    Args:
        query: 搜索字符串，支持通配符如 *.py, D:\\Project\\*.md
        max_results: 最大返回数量
    
    Returns:
        list[dict]: [{'name', 'path', 'size', 'date'}, ...]
    """
    
    # 优先 CLI 模式
    if os.path.exists(ES_EXE):
        return _cli_search(query, max_results)
    
    # CLI 不存在，提示并尝试 HTTP
    print("⚠️ 内嵌 es.exe 未找到")
    print("💡 建议: 下载 Everything CLI (67KB)")
    print("   https://www.voidtools.com/downloads/ → ES-1.1.0.30.x64.zip")
    print("   解压后放入: memory/everything_search/es.exe")
    print("   这样无需启动 Everything GUI 也可搜索\n")
    
    try:
        return _http_search(query, max_results)
    except Exception as e:
        print(f"❌ HTTP 模式也失败: {e}")
        print("请确保 Everything GUI 已安装并开启了 HTTP 服务器")
        print("菜单: 工具 → 选项 → HTTP服务器 → 启用 (默认端口8025)")
        return []

def _cli_search(query, max_results):
    """CLI 模式搜索"""
    result = subprocess.run(
        [ES_EXE, "-n", str(max_results), query],
        capture_output=True, text=True, timeout=30
    )
    
    results = []
    for line in result.stdout.strip().split('\n'):
        if not line or line.startswith('Total='):
            continue
        # es.exe 输出纯路径，取最后一段为文件名
        path = line.strip()
        name = os.path.basename(path)
        results.append({
            'name': name,
            'path': path,
            'size': '',
            'date': ''
        })
    return results

def _http_search(query, max_results):
    """HTTP 模式搜索"""
    url = f"{EVERYTHING_URL}?s={query}&n={max_results}"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    results = []
    table = soup.find('table')
    if table:
        for row in table.find_all('tr')[2:]:
            cells = row.find_all('td')
            if len(cells) >= 4:
                results.append({
                    'name': cells[0].get_text(strip=True),
                    'path': cells[1].get_text(strip=True),
                    'size': cells[2].get_text(strip=True),
                    'date': cells[3].get_text(strip=True)
                })
    return results

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "*"
    
    print(f"搜索: {query} (CLI: {'✓' if os.path.exists(ES_EXE) else '✗'})\n")
    for r in everything_search(query):
        print(f"{r['name']} | {r['path']} | {r['size']}")
