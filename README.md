# 📖 课伴（Keban）— 乡村课堂AI助教


**教师端 + 学生端双应用**，AI赋能乡村教育。

---

## 🏗️ 项目结构

```
keban/
├── server/                ← 后端服务（Flask API）
├── teacher-client/        ← 教师端（Vue3）
├── student-client/        ← 学生端（Vue3）
└── README.md
```

三个项目独立运行，通过 API 连接。

---

## 🚀 快速开始(该方法适用于在本地沙箱部署)

### 1. 后端服务

```bash
cd server
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
python app.py
# → http://localhost:5000
```

### 2. 教师端

```bash
cd teacher-client
npm install
npm run dev
# → http://localhost:3001
```

**首次使用**：打开 http://localhost:3001 → 配置 API Key → 创建教师账号 → 登录使用

### 3. 学生端

```bash
cd student-client
npm install
npm run dev
# → http://localhost:3002
```

**登录方式**：教师端创建账号 → 学生用账号密码登录（不能自行注册）

---

## 🧭 使用流程

### 首次启动（只需一次）

1. 打开教师端（http://localhost:3001）
2. 填写阿里云 DashScope API Key（免费额度够用）
3. 创建教师账号（用户名+密码）
4. 用教师账号登录 → 进入工作台
5. 在「学生管理」中添加学生账号
6. 把账号密码告诉学生（默认 123456）

### 日常使用

**教师端（3001）功能一览：**

| 模块 | 说明 |
|---|---|
| 💡 课后复盘 | 输入课堂内容，AI分析亮点/盲区/节奏 |
| 📖 备课助手 | 输入知识点，生成课件大纲+练习题 |
| 📊 学情看板 | 提问趋势、科目分布、薄弱知识点可视化 |
| 📨 家校简报 | AI生成给家长的简报，可复制发微信 |
| 📆 教师周报 | 自动汇总本周数据，可导出 TXT |
| 👥 学生管理 | 添加/批量导入/Excel导入/搜索/删除学生 |
| 🔑 重置密码 | 重置学生密码（防忘记） |
| 📥 导出账号 | 导出学生列表 Excel（含默认密码） |
| 📊 成绩管理 | 导入成绩 / 按考试筛选 / 统计等级分布 |
| 📄 智能出卷 | AI生成试卷，支持下载 TXT |
| ⭐ 积分管理 | 学生积分排行 / 手动加减分 / 明细查询 |
| 🎁 兑换管理 | 添加/上下架兑换项目 / 确认学生兑换 |
| 🚨 风险预警 | 树洞敏感词自动预警，可解除风险 |
| 📨 学生简报 | AI分析单个学生的学习报告 |
| ✉️ 留言管理 | 查看学生留言并回复 |

**学生端（3002）功能一览：**

| 模块 | 说明 |
|---|---|
| 📷 拍题答疑 | 拍照上传，AI用小学生能听懂的方式讲解 |
| 📚 错题本 | 上传错题 / AI讲解 / 按科目筛选 / 删除 |
| 🎤 语音问答 | 语音输入或打字提问，AI回答，可朗读 |
| 💬 心情树洞 | 选心情聊天，情感陪伴，敏感词自动预警 |
| 📊 成绩查看 | 成绩列表 + 等级标签 + 趋势展示 |
| ⭐ 积分系统 | 积分余额 / 兑换奖品 / 明细记录 / 排行榜 |
| ✉️ 留言 | 给老师发消息，查看老师回复 |

---

## 🔐 认证机制

- **教师端**：首次启动时配置 Key → 创建教师账号 → 登录后使用
- **学生端**：不能自行注册，必须由教师在后台添加账号
- 登录 Token 保存在浏览器 localStorage

---

## ⚙️ 客户端部署(正式部署，适用于生产环境)

### 配置服务器地址

修改 `teacher-client/src/config.js` 和 `student-client/src/config.js`：

```js
// 开发模式（Vite代理）—— 注释此行
export const API_BASE = ''

// 部署到服务器 —— 取消注释下面这行
// export const API_BASE = 'http://你的服务器IP:5000'
```

即更改为(123.456.789.123为示例IP，更改为真实的公网IP即可)
```
// export const API_BASE = ''
export const API_BASE = 'http://123.456.789.123:5000'
```

### 构建前端

```bash
cd teacher-client && npm run build   # dist/ 文件夹
cd student-client && npm run build   # dist/ 文件夹
```

上传俩个dist文件夹至服务器并分别解析域名指向其中的index.html文件即可
即http://teacher.example.com/ 指向教师端构建出来的index.html即可访问教师端 http://student.example.com/student/ 指向学生端构建出来的index.html即可访问学生端

## 服务端部署

首先上传服务端文件进服务器，假设解压后服务端的地址为/根目录/www/wwwroot/keban/server/...
然后安装 Python 依赖
```
cd /www/wwwroot/keban/server

#安装python3-venv
apt install python3-venv -y

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```
启动服务端
```
# 确保在虚拟环境中（前方有 (venv) 标志）
# 启动 Flask 服务
nohup python app.py > app.log 2>&1 &
```

验证服务端是否启动

```
curl http://127.0.0.1:5000/api/teacher/students
```
如果返回 {"error":"需要认证"} 表示服务端运行正常。

## 🔑 获取 API Key

1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com/)
2. 注册/登录 → 我的 API Key
3. 创建新 Key，复制保存
4. 在教师端首次配置时粘贴

**费用**：新用户有免费额度，日常使用基本不花钱。

---

## 🛠️ 技术栈

| 项目 | 技术 |
|---|---|
| 后端 | Python + Flask + SQLite |
| 教师端 | Vue3 + Vite + 原生CSS |
| 学生端 | Vue3 + Vite + 原生CSS |
| AI | 阿里云 DashScope（Qwen-Max / Qwen3-VL-Plus）|
| 语音 | Web Speech API + FunASR（可选兜底）|
| 数据导出 | SheetJS (xlsx) 导出 Excel |

---

## 📄 文件说明

```
server/
├── app.py              # Flask 主入口（API + 认证）
├── api/                # Qwen/FunASR 封装
├── db/__init__.py      # SQLite 建表 + 认证工具
├── uploads/            # 图片上传目录
├── requirements.txt    # Python 依赖
└── .env                # 环境变量（备用）

teacher-client/
├── src/views/
│   ├── Setup.vue              # 首次配置（Key + 教师账号）
│   ├── Login.vue              # 教师登录
│   └── TeacherDashboard.vue   # 工作台（15+个功能模块）
├── src/config.js              # 服务器地址配置
└── src/router/index.js        # 路由 + 认证守卫

student-client/
├── src/views/
│   ├── Login.vue              # 学生登录
│   └── StudentHome.vue        # 学习首页（7大模块）
├── src/config.js              # 服务器地址配置
└── src/router/index.js        # 路由 + 认证守卫
```
