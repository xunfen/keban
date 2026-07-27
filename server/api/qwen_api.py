import os, json
from dotenv import load_dotenv
import dashscope
from dashscope import Generation, MultiModalConversation

load_dotenv()
TEXT_MODEL = 'qwen-max'
VL_MODEL = 'qwen3-vl-plus'

def set_api_key(key): dashscope.api_key = key
def is_configured(): return bool(dashscope.api_key) and dashscope.api_key != 'YOUR_API_KEY_HERE'

def _call(prompt, sp=None):
    if not is_configured(): return '[配置错误] 请先在启动页面配置API Key'
    msgs = []
    if sp: msgs.append({'role':'system','content':sp})
    msgs.append({'role':'user','content':prompt})
    try:
        r = Generation.call(model=TEXT_MODEL,messages=msgs,result_format='message')
        return r.output.choices[0].message.content
    except Exception as e: return f'[API错误] {str(e)}'

def review_analysis(content):
    return _call(content,'你是一位有20年经验的教研员。请从以下课堂内容中分析：1）教学亮点（最多3条）2）学生可能卡壳的知识点（最多3条）3）教学节奏改进建议（最多2条）。请用简短的要点形式输出，每条不超过30字。')

def prepare_lesson(topic):
    sp = f'你是一位乡村小学教师的教学助手。请根据知识点"{topic}"生成备课方案，返回严格合法的JSON格式：{{"outline":{{"goals":["教学目标1","教学目标2"],"key_points":["重点1","难点1"],"flow":{{"导入":"1-2句话","新授":"1-2句话","练习":"1-2句话","总结":"1-2句话"}}}},"exercises":[{{"question":"题目1","answer":"答案1","difficulty":"易"}}]}}共5道题，难度依次为易、易、中、中、难。不要输出JSON以外的任何文字。'
    return _call(topic,sp)

def solve_question(path):
    if not is_configured(): return '[配置错误]'
    try:
        r = MultiModalConversation.call(model=VL_MODEL,messages=[{'role':'user','content':[{'image':f'file://{path}'},{'text':'请先识别图片中的题目内容，然后用小学生能听懂的方式一步步讲解。最后给出答案。'}]}])
        return r.output.choices[0].message.content[0]['text']
    except Exception as e: return f'[API错误] {str(e)}'

def emotional_chat(msg, mood='neutral'):
    return _call(msg,f'你是一个温暖的大哥哥/大姐姐，在和一个小孩子聊天。孩子现在的心情是{mood}。请用简单、温暖、鼓励的语气回复。每次回复不超过50字。如果涉及自伤、霸凌、虐待等严重问题，请在回复末尾加上[ALERT]标记。')

def generate_report(stats, student=''):
    return _call('请生成简报',f'请根据以下学习数据生成一份给家长（或爷爷奶奶）的简报：1）语言亲切简单，不用专业术语 2）先说好消息，再温和提建议 3）不超过150字 4）适合在微信里发文字消息。数据：{stats}')

def generate_weekly_report(stats):
    return _call('请生成周报',f'你是一位教研组长，请根据以下本周教学数据生成周报：1）本周教学进度概述 2）学生整体表现 3）薄弱知识点分析 4）下周教学建议。数据：{stats}，要求条理清晰，不超过500字。')
