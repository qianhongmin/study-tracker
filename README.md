# 学习追踪工具 Study Tracker

一个记录"每天学了什么、学了多久"的个人工具，并在此基础上做统计、可视化，再用大模型对真实学习数据做分析——自动出复习题、生成学习总结与下周建议。

解决的问题：普通待办/笔记工具只记录"做了什么"，不会告诉你"学得怎么样、哪里有问题、下一步该怎么办"。这个项目把**记录 → 统计 → 可视化 → AI 分析**串成一条完整链路，让数据真正产生决策价值。

## 在线演示

**https://cqxsm111.pythonanywhere.com**

| 页面 | 路径 | 说明 |
|---|---|---|
| 记录列表 + 统计 + 趋势图 | `/` | 首页 |
| 新增记录 | `/add`（POST） | 表单提交后重定向回首页（PRG 模式） |
| AI 出题 | `/quiz` | 读取数据库中的真实记录，让 AI 只针对已学科目出题 |
| AI 学习总结 | `/summary` | 让 AI 分析学习节奏、指出问题、给出下周建议 |
| AI 自由问答 | `/ai` | 输入任意问题，后端转发给大模型 |

## 功能

- [x] 记录学习条目：科目 / 时长（分钟）/ 笔记，日期由服务端自动写入
- [x] 查看全部记录
- [x] 统计：各科目合计时长、每天合计时长（SQL 聚合，非 Python 手算）
- [x] 学习趋势柱状图（Chart.js）
- [x] AI 基于真实学习记录生成复习题
- [x] AI 生成学习总结 + 问题诊断 + 可执行建议
- [x] 独立部署上线，支持 HTTPS
- [ ] 表单输入校验（网页版尚未实现，见"已知限制"）
- [ ] 删除 / 编辑记录（CRUD 尚不完整）
- [ ] 用户登录与数据隔离（当前任何人可写入，见"已知限制"）

## 技术栈

Python · Flask · SQLite · Jinja2 · Chart.js · DeepSeek API（OpenAI 兼容格式）· Git · PythonAnywhere

## 快速开始

```bash
# 1. 安装依赖
pip install flask requests markdown

# 2. 初始化数据库（首次运行必须执行，创建 records 表）
python db_init.py

# 3. 配置大模型 API Key（AI 功能需要；不配置则普通记录/统计功能照常可用）
#    Windows PowerShell：
$env:DEEPSEEK_KEY = "sk-你自己的key"
#    Linux / macOS：
export DEEPSEEK_KEY="sk-你自己的key"

# 4. 启动
python app.py
```

访问 http://127.0.0.1:5000

> Key 获取：在 DeepSeek 开放平台注册并充值后创建 API Key。本项目通过环境变量读取 Key，代码与仓库中不含任何凭证。

## 项目结构

```
tracker-web/
├── app.py            Flask 主程序：路由、数据库读写、调用大模型
├── db_init.py        一次性建表脚本（CREATE TABLE records）
├── db_insert.py      示例数据插入脚本（executemany 批量写入）
├── templates/        Jinja2 模板
│   ├── index.html    首页：表单 + 记录列表 + 统计 + 图表
│   ├── quiz.html     AI 出题页
│   ├── summary.html  AI 学习总结页
│   └── ask.html      AI 问答页
└── static/           静态资源
    ├── style.css     页面样式
    └── chart.umd.js  Chart.js（本地引用，不依赖 CDN）
```

### 数据库

单表 `records`：

| 列 | 类型 | 说明 |
|---|---|---|
| date | TEXT | 日期，`YYYY-MM-DD` |
| subject | TEXT | 科目 |
| minutes | INTEGER | 学习分钟数 |
| note | TEXT | 一句话笔记 |

统计完全交给 SQL 聚合，例如各科目合计：

```sql
SELECT subject, SUM(minutes) AS total FROM records GROUP BY subject
```

## 设计要点（我在实现中做的关键决定）

1. **校验标准应与处理标准一致**：命令行版曾用 `isdigit()` 做入口校验，但统计处实际用 `int()` 处理——两套标准会导致"入口放行、下游崩"（如全角数字）。改用 `try: int(x)` 探雷后，校验与处理变成同一个动作，逻辑才真正闭合。网页版目前尚未补上这层校验（见"已知限制"）。
2. **Post/Redirect/Get**：表单提交后重定向回首页。实测过不重定向时刷新页面会重复写入一条记录，因此采用 PRG 规避。
3. **AI 必须"喂数据"才有价值**：大模型不知道用户学过什么。本项目把数据库记录拼成文本，用 `system` 角色设定"只根据记录出题、不得编造未学科目"的约束，AI 输出会真实反映个人数据。
4. **AI 输出是 Markdown，需要渲染**：用 `markdown` 库转成 HTML，模板中配合 `| safe` 输出。
5. **部署前改造两处代码**：数据库改用基于 `__file__` 的绝对路径（WSGI 启动时工作目录不是项目目录）；API Key 改由环境变量读取（凭证不进代码、不进仓库）。
6. **前端库本地化**：Chart.js 下载到 `static/` 而非用 CDN，避免网络环境不可达导致图表空白。

## 部署

托管在 PythonAnywhere（免费档），要点：

- WSGI 入口文件中把项目目录加入 `sys.path`，并设置 `os.environ["DEEPSEEK_KEY"]`，最后 `from app import app as application`
- 服务器 Python 版本需与安装依赖的版本一致
- 发布流程：本地提交 → 打包上传 → 解压覆盖 → Reload Web App
- 排错看平台的 error log（等价于本地看终端输出）

## 已知限制

- **无身份认证**：公开可访问，任何人都能读写这份数据；`/quiz`、`/summary` 会消耗 API 额度。计划通过登录系统解决。
- **表单缺少输入校验**：时长字段直接写入数据库，非数字输入会污染统计结果（SQLite 弱类型不会拒绝它）。
- **CRUD 不完整**：只能新增和查询，缺少修改、删除。
- **历史数据存在测试脏数据**：早期练习写库时插入的无效科目（例如"火车""数据测试"）仍在库中，会影响统计与 AI 分析的可信度——这也是本项目暴露出的"数据治理"真实课题。
- **单用户设计**：数据表没有用户维度。

## 开发历程

这个项目分四个阶段从零搭建，每一步都先做出"能用的东西"，再往上加能力：

1. **命令行版**：Python 基础语法 → 文件读写与 JSON 持久化 → 菜单循环 → SQL 之外的手写分组统计 → 输入容错 → 函数化重构。
2. **网页版**：Flask 路由 → 模板渲染（后端→前端）→ 表单提交（前端→后端）→ SQLite 替换 JSON → CSS 与 Chart.js 可视化。
3. **AI 增强**：调用大模型 API → 把数据库真实数据拼进 prompt → 用 system 角色约束输出 → Markdown 渲染。
4. **上线运维**：路径与凭证改造 → 打包部署 → WSGI 配置 → HTTPS 验证 → git/GitHub 版本管理。

## License

个人学习项目。
