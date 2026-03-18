# X 监控配置

# 要监控的 X 账号（带 @ 符号）
ACCOUNTS = ["@elonmusk", "@OpenAI"]

# 要搜索的关键词
KEYWORDS = ["AI agent", "LLM"]

# 每个来源抓取的推文数量
TWEETS_PER_SOURCE = 10

# 数据目录
DATA_DIR = "data"

# 缓存文件路径（用于去重）
CACHE_FILE = "cache.json"

# 缓存最大条目数（防止文件无限增长）
MAX_CACHE_SIZE = 500
