#=============== MAIN APPLICATION ===============#
from flask import Flask, request, render_template, send_file, jsonify
from googletrans import Translator
from gtts import gTTS
import os
from io import BytesIO
import sqlite3
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'naan_mudhalvan_secret_key'

# Initialize translator
translator = Translator()

# Supported languages with focus on Indian languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ta': 'Tamil',
    'hi': 'Hindi',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'pa': 'Punjabi'
}

# Database setup for translation history
def init_db():
    conn = sqlite3.connect('translations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS translations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  source_text TEXT,
                  translated_text TEXT,
                  source_lang TEXT,
                  target_lang TEXT,
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_db()

#=============== CORE FUNCTIONS ===============#
def translate_text(text, src='auto', dest='en'):
    """Translate text using Google Translate API"""
    try:
        translation = translator.translate(text, src=src, dest=dest)
        save_to_history(text, translation.text, src, dest)
        return translation.text
    except Exception as e:
        return f"Translation error: {str(e)}"

def text_to_speech(text, lang='en'):
    """Convert text to speech and return audio file"""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None

def save_to_history(source_text, translated_text, src_lang, dest_lang):
    """Save translation to database"""
    conn = sqlite3.connect('translations.db')
    c = conn.cursor()
    c.execute("INSERT INTO translations (source_text, translated_text, source_lang, target_lang, timestamp) VALUES (?, ?, ?, ?, ?)",
              (source_text, translated_text, src_lang, dest_lang, datetime.now()))
    conn.commit()
    conn.close()

def get_history():
    """Retrieve translation history"""
    conn = sqlite3.connect('translations.db')
    c = conn.cursor()
    c.execute("SELECT * FROM translations ORDER BY timestamp DESC LIMIT 10")
    history = c.fetchall()
    conn.close()
    return history

#=============== FLASK ROUTES ===============#
@app.route('/', methods=['GET', 'POST'])
def index():
    """Main translation interface"""
    history = get_history()
    
    if request.method == 'POST':
        text = request.form['text']
        src_lang = request.form['src_lang']
        dest_lang = request.form['dest_lang']
        
        translated = translate_text(text, src_lang, dest_lang)
        audio_file = None
        
        if 'generate_audio' in request.form:
            audio_buffer = text_to_speech(translated, dest_lang)
            if audio_buffer:
                return send_file(audio_buffer, mimetype='audio/mpeg', download_name='translation.mp3')
        
        return render_template('index.html', 
                            languages=SUPPORTED_LANGUAGES,
                            original_text=text,
                            translated_text=translated,
                            src_lang=src_lang,
                            dest_lang=dest_lang,
                            history=history)
    
    return render_template('index.html', 
                         languages=SUPPORTED_LANGUAGES,
                         history=history)

@app.route('/api/translate', methods=['POST'])
def api_translate():
    """API endpoint for translation"""
    data = request.get_json()
    text = data.get('text', '')
    src_lang = data.get('src_lang', 'auto')
    dest_lang = data.get('dest_lang', 'en')
    
    translated = translate_text(text, src_lang, dest_lang)
    return jsonify({
        'original_text': text,
        'translated_text': translated,
        'source_language': src_lang,
        'target_language': dest_lang
    })

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear translation history"""
    conn = sqlite3.connect('translations.db')
    c = conn.cursor()
    c.execute("DELETE FROM translations")
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

#=============== RUN APPLICATION ===============#

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)