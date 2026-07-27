def recognize_audio(audio_path, dialect='普通话'):
    try:
        from funasr import AutoModel
        model = AutoModel(model="paraformer-zh",vad_model="fsmn-vad",punc_model="ct-punc")
        result = model.generate(input=audio_path)
        return result[0]['text'] if result else ''
    except ImportError: return '[请安装funasr] pip install funasr'
    except Exception as e: return f'[识别失败] {str(e)}'
