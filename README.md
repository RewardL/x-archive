# X Archive

自动抓取 X/Twitter 数据并归档为 Markdown 文件。

## 功能

- 监控指定用户的最新推文
- 按关键词搜索相关推文
- 自动去重，避免重复保存
- 按日期组织 Markdown 文件
- 通过 GitHub Actions 定时运行

## 配置

编辑 `config.py` 设置要监控的账号和关键词：

```python
ACCOUNTS = ["@elonmusk", "@OpenAI"]
KEYWORDS = ["AI agent", "LLM"]
TWEETS_PER_SOURCE = 10
```

## 本地运行

1. 安装 xreach：
   ```bash
   npm install -g xreach-cli
   ```

2. 配置 X/Twitter 认证（二选一）：
   
   **方式 A：从浏览器提取（推荐）**
   ```bash
   # 设置环境变量
   export X_COOKIE_SOURCE=chrome
   ```
   
   **方式 B：手动设置 token**
   ```bash
   # 从浏览器开发者工具的 Cookies 中获取 auth_token 和 ct0
   export X_AUTH_TOKEN=your_auth_token
   export X_CT0=your_ct0_token
   ```

3. 运行脚本：
   ```bash
   python fetch_x.py
   ```

## 自动运行（GitHub Actions）

1. 推送代码到 GitHub

2. 配置 Secrets（Settings → Secrets and variables → Actions）：
   - `X_AUTH_TOKEN`: 你的 auth_token cookie
   - `X_CT0`: 你的 ct0 cookie
   
   获取方式：登录 x.com，打开开发者工具 → Application → Cookies → x.com，复制这两个值

3. GitHub Actions 会每 6 小时自动运行一次，也可以在 Actions 页面手动触发

## 数据目录

抓取的数据保存在 `data/` 目录下，按日期命名：

```
data/
├── 2026-03-17.md
├── 2026-03-18.md
└── ...
```

## 注意事项

- xreach 在 GitHub Actions 上可能受到 X 的 IP 限制
- 如果抓取失败，可考虑配置代理或使用 Twitter API v2
