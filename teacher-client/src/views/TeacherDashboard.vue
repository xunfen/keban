<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span>📖</span> 课伴
      </div>
      <nav class="sidebar-nav">
        <button v-for="item in navItems" :key="item.key"
          class="nav-item" :class="{active: active===item.key}"
          @click="active=item.key">
          <span class="nav-icon">{{ item.icon }}</span>
          {{ item.label }}
        </button>
      </nav>
      <div class="sidebar-footer">
        <NetworkStatus />
        <button class="btn btn-sm btn-ghost" @click="logout" style="margin-top:8px;width:100%;font-size:13px;padding:6px 12px;color:var(--c-text-muted)">🚪 退出登录</button>
      </div>
    </aside>

    <!-- Content -->
    <main class="main-area">
      <h1 class="page-title">{{ currentNav?.label }}</h1>
      <p class="page-sub">{{ currentNav?.desc }}</p>

      <!-- ======== 课后复盘 ======== -->
      <div v-show="active==='review'">
        <div class="card">
          <div class="card-header"><span class="card-icon">💡</span><h3>输入课堂内容</h3></div>
          <div class="form-group">
            <textarea v-model="reviewText" placeholder="粘贴课堂实录或描述上课内容…例如：'今天讲了分数加减法，大部分学生能理解同分母，但异分母开始混乱…'" rows="5"></textarea>
          </div>
          <button class="btn btn-primary" :disabled="loading.review||!reviewText.trim()" @click="doReview">
            <span v-if="loading.review" class="spinner"></span>
            {{ loading.review ? 'AI 分析中…' : '开始分析 📊' }}
          </button>
        </div>

        <div v-if="reviewResult" class="card">
          <div class="card-header"><span class="card-icon">📋</span><h3>分析结果</h3></div>
          <div class="result-box">
            <div v-for="(sec, i) in reviewSections" :key="i" class="result-section">
              <h4>{{ sec.icon }} {{ sec.title }}</h4>
              <p>{{ sec.content }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ======== 备课助手 ======== -->
      <div v-show="active==='prepare'">
        <div class="card">
          <div class="card-header"><span class="card-icon">📖</span><h3>输入知识点</h3></div>
          <div class="form-group">
            <input v-model="topic" placeholder="例如：三年级数学·分数加法" />
          </div>
          <button class="btn btn-primary" :disabled="loading.prepare||!topic.trim()" @click="doPrepare">
            <span v-if="loading.prepare" class="spinner"></span>
            {{ loading.prepare ? '生成中…' : '生成备课方案 ✨' }}
          </button>
        </div>

        <div v-if="lessonPlan" class="grid-2">
          <div class="card">
            <div class="card-header"><span class="card-icon">📋</span><h3>课件大纲</h3></div>
            <p class="form-label">教学目标</p>
            <ul style="padding-left:20px;margin-bottom:12px"><li v-for="g in lessonPlan.outline?.goals" :key="g">{{ g }}</li></ul>
            <p class="form-label">重难点</p>
            <div class="flex mb-2">
              <span v-for="p in lessonPlan.outline?.key_points" :key="p" class="tag tag-orange">{{ p }}</span>
            </div>
            <p class="form-label">教学流程</p>
            <div v-for="(v,k) in lessonPlan.outline?.flow" :key="k" style="margin-bottom:8px">
              <span class="tag tag-blue">{{ k }}</span>
              <span style="font-size:13px;color:var(--c-text-secondary);margin-left:6px">{{ v }}</span>
            </div>
          </div>
          <div class="card">
            <div class="card-header"><span class="card-icon">📝</span><h3>练习题</h3></div>
            <div v-for="(ex,i) in lessonPlan.exercises" :key="i" class="exercise-item">
              <div class="flex">
                <strong>第{{ i+1 }}题</strong>
                <span class="tag" :class="diffTag(ex.difficulty)">{{ ex.difficulty }}</span>
              </div>
              <p style="margin:6px 0">{{ ex.question }}</p>
              <p class="ex-answer">✅ {{ ex.answer }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ======== 学情看板 ======== -->
      <div v-show="active==='stats'">
        <div class="stats-filter">
          <button v-for="d in [1,7,30]" :key="d" class="btn btn-sm" :class="statsDays===d?'btn-primary':'btn-outline'" @click="loadStats(d)">{{ {1:'今天',7:'本周',30:'本月'}[d] }}</button>
        </div>
        <div v-if="stats" class="stats-row">
          <div class="stat-card"><div class="stat-num">{{ stats.total_questions }}</div><div class="stat-label">📌 总提问</div></div>
          <div class="stat-card"><div class="stat-num" style="color:var(--c-green)">{{ Object.values(stats.by_subject||{}).reduce((a,b)=>a+b,0) }}</div><div class="stat-label">📊 已回答</div></div>
          <div class="stat-card"><div class="stat-num" style="color:var(--c-orange)">{{ (stats.weak_topics||[]).length }}</div><div class="stat-label">⚠️ 薄弱点</div></div>
        </div>

        <div v-if="stats" class="card">
          <p class="chart-title">📈 提问趋势</p>
          <div class="bar-chart" v-if="stats.daily_trend?.length">
            <div v-for="d in stats.daily_trend" :key="d.date" class="bar" :style="{height: barH(d.count)+'px'}" :title="d.date+': '+d.count+'次'">
              <span class="bar-label">{{ d.date.slice(5) }}</span>
            </div>
          </div>
        </div>

        <div v-if="stats" class="card">
          <p class="chart-title">📊 科目分布</p>
          <div class="pie-wrap">
            <div class="pie-visual" :style="pieStyle"></div>
            <div class="pie-legend">
              <div v-for="(cnt,sub) in stats.by_subject" :key="sub" class="pie-item">
                <span class="pie-dot" :style="{background: pc(sub)}"></span> {{ sub }}：{{ cnt }} 次
              </div>
            </div>
          </div>
        </div>

        <div v-if="stats" class="card">
          <p class="chart-title">⚠️ 薄弱知识点</p>
          <div v-if="stats.weak_topics?.length" class="flex">
            <span v-for="t in stats.weak_topics" :key="t.topic" class="tag tag-red" style="font-size:13px;padding:4px 14px" :title="t.count+'次错误'">{{ t.topic }}（{{ t.count }}次）</span>
          </div>
          <p v-else class="muted">暂无薄弱数据，等学生提问多了就会显示</p>
        </div>
      </div>

      <!-- ======== 家校简报 ======== -->
      <div v-show="active==='report'">
        <div class="card">
          <div class="card-header"><span class="card-icon">📨</span><h3>生成简报</h3></div>
          <div class="form-group">
            <label class="form-label">选择学生（选填，不选则生成班级简报）</label>
            <select v-model="reportStudentId">
              <option :value="null">— 全班简报 —</option>
              <option v-for="s in students" :key="s.id" :value="s.id">{{ s.display_name||s.username }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">选择日期</label>
            <input type="date" v-model="reportDate" />
          </div>
          <button class="btn btn-primary" :disabled="loading.report" @click="doReport">
            <span v-if="loading.report" class="spinner"></span>
            {{ loading.report ? '生成中…' : '生成简报 ✨' }}
          </button>
          <div v-if="reportText" class="report-preview md" v-html="renderMd(reportText)"></div>
          <div v-if="reportText" class="action-row">
            <button class="btn btn-sm btn-outline" @click="copy(reportText)">📋 复制</button>
          </div>
        </div>
      </div>

      <!-- ======== 教师周报 ======== -->
      <div v-show="active==='weekly'">
        <div class="card">
          <div class="card-header"><span class="card-icon">📆</span><h3>生成周报</h3></div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">开始日期</label>
              <input type="date" v-model="weekStart" />
            </div>
            <div class="form-group">
              <label class="form-label">结束日期</label>
              <input type="date" v-model="weekEnd" />
            </div>
          </div>
          <button class="btn btn-primary" :disabled="loading.weekly" @click="doWeekly">
            <span v-if="loading.weekly" class="spinner"></span>
            {{ loading.weekly ? '生成中…' : '生成周报 📄' }}
          </button>
          <div v-if="weeklyText" class="report-preview md" v-html="renderMd(weeklyText)"></div>
          <div v-if="weeklyText" class="action-row">
            <button class="btn btn-sm btn-outline" @click="download(weeklyText)">⬇️ 下载 TXT</button>
          </div>
        </div>
      </div>

      <!-- ======== 学生管理 ======== -->
      <div v-show="active==='students'">
        <div class="card">
          <div class="card-header"><span class="card-icon">➕</span><h3>添加单个学生</h3></div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">用户名</label>
              <input v-model="newStu.user" placeholder="如：zhangxiao" />
            </div>
            <div class="form-group">
              <label class="form-label">密码</label>
              <input v-model="newStu.pass" placeholder="默认 123456" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">姓名（可选）</label>
            <input v-model="newStu.name" placeholder="如：张小明的账号" />
          </div>
          <button class="btn btn-primary" :disabled="!newStu.user||!newStu.pass||loading.addStu" @click="addStudent">
            {{ loading.addStu?'添加中…':'添加学生 ➕' }}
          </button>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-icon">📋</span><h3>批量导入</h3></div>
          <p class="form-hint" style="margin-bottom:10px">每行一个学生姓名，系统自动生成用户名（拼音+4位数字），密码统一 123456</p>
          <textarea v-model="batchText" rows="6" placeholder="张小明的账号
李磊
王芳"></textarea>
          <div class="flex" style="gap:8px;margin-top:8px">
            <button class="btn btn-primary" :disabled="!batchText.trim()||loading.batch" @click="batchImport">
              {{ loading.batch?'导入中…':'导入学生名单 📥' }}
            </button>
            <button class="btn btn-outline" @click="$refs.excelStudent.click()">📊 从 Excel 导入</button>
            <button class="btn btn-sm btn-ghost" @click="downloadStudentTemplate" title="下载示例表格">📄 示例</button>
          </div>
          <input ref="excelStudent" type="file" accept=".xlsx,.xls" hidden @change="importStudentExcel" />
          <p v-if="batchResult" class="muted mt-2">✅ 成功 {{ batchResult.ok }} 人，失败 {{ batchResult.fail }} 人</p>
          <p v-if="excelStuMsg" class="mt-2" :class="excelStuOk?'success-text':'error-text'">{{ excelStuMsg }}</p>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-icon">👥</span><h3>学生列表（{{ students.length }}人）</h3></div>
          <div style="display:flex;gap:8px;margin-bottom:10px">
            <input v-model="stuSearch" placeholder="🔍 搜索用户名/姓名…" style="flex:1" />
            <button class="btn btn-sm btn-outline" @click="exportStudentsExcel">📥 导出账号（含默认密码）</button>
          </div>
          <div v-if="filteredStudents.length===0" class="muted" style="padding:20px 0;text-align:center">没有找到匹配的学生</div>
          <div v-for="s in filteredStudents" :key="s.id" class="student-row">
            <div class="student-info" @click="selectStudent(s)">
              <strong>{{ s.display_name||s.username }}</strong>
              <span class="muted" style="margin-left:6px;font-size:12px">@{{ s.username }}</span>
              <span v-if="solvedCounts[s.id]" class="tag tag-blue" style="margin-left:8px">{{ solvedCounts[s.id] }}题</span>
            </div>
            <div style="display:flex;gap:4px">
              <button class="btn btn-sm btn-ghost" @click="resetStuPw(s)" title="重置密码">🔑</button>
              <button class="btn btn-sm btn-ghost" @click="delStudent(s.id)" style="color:var(--c-red)">删除</button>
            </div>
          </div>
        </div>

        <!-- 学生详情弹窗 -->
        <div v-if="selectedStudent" class="modal-overlay" @click.self="selectedStudent=null">
          <div class="modal-card">
            <div class="modal-header">
              <h3>📋 {{ selectedStudent.display_name||selectedStudent.username }} 的学习记录</h3>
              <button class="btn btn-sm btn-ghost" @click="selectedStudent=null">✕</button>
            </div>
            <div class="modal-body">
              <h4 style="margin-bottom:8px">📷 拍题记录</h4>
              <p v-if="stuQuestions.length===0" class="muted" style="padding:10px;text-align:center">暂无拍题记录</p>
              <div v-for="q in stuQuestions" :key="q.id" class="stu-q-item" @click="qOpenTeacher=qOpenTeacher===q.id?null:q.id">
                <p class="q-text">{{ (q.content||'').slice(0,80) }}{{ (q.content||'').length>80?'…':'' }}</p>
                <p class="q-meta">{{ q.subject }} · {{ q.date }}</p>
                <div v-if="qOpenTeacher===q.id" style="margin-top:10px">
                  <div v-if="q.image_path" style="margin-bottom:10px">
                    <img :src="q.image_path" style="max-width:100%;border-radius:8px" />
                  </div>
                  <div class="md" v-html="renderMd(q.content||'')"></div>
                </div>
              </div>
              <h4 style="margin:12px 0 8px">📚 错题本</h4>
              <p v-if="stuWrong.length===0" class="muted" style="padding:10px;text-align:center">暂无错题</p>
              <div v-for="w in stuWrong" :key="w.id" class="stu-q-item" @click="wOpenTeacher=wOpenTeacher===w.id?null:w.id">
                <p class="q-text">{{ (w.question||'').slice(0,80) }}{{ (w.question||'').length>80?'…':'' }}</p>
                <p class="q-meta">{{ w.subject||'数学' }} · {{ w.date }}</p>
                <div v-if="wOpenTeacher===w.id" style="margin-top:10px">
                  <div v-if="w.image_path" style="margin-bottom:10px">
                    <img :src="w.image_path" style="max-width:100%;border-radius:8px" />
                  </div>
                  <div class="md" v-html="renderMd(w.explanation||w.question||'')"></div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-sm btn-primary" @click="genStuReport(selectedStudent)">📨 生成该学生简报</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ======== 风险学生 ======== -->
      <div v-show="active==='risk'">
        <div class="card">
          <div class="card-header"><span class="card-icon">🚨</span><h3>风险学生（{{ atRiskStudents.length }}人）</h3></div>
          <p class="form-hint" style="margin-bottom:12px">触发预警的学生会被暂停树洞功能，确认风险解除后可恢复</p>
          <div v-if="atRiskStudents.length===0" class="empty-state">
            <div class="icon">✅</div>
            <p>暂无风险学生</p>
          </div>
          <div v-for="s in atRiskStudents" :key="s.id" class="student-row">
            <div>
              <strong>{{ s.display_name||s.username }}</strong>
              <span class="tag tag-red" style="margin-left:8px">{{ s.alert_count }} 次预警</span>
              <span class="muted" style="margin-left:8px;font-size:12px">最后预警：{{ s.last_alert||'未知' }}</span>
            </div>
            <button class="btn btn-sm btn-success" @click="unblockStudent(s.id)">✅ 解除风险</button>
          </div>
        </div>
      </div>

      <!-- ======== 成绩管理 ======== -->
      <div v-show="active==='scores'">
        <div class="card">
          <div class="card-header"><span class="card-icon">📥</span><h3>导入成绩</h3></div>
          <p class="form-hint" style="margin-bottom:10px">每行一个：姓名,科目,分数,考试名称（可选）| 分数自动转ABCDE等级</p>
          <textarea v-model="scoreBatch" rows="5" placeholder="张小明的账号,数学,85,期中考试
李磊,语文,92
王芳,英语,78"></textarea>
          <div class="flex" style="gap:8px;margin-top:8px">
            <button class="btn btn-primary" :disabled="!scoreBatch.trim()||loading.score" @click="importScores">
              {{ loading.score?'导入中…':'导入成绩 📥' }}
            </button>
            <button class="btn btn-outline" @click="$refs.excelScore.click()">📊 从 Excel 导入</button>
            <button class="btn btn-sm btn-ghost" @click="downloadScoreTemplate" title="下载示例表格">📄 示例</button>
          </div>
          <input ref="excelScore" type="file" accept=".xlsx,.xls" hidden @change="importScoreExcel" />
          <p v-if="scoreResult" class="muted mt-2">✅ 成功 {{ scoreResult.ok }} 条</p>
          <p v-if="excelScoreMsg" class="mt-2" :class="excelScoreOk?'success-text':'error-text'">{{ excelScoreMsg }}</p>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-icon">📊</span><h3>成绩统计</h3></div>
          <div class="form-group">
            <label class="form-label">筛选考试</label>
            <select v-model="examFilter" @change="loadScoreStats">
              <option value="">—— 最近成绩 ——</option>
              <option v-for="e in examList" :key="e" :value="e">{{ e }}</option>
            </select>
          </div>
          <div v-if="scoreStats">
            <div class="stats-row">
              <div class="stat-card"><div class="stat-num">{{ scoreStats.avg }}</div><div class="stat-label">📌 平均分</div></div>
              <div class="stat-card"><div class="stat-num" style="color:#16a34a">{{ scoreStats.max }}</div><div class="stat-label">🏆 最高分</div></div>
              <div class="stat-card"><div class="stat-num" style="color:#dc2626">{{ scoreStats.min }}</div><div class="stat-label">⚠️ 最低分</div></div>
            </div>
            <p class="chart-title">📊 等级分布</p>
            <div class="flex">
              <span v-for="(v,k) in scoreStats.grade_dist" :key="k" class="tag" :class="gradeTag(k)" style="font-size:14px;padding:6px 16px">{{ k }}：{{ v }}人</span>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-icon">📈</span><h3>成绩列表</h3></div>
          <div v-if="allScores.length===0" class="muted" style="padding:20px;text-align:center">暂无成绩数据</div>
          <div v-for="s in allScores" :key="s.id" class="student-row">
            <div>
              <strong>{{ s.display_name||s.username }}</strong>
              <span class="tag" :class="gradeTag(s.grade)" style="margin-left:8px">{{ s.grade }}</span>
              <span class="muted" style="margin-left:8px;font-size:13px">{{ s.subject }} · {{ s.score }}分 · {{ s.exam_name||'日常测验' }}</span>
            </div>
            <span class="muted" style="font-size:12px">{{ s.date }}</span>
          </div>
        </div>
      </div>

      <!-- ======== 智能出卷 ======== -->
      <div v-show="active==='exam'">
        <div class="card">
          <div class="card-header"><span class="card-icon">📄</span><h3>生成试卷</h3></div>
          <div class="grid-2">
            <div class="form-group"><label class="form-label">科目</label><input v-model="examSubject" placeholder="数学" /></div>
            <div class="form-group"><label class="form-label">难度</label>
              <select v-model="examDifficulty"><option>简单</option><option selected>中等</option><option>困难</option></select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">考察知识点</label>
            <input v-model="examTopics" placeholder="如：分数加减法、小数乘除" />
          </div>
          <div class="form-group">
            <label class="form-label">题目数量</label>
            <input v-model="examCount" type="number" min="1" max="50" />
          </div>
          <button class="btn btn-primary" :disabled="loading.exam" @click="genExam">
            <span v-if="loading.exam" class="spinner"></span>{{ loading.exam?'生成中…':'生成试卷 ✨' }}
          </button>
          <div v-if="examResult" class="report-preview md" style="margin-top:12px" v-html="renderMd(examResult)"></div>
          <div v-if="examResult" class="action-row">
            <button class="btn btn-sm btn-outline" @click="copy(examResult)">📋 复制</button>
          </div>
        </div>
      </div>

      <!-- ======== 学生留言 ======== -->
      <div v-show="active==='messages'">
        <div class="card" v-for="m in teacherMsgs" :key="m.id">
          <div class="card-header" style="justify-content:space-between">
            <div>
              <span class="card-icon">👤</span>
              <strong>{{ m.display_name||m.from_name }}</strong>
              <span v-if="!m.is_read" class="tag tag-red" style="margin-left:8px">新</span>
            </div>
            <span class="muted" style="font-size:12px">{{ m.date }}</span>
          </div>
          <p style="margin-bottom:10px">{{ m.content }}</p>
          <div v-if="m.reply" class="result-section" style="border-left-color:var(--c-green)">
            <p style="font-size:13px;color:var(--c-green)"><strong>✅ 已回复：</strong>{{ m.reply }}</p>
          </div>
          <div v-else class="action-row">
            <input v-model="replyTexts[m.id]" placeholder="输入回复…" style="flex:1" />
            <button class="btn btn-sm btn-primary" :disabled="!replyTexts[m.id]?.trim()" @click="replyMsg(m.id)">回复</button>
          </div>
        </div>
        <div v-if="teacherMsgs.length===0" class="empty-state">
          <div class="icon">💬</div>
          <p>暂无学生留言</p>
        </div>
      </div>

      <!-- 预警轮询通知 -->

      <!-- ======== 积分管理 ======== -->
      <div v-show="active==='points_mgmt'">
        <div class="card">
          <div class="card-header"><h3>🏆 积分排行</h3></div>
          <div v-if="ptStudents.length===0" class="muted" style="padding:20px;text-align:center">暂无学生数据</div>
          <div v-for="(s,i) in ptStudents" :key="s.id" class="student-row">
            <div class="flex" style="gap:8px;align-items:center">
              <span style="font-size:18px">{{ ['🥇','🥈','🥉',''][i] || '#'+(i+1) }}</span>
              <strong>{{ s.display_name||s.username }}</strong>
              <span class="tag tag-orange" style="font-size:14px">⭐ {{ s.total||0 }}</span>
            </div>
            <div class="flex" style="gap:4px">
              <button class="btn btn-sm btn-success" @click="openAdjust(s,10)">➕</button>
              <button class="btn btn-sm btn-ghost" style="color:var(--c-red)" @click="openAdjust(s,-5)">➖</button>
              <button class="btn btn-sm btn-outline" @click="viewPtHistory(s)">📋</button>
            </div>
          </div>
        </div>

        <!-- 加减分弹窗 -->
        <div v-if="adjustStudent" class="modal-overlay" @click.self="adjustStudent=null">
          <div class="modal-card" style="width:400px">
            <div class="modal-header">
              <h3>{{ adjPoints>0?'➕ 加分':'➖ 扣分' }} — {{ adjustStudent.display_name||adjustStudent.username }}</h3>
              <button class="btn btn-sm btn-ghost" @click="adjustStudent=null">✕</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">分数</label>
                <input v-model.number="adjPoints" type="number" />
              </div>
              <div class="form-group">
                <label class="form-label">理由（必填）</label>
                <input v-model="adjReason" placeholder="如：课堂表现优秀" />
              </div>
              <button class="btn btn-primary" :disabled="!adjReason.trim()||adjusting" @click="doAdjust">
                {{ adjusting?'提交中…':'确认提交 ✅' }}
              </button>
              <p v-if="adjMsg" class="mt-2 success-text">{{ adjMsg }}</p>
            </div>
          </div>
        </div>

        <!-- 积分明细弹窗 -->
        <div v-if="historyStudent" class="modal-overlay" @click.self="historyStudent=null">
          <div class="modal-card" style="width:500px">
            <div class="modal-header">
              <h3>📋 {{ historyStudent.display_name||historyStudent.username }} 的积分明细</h3>
              <button class="btn btn-sm btn-ghost" @click="historyStudent=null">✕</button>
            </div>
            <div class="modal-body">
              <div v-for="h in ptDetail" :key="h.id||h.created_at" class="student-row" style="flex-wrap:wrap">
                <div>
                  <span :style="{color: h.points>0?'var(--c-green)':'var(--c-red)', fontWeight:600}">{{ h.points>0?'+':'' }}{{ h.points }}</span>
                  <span class="muted" style="margin-left:6px;font-size:13px">{{ h.reason }}</span>
                </div>
                <span class="muted" style="font-size:12px">{{ h.created_at }}</span>
              </div>
              <div v-if="ptDetail.length===0" class="muted" style="padding:20px;text-align:center">暂无记录</div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-sm btn-outline" @click="historyStudent=null">关闭</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ======== 兑换管理 ======== -->
      <div v-show="active==='rewards_mgmt'">
        <div class="card">
          <div class="card-header"><h3>➕ 添加兑换项</h3></div>
          <div class="grid-3">
            <div class="form-group"><label class="form-label">名称</label><input v-model="newReward.name" placeholder="如：免一次作业" /></div>
            <div class="form-group"><label class="form-label">所需积分</label><input v-model.number="newReward.cost" type="number" min="1" /></div>
            <div class="form-group"><label class="form-label">库存（-1=不限）</label><input v-model.number="newReward.stock" type="number" min="-1" /></div>
          </div>
          <button class="btn btn-primary" :disabled="!newReward.name.trim()||loading.rw" @click="addReward">
            {{ loading.rw?'添加中…':'添加兑换项 ➕' }}
          </button>
          <p v-if="rwMsg" class="mt-2" :class="rwMsgOk?'success-text':'error-text'">{{ rwMsg }}</p>
        </div>

        <div class="card">
          <div class="card-header"><h3>🎁 兑换项列表</h3></div>
          <div v-for="r in rewardList" :key="r.id" class="student-row">
            <div>
              <strong>{{ r.name }}</strong>
              <span class="tag tag-orange" style="margin-left:8px">⭐ {{ r.cost }}</span>
              <span class="muted" style="margin-left:8px;font-size:12px">{{ r.stock===-1?'不限量':'剩余 '+r.stock }}</span>
              <span v-if="r.enabled" class="tag tag-green" style="margin-left:4px">上架</span>
              <span v-else class="tag tag-red" style="margin-left:4px">下架</span>
            </div>
            <div class="flex" style="gap:4px">
              <button class="btn btn-sm btn-outline" @click="toggleReward(r)">{{ r.enabled?'下架':'上架' }}</button>
              <button class="btn btn-sm btn-ghost" style="color:var(--c-red)" @click="delReward(r.id)">🗑️</button>
            </div>
          </div>
          <div v-if="rewardList.length===0" class="muted" style="padding:20px;text-align:center">暂未设置兑换项</div>
        </div>

        <div class="card">
          <div class="card-header"><h3>📋 兑换记录</h3></div>
          <div v-for="r in redemptions" :key="r.id" class="student-row">
            <div>
              <strong>{{ r.display_name||r.username }}</strong>
              <span> 兑换「{{ r.reward_name }}」</span>
              <span class="tag tag-orange" style="margin:0 8px">⭐ {{ r.cost }}</span>
              <span class="tag" :class="r.status==='confirmed'?'tag-green':'tag-orange'">{{ r.status==='confirmed'?'已确认':'待确认' }}</span>
            </div>
            <button v-if="r.status!=='confirmed'" class="btn btn-sm btn-success" @click="confirmRedeem(r.id)">✅ 确认</button>
          </div>
          <div v-if="redemptions.length===0" class="muted" style="padding:20px;text-align:center">暂无兑换记录</div>
        </div>
      </div>

      <!-- ======== 系统设置 ======== -->
      <div v-show="active==='settings'">
        <div class="card">
          <div class="card-header"><span class="card-icon">🔑</span><h3>修改 API Key</h3></div>
          <p class="form-hint" style="margin-bottom:10px">更新阿里云 DashScope API Key，新的 Key 会立即生效</p>
          <div class="form-group">
            <label class="form-label">当前状态</label>
            <p class="muted">{{ apiKeyStatus ? '✅ 已配置' : '❌ 未配置' }}</p>
          </div>
          <div class="form-group">
            <label class="form-label">新的 API Key</label>
            <input v-model="newApiKey" type="password" placeholder="sk-..." />
          </div>
          <button class="btn btn-primary" :disabled="!newApiKey.trim()||loading.apiKey" @click="updateApiKey">
            {{ loading.apiKey?'更新中…':'更新 API Key 🔑' }}
          </button>
          <p v-if="apiKeyMsg" class="mt-2" :class="apiKeyOk?'success-text':'error-text'">{{ apiKeyMsg }}</p>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-icon">👤</span><h3>创建教师账号</h3></div>
          <p class="form-hint" style="margin-bottom:10px">一个班级可以有多个教师，创建后新教师可以独立登录管理</p>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">用户名</label>
              <input v-model="newTeacher.user" placeholder="如：teacher2" />
            </div>
            <div class="form-group">
              <label class="form-label">密码</label>
              <input v-model="newTeacher.pass" type="password" placeholder="至少4位" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">姓名（可选）</label>
            <input v-model="newTeacher.name" placeholder="如：王老师" />
          </div>
          <button class="btn btn-primary" :disabled="!newTeacher.user||!newTeacher.pass||loading.createTeacher" @click="createTeacher">
            {{ loading.createTeacher?'创建中…':'创建教师账号 👤' }}
          </button>
          <p v-if="teacherMsg" class="mt-2" :class="teacherMsgOk?'success-text':'error-text'">{{ teacherMsg }}</p>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-icon">👥</span><h3>教师列表（{{ teachersList.length }}人）</h3></div>
          <div v-if="teachersList.length===0" class="muted" style="padding:20px 0;text-align:center">暂无其他教师</div>
          <div v-for="t in teachersList" :key="t.id" class="student-row">
            <div>
              <strong>{{ t.display_name||t.username }}</strong>
              <span class="muted" style="margin-left:6px;font-size:12px">@{{ t.username }}</span>
              <span class="tag tag-blue" style="margin-left:8px;font-size:11px">教师</span>
            </div>
            <span class="muted" style="font-size:12px">{{ t.created_at?.slice(0,10)||'' }}</span>
          </div>
        </div>
      </div>

    </main>
      
  </div>





</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import NetworkStatus from '../components/NetworkStatus.vue'
import { API_BASE } from '../config.js'
import { marked } from 'marked'
import katex from 'katex'
import * as XLSX from 'xlsx'

function authHeaders() {
  const t = localStorage.getItem('kp_teacher_token')
  return t ? { 'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' }
}

const navItems = [
  { key:'review', icon:'💡', label:'课后复盘', desc:'输入课堂内容，AI帮你分析亮点与改进点' },
  { key:'prepare', icon:'📖', label:'备课助手', desc:'输入知识点，一键生成课件大纲和练习题' },
  { key:'stats', icon:'📊', label:'学情看板', desc:'学生提问数据可视化，发现教学盲区' },
  { key:'report', icon:'📨', label:'家校简报', desc:'AI生成给家长的学习简报，可转发微信' },
  { key:'weekly', icon:'📆', label:'教师周报', desc:'自动汇总本周教学数据，生成周报' },
  { key:'students', icon:'👥', label:'学生管理', desc:'添加/导入/管理学生账号' },
  { key:'risk', icon:'🚨', label:'风险学生', desc:'查看和解除学生风险状态' },
  { key:'scores', icon:'📊', label:'成绩管理', desc:'导入成绩、查看统计和波形图' },
  { key:'exam', icon:'📄', label:'智能出卷', desc:'输入知识点自动生成试卷' },
  { key:'messages', icon:'💬', label:'学生留言', desc:'查看和回复学生留言' },
  { key:'settings', icon:'⚙️', label:'系统设置', desc:'API Key 管理、教师账号管理' },
  { key:'points_mgmt', icon:'⭐', label:'积分管理', desc:'学生积分排行、加减分、明细' },
  { key:'rewards_mgmt', icon:'🎁', label:'兑换管理', desc:'设置可兑换的奖励、确认兑换' },
]
const active = ref('review')
const currentNav = computed(() => navItems.find(n=>n.key===active.value))
const loading = ref({})

/* 复盘 */
const reviewText = ref('')
const reviewResult = ref('')
const reviewSections = computed(() => {
  if (!reviewResult.value) return []
  const lines = reviewResult.value.split('\n').filter(Boolean)
  const titles = ['教学亮点','知识盲区','节奏建议']
  const icons = ['💡','🔍','⏱️']
  const sections = []
  let cur = null
  for (const line of lines) {
    const idx = titles.findIndex(t => line.includes(t))
    if (idx>=0) { cur = {title:titles[idx], icon:icons[idx], content:''}; sections.push(cur) }
    else if (cur) cur.content += (cur.content?'；':'')+line.replace(/^[-•·\d.\s、]+/,'').trim()
  }
  return sections
})
async function doReview() {
  if (!reviewText.value.trim()) return
  loading.value.review = true
  try {
    const r = await fetch(API_BASE+'/api/teacher/review',{method:'POST',headers:authHeaders(),body:JSON.stringify({content:reviewText.value})})
    const d = await r.json(); reviewResult.value = d.result || ''
  } catch(e) { alert('请求失败：'+e.message) }
  loading.value.review = false
}

/* 备课 */
const topic = ref('')
const lessonPlan = ref(null)
async function doPrepare() {
  if (!topic.value.trim()) return
  loading.value.prepare = true
  try {
    const r = await fetch(API_BASE+'/api/teacher/prepare',{method:'POST',headers:authHeaders(),body:JSON.stringify({topic:topic.value})})
    const d = await r.json(); lessonPlan.value = d
  } catch(e) { alert('请求失败：'+e.message) }
  loading.value.prepare = false
}
function diffTag(d) { return d==='易'?'tag-green':d==='中'?'tag-orange':'tag-red' }

/* 学情 */
const stats = ref(null); const statsDays = ref(7)
async function loadStats(d) {
  statsDays.value = d
}
function barH(c) {
  const mx = Math.max(...(stats.value?.daily_trend||[]).map(d=>d.count),1)
  return Math.round((c/mx)*100)
}
const pc = s => ({'数学':'#2563eb','语文':'#d97706','英语':'#16a34a'}[s]||'#94a3b8')
const pieStyle = computed(() => {
  if (!stats.value?.by_subject) return {}
  const items = Object.entries(stats.value.by_subject)
  const total = items.reduce((s,[,v])=>s+v,0); if (!total) return {}
  let conic = ''; let a = 0
  for (const [sub,cnt] of items) { const pct = cnt/total*360; conic += `${pc(sub)} ${a}deg ${a+pct}deg,`; a += pct }
  return {background:`conic-gradient(${conic.slice(0,-1)})`}
})

/* 简报 */
const reportDate = ref(new Date().toISOString().slice(0,10))
const reportText = ref('')
const reportStudentId = ref(null)
const students = ref([])
const stuSearch = ref('')
const filteredStudents = computed(() => {
  if (!stuSearch.value.trim()) return students.value
  const q = stuSearch.value.trim().toLowerCase()
  return students.value.filter(s =>
    (s.username||'').toLowerCase().includes(q) ||
    (s.display_name||'').toLowerCase().includes(q)
  )
})
async function doReport() {
  loading.value.report = true
  try {
    const body = {stats:stats.value||{}}
    if (reportStudentId.value) body.student_id = reportStudentId.value
    const r = await fetch(API_BASE+'/api/teacher/report',{method:'POST',headers:authHeaders(),body:JSON.stringify(body)})
    const d = await r.json(); reportText.value = d.report || d.result || ''
  } catch(e) { alert('请求失败：'+e.message) }
  loading.value.report = false
}

/* 周报 */
const weekStart = ref(new Date(Date.now()-6*864e5).toISOString().slice(0,10))
const weekEnd = ref(new Date().toISOString().slice(0,10))
const weeklyText = ref('')
async function doWeekly() {
  loading.value.weekly = true
  try {
    const r = await fetch(API_BASE+'/api/teacher/weekly-report',{method:'POST',headers:authHeaders(),body:JSON.stringify({start:weekStart.value,end:weekEnd.value})})
    const d = await r.json(); weeklyText.value = d.report || d.result || ''
  } catch(e) { alert('请求失败：'+e.message) }
  loading.value.weekly = false
}
function copy(t) { navigator.clipboard.writeText(t).then(()=>alert('已复制！')) }
function download(t) {
  const b = new Blob([t],{type:'text/plain'})
  const a = document.createElement('a'); a.href=URL.createObjectURL(b); a.download=`周报_${weekStart.value}_${weekEnd.value}.txt`; a.click()
}

/* ====== 学生管理 ====== */
const newStu = reactive({user:'', pass:'123456', name:''})

const loadingStu = reactive({addStu:false, batch:false})
const batchText = ref('')
const batchResult = ref(null)

function authPost(url, body) {
  return fetch(API_BASE+url, {method:'POST', headers: authHeaders(), body: JSON.stringify(body)}).then(r=>r.json())
}
function authGet(url) {
  return fetch(API_BASE+url, {headers: authHeaders()}).then(r => r.json())
}

async function loadStudents() {
  const d = await authGet('/api/teacher/students')
  students.value = Array.isArray(d) ? d : []
  loadSolvedCounts()
}
async function addStudent() {
  loadingStu.addStu = true; batchResult.value = null
  try {
    const d = await authPost('/api/teacher/students', {
      username: newStu.user.trim(),
      password: newStu.pass,
      display_name: newStu.name.trim() || newStu.user.trim()
    })
    if (d.ok) { newStu.user=''; newStu.pass='123456'; newStu.name=''; loadStudents(); alert('✅ 添加成功') }
    else { alert('❌ '+(d.error||'添加失败')) }
  } catch(e) { alert('请求失败：'+e.message) }
  loadingStu.addStu = false
}
async function batchImport() {
  loadingStu.batch = true; batchResult.value = null
  const names = batchText.value.trim().split('\n').filter(Boolean)
  const d = await authPost('/api/teacher/students/batch', {names})
  batchResult.value = d
  loadingStu.batch = false
  loadStudents()
}

/* ====== Excel 导入学生 ====== */
const excelStuMsg = ref('')
const excelStuOk = ref(false)
const loadingExcelStu = reactive({excelStu:false})

function downloadStudentTemplate() {
  const wb = XLSX.utils.book_new()
  const data = [['姓名'], ['张三'], ['李四'], ['王芳']]
  const ws = XLSX.utils.aoa_to_sheet(data)
  XLSX.utils.book_append_sheet(wb, ws, '学生名单')
  XLSX.writeFile(wb, '学生导入模板.xlsx')
}

async function importStudentExcel(e) {
  const file = e.target.files?.[0]
  if (!file) return
  loadingExcelStu.excelStu = true; excelStuMsg.value = ''
  try {
    const data = await file.arrayBuffer()
    const wb = XLSX.read(data)
    const ws = wb.Sheets[wb.SheetNames[0]]
    const rows = XLSX.utils.sheet_to_json(ws, {header: 1})
    // 找有数据的列：取第一列（姓名）
    const names = rows.map(r => (r[0]||'').toString().trim()).filter(Boolean)
    if (names.length === 0) {
      excelStuMsg.value = '❌ 未找到学生姓名数据，请确保第一列是姓名'
      excelStuOk.value = false
      loadingExcelStu.excelStu = false
      return
    }
    // 自动跳过表头：检测第一行是否像表头
    const first = names[0]
    const isHeader = /^(姓名|name|学生|学生姓名|学生名|username|display_name)$/i.test(first)
    const finalNames = isHeader ? names.slice(1) : names
    const r = await authPost('/api/teacher/students/batch', {names: finalNames})
    excelStuMsg.value = '✅ 成功导入 ' + r.ok + ' 人' + (r.fail ? '，' + r.fail + ' 人失败' : '')
    excelStuOk.value = true
    await loadStudents();
  } catch(e) {
    excelStuMsg.value = '❌ 导入失败：' + (e.message||'未知错误')
    excelStuOk.value = false
  }
  loadingExcelStu.excelStu = false
  e.target.value = ''
}

async function delStudent(id) {
  if (!confirm('确定删除该学生？')) return
  try {
    const r = await fetch(API_BASE + '/api/teacher/students/' + id, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (r.ok) {
      students.value = students.value.filter(s => s.id !== id)
      delete solvedCounts.value[id]
    } else {
      alert('删除失败')
    }
  } catch (e) {
    alert('删除出错：' + e.message)
  }
}

/* ====== 学生详情 ====== */
const selectedStudent = ref(null)
const stuQuestions = ref([])
const qOpenTeacher = ref(null)
const stuWrong = ref([])
const wOpenTeacher = ref(null)
const solvedCounts = ref({})

async function selectStudent(s) {
  selectedStudent.value = s
  const dw = await authGet('/api/teacher/student-wrong?student_id='+s.id)
  stuWrong.value = Array.isArray(dw) ? dw : []
}
async function genStuReport(s) {
}

function renderMd(t) {
  if (!t) return ''
  let html = t
  // Block math: $$...$$
  html = html.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
    try { return '<div class="katex-block">' + katex.renderToString(tex.trim(), {displayMode:true,throwOnError:false}) + '</div>' }
    catch { return '$$' + tex + '$$' }
  })
  // Inline math: $...$
  html = html.replace(/\$([^$]+?)\$/g, (_, tex) => {
    try { return katex.renderToString(tex.trim(), {displayMode:false,throwOnError:false}) }
    catch { return '$' + tex + '$' }
  })
  return marked(html)
}

/* 统计每个学生做题数 */
async function loadSolvedCounts() {
  try {
    const d = await authGet('/api/teacher/students/solved-counts')
    solvedCounts.value = d || {}
  } catch {}
}

/* ====== 风险学生 ====== */
const atRiskStudents = ref([])
async function loadAtRisk() {
  const d = await authGet('/api/teacher/at-risk')
  atRiskStudents.value = Array.isArray(d) ? d : []
}
async function unblockStudent(id) {
  if (!confirm('确认该学生风险已解除？将恢复树洞使用权限。')) return
  await authPost('/api/teacher/unblock/'+id, {})
  loadAtRisk()
  loadStudents()
  alert('✅ 已解除风险，该学生可继续使用树洞')
}

/* ====== 成绩管理 ====== */
const scoreBatch = ref('')
const loadingScore = reactive({score:false})
const scoreResult = ref(null)
const scoreStats = ref(null)
const allScores = ref([])
const examFilter = ref('')
const examList = ref([])

async function importScores() {
  loadingScore.score = true
  const scores = lines.map(l => {
    const parts = l.split(',').map(s=>s.trim())
    return { name: parts[0], subject: parts[1]||'数学', score: parseFloat(parts[2])||0, exam_name: parts[3]||'日常测验' }
  })
}

/* ====== Excel 导入成绩 ====== */
const excelScoreMsg = ref('')
const excelScoreOk = ref(false)

function downloadScoreTemplate() {
  // 设列宽
}

async function importScoreExcel(e) {
  const file = e.target.files?.[0]
  if (!file) return
  excelScoreMsg.value = ''
  try {
    const data = await file.arrayBuffer()
    const wb = XLSX.read(data)
    const ws = wb.Sheets[wb.SheetNames[0]]
    const rows = XLSX.utils.sheet_to_json(ws, {header: 1})
    // 找表头行
    let headerRow = 0
    for (let i = 0; i < Math.min(3, rows.length); i++) {
      const row = (rows[i]||[]).map(c => (c||'').toString().toLowerCase().trim())
      if (row.some(c => /^(姓名|name|学生|学生姓名|学号)$/i.test(c))) {
        headerRow = i
        break
      }
    }
    // 确定各列索引
    const headers = (rows[headerRow]||[]).map(c => (c||'').toString().toLowerCase().trim())
    const nameIdx = headers.findIndex(h => /^(姓名|name|学生|学生姓名|学生名|username)$/.test(h))
    const subjIdx = headers.findIndex(h => /^(科目|subject|学科|课程)$/.test(h))
    const scoreIdx = headers.findIndex(h => /^(分数|score|成绩|得分|grade)$/.test(h))
    const examIdx = headers.findIndex(h => /^(考试名称|考试|exam|exam_name|测验|测试)$/.test(h))
    
    if (nameIdx === -1 || scoreIdx === -1) {
      excelScoreMsg.value = '❌ 需要至少包含「姓名」和「分数」两列'
      excelScoreOk.value = false
      e.target.value = ''
      return
    }
    
    const scores = []
    for (let i = headerRow + 1; i < rows.length; i++) {
      const row = rows[i] || []
      const name = (row[nameIdx]||'').toString().trim()
      const score = parseFloat(row[scoreIdx])
      if (!name || isNaN(score)) continue
      scores.push({
        name,
        subject: subjIdx >= 0 ? (row[subjIdx]||'').toString().trim() : '数学',
        score,
        exam_name: examIdx >= 0 ? (row[examIdx]||'').toString().trim() : '日常测验'
      })
    }
    
    if (scores.length === 0) {
      excelScoreMsg.value = '❌ 未找到有效的成绩数据'
      excelScoreOk.value = false
      e.target.value = ''
      return
    }
    
    const r = await authPost('/api/teacher/scores', {scores})
    excelScoreMsg.value = '✅ 成功导入 ' + r.ok + ' 条成绩'
    excelScoreOk.value = true
    loadScoreStats()
  } catch(e) {
    excelScoreMsg.value = '❌ 导入失败：' + (e.message||'未知错误')
    excelScoreOk.value = false
  }
  e.target.value = ''
}

async function loadScoreStats() {
  const d = await authGet('/api/teacher/scores/stats?exam='+encodeURIComponent(examFilter.value))
  scoreStats.value = d
  allScores.value = d.list || []
}

/* ====== 数据导出 ====== */
function exportStudentsExcel() {
  const wb = XLSX.utils.book_new()
  const data = [['序号','用户名','姓名','密码','创建时间']].concat(
    students.value.map((s,i) => [i+1, s.username, s.display_name||'', '123456', s.created_at?.slice(0,10)||''])
  )
  const ws = XLSX.utils.aoa_to_sheet(data)
  XLSX.utils.book_append_sheet(wb, ws, '学生账号')
  XLSX.writeFile(wb, '学生账号.xlsx')
}

function exportScoresExcel() {
  const wb = XLSX.utils.book_new()
  const data = [['序号','姓名','科目','分数','等级','考试名称','日期']]
  allScores.value.forEach((s,i) => {
    data.push([i+1, s.display_name||s.username, s.subject, s.score, s.grade, s.exam_name||'', s.date||''])
  })
  const ws = XLSX.utils.aoa_to_sheet(data)
  XLSX.utils.book_append_sheet(wb, ws, '成绩')
  XLSX.writeFile(wb, '成绩数据.xlsx')
}

function exportPointsExcel() {
  const wb = XLSX.utils.book_new()
  const data = [['排名','姓名','积分']]
  ptStudents.value.forEach((s,i) => {
    data.push([i+1, s.display_name||s.username, s.total||0])
  })
  const ws = XLSX.utils.aoa_to_sheet(data)
  XLSX.utils.book_append_sheet(wb, ws, '积分排行')
  XLSX.writeFile(wb, '积分排行.xlsx')
}

function gradeTag(g) {
  return {'A':'tag-green','B':'tag-blue','C':'tag-orange','D':'tag-red','E':'tag-red'}[g]||'tag-blue'
}

/* ====== 智能出卷 ====== */
const examSubject = ref('数学')
const examTopics = ref('')
const examDifficulty = ref('中等')
const examCount = ref(10)
const examResult = ref('')
const loadingExam = reactive({exam:false})
async function genExam() {
  loadingExam.exam = true
  const d = await authPost('/api/teacher/exam/generate', {
    subject: examSubject.value,
    topics: examTopics.value,
    difficulty: examDifficulty.value,
    count: parseInt(examCount.value) || 10
  })
  examResult.value = d.exam || '生成失败'
  loadingExam.exam = false
}

/* ====== 学生留言 ====== */
/* ====== 系统设置 ====== */
const newApiKey = ref('')
const apiKeyStatus = ref(false)
const loadingKey = reactive({apiKey:false})
const apiKeyMsg = ref('')
const apiKeyOk = ref(false)

async function loadApiKeyStatus() {
  try {
    const d = await authGet('/api/teacher/config/key')
    apiKeyStatus.value = d.configured
  } catch {}
}
async function updateApiKey() {
  loadingKey.apiKey = true; apiKeyMsg.value = ''
  try {
    const d = await authPost('/api/teacher/config/key', { api_key: newApiKey.value.trim() })
    if (d.ok) {
      apiKeyOk.value = true
      apiKeyMsg.value = '✅ API Key 已更新成功！'
      newApiKey.value = ''
      apiKeyStatus.value = true
    } else {
      apiKeyOk.value = false
      apiKeyMsg.value = '❌ ' + (d.error||'更新失败')
    }
  } catch(e) {
    apiKeyOk.value = false
    apiKeyMsg.value = '❌ 请求失败：'+e.message
  }
  loadingKey.apiKey = false
}

const newTeacher = reactive({user:'', pass:'', name:''})
const loadingTeacher = reactive({createTeacher:false})
const teacherMsg = ref('')
const teacherMsgOk = ref(false)
const teachersList = ref([])

async function loadTeachers() {
  const d = await authGet('/api/teacher/teachers')
  teachersList.value = Array.isArray(d) ? d : []
}

const tPwForm = reactive({old:'', new1:'', new2:''})
const tPwMsg = ref('')
const tPwOk = ref(false)
const tCanPw = computed(() => tPwForm.old && tPwForm.new1 && tPwForm.new2 && tPwForm.new1 === tPwForm.new2 && tPwForm.new1.length >= 4)

async function doTeacherPw() {
  if (!tCanPw.value) return
  loading.value.tPw = true; tPwMsg.value = ''
  try {
    const d = await authPost('/api/auth/change-password', { old_password: tPwForm.old, new_password: tPwForm.new1 })
    if (d.ok) {
      tPwOk.value = true; tPwMsg.value = '✅ 密码修改成功！'
      tPwForm.old = ''; tPwForm.new1 = ''; tPwForm.new2 = ''
    } else {
      tPwOk.value = false; tPwMsg.value = '❌ ' + (d.error||'修改失败')
    }
  } catch(e) {
    tPwOk.value = false; tPwMsg.value = '❌ 请求失败：'+e.message
  }
  loading.value.tPw = false
}

async function createTeacher() {
  loadingTeacher.createTeacher = true; teacherMsg.value = ''
  try {
    const d = await authPost('/api/teacher/teachers', {
      username: newTeacher.user.trim(),
      password: newTeacher.pass,
      display_name: newTeacher.name.trim() || newTeacher.user.trim()
    })
    if (d.ok) {
      teacherMsgOk.value = true
      teacherMsg.value = '✅ ' + (d.message||'创建成功')
      newTeacher.user = ''; newTeacher.pass = ''; newTeacher.name = ''
      loadTeachers()
    } else {
      teacherMsgOk.value = false
      teacherMsg.value = '❌ ' + (d.error||'创建失败')
    }
  } catch(e) {
    teacherMsgOk.value = false
    teacherMsg.value = '❌ 请求失败：'+e.message
  }
  loadingTeacher.createTeacher = false
}

/* ====== 积分管理 ====== */
const ptStudents = ref([])
const ptDetail = ref([])
const adjustStudent = ref(null)
const historyStudent = ref(null)
const adjPoints = ref(10)
const adjReason = ref('')
const adjusting = ref(false)
const adjMsg = ref('')

async function loadPtStudents() {
  const d = await authGet('/api/teacher/points')
  ptStudents.value = Array.isArray(d) ? d : []
}
function openAdjust(s, pts) {
  adjustStudent.value = s
  adjPoints.value = pts
  adjReason.value = ''
  adjMsg.value = ''
}
async function doAdjust() {
  if (!adjReason.value.trim() || !adjustStudent.value) return
  adjusting.value = true; adjMsg.value = ''
  try {
    const d = await authPost('/api/teacher/points/adjust', {
      student_id: adjustStudent.value.id,
      points: adjPoints.value,
      reason: adjReason.value.trim()
    })
    if (d.ok) {
      adjMsg.value = '✅ 操作成功'
      loadPtStudents()
    } else {
      adjMsg.value = '❌ ' + (d.error||'操作失败')
    }
  } catch(e) { adjMsg.value = '❌ 请求失败：'+e.message }
  adjusting.value = false
}

/* ====== 兑换管理 ====== */
const newReward = reactive({name:'', cost:10, stock:-1})
const loadingRw = reactive({rw:false})
const rwMsg = ref('')
const rwMsgOk = ref(false)
const rewardList = ref([])
const redemptions = ref([])

async function loadRewards() {
  const d = await authGet('/api/teacher/rewards')
  rewardList.value = Array.isArray(d) ? d : []
}
async function loadRedemptions() {
  const d = await authGet('/api/teacher/redemptions')
  redemptions.value = Array.isArray(d) ? d : []
}
async function addReward() {
  loadingRw.rw = true; rwMsg.value = ''
  try {
    const d = await authPost('/api/teacher/rewards', {
      name: newReward.name.trim(),
      cost: newReward.cost,
      stock: newReward.stock
    })
    if (d.ok) {
      rwMsgOk.value = true; rwMsg.value = '✅ ' + (d.message||'添加成功')
      newReward.name = ''; newReward.cost = 10; newReward.stock = -1
      loadRewards()
    } else {
      rwMsgOk.value = false; rwMsg.value = '❌ ' + (d.error||'添加失败')
    }
  } catch(e) {
    rwMsgOk.value = false; rwMsg.value = '❌ 请求失败：'+e.message
  }
  loadingRw.rw = false
}
async function toggleReward(r) {
  await authPost('/api/teacher/rewards/'+r.id+'/toggle', {})
  loadRewards()
}
async function delReward(id) {
  if (!confirm('确定删除该兑换项？')) return
  await fetch(API_BASE+'/api/teacher/rewards/'+id, {method:'DELETE', headers:authHeaders()})
  loadRewards()
}
async function confirmRedeem(id) {
  const d = await authPost('/api/teacher/redemptions/'+id+'/confirm', {})
  if (d.ok) loadRedemptions()
}

/* ====== 批量操作 ====== */
const selectedStuIds = ref([])
const selectAllStu = ref(false)

function toggleAllStu() {
  if (selectAllStu.value) {
    selectedStuIds.value = students.value.map(s => s.id)
  } else {
    selectedStuIds.value = []
  }
}
// Watch for students list changes to update select all
watch(() => students.value.length, () => {
  if (students.value.length === selectedStuIds.value.length && students.value.length > 0) {
    selectAllStu.value = true
  } else {
    selectAllStu.value = false
  }
})

async function batchDeleteStu() {
  if (selectedStuIds.value.length === 0) return
  if (!confirm(`确定删除选中的 ${selectedStuIds.value.length} 名学生？所有相关数据将一并删除。`)) return
  let ok = 0, fail = 0
  for (const id of selectedStuIds.value) {
    try {
      const d = await authPost('/api/teacher/students/batch-delete', { ids: [id] })
      if (d && d.ok) ok++; else fail++
    } catch { fail++ }
  }
  selectedStuIds.value = []
  loadStudents()
  loadPtStudents()
  alert(`✅ 删除 ${ok} 人${fail ? '，失败 '+fail+' 人' : ''}`)
}

async function resetStuPw(s) {
  const newPw = prompt(`重置 ${s.display_name||s.username} 的密码为：`, '123456')
  if (!newPw || newPw.length < 4) { alert('密码至少4位'); return }
  const d = await authPost('/api/teacher/students/reset-pw', { student_id: s.id, new_password: newPw })
  if (d && d.ok) {
    alert(`✅ 密码已重置为：${newPw}`)
  } else {
    alert('❌ ' + ((d&&d.error)||'重置失败'))
  }
}


  const teacherMsgs = ref([])
const replyTexts = ref({})
async function loadMsgs() {
  const d = await authGet('/api/teacher/messages')
  teacherMsgs.value = Array.isArray(d) ? d : []
}
async function replyMsg(mid) {
  const d = await authPost('/api/teacher/messages/reply', {
    message_id: mid,
    reply: replyTexts.value[mid]?.trim()
  })
  if (d.ok) { replyTexts.value[mid]=''; loadMsgs() }
}

/* ====== 预警轮询 ====== */
const alertBanner = ref('')

async function logout() {
  localStorage.removeItem('kp_teacher_token')
  window.location.href = '/login'
}

let alertTimer = null
async function pollAlerts() {
  try {
    const d = await authGet('/api/teacher/alerts/pending')
    if (Array.isArray(d) && d.length > 0) {
      alertBanner.value = d.length
    } else {
      alertBanner.value = ''
    }
  } catch {}
  alertTimer = setTimeout(pollAlerts, 30000)
}

/* ====== 初始化 ====== */
onMounted(() => {
  loadStudents()
  loadStats(7)
  loadAtRisk()
  loadScoreStats()
  loadMsgs()
  pollAlerts()
  loadApiKeyStatus()
  loadTeachers()
  loadPtStudents()
  loadRewards()
  loadRedemptions()
})
</script>