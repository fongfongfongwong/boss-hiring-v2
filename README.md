# Boss 直聘自动化招聘系统

基于 **RPA + AI** 的全流程自动化招聘系统。内部同事通过 Web 界面输入岗位需求，系统自动完成从职位分析、候选人搜索沟通、简历收集评分到联系方式获取的完整闭环。

## 功能特性

- **AI 职位分析** — 输入职位名称，AI 自动生成 JD、搜索关键词矩阵和评分标准
- **智能反检测 RPA** — 通过真实浏览器 Profile + 人类行为模拟绕过 Boss 直聘反爬
- **自动候选人沟通** — AI 驱动的个性化打招呼和多轮对话
- **简历 AI 深度评分** — 五维度（技能/经验/学历/项目/综合）自动评分
- **联系方式自动获取** — 对达标候选人自动跟进索要微信/手机号
- **Web 管理看板** — 招聘漏斗、候选人列表、简历详情、实时日志

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 后端 | FastAPI + Python 3.11+ |
| 浏览器自动化 | Playwright + playwright-stealth |
| AI/LLM | OpenAI 兼容接口 (GPT-4o / DeepSeek / Claude) |
| 数据库 | SQLite + SQLAlchemy |

## 快速开始

### 1. 安装后端

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # 编辑填入 LLM API Key
```

### 2. 安装前端

```bash
cd frontend
npm install
npm run build
```

### 3. 首次登录 Boss 直聘

```bash
cd backend
python main.py setup
# 在弹出的浏览器中登录你的 Boss 直聘招聘者账号
# 登录完成后按 Ctrl+C
```

### 4. 启动服务

```bash
cd backend
python main.py serve
```

打开 `http://localhost:8000`，点击「新建招聘任务」开始使用。

## 使用流程

1. **新建任务** — 输入职位名称（如 "Quant Trader"），AI 自动分析
2. **调整配置** — 预览 JD、编辑关键词、设置每日上限和评分阈值
3. **一键启动** — 系统全自动在后台运行
4. **实时监控** — 在看板页面查看招聘漏斗和实时日志
5. **查看结果** — 在候选人页面查看简历、评分和联系方式

## 项目结构

```
boss-recruiter/
├── frontend/              # React 前端
│   └── src/
│       ├── pages/         # Dashboard, CreateTask, CandidateList, ...
│       ├── api/           # API 客户端
│       └── hooks/         # WebSocket Hook
│
├── backend/               # Python 后端 + 自动化引擎
│   ├── analyzer/          # 模块一: 职位分析
│   ├── rpa/               # 模块二: RPA 浏览器引擎
│   ├── communicator/      # 模块三+五: 候选人沟通 + 联系方式获取
│   ├── resume_analysis/   # 模块四: 简历 AI 分析
│   ├── pipeline/          # 流水线编排器
│   ├── web/               # FastAPI 路由
│   └── database/          # SQLAlchemy ORM
```

## 免责声明

本项目仅供学习和研究用途。请遵守 Boss 直聘的用户协议和相关法律法规。
