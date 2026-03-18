#!/usr/bin/env python3
"""
X 监控脚本 - 抓取 X/Twitter 数据并保存为 Markdown
"""
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

from config import (
    ACCOUNTS, KEYWORDS, TWEETS_PER_SOURCE,
    DATA_DIR, CACHE_FILE, MAX_CACHE_SIZE
)

SCRIPT_DIR = Path(__file__).parent
CACHE_PATH = SCRIPT_DIR / CACHE_FILE
DATA_PATH = SCRIPT_DIR / DATA_DIR


def get_auth_args() -> str:
    """获取认证参数"""
    auth_token = os.environ.get("X_AUTH_TOKEN", "")
    ct0 = os.environ.get("X_CT0", "")
    cookie_source = os.environ.get("X_COOKIE_SOURCE", "")
    
    if auth_token and ct0:
        return f"--auth-token {auth_token} --ct0 {ct0}"
    elif cookie_source:
        return f"--cookie-source {cookie_source}"
    return ""


def run_xreach(args: str) -> list:
    """调用 xreach CLI，返回解析后的 JSON"""
    auth_args = get_auth_args()
    try:
        result = subprocess.run(
            f"xreach {auth_args} {args} --json",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            print(f"[警告] xreach 调用失败: {result.stderr.strip()}")
            return []
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        return data if isinstance(data, list) else []
    except subprocess.TimeoutExpired:
        print(f"[警告] xreach 超时: {args}")
        return []
    except json.JSONDecodeError as e:
        print(f"[警告] JSON 解析失败: {e}")
        return []


def load_cache() -> set:
    """加载已保存的推文 ID 缓存"""
    if not CACHE_PATH.exists():
        return set()
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return set(data.get("seen_ids", []))
    except Exception:
        return set()


def save_cache(seen_ids: set):
    """保存缓存，只保留最近 N 条"""
    ids = list(seen_ids)[-MAX_CACHE_SIZE:]
    CACHE_PATH.write_text(
        json.dumps({"seen_ids": ids}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def fetch_user_tweets(account: str) -> list:
    """抓取用户时间线"""
    print(f"[抓取] 用户 {account} 的最新推文...")
    tweets = run_xreach(f'tweets {account} -n {TWEETS_PER_SOURCE}')
    result = []
    for t in tweets:
        if isinstance(t, dict):
            t["_source"] = f"用户 {account}"
            t["_source_type"] = "user"
            result.append(t)
    return result


def fetch_keyword_tweets(keyword: str) -> list:
    """按关键词搜索"""
    print(f"[抓取] 关键词 \"{keyword}\" ...")
    tweets = run_xreach(f'search "{keyword}" -n {TWEETS_PER_SOURCE}')
    result = []
    for t in tweets:
        if isinstance(t, dict):
            t["_source"] = f"关键词 \"{keyword}\""
            t["_source_type"] = "keyword"
            result.append(t)
    return result


def filter_new_tweets(tweets: list, seen_ids: set) -> list:
    """过滤掉已保存的推文"""
    new_tweets = []
    for t in tweets:
        tweet_id = t.get("id") or t.get("rest_id")
        if tweet_id and tweet_id not in seen_ids:
            new_tweets.append(t)
            seen_ids.add(str(tweet_id))
    return new_tweets


def parse_tweet(tweet: dict) -> dict:
    """解析推文数据，提取关键字段"""
    tweet_id = tweet.get("id") or tweet.get("rest_id") or ""
    
    user = tweet.get("user", {})
    if isinstance(user, dict):
        username = user.get("screenName") or user.get("screen_name") or "unknown"
        name = user.get("name") or username
    else:
        username = "unknown"
        name = "unknown"
    
    text = tweet.get("text") or tweet.get("full_text") or ""
    text = text.replace("\n", " ").strip()
    
    created_at = tweet.get("createdAt") or tweet.get("created_at") or ""
    if created_at:
        try:
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            time_str = dt.strftime("%H:%M")
        except Exception:
            time_str = created_at[:16] if len(created_at) > 16 else created_at
    else:
        time_str = "未知时间"
    
    url = tweet.get("url") or f"https://x.com/{username}/status/{tweet_id}"
    
    return {
        "id": tweet_id,
        "username": username,
        "name": name,
        "text": text,
        "time": time_str,
        "url": url,
        "source": tweet.get("_source", ""),
        "source_type": tweet.get("_source_type", "")
    }


def format_markdown(tweets: list, date_str: str) -> str:
    """格式化推文为 Markdown"""
    lines = [f"# {date_str}", ""]
    
    grouped = {}
    for t in tweets:
        source = t["source"]
        if source not in grouped:
            grouped[source] = []
        grouped[source].append(t)
    
    for source, items in grouped.items():
        lines.append(f"## {source}")
        lines.append("")
        
        for t in items:
            lines.append(f"### {t['time']} @{t['username']}")
            lines.append("")
            lines.append(t["text"])
            lines.append("")
            lines.append(f"[链接]({t['url']})")
            lines.append("")
            lines.append("---")
            lines.append("")
    
    return "\n".join(lines)


def save_markdown(content: str, date_str: str):
    """保存 Markdown 文件"""
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    file_path = DATA_PATH / f"{date_str}.md"
    
    if file_path.exists():
        existing = file_path.read_text(encoding="utf-8")
        content = existing.rstrip() + "\n\n" + content.split("\n", 2)[-1]
    
    file_path.write_text(content, encoding="utf-8")
    print(f"[保存] {file_path}")


def main():
    print(f"=== X 监控脚本开始 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print()
    
    seen_ids = load_cache()
    print(f"[缓存] 已有 {len(seen_ids)} 条记录")
    
    all_tweets = []
    
    for account in ACCOUNTS:
        tweets = fetch_user_tweets(account)
        all_tweets.extend(tweets)
    
    for keyword in KEYWORDS:
        tweets = fetch_keyword_tweets(keyword)
        all_tweets.extend(tweets)
    
    print()
    print(f"[统计] 共抓取 {len(all_tweets)} 条推文")
    
    new_tweets = filter_new_tweets(all_tweets, seen_ids)
    print(f"[统计] 其中 {len(new_tweets)} 条是新的")
    
    save_cache(seen_ids)
    
    if not new_tweets:
        print("[完成] 没有新推文")
        return
    
    parsed = [parse_tweet(t) for t in new_tweets]
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    md_content = format_markdown(parsed, date_str)
    save_markdown(md_content, date_str)
    
    print()
    print(f"=== 完成，保存了 {len(new_tweets)} 条新推文 ===")


if __name__ == "__main__":
    main()
