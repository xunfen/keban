import os, json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

from api.qwen_api import (
    review_analysis, prepare_lesson, solve_question,
    emotional_chat, generate_report, generate_weekly_report,
    set_api_key, is_configured
)
from db import init_db, get_db, create_user, auth_user, set_token, resolve_token, auto_username, hash_pw

GRADE_MAP = [(90,'A'),(80,'B'),(70,'C'),(60,'D'),(0,'E')]
def to_grade(s):
    for t,g in GRADE_MAP:
        if s>=t: return g
    return 'E'

app = Flask(__name__)
CORS(app)

UPLOAD = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD, exist_ok=True)
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
ALLOWED = {'png','jpg','jpeg','gif','webp'}

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD, filename)

@app.route('/')
@app.route('/<path:filename>')
def serve_frontend(filename='index.html'):
    from flask import send_from_directory
    if filename.startswith('api/') or filename.startswith('uploads/'):
        return '', 404
    base = os.path.dirname(os.path.dirname(__file__))
    dist_dir = os.path.join(base, 'teacher-client', 'dist')
    file_path = os.path.join(dist_dir, filename)
    if os.path.isfile(file_path):
        return send_from_directory(dist_dir, filename)
    return send_from_directory(dist_dir, 'index.html')

def allowed_file(name):
    return '.' in name and name.rsplit('.',1)[1].lower() in ALLOWED

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f: return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f: json.dump(cfg, f)

def need_auth(role=None):
    auth = request.headers.get('Authorization','')
    token = auth.replace('Bearer ','') if auth.startswith('Bearer ') else auth
    user = resolve_token(token)
    if not user:
        return None, (jsonify({'error':'未登录或token已失效'}), 401)
    if role and user['role'] != role:
        return None, (jsonify({'error':'权限不足'}), 403)
    return user, None

# ============ 系统 ============
cfg = load_config()
if cfg.get('api_key'):
    set_api_key(cfg['api_key'])

@app.route('/api/teacher/config/key', methods=['POST'])
def update_api_key():
    """教师更改 API Key"""
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    key = (d.get('api_key') or '').strip()
    if not key or not key.startswith('sk-'):
        return jsonify({'error':'API Key格式不对'}),400
    set_api_key(key)
    save_config({'api_key': key})
    return jsonify({'ok':True, 'message':'API Key 已更新'})

@app.route('/api/teacher/config/key', methods=['GET'])
def get_api_key_status():
    """查看 Key 配置状态（不返回实际 key）"""
    user, err = need_auth('teacher')
    if err: return err
    cfg = load_config()
    return jsonify({
        'configured': is_configured(),
        'has_key': bool(cfg.get('api_key'))
    })

@app.route('/api/teacher/teachers', methods=['GET'])
def list_teachers():
    """列出所有教师账号"""
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT id,username,display_name,created_at FROM users WHERE role="teacher" ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/teachers', methods=['POST'])
def create_teacher():
    """创建其他教师账号"""
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    username = (d.get('username') or '').strip()
    password = (d.get('password') or '').strip()
    display = (d.get('display_name') or username).strip()
    if not username or not password:
        return jsonify({'error':'请填写用户名和密码'}),400
    if create_user(username, password, 'teacher', display):
        return jsonify({'ok':True, 'message':f'教师 {display} 创建成功'})
    return jsonify({'error':'创建失败，用户名可能已存在'}),400

@app.route('/api/auth/change-password', methods=['POST'])
def change_password():
    """任意已登录用户修改自己的密码"""
    user, err = need_auth()
    if err: return err
    d = request.get_json() or {}
    old_pw = d.get('old_password', '')
    new_pw = d.get('new_password', '').strip()
    if not old_pw or not new_pw:
        return jsonify({'error':'请填写旧密码和新密码'}),400
    if len(new_pw) < 4:
        return jsonify({'error':'新密码至少4位'}),400
    # 验证旧密码
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE id=?', (user['id'],)).fetchone()
    if not row or row['password_hash'] != hash_pw(old_pw):
        db.close()
        return jsonify({'error':'旧密码不正确'}),400
    # 更新密码
    db.execute('UPDATE users SET password_hash=?, plain_password=? WHERE id=?', (hash_pw(new_pw), new_pw, user['id']))
    db.commit(); db.close()
    return jsonify({'ok':True, 'message':'密码修改成功'})

@app.route('/api/health')
def health():
    db = get_db()
    has_teacher = db.execute('SELECT COUNT(*) FROM users WHERE role="teacher"').fetchone()[0] > 0
    db.close()
    return jsonify({
        'configured': is_configured(),
        'has_teacher': has_teacher
    })

@app.route('/api/setup/init', methods=['POST'])
def setup_init():
    """首次启动：配置API Key + 创建教师账号"""
    d = request.get_json() or {}
    key = (d.get('api_key') or '').strip()
    username = (d.get('username') or '').strip()
    password = (d.get('password') or '').strip()
    if not key or not key.startswith('sk-'):
        return jsonify({'ok':False,'error':'API Key格式不对'}),400
    if not username or not password:
        return jsonify({'ok':False,'error':'请填写教师账号和密码'}),400
    set_api_key(key)
    save_config({'api_key': key})
    if not create_user(username, password, 'teacher', '教师'):
        return jsonify({'ok':False,'error':'创建账号失败，可能已存在'}),400
    return jsonify({'ok':True})

@app.route('/api/setup/status')
def setup_status():
    """检查初始化状态"""
    return jsonify({
        'need_init': not is_configured(),
        'need_teacher': not load_config().get('teacher_created')
    })



# ============ 认证 ============
@app.route('/api/auth/login', methods=['POST'])
def login():
    d = request.get_json() or {}
    user = auth_user(d.get('username','').strip(), d.get('password',''))
    if not user:
        return jsonify({'error':'用户名或密码错误'}),401
    token = user['token']
    if not token:
        token = __import__('secrets').token_hex(32)
        set_token(user['id'], token)
    return jsonify({'token':token, 'role':user['role'], 'username':user['username'], 'display_name':user.get('display_name','')})

@app.route('/api/auth/me')
def auth_me():
    user, err = need_auth()
    if err: return err
    return jsonify({'username':user['username'],'role':user['role'],'display_name':user.get('display_name','')})

# ============ 教师端-学生管理 ============
@app.route('/api/teacher/students', methods=['GET'])
def list_students():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT id,username,display_name,created_at FROM users WHERE role="student" ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/students', methods=['POST'])
def add_student():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    username = (d.get('username') or '').strip()
    password = (d.get('password') or '').strip()
    display = (d.get('display_name') or username).strip()
    if not username or not password:
        return jsonify({'error':'请填写用户名和密码'}),400
    if create_user(username, password, 'student', display):
        return jsonify({'ok':True})
    return jsonify({'error':'创建失败，用户名可能已存在'}),400

@app.route('/api/teacher/students/<int:sid>', methods=['DELETE'])
def delete_student(sid):
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    db.execute('DELETE FROM users WHERE id=? AND role="student"', (sid,))
    db.execute('DELETE FROM points_log WHERE user_id=?', (sid,))
    db.execute('DELETE FROM scores WHERE user_id=?', (sid,))
    db.execute('DELETE FROM messages WHERE from_user_id=?', (sid,))
    db.execute('DELETE FROM questions WHERE user_id=?', (sid,))
    db.execute('DELETE FROM alerts WHERE user_id=?', (sid,))
    db.execute('DELETE FROM chat_logs WHERE user_id=?', (sid,))
    db.execute('DELETE FROM wrong_questions WHERE user_id=?', (sid,))
    db.execute('UPDATE redemptions SET status="cancelled" WHERE user_id=?', (sid,))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/teacher/students/batch', methods=['POST'])
def batch_students():
    """批量导入学生（只传姓名，系统自动生成用户名）"""
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    names = d.get('names', d.get('students', []))
    from db import auto_username
    ok, fail = 0, 0
    for entry in names:
        if isinstance(entry, str):
            name = entry
        elif isinstance(entry, dict):
            name = entry.get('name','') or entry.get('display_name','') or entry.get('username','')
        else:
            name = str(entry)
        if not name or not name.strip():
            fail += 1
            continue
        name = name.strip()
        username = auto_username(name)
        if create_user(username, '123456', 'student', name):
            ok += 1
        else:
            fail += 1
    return jsonify({'ok':ok, 'fail':fail})

# ============ 教师端-原有功能 ============
@app.route('/api/teacher/review', methods=['POST'])
def teacher_review():
    user, err = need_auth('teacher')
    if err: return err
    content = (request.get_json() or {}).get('content','').strip()
    if not content: return jsonify({'error':'请输入课堂内容'}),400
    return jsonify({'result': review_analysis(content)})

@app.route('/api/teacher/prepare', methods=['POST'])
def teacher_prepare():
    user, err = need_auth('teacher')
    if err: return err
    topic = (request.get_json() or {}).get('topic','').strip()
    if not topic: return jsonify({'error':'请输入知识点'}),400
    text = prepare_lesson(topic)
    try: return jsonify(json.loads(text))
    except: return jsonify({'result':text})

@app.route('/api/teacher/stats', methods=['GET'])
def teacher_stats():
    user, err = need_auth('teacher')
    if err: return err
    days = request.args.get('days',7,type=int)
    db = get_db()
    since = (datetime.now()-timedelta(days=days)).strftime('%Y-%m-%d')
    total = db.execute('SELECT COUNT(*) FROM questions WHERE date>=?',(since,)).fetchone()[0] or 0
    by_subj = {r['subject']:r['cnt'] for r in db.execute('SELECT subject,COUNT(*) cnt FROM questions WHERE date>=? GROUP BY subject',(since,)).fetchall()}
    daily = [{'date':r['date'],'count':r['cnt']} for r in db.execute('SELECT date,COUNT(*) cnt FROM questions WHERE date>=? GROUP BY date ORDER BY date',(since,)).fetchall()]
    weak = [{'topic':r['topic'],'count':r['cnt']} for r in db.execute('SELECT topic,COUNT(*) cnt FROM questions WHERE date>=? AND is_correct=0 AND topic!=\'\' GROUP BY topic ORDER BY cnt DESC LIMIT 5',(since,)).fetchall()]
    db.close()
    return jsonify({'total_questions':total,'by_subject':by_subj,'daily_trend':daily,'weak_topics':weak})

@app.route('/api/teacher/report', methods=['POST'])
def teacher_report():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    sid = d.get('student_id')
    student_name = ''
    if sid:
        db = get_db()
        row = db.execute('SELECT display_name,username FROM users WHERE id=? AND role="student"', (sid,)).fetchone()
        db.close()
        if row:
            student_name = row['display_name'] or row['username']
    return jsonify({'report':generate_report(json.dumps(d.get('stats',{}),ensure_ascii=False), student_name)})

@app.route('/api/teacher/weekly-report', methods=['POST'])
def teacher_weekly_report():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    return jsonify({'report':generate_weekly_report(json.dumps(d.get('stats',{}),ensure_ascii=False))})

# ============ 教师端-查看学生记录 ============
@app.route('/api/teacher/at-risk', methods=['GET'])
def at_risk_students():
    """查看被标记的风险学生"""
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('''
        SELECT u.id,u.username,u.display_name,u.blocked,
               (SELECT COUNT(*) FROM alerts WHERE user_id=u.id AND handled=0) as alert_count,
               (SELECT MAX(date) FROM alerts WHERE user_id=u.id) as last_alert
        FROM users u WHERE u.role='student' AND (u.blocked=1 OR u.id IN (SELECT user_id FROM alerts WHERE handled=0))
        ORDER BY last_alert DESC
    ''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/unblock/<int:sid>', methods=['POST'])
def unblock_student(sid):
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    db.execute('UPDATE users SET blocked=0 WHERE id=?', (sid,))
    db.execute('UPDATE alerts SET handled=1 WHERE user_id=? AND handled=0', (sid,))
    db.commit(); db.close()
    return jsonify({'ok':True})

# ============ 成绩管理 ============
@app.route('/api/teacher/scores', methods=['GET'])
def list_scores():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    sid = request.args.get('student_id', type=int)
    if sid:
        rows = db.execute('''SELECT s.*,u.display_name,u.username FROM scores s JOIN users u ON s.user_id=u.id WHERE s.user_id=? ORDER BY s.date DESC''', (sid,)).fetchall()
    else:
        rows = db.execute('''SELECT s.*,u.display_name,u.username FROM scores s JOIN users u ON s.user_id=u.id ORDER BY s.date DESC''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/scores', methods=['POST'])
def add_scores():
    """导入/添加成绩：支持单条和批量"""
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    items = d.get('scores', [d])  # 单条或批量
    ok, fail = 0, 0
    db = get_db()
    for item in items:
        sid = item.get('user_id') or item.get('student_id')
        if not sid:
            # 尝试通过姓名查找
            name = item.get('name','').strip()
            if name:
                u = db.execute('SELECT id FROM users WHERE (display_name=? OR username=?) AND role="student"', (name,name)).fetchone()
                if u: sid = u['id']
        if not sid:
            fail += 1; continue
        subject = item.get('subject','数学').strip()
        score = float(item.get('score',0))
        grade = to_grade(score)
        exam = item.get('exam_name','日常测验').strip()
        term = item.get('term','').strip()
        date = item.get('date', datetime.now().strftime('%Y-%m-%d'))
        db.execute('INSERT INTO scores(user_id,subject,score,grade,exam_name,term,date) VALUES(?,?,?,?,?,?,?)',
                   (sid,subject,score,grade,exam,term,date))
        ok += 1
    db.commit(); db.close()
    return jsonify({'ok':ok,'fail':fail})

@app.route('/api/teacher/scores/stats', methods=['GET'])
def score_stats():
    user, err = need_auth('teacher')
    if err: return err
    exam = request.args.get('exam','')
    db = get_db()
    if exam:
        rows = db.execute('''SELECT user_id,u.display_name,u.username,s.score,s.grade,s.subject
            FROM scores s JOIN users u ON s.user_id=u.id WHERE s.exam_name=? ORDER BY s.score DESC''', (exam,)).fetchall()
    else:
        rows = db.execute('''SELECT user_id,u.display_name,u.username,s.score,s.grade,s.subject
            FROM scores s JOIN users u ON s.user_id=u.id ORDER BY s.date DESC LIMIT 200''').fetchall()
    db.close()
    scores_list = [dict(r) for r in rows]
    if not scores_list:
        return jsonify({'avg':0,'max':0,'min':0,'grade_dist':{},'list':[]})
    vals = [s['score'] for s in scores_list]
    dist = {'A':0,'B':0,'C':0,'D':0,'E':0}
    for s in scores_list:
        g = s['grade']
        if g in dist: dist[g] = dist.get(g,0)+1
    return jsonify({
        'avg': round(sum(vals)/len(vals),1),
        'max': max(vals),
        'min': min(vals),
        'total': len(vals),
        'grade_dist': dist,
        'list': scores_list
    })

# ============ 学生成绩查看 ============
@app.route('/api/student/scores', methods=['GET'])
def my_scores():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT id,subject,grade,exam_name,term,date FROM scores WHERE user_id=? ORDER BY date DESC', (user['id'],)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/student/scores/chart', methods=['GET'])
def my_score_chart():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT exam_name,subject,grade,date,score FROM scores WHERE user_id=? ORDER BY date ASC', (user['id'],)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ============ 师生消息 ============
@app.route('/api/student/messages', methods=['GET'])
def my_messages():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT * FROM messages WHERE from_user_id=? ORDER BY date DESC', (user['id'],)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/student/messages', methods=['POST'])
def send_message():
    user, err = need_auth('student')
    if err: return err
    d = request.get_json() or {}
    content = d.get('content','').strip()
    if not content: return jsonify({'error':'请输入内容'}),400
    db = get_db()
    db.execute('INSERT INTO messages(from_user_id,from_name,content,date) VALUES(?,?,?,?)',
               (user['id'], user.get('display_name','') or user['username'], content, datetime.now().strftime('%Y-%m-%d %H:%M')))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/teacher/messages', methods=['GET'])
def teacher_messages():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('''SELECT m.*,u.display_name,u.username FROM messages m
        JOIN users u ON m.from_user_id=u.id
        ORDER BY CASE WHEN m.is_read=0 THEN 0 ELSE 1 END, m.date DESC''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/messages/reply', methods=['POST'])
def reply_message():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    mid = d.get('message_id')
    reply = d.get('reply','').strip()
    if not mid or not reply: return jsonify({'error':'参数不全'}),400
    db = get_db()
    db.execute('UPDATE messages SET reply=?,is_read=1,reply_date=? WHERE id=?',
               (reply, datetime.now().strftime('%Y-%m-%d %H:%M'), mid))
    db.commit(); db.close()
    return jsonify({'ok':True})

# ============ 预警轮询 ============
@app.route('/api/teacher/alerts/pending', methods=['GET'])
def pending_alerts():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('''SELECT a.*,u.display_name,u.username FROM alerts a
        JOIN users u ON a.user_id=u.id WHERE a.handled=0 ORDER BY a.date DESC LIMIT 20''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ============ 智能出卷 ============
@app.route('/api/teacher/exam/generate', methods=['POST'])
def generate_exam():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    subject = d.get('subject','数学')
    topics = d.get('topics','').strip()
    difficulty = d.get('difficulty','中等')
    count = int(d.get('count',10))
    from api.qwen_api import _call
    prompt = f'请出一份{subject}试卷，考察知识点：{topics}，难度：{difficulty}，共{count}题（含答案）。格式清晰，每题一行。'
    text = _call(prompt, '你是一位有经验的教师，请出一套试卷。')
    return jsonify({'exam': text})

@app.route('/api/teacher/student-questions', methods=['GET'])
def student_questions():
    user, err = need_auth('teacher')
    if err: return err
    sid = request.args.get('student_id', type=int)
    if not sid: return jsonify({'error':'请指定学生'}),400
    db = get_db()
    rows = db.execute('SELECT id,subject,topic,date,content,student_name FROM questions WHERE user_id=? ORDER BY date DESC LIMIT 100', (sid,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ============ 学生错题 ============
@app.route('/api/student/wrong/list', methods=['GET'])
@app.route('/api/student/wrong', methods=['GET'])
def my_wrong():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT * FROM wrong_questions WHERE user_id=? ORDER BY date DESC', (user['id'],)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/student/wrong/add', methods=['POST'])
@app.route('/api/student/wrong', methods=['POST'])
def add_wrong():
    user, err = need_auth('student')
    if err: return err
    img_path = ''
    if 'file' in request.files:
        f = request.files['file']
        if f and f.filename:
            import uuid
            ext = f.filename.rsplit('.',1)[-1] if '.' in f.filename else 'jpg'
            name = f"{uuid.uuid4().hex}.{ext}"
            path = os.path.join(UPLOAD, name)
            f.save(path)
            img_path = '/uploads/' + name
    d = request.form.to_dict() if not request.is_json else (request.get_json() or {})
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    db.execute('INSERT INTO wrong_questions(user_id,student_name,image_path,subject,question,explanation,date) VALUES(?,?,?,?,?,?,?)',
               (user['id'], user.get('display_name','') or user['username'], img_path,
                d.get('subject','数学'), d.get('question',''), d.get('explanation',''), now))
    db.execute('INSERT INTO points_log(user_id,points,type,reason,created_at) VALUES(?,?,?,?,?)',
               (user['id'], 10, 'earn', '添加错题 +10分', now))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/student/wrong/delete', methods=['POST'])
def del_wrong_post():
    user, err = need_auth('student')
    if err: return err
    d = request.get_json() or {}
    wid = d.get('id') or d.get('wrong_id')
    if not wid: return jsonify({'error':'缺少错题ID'}),400
    db = get_db()
    db.execute('DELETE FROM wrong_questions WHERE id=? AND user_id=?', (wid, user['id']))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/student/wrong/<int:wid>', methods=['DELETE'])
def del_wrong(wid):
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    db.execute('DELETE FROM wrong_questions WHERE id=? AND user_id=?', (wid, user['id']))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/student/wrong/upload', methods=['POST'])
def wrong_upload():
    user, err = need_auth('student')
    if err: return err
    d = request.get_json() or {}
    image_b64 = d.get('image', '')
    subject = d.get('subject', '数学')
    note = d.get('note', '')
    img_path = ''
    if image_b64 and image_b64.startswith('data:image'):
        import uuid, base64
        header, data = image_b64.split(',', 1)
        ext = 'png'
        if 'jpeg' in header or 'jpg' in header: ext = 'jpg'
        name = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(UPLOAD, name)
        with open(path, 'wb') as f:
            f.write(base64.b64decode(data))
        img_path = '/uploads/' + name
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    db.execute('INSERT INTO wrong_questions(user_id,student_name,image_path,subject,question,explanation,date) VALUES(?,?,?,?,?,?,?)',
               (user['id'], user.get('display_name','') or user['username'], img_path,
                subject, note or '', '', now))
    db.execute('INSERT INTO points_log(user_id,points,type,reason,created_at) VALUES(?,?,?,?,?)',
               (user['id'], 10, 'earn', '上传错题 +10分', now))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/teacher/student-wrong', methods=['GET'])
def teacher_student_wrong():
    user, err = need_auth('teacher')
    if err: return err
    sid = request.args.get('student_id', type=int)
    if not sid: return jsonify({'error':'请指定学生'}),400
    db = get_db()
    rows = db.execute('SELECT * FROM wrong_questions WHERE user_id=? ORDER BY date DESC', (sid,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# ============ 学生端 ============
@app.route('/api/student/solve', methods=['POST'])
def student_solve():
    user, err = need_auth('student')
    if err: return err
    f = request.files.get('file') or request.files.get('image')
    if not f: return jsonify({'error':'请上传图片'}),400
    if not f or not allowed_file(f.filename): return jsonify({'error':'不支持的图片格式'}),400
    import uuid
    ext = f.filename.rsplit('.',1)[-1] if '.' in f.filename else 'jpg'
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD, name)
    f.save(path)
    img_path = '/uploads/' + name
    text = solve_question(path)
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    db.execute('INSERT INTO questions(user_id,student_name,subject,date,content,image_path,is_correct) VALUES(?,?,?,?,?,?,?)',
               (user['id'], user.get('display_name','') or user['username'], '数学', now, text, img_path, 1))
    db.execute('INSERT INTO points_log(user_id,points,type,reason,created_at) VALUES(?,?,?,?,?)',
               (user['id'], 5, 'earn', '拍题解题 +5分', now))
    db.commit(); db.close()
    return jsonify({'ok':True, 'explanation':text, 'image_path': img_path})

HOTLINE = '\n\n📞 需要帮助？可以拨打这些免费电话：\n\n🏠 全国心理援助热线：400-161-9995\n👫 希望24热线：400-161-9995（学生专线按1）\n🧡 12355 青少年服务台：12355\n🆘 报警电话：110'

@app.route('/api/student/ask', methods=['POST'])
def student_ask():
    user, err = need_auth('student')
    if err: return err
    d = request.get_json() or {}
    question = d.get('question','').strip()
    if not question: return jsonify({'error':'请输入问题'}),400
    from api.qwen_api import _call
    answer = _call(question, f'你是一个知识渊博的老师，请用简单易懂的语言回答学生的问题。如果不知道就说不知道，不要编造。')
    return jsonify({'answer': answer})

@app.route('/api/student/chat', methods=['POST'])
def student_chat():
    user, err = need_auth()
    if err: return err
    
    # 检查是否被暂停服务
    if user.get('blocked'):
        return jsonify({'reply':'⚠️ 你的账号已被暂停使用。请与老师联系。\n'+HOTLINE, 'alert':True, 'blocked':True})
    
    d = request.get_json() or {}
    msg = d.get('message','').strip()
    if not msg: return jsonify({'error':'请输入内容'}),400
    
    reply = emotional_chat(msg, d.get('mood','neutral'))
    alert = '[ALERT]' in reply
    clean = reply.replace('[ALERT]','').strip()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 记录聊天日志
    db = get_db()
    db.execute('INSERT INTO chat_logs(user_id,student_name,message,reply,mood,has_alert,date) VALUES(?,?,?,?,?,?,?)',
               (user['id'], user.get('display_name','') or user['username'], msg, clean, d.get('mood','neutral'), alert, now))
    
    if alert:
        db.execute('INSERT INTO alerts(user_id,student,content,date,handled) VALUES(?,?,?,?,?)',(user['id'],user['username'],msg,now,0))
        # 标记该学生需要关注
        db.execute('UPDATE users SET blocked=1 WHERE id=? AND blocked=0', (user['id'],))
    
    db.commit(); db.close()
    
    # 返回结果：有预警时附带热线
    result = {'reply': clean, 'alert': alert, 'blocked': False}
    if alert:
        result['reply'] = clean + '\n\n💛 老师已经收到你的消息，会来关心你的。' + HOTLINE
        result['blocked'] = True
    return jsonify(result)

@app.route('/api/voice/recognize', methods=['POST'])
def voice_recognize():
    user, err = need_auth()
    if err: return err
    return jsonify({'text':'[识别服务] 请安装FunASR'})

# ============ 积分系统 ============

def get_student_points(user_id):
    db = get_db()
    row = db.execute('SELECT COALESCE(SUM(points),0) FROM points_log WHERE user_id=?', (user_id,)).fetchone()
    db.close()
    return row[0] if row else 0

# 学生端
@app.route('/api/student/points', methods=['GET'])
def my_points():
    user, err = need_auth('student')
    if err: return err
    total = get_student_points(user['id'])
    return jsonify({'total': total})

@app.route('/api/student/points/history', methods=['GET'])
def my_points_history():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT points,type,reason,created_at FROM points_log WHERE user_id=? ORDER BY created_at DESC LIMIT 100', (user['id'],)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/student/rewards', methods=['GET'])
def student_rewards():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT id,name,cost,stock FROM rewards WHERE enabled=1 ORDER BY cost ASC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/student/redeem', methods=['POST'])
def student_redeem():
    user, err = need_auth('student')
    if err: return err
    d = request.get_json() or {}
    reward_id = d.get('reward_id')
    if not reward_id: return jsonify({'error':'请选择兑换项'}),400
    db = get_db()
    r = db.execute('SELECT * FROM rewards WHERE id=? AND enabled=1', (reward_id,)).fetchone()
    if not r:
        db.close()
        return jsonify({'error':'兑换项不存在或已下架'}),400
    if r['stock'] == 0:
        db.close()
        return jsonify({'error':'库存不足'}),400
    total = get_student_points(user['id'])
    if total < r['cost']:
        db.close()
        return jsonify({'error':f'积分不足，需要 {r["cost"]} 分，当前 {total} 分'}),400
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    db.execute('INSERT INTO points_log(user_id,points,type,reason,created_at) VALUES(?,?,?,?,?)',
               (user['id'], -r['cost'], 'redeem', f'兑换：{r["name"]}', now))
    db.execute('INSERT INTO redemptions(user_id,reward_id,reward_name,cost,status,created_at) VALUES(?,?,?,?,?,?)',
               (user['id'], reward_id, r['name'], r['cost'], 'pending', now))
    if r['stock'] > 0:
        db.execute('UPDATE rewards SET stock=stock-1 WHERE id=?', (reward_id,))
    db.commit(); db.close()
    return jsonify({'ok':True, 'message':f'成功兑换「{r["name"]}」，等待老师确认'})

@app.route('/api/student/redemptions', methods=['GET'])
def my_redemptions():
    user, err = need_auth('student')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT r.*,w.name as reward_name FROM redemptions r JOIN rewards w ON r.reward_id=w.id WHERE r.user_id=? ORDER BY r.created_at DESC LIMIT 50', (user['id'],)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# 教师端
@app.route('/api/teacher/points', methods=['GET'])
def teacher_points():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('''SELECT u.id,u.display_name,u.username,
        COALESCE((SELECT SUM(points) FROM points_log WHERE user_id=u.id),0) as total
        FROM users u WHERE u.role="student" ORDER BY total DESC''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/points/adjust', methods=['POST'])
def adjust_points():
    """教师加减分，需要填写理由"""
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    student_id = d.get('student_id')
    points = d.get('points', 0)
    reason = (d.get('reason') or '').strip()
    if not student_id: return jsonify({'error':'请选择学生'}),400
    if points == 0: return jsonify({'error':'分数不能为0'}),400
    if not reason: return jsonify({'error':'请填写加减分理由'}),400
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    typ = 'teacher_add' if points > 0 else 'teacher_sub'
    db = get_db()
    db.execute('INSERT INTO points_log(user_id,points,type,reason,operator_id,created_at) VALUES(?,?,?,?,?,?)',
               (student_id, points, typ, reason, user['id'], now))
    db.commit(); db.close()
    return jsonify({'ok':True, 'message':f'已{"加" if points>0 else "减"} {abs(points)} 分'})

@app.route('/api/teacher/points/history', methods=['GET'])
def teacher_points_history():
    user, err = need_auth('teacher')
    if err: return err
    sid = request.args.get('student_id', type=int)
    db = get_db()
    if sid:
        rows = db.execute('SELECT points,type,reason,created_at FROM points_log WHERE user_id=? ORDER BY created_at DESC LIMIT 200', (sid,)).fetchall()
    else:
        rows = db.execute('SELECT p.*,u.display_name,u.username FROM points_log p JOIN users u ON p.user_id=u.id ORDER BY p.created_at DESC LIMIT 200').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

# 奖励管理
@app.route('/api/teacher/rewards', methods=['GET'])
def list_rewards():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT * FROM rewards ORDER BY cost ASC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/rewards', methods=['POST'])
def add_reward():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    name = (d.get('name') or '').strip()
    cost = int(d.get('cost', 10))
    stock = int(d.get('stock', -1))
    if not name: return jsonify({'error':'请填写兑换名称'}),400
    if cost <= 0: return jsonify({'error':'积分需要大于0'}),400
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    db = get_db()
    db.execute('INSERT INTO rewards(name,cost,stock,enabled,created_at) VALUES(?,?,?,1,?)', (name, cost, stock, now))
    db.commit(); db.close()
    return jsonify({'ok':True, 'message':'兑换项添加成功'})

@app.route('/api/teacher/rewards/<int:rid>', methods=['DELETE'])
def delete_reward(rid):
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    db.execute('DELETE FROM rewards WHERE id=?', (rid,))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/teacher/rewards/<int:rid>/toggle', methods=['POST'])
def toggle_reward(rid):
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    r = db.execute('SELECT enabled FROM rewards WHERE id=?', (rid,)).fetchone()
    if r:
        db.execute('UPDATE rewards SET enabled=? WHERE id=?', (0 if r['enabled'] else 1, rid))
        db.commit()
    db.close()
    return jsonify({'ok':True})

# 教师确认兑换
@app.route('/api/teacher/redemptions', methods=['GET'])
def teacher_redemptions():
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('''SELECT r.*,u.display_name,u.username FROM redemptions r
        JOIN users u ON r.user_id=u.id ORDER BY r.status, r.created_at DESC LIMIT 100''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/teacher/redemptions/<int:rid>/confirm', methods=['POST'])
def confirm_redemption(rid):
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    db.execute('UPDATE redemptions SET status="confirmed" WHERE id=?', (rid,))
    db.commit(); db.close()
    return jsonify({'ok':True, 'message':'已确认兑换'})

# 排行榜
@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    db = get_db()
    rows = db.execute('''SELECT u.id,u.display_name,u.username,
        COALESCE((SELECT SUM(points) FROM points_log WHERE user_id=u.id),0) as total
        FROM users u WHERE u.role="student" ORDER BY total DESC LIMIT 50''').fetchall()
    db.close()
    result = []
    for i, r in enumerate(rows):
        d = dict(r)
        d['rank'] = i + 1
        result.append(d)
    return jsonify(result)



@app.route('/api/teacher/students/batch-delete', methods=['POST'])
def batch_delete_students():
    """批量删除学生（也支持单个或多个ids）"""
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    ids = d.get('ids', [])
    if not ids: return jsonify({'ok':True, 'deleted':0})
    db = get_db()
    for sid in ids:
        db.execute('DELETE FROM users WHERE id=? AND role="student"', (sid,))
        db.execute('DELETE FROM points_log WHERE user_id=?', (sid,))
        db.execute('DELETE FROM scores WHERE user_id=?', (sid,))
        db.execute('DELETE FROM messages WHERE from_user_id=?', (sid,))
        db.execute('DELETE FROM questions WHERE user_id=?', (sid,))
        db.execute('DELETE FROM alerts WHERE user_id=?', (sid,))
        db.execute('DELETE FROM chat_logs WHERE user_id=?', (sid,))
        db.execute('DELETE FROM wrong_questions WHERE user_id=?', (sid,))
        db.execute('UPDATE redemptions SET status="cancelled" WHERE user_id=?', (sid,))
    db.commit(); db.close()
    return jsonify({'ok':True, 'deleted':len(ids)})

@app.route('/api/teacher/students/solved-counts', methods=['GET'])
def students_solved_counts():
    """统计每个学生做题数"""
    user, err = need_auth('teacher')
    if err: return err
    db = get_db()
    rows = db.execute('SELECT user_id,COUNT(*) cnt FROM questions GROUP BY user_id').fetchall()
    db.close()
    return jsonify({str(r['user_id']): r['cnt'] for r in rows})

@app.route('/api/teacher/students/reset-pw', methods=['POST'])
def reset_student_password():
    user, err = need_auth('teacher')
    if err: return err
    d = request.get_json() or {}
    sid = d.get('student_id')
    new_pw = (d.get('new_password') or '').strip()
    if not sid: return jsonify({'error':'no student'}),400
    if not new_pw or len(new_pw) < 4: return jsonify({'error':'pw too short'}),400
    db = get_db()
    db.execute('UPDATE users SET password_hash=?, plain_password=? WHERE id=? AND role="student"', (hash_pw(new_pw), new_pw, sid))
    db.commit(); db.close()
    return jsonify({'ok':True})


if __name__=='__main__':
    init_db()
    print('🌿 课伴服务端 → http://localhost:5000')
    app.run(host='0.0.0.0',port=5000,debug=True)
