<template>
  <div class="student-app">
    <!-- Header -->
    <div class="app-header">
      <div class="net-top">
      <NetworkStatus />
      <button class="btn btn-sm btn-ghost settings-btn" @click="showSettings=true" title="设置">⚙️</button>
      <button class="btn btn-sm btn-ghost settings-btn" @click="logout" title="退出登录" style="margin-left:4px">🚪</button>
    </div>
      <h1>🧑‍🎓 学习小天地</h1>
      <p class="sub">不懂就问，天天向上！</p>
      <div class="points-bar">
        <span class="points-num">⭐ {{ serverPoints }}</span>
        <span style="font-size:12px;color:var(--c-tag)">积分</span>
      </div>
    </div>

    <!-- Content -->
    <div class="content">

      <!-- ===== 拍题 ===== -->
      <div v-show="tab==='solve'">
        <div class="card">
          <div class="card-header"><span class="icon">📷</span><h3>拍题答疑</h3></div>
          <p class="card-desc">拍照上传题目，AI一步步讲给你听</p>
          <div class="upload-area" @click="$refs.fi.click()">
            <div class="upload-icon">📸</div>
            <div class="upload-text">点击拍照或选择图片</div>
            <div class="upload-hint">支持 jpg / png</div>
          </div>
          <input ref="fi" type="file" accept="image/*" capture="environment" hidden @change="onFile" />
          <img v-if="preview" :src="preview" class="preview-img" />
          <button class="btn btn-primary btn-block mt-2" :disabled="!file||loading.solve" @click="doSolve">
            <span v-if="loading.solve" class="spinner"></span>{{ loading.solve?'AI讲解中…':'开始解答 ✨' }}
          </button>
        </div>
        <div v-if="solveResult" class="card">
          <div class="card-header"><span class="icon">💡</span><h3>AI讲解</h3></div>
          <div class="md" v-html="rendered"></div>
          <div class="action-row">
            <button class="btn btn-sm btn-secondary" :disabled="wrongAdded" @click="addWrong">{{ wrongAdded?'已加入':'📚 加入错题本 +10' }}</button>
          </div>
        </div>
      </div>

      <!-- ===== 错题本 ===== -->
      <div v-show="tab==='wrong'">
        <div class="card">
          <div class="card-header"><span class="icon">📸</span><h3>上传错题</h3></div>
          <div class="upload-area" @click="$refs.wrongFile.click()">
            <div v-if="wrongPreview" class="preview-wrap">
              <img :src="wrongPreview" class="preview-img" />
            </div>
            <div v-else>
              <div class="upload-icon">📷</div>
              <div class="upload-text">拍照或选择错题图片</div>
            </div>
          </div>
          <input ref="wrongFile" type="file" accept="image/*" capture="environment" hidden @change="onWrongFile" />
          <div class="form-group" style="margin-top:8px">
            <select v-model="wrongSubject" style="margin-bottom:8px">
              <option>数学</option><option>语文</option><option>英语</option>
            </select>
            <input v-model="wrongNote" placeholder="备注（选填）" />
          </div>
          <button class="btn btn-primary btn-block" :disabled="!wrongFileSelected||loading.wrongUpload" @click="uploadWrong">
            {{ loading.wrongUpload?'上传中…':'上传错题 📤' }}
          </button>
        </div>

        <div style="display:flex;gap:8px;margin-bottom:12px">
          <button v-for="s in ['全部','数学','语文','英语']" :key="s"
            class="btn btn-sm" :class="wFilter===s?'btn-primary':'btn-outline'" @click="wFilter=s">{{ s }}</button>
        </div>
        <div v-if="filteredWrong.length===0" class="empty">
          <div class="emoji">🎉</div>
          <p>还没有错题，继续保持！</p>
        </div>
        <div v-for="(w,i) in filteredWrong" :key="w.id" class="wrong-item" @click="wOpen=i">
          <p class="wrong-q">{{ (w.question||w.q||'').slice(0,60) }}{{ (w.question||w.q||'').length>60?'…':'' }}</p>
          <div class="wrong-meta"><span>{{ w.subject||w.sub }}</span>·<span>{{ w.date }}</span></div>
          <div v-if="wOpen===i" class="wrong-detail">
            <div v-if="w.image_path" style="margin-bottom:10px">
              <img :src="w.image_path" style="max-width:100%;border-radius:8px" />
            </div>
            <div v-if="w.question" class="md" v-html="renderMd(w.question)"></div>
            <div v-if="w.explanation||w.expl" class="md" style="margin-top:10px;padding-top:10px;border-top:1px solid #eee" v-html="renderMd(w.explanation||w.expl||'')"></div>
            <div v-if="!w.question&&!w.explanation&&!w.expl" class="md" style="color:#999">暂无内容</div>
            <div class="action-row">
              <button class="btn btn-sm btn-ghost" @click.stop="delWrong(w.id)">🗑️ 删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 语音 ===== -->
      <div v-show="tab==='voice'">
        <div class="card">
          <div class="card-header"><span class="icon">🎤</span><h3>语音问答</h3></div>
          <p class="card-desc">按住说话提问，或打字也行</p>
          <div class="mic-area">
            <button class="mic-btn" :class="{recording:rec}" @mousedown="startRec" @mouseup="stopRec" @touchstart.prevent="startRec" @touchend="stopRec">🎙️</button>
            <p class="mic-hint">{{ rec ? '松开停止录音' : (voiceText || '点击麦克风说话') }}</p>
          </div>
          <div class="form-group"><input v-model="voiceText" placeholder="或手动输入问题…" /></div>
          <button class="btn btn-primary btn-block" :disabled="!voiceText.trim()||loading.voice" @click="askVoice">
            <span v-if="loading.voice" class="spinner"></span>{{ loading.voice?'思考中…':'提问 💬' }}
          </button>
        </div>
        <div v-if="voiceAnswer" class="card">
          <div class="card-header"><span class="icon">🤖</span><h3>回答</h3></div>
          <div class="chat-box">
            <div class="chat-msg ai"><div class="chat-bubble">{{ voiceAnswer }}</div></div>
          </div>
          <button class="btn btn-sm btn-outline mt-2" @click="speak(voiceAnswer)">🔊 朗读</button>
        </div>
      </div>

      <!-- ===== 树洞 ===== -->
      <div v-show="tab==='mood'">
        <div class="card">
          <div class="card-header"><span class="icon">💬</span><h3>心情树洞</h3></div>
          <p class="card-desc">今天心情怎么样？跟我说说吧～</p>
          <div class="mood-grid">
            <button v-for="m in moods" :key="m.key" class="mood-btn" :class="{active:selMood===m.key}" @click="selMood=m.key">{{ m.emoji }}</button>
          </div>
          <div class="form-group"><input v-model="moodMsg" placeholder="想说什么都可以…" @keyup.enter="doChat" /></div>
          <button class="btn btn-primary btn-block" :disabled="!moodMsg.trim()||loading.mood" @click="doChat">
            <span v-if="loading.mood" class="spinner"></span>{{ loading.mood?'想想怎么回…':'发送 💌' }}
          </button>
        </div>
        <div v-if="chats.length" class="card">
          <div class="card-header"><span class="icon">📝</span><h3>对话</h3></div>
          <div class="chat-box">
            <div v-for="(c,i) in chats" :key="i" class="chat-msg" :class="c.role">
              <div class="chat-bubble">{{ c.text }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 成绩 ===== -->
      <div v-show="tab==='scores'">
        <div class="card">
          <div class="card-header"><span class="icon">📊</span><h3>我的成绩</h3></div>
          <p class="card-desc">成绩等级说明：A(90+) B(80+) C(70+) D(60+) E(不及格)</p>
          <div v-if="myScores.length===0" class="empty"><div class="emoji">📝</div><p>暂无成绩</p></div>
          <div v-for="s in myScores" :key="s.id" class="wrong-item">
            <div class="flex">
              <strong>{{ s.subject }}</strong>
              <span class="tag" :class="gradeTag(s.grade)" style="font-size:18px;padding:4px 16px">{{ s.grade }}</span>
            </div>
            <p class="wrong-meta">{{ s.exam_name }} · {{ s.date }} · {{ s.term||'-' }}</p>
          </div>
        </div>
        <div v-if="scoreChart.length" class="card">
          <div class="card-header"><span class="icon">📈</span><h3>成绩趋势</h3></div>
          <div v-for="c in scoreChart" :key="c.date+'_'+c.subject" class="flex" style="margin:8px 0">
            <span class="tag" :class="gradeTag(c.grade)" style="font-size:14px">{{ c.grade }}</span>
            <span style="font-size:13px">{{ c.exam_name }} · {{ c.subject }}</span>
            <span class="muted" style="font-size:12px">{{ c.date }}</span>
          </div>
        </div>
      </div>

      <!-- ===== 积分 ===== -->
      <div v-show="tab==='points'">
        <div class="card" style="text-align:center">
          <div class="points-num" style="font-size:48px">⭐ {{ serverPoints }}</div>
          <p class="card-desc">当前积分</p>
          <div class="flex" style="gap:8px;justify-content:center;margin-top:8px">
            <button class="btn btn-sm" :class="ptSubTab==='rewards'?'btn-primary':'btn-outline'" @click="ptSubTab='rewards'">🎁 兑换</button>
            <button class="btn btn-sm" :class="ptSubTab==='history'?'btn-primary':'btn-outline'" @click="ptSubTab='history'">📋 明细</button>
            <button class="btn btn-sm" :class="ptSubTab==='rank'?'btn-primary':'btn-outline'" @click="ptSubTab='rank'">🏆 排行</button>
          </div>
        </div>

        <!-- 兑换 -->
        <div v-if="ptSubTab==='rewards'">
          <div v-if="rewardsList.length===0" class="card">
            <div class="empty"><div class="emoji">🎁</div><p>暂无兑换项目</p></div>
          </div>
          <div v-for="r in rewardsList" :key="r.id" class="card">
            <div class="card-header" style="justify-content:space-between">
              <h3>🎁 {{ r.name }}</h3>
              <span class="tag tag-orange" style="font-size:16px">⭐ {{ r.cost }}</span>
            </div>
            <p class="muted" style="font-size:12px">{{ r.stock===-1?'不限量':('剩余 '+r.stock+' 个') }}</p>
            <button class="btn btn-primary btn-block mt-2" :disabled="redeeming===r.id" @click="doRedeem(r)">
              {{ redeeming===r.id?'兑换中…':'兑换 ⭐' }}
            </button>
          </div>
        </div>

        <!-- 明细 -->
        <div v-if="ptSubTab==='history'">
          <div class="card">
            <div class="card-header"><h3>📋 积分明细</h3></div>
            <div v-if="ptHistory.length===0" class="empty"><div class="emoji">📝</div><p>暂无记录</p></div>
            <div v-for="h in ptHistory" :key="h.id || h.created_at" class="student-row" style="flex-wrap:wrap">
              <div>
                <span :style="{color: h.points>0?'var(--c-green)':'var(--c-red)', fontWeight:600}">{{ h.points>0?'+':'' }}{{ h.points }}</span>
                <span class="muted" style="margin-left:8px;font-size:13px">{{ h.reason }}</span>
              </div>
              <span class="muted" style="font-size:12px">{{ h.created_at }}</span>
            </div>
          </div>
        </div>

        <!-- 排行榜 -->
        <div v-if="ptSubTab==='rank'">
          <div class="card" v-for="(s,i) in leaderboard" :key="s.id">
            <div class="student-row">
              <div class="flex" style="gap:8px;align-items:center">
                <span style="font-size:20px">{{ ['🥇','🥈','🥉',''][i] || '#'+(i+1) }}</span>
                <strong>{{ s.display_name||s.username }}</strong>
              </div>
              <span class="tag" :class="i<3?'tag-orange':'tag-blue'" style="font-size:15px">⭐ {{ s.total||0 }}</span>
            </div>
          </div>
          <div v-if="leaderboard.length===0" class="card">
            <div class="empty"><div class="emoji">🏆</div><p>暂无排名数据</p></div>
          </div>
        </div>
      </div>

      <!-- ===== 留言 ===== -->
      <div v-show="tab==='msgs'">
        <div class="card">
          <div class="card-header"><span class="icon">✉️</span><h3>给老师留言</h3></div>
          <div class="form-group">
            <textarea v-model="msgContent" rows="3" placeholder="有问题想问老师？作业不会做？写在这里吧～"></textarea>
          </div>
          <button class="btn btn-primary" :disabled="!msgContent.trim()||loading.msg" @click="sendMsg" style="width:100%">
            {{ loading.msg?'发送中…':'发送留言 💌' }}
          </button>
        </div>
        <div class="card">
          <div class="card-header"><span class="icon">📋</span><h3>我的留言</h3></div>
          <div v-if="myMsgs.length===0" class="empty"><div class="emoji">💬</div><p>还没有留言</p></div>
          <div v-for="m in myMsgs" :key="m.id" class="wrong-item">
            <p style="font-weight:500">{{ m.content }}</p>
            <p class="wrong-meta">{{ m.date }}</p>
            <div v-if="m.reply" class="result-section" style="margin-top:8px;border-left-color:var(--c-green)">
              <p style="font-size:13px;color:var(--c-green)"><strong>✅ 老师回复：</strong>{{ m.reply }}</p>
            </div>
            <div v-else class="muted" style="margin-top:8px;font-size:12px">⏳ 等待老师回复…</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Nav -->
    <nav class="bottom-nav">
      <button v-for="t in tabs" :key="t.key" class="nav-tab" :class="{active:tab===t.key}" @click="tab=t.key">
        <span class="nav-icon">{{ t.icon }}</span>
        {{ t.label }}
      </button>
    </nav>

    <!-- 设置弹窗 -->
    <div v-if="showSettings" class="modal-overlay" @click.self="showSettings=false">
      <div class="modal-content" @click.stop>
        <h3 style="margin-bottom:16px">⚙️ 设置</h3>
        <div class="card" style="box-shadow:none;padding:0">
          <h4 style="margin-bottom:8px">🔐 修改密码</h4>
          <div class="form-group">
            <label class="form-label">当前密码</label>
            <input v-model="pwForm.old" type="password" placeholder="输入当前密码" />
          </div>
          <div class="form-group">
            <label class="form-label">新密码</label>
            <input v-model="pwForm.new1" type="password" placeholder="至少4位" />
          </div>
          <div class="form-group">
            <label class="form-label">确认新密码</label>
            <input v-model="pwForm.new2" type="password" placeholder="再次输入新密码" />
          </div>
          <button class="btn btn-primary btn-block" :disabled="!canChangePw||loading.pw" @click="changePw">
            {{ loading.pw?'修改中…':'修改密码 🔐' }}
          </button>
          <p v-if="pwMsg" class="mt-2" style="font-size:13px" :class="pwOk?'success-text':'error-text'">{{ pwMsg }}</p>
        </div>
        <button class="btn btn-sm btn-ghost mt-2" @click="showSettings=false" style="width:100%;text-align:center">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import { compressImage } from '../utils/compress.js'
import NetworkStatus from '../components/NetworkStatus.vue'
import { API_BASE } from '../config.js'

function stuHeaders() {
  const t = localStorage.getItem('kp_student_token')
  return t ? { 'Authorization': 'Bearer ' + t } : {}
}

const tabs = [
  {key:'solve', icon:'📷', label:'拍题'},
  {key:'wrong', icon:'📚', label:'错题'},
  {key:'voice', icon:'🎤', label:'语音'},
  {key:'mood', icon:'💬', label:'树洞'},
  {key:'scores', icon:'📊', label:'成绩'},
  {key:'points', icon:'⭐', label:'积分'},
  {key:'msgs', icon:'✉️', label:'留言'},
]
const tab = ref('solve')
const loading = ref({})

/* ===== 设置/修改密码 ===== */
const showSettings = ref(false)

async function logout() {
  localStorage.removeItem('kp_student_token')
  localStorage.removeItem('kp_student_name')
  window.location.href = '/login'
}

const pwForm = reactive({old:'', new1:'', new2:''})
const pwMsg = ref('')
const pwOk = ref(false)
const loadingPw = reactive({pw:false})

const canChangePw = computed(() => pwForm.old && pwForm.new1 && pwForm.new2 && pwForm.new1 === pwForm.new2 && pwForm.new1.length >= 4)

async function changePw() {
  if (!canChangePw.value) return
  loadingPw.pw = true; pwMsg.value = ''
  try {
    const r = await fetch(API_BASE+'/api/auth/change-password', {
      method:'POST',
      headers: {...stuHeaders(), 'Content-Type':'application/json'},
      body: JSON.stringify({ old_password: pwForm.old, new_password: pwForm.new1 })
    })
    const d = await r.json()
    if (d.ok) {
      pwOk.value = true
      pwMsg.value = '✅ 密码修改成功！下次登录请用新密码'
      pwForm.old = ''; pwForm.new1 = ''; pwForm.new2 = ''
    } else {
      pwOk.value = false
      pwMsg.value = '❌ ' + (d.error||'修改失败')
    }
  } catch(e) {
    pwOk.value = false
    pwMsg.value = '❌ 请求失败：'+e.message
  }
  loadingPw.pw = false
}

/* ===== 积分 ===== */
const serverPoints = ref(0)
const ptSubTab = ref('rewards')
const rewardsList = ref([])
const redeeming = ref(null)
const ptHistory = ref([])
const leaderboard = ref([])

async function loadMyPoints() {
  try {
    const r = await fetch(API_BASE+'/api/student/points', {headers:stuHeaders()})
    const d = await r.json()
    serverPoints.value = d.total||0
    // 同步到本地存储，保持一致性
  } catch {}
}
async function loadRewards() {
  const r = await fetch(API_BASE+'/api/student/rewards', {headers:stuHeaders()})
  const d = await r.json(); rewardsList.value = Array.isArray(d) ? d : []
}
async function loadPtHistory() {
  const r = await fetch(API_BASE+'/api/student/points/history', {headers:stuHeaders()})
  const d = await r.json(); ptHistory.value = Array.isArray(d) ? d : []
}
async function loadLeaderboard() {
  const r = await fetch(API_BASE+'/api/leaderboard', {headers:stuHeaders()})
  const d = await r.json(); leaderboard.value = Array.isArray(d) ? d : []
}
async function doRedeem(r) {
  if (!confirm(`确定用 ⭐${r.cost} 兑换「${r.name}」吗？`)) return
  redeeming.value = r.id
  try {
    const rd = await fetch(API_BASE+'/api/student/redeem', {method:'POST', headers:{...stuHeaders(),'Content-Type':'application/json'}, body:JSON.stringify({reward_id:r.id})})
    const d = await rd.json()
    if (d.ok) {
      alert('✅ '+d.message)
      loadMyPoints(); loadRewards(); loadPtHistory()
    } else {
      alert('❌ '+(d.error||'兑换失败'))
    }
  } catch(e) { alert('请求失败：'+e.message) }
  redeeming.value = null
}

/* ===== 拍题 ===== */
const preview = ref('')
const file = ref(null)
const solveResult = ref('')
const rendered = ref('')
const wrongAdded = ref(false)

async function onFile(e) {
  const f = e.target.files[0]
  if (!f) return
  file.value = f
  const reader = new FileReader()
  reader.onload = ev => { preview.value = ev.target.result }
  reader.readAsDataURL(f)
  wrongAdded.value = false
}

async function doSolve() {
  if (!file.value) return
  loading.value.solve = true
  solveResult.value = ''
  rendered.value = ''
  try {
    const fd = new FormData()
    fd.append('image', file.value)
    const r = await fetch(API_BASE+'/api/student/solve', {method:'POST', headers:stuHeaders(), body:fd})
    const d = await r.json()
    if (d.ok) {
      solveResult.value = d.explanation||d.result||''
      rendered.value = marked(solveResult.value)
      loadMyPoints()
    } else {
      solveResult.value = d.error||'解答失败'
      rendered.value = solveResult.value
    }
  } catch(e) {
    solveResult.value = '请求失败：'+e.message
    rendered.value = solveResult.value
  }
  loading.value.solve = false
}

async function addWrong() {
  try {
    const r = await fetch(API_BASE+'/api/student/wrong/add', {
      method:'POST',
      headers:{...stuHeaders(),'Content-Type':'application/json'},
      body: JSON.stringify({question: solveResult.value})
    })
    const d = await r.json()
    if (d.ok) {
      wrongAdded.value = true
      loadMyPoints()
    } else {
      alert('❌ '+(d.error||'添加失败'))
    }
  } catch(e) { alert('请求失败：'+e.message) }
}

/* ===== 错题本 ===== */
const wrongPreview = ref('')
const wrongSubject = ref('数学')
const wrongNote = ref('')
const wrongFileSelected = ref(null)
const wFilter = ref('全部')
const filteredWrong = ref([])
const wOpen = ref(-1)
let wrongList = []

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

function onWrongFile(e) {
  const f = e.target.files[0]
  if (!f) return
  wrongFileSelected.value = f
  const reader = new FileReader()
  reader.onload = ev => { wrongPreview.value = ev.target.result }
  reader.readAsDataURL(f)
}

async function uploadWrong() {
  if (!wrongFileSelected.value) return
  loading.value.wrongUpload = true
  try {
    let imageBase64 = wrongPreview.value
    const r = await fetch(API_BASE+'/api/student/wrong/upload', {
      method:'POST',
      headers:{...stuHeaders(),'Content-Type':'application/json'},
      body: JSON.stringify({
        image: imageBase64,
        subject: wrongSubject.value,
        note: wrongNote.value
      })
    })
    const d = await r.json()
    if (d.ok) {
      alert('✅ 错题上传成功！+10积分')
      wrongFileSelected.value = null
      wrongPreview.value = ''
      wrongSubject.value = '数学'
      wrongNote.value = ''
      loadWrongList()
      loadMyPoints()
    } else {
      alert('❌ '+(d.error||'上传失败'))
    }
  } catch(e) { alert('请求失败：'+e.message) }
  loading.value.wrongUpload = false
}

async function loadWrongList() {
  try {
    const r = await fetch(API_BASE+'/api/student/wrong/list', {headers:stuHeaders()})
    const d = await r.json()
    wrongList = Array.isArray(d) ? d : []
    applyWFilter()
  } catch { wrongList = []; filteredWrong.value = [] }
}

function applyWFilter() {
  if (wFilter.value === '全部') {
    filteredWrong.value = [...wrongList]
  } else {
    filteredWrong.value = wrongList.filter(w => (w.subject||w.sub) === wFilter.value)
  }
}

// 监听筛选条件变化
import { watch } from 'vue'
watch(wFilter, applyWFilter)

async function delWrong(id) {
  if (!confirm('确定删除这条错题吗？')) return
  try {
    const r = await fetch(API_BASE+'/api/student/wrong/delete', {
      method:'POST',
      headers:{...stuHeaders(),'Content-Type':'application/json'},
      body: JSON.stringify({id})
    })
    const d = await r.json()
    if (d.ok) {
      loadWrongList()
    } else {
      alert('❌ '+(d.error||'删除失败'))
    }
  } catch(e) { alert('请求失败：'+e.message) }
}

/* ===== 语音 ===== */
const rec = ref(false)
let mediaRecorder = null
let audioChunks = []
let recognition = null
const voiceText = ref('')
const voiceAnswer = ref('')

async function startRec() {
  rec.value = true
  // Try speech recognition first (voice-to-text)
  try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      recognition = new SpeechRecognition()
      recognition.lang = 'zh-CN'
      recognition.continuous = false
      recognition.interimResults = false
      recognition.onresult = function(ev) {
        voiceText.value = ev.results[0][0].transcript
        rec.value = false
      }
      recognition.onerror = function() { rec.value = false }
      recognition.start()
      return
    }
  } catch {}
  // Fallback: record audio
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true})
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data)
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop())
      const blob = new Blob(audioChunks, {type:'audio/webm'})
      const fd = new FormData()
      fd.append('audio', blob, 'voice.webm')
      try {
        loading.value.voice = true
        const r = await fetch(API_BASE+'/api/student/voice', {method:'POST', headers:stuHeaders(), body:fd})
        const d = await r.json()
        voiceAnswer.value = d.text||'未识别'
      } catch(e) { voiceAnswer.value = '请求失败：'+e.message }
      loading.value.voice = false
    }
    mediaRecorder.start()
  } catch(e) { rec.value = false }
}

function stopRec() {
  if (recognition) {
    recognition.stop()
    recognition = null
  }
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  rec.value = false
}

async function askVoice() {
  if (!voiceText.value.trim()) return
  loading.value.voice = true
  voiceAnswer.value = ''
  try {
    const r = await fetch(API_BASE+'/api/student/ask', {
      method:'POST',
      headers:{...stuHeaders(),'Content-Type':'application/json'},
      body: JSON.stringify({question: voiceText.value})
    })
    const d = await r.json()
    voiceAnswer.value = d.answer||d.text||'未获取到回答'
  } catch(e) { voiceAnswer.value = '请求失败：'+e.message }
  loading.value.voice = false
}

function speak(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'zh-CN'
    window.speechSynthesis.speak(u)
  }
}

/* ===== 树洞 ===== */
const moods = [
  {key:'happy', emoji:'😊'},
  {key:'sad', emoji:'😢'},
  {key:'angry', emoji:'😠'},
  {key:'confused', emoji:'🤔'},
  {key:'tired', emoji:'😴'},
  {key:'excited', emoji:'🎉'},
]
const selMood = ref('happy')
const moodMsg = ref('')
const chats = ref([])

async function doChat() {
  if (!moodMsg.value.trim()) return
  const userText = moodMsg.value
  moodMsg.value = ''
  chats.value.push({role:'user', text: userText})
  loading.value.mood = true
  try {
    const r = await fetch(API_BASE+'/api/student/chat', {
      method:'POST',
      headers:{...stuHeaders(),'Content-Type':'application/json'},
      body: JSON.stringify({message: userText, mood: selMood.value})
    })
    const d = await r.json()
    chats.value.push({role:'assistant', text: d.reply||d.text||'嗯嗯'})
  } catch(e) {
    chats.value.push({role:'assistant', text: '抱歉，我走神了…'})
  }
  loading.value.mood = false
}

/* ===== 成绩 ===== */
const myScores = ref([])
const scoreChart = ref([])

function gradeTag(g) {
  if (!g) return 'tag-blue'
  const m = {A:'tag-green', B:'tag-blue', C:'tag-orange', D:'tag-red', E:'tag-red'}
  return m[g.toUpperCase()] || 'tag-blue'
}

async function loadMyScores() {
  try {
    const r = await fetch(API_BASE+'/api/student/scores', {headers:stuHeaders()})
    const d = await r.json()
    myScores.value = Array.isArray(d) ? d : []
    // Build chart data
    scoreChart.value = [...myScores.value].sort((a,b) => new Date(a.date)-new Date(b.date))
  } catch { myScores.value = []; scoreChart.value = [] }
}

/* ===== 留言 ===== */
const msgContent = ref('')
const myMsgs = ref([])

async function sendMsg() {
  if (!msgContent.value.trim()) return
  loading.value.msg = true
  try {
    const r = await fetch(API_BASE+'/api/student/messages', {
      method:'POST',
      headers:{...stuHeaders(),'Content-Type':'application/json'},
      body: JSON.stringify({content: msgContent.value})
    })
    const d = await r.json()
    if (d.ok) {
      msgContent.value = ''
      loadMyMsgs()
    } else {
      alert('❌ '+(d.error||'发送失败'))
    }
  } catch(e) { alert('请求失败：'+e.message) }
  loading.value.msg = false
}

async function loadMyMsgs() {
  try {
    const r = await fetch(API_BASE+'/api/student/messages', {headers:stuHeaders()})
    const d = await r.json()
    myMsgs.value = Array.isArray(d) ? d : []
  } catch { myMsgs.value = [] }
}

/* ===== 初始化 ===== */
onMounted(() => {
  loadMyPoints()
  loadRewards()
  loadPtHistory()
  loadLeaderboard()
  loadWrongList()
  loadMyScores()
  loadMyMsgs()
})
</script>

<style scoped>
.badge-overlay { position:fixed; inset:0; background:rgba(0,0,0,.35); display:flex; align-items:center; justify-content:center; z-index:999; }
.badge-modal { background:#fff; border-radius:24px; padding:32px; text-align:center; animation:pop .3s ease; width:300px; }
.badge-big { font-size:72px; }
.badge-modal h3 { margin:8px 0 4px; font-size:20px; }
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.35); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-content { background:#fff; border-radius:16px; padding:24px; width:90%; max-width:380px; animation:pop .3s ease; }
@keyframes pop { 0%{transform:scale(.5);opacity:0} 100%{transform:scale(1);opacity:1} }
</style>
