# backend/api/voice_service.py - Multilingual Voice Alert Service (Windows-compatible)

from gtts import gTTS
import os
import logging
import threading
from datetime import datetime
import io
import tempfile
import subprocess

# Initialize logger FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAlertService:
    """Multilingual voice alert service for DriAlert"""
    
    # Alert messages in multiple Indian languages
    ALERTS = {
        'english': {
            'drowsy': "Warning! Driver is drowsy. Please take a break.",
            'yawning': "Driver is yawning. Consider resting.",
            'high_risk': "High risk detected. Pull over safely.",
            'monitoring_started': "Drowsiness monitoring started.",
            'monitoring_stopped': "Monitoring stopped."
        },
        'hindi': {
            'drowsy': "चेतावनी! ड्राइवर सो रहा है। कृपया ब्रेक लें।",
            'yawning': "ड्राइवर जम्हाई ले रहा है। आराम करने पर विचार करें।",
            'high_risk': "उच्च जोखिम का पता चला। सुरक्षित रूप से गाड़ी रोकें।",
            'monitoring_started': "निगरानी शुरू हो गई है।",
            'monitoring_stopped': "निगरानी बंद हो गई।"
        },
        'kannada': {
            'drowsy': "ಎಚ್ಚರಿಕೆ! ಚಾಲಕ ನಿದ್ದೆ ಮಾಡುತ್ತಿದ್ದಾರೆ. ದಯವಿಟ್ಟು ವಿರಾಮ ತೆಗೆದುಕೊಳ್ಳಿ.",
            'yawning': "ಚಾಲಕ ಆಕಳಿಕೆ ಬರುತ್ತಿದೆ. ವಿಶ್ರಾಂತಿ ಪಡೆಯಿರಿ.",
            'high_risk': "ಹೆಚ್ಚಿನ ಅಪಾಯ ಪತ್ತೆಯಾಗಿದೆ. ಸುರಕ್ಷಿತವಾಗಿ ನಿಲ್ಲಿಸಿ.",
            'monitoring_started': "ಮೇಲ್ವಿಚಾರಣೆ ಪ್ರಾರಂಭವಾಗಿದೆ.",
            'monitoring_stopped': "ಮೇಲ್ವಿಚಾರಣೆ ನಿಲ್ಲಿಸಲಾಗಿದೆ."
        },
        'tamil': {
            'drowsy': "எச்சரிக்கை! ஓட்டுநர் தூங்குகிறார். தயவுசெய்து ஓய்வெடுங்கள்.",
            'yawning': "ஓட்டுநர் கொட்டாவி விடுகிறார். ஓய்வெடுக்கவும்.",
            'high_risk': "அதிக ஆபத்து கண்டறியப்பட்டது. பாதுகாப்பாக நிறுத்தவும்.",
            'monitoring_started': "கண்காணிப்பு தொடங்கியது.",
            'monitoring_stopped': "கண்காணிப்பு நிறுத்தப்பட்டது."
        },
        'telugu': {
            'drowsy': "హెచ్చరిక! డ్రైవర్ నిద్రపోతున్నాడు. దయచేసి విశ్రాంతి తీసుకోండి.",
            'yawning': "డ్రైవర్ ఆవాలింపు చేస్తున్నాడు. విశ్రాంతి తీసుకోండి.",
            'high_risk': "అధిక ప్రమాదం గుర్తించబడింది. సురక్షితంగా ఆపండి.",
            'monitoring_started': "పర్యవేక్షణ ప్రారంభమైంది.",
            'monitoring_stopped': "పర్యవేక్షణ ఆపివేయబడింది."
        },
        'malayalam': {
            'drowsy': "മുന്നറിയിപ്പ്! ഡ്രൈവർ ഉറങ്ങുകയാണ്. ദയവായി വിശ്രമിക്കുക.",
            'yawning': "ഡ്രൈവർ കോട്ടുവായുന്നു. വിശ്രമിക്കാൻ ശ്രമിക്കുക.",
            'high_risk': "ഉയർന്ന അപകടം കണ്ടെത്തി. സുരക്ഷിതമായി നിർത്തുക.",
            'monitoring_started': "നിരീക്ഷണം ആരംഭിച്ചു.",
            'monitoring_stopped': "നിരീക്ഷണം നിർത്തി."
        },
        'marathi': {
            'drowsy': "चेतावणी! ड्रायव्हर झोपतो आहे. कृपया विश्रांती घ्या.",
            'yawning': "ड्रायव्हर जांभई देत आहे. विश्रांती विचारात घ्या.",
            'high_risk': "उच्च जोखीम आढळली. सुरक्षितपणे थांबवा.",
            'monitoring_started': "देखरेख सुरू झाली.",
            'monitoring_stopped': "देखरेख बंद झाली."
        },
        'gujarati': {
            'drowsy': "ચેતવણી! ડ્રાઇવર સૂઈ રહ્યો છે. કૃપા કરીને વિરામ લો.",
            'yawning': "ડ્રાઇવર બગાસું ખાય છે. આરામ કરવાનું વિચારો.",
            'high_risk': "ઉચ્ચ જોખમ શોધાયું. સુરક્ષિત રીતે રોકો.",
            'monitoring_started': "દેખરેખ શરૂ થઈ.",
            'monitoring_stopped': "દેખરેખ બંધ થઈ."
        },
        'bengali': {
            'drowsy': "সতর্কবার্তা! চালক ঘুমাচ্ছেন। দয়া করে বিশ্রাম নিন।",
            'yawning': "চালক হাই তুলছেন। বিশ্রাম নেওয়ার কথা ভাবুন।",
            'high_risk': "উচ্চ ঝুঁকি সনাক্ত করা হয়েছে। নিরাপদে থামুন।",
            'monitoring_started': "পর্যবেক্ষণ শুরু হয়েছে।",
            'monitoring_stopped': "পর্যবেক্ষণ বন্ধ হয়েছে।"
        }
    }
    
    # Language codes for gTTS
    LANG_CODES = {
        'english': 'en',
        'hindi': 'hi',
        'kannada': 'kn',
        'tamil': 'ta',
        'telugu': 'te',
        'malayalam': 'ml',
        'marathi': 'mr',
        'gujarati': 'gu',
        'bengali': 'bn'
    }
    
    def __init__(self):
        self.audio_cache = {}
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'audio_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info("✅ Voice Alert Service initialized (Windows mode)")
    
    def generate_audio(self, text, language='english'):
        """Generate audio from text using gTTS"""
        try:
            lang_code = self.LANG_CODES.get(language, 'en')
            
            # Check cache
            cache_key = f"{language}_{text[:20]}"
            if cache_key in self.audio_cache:
                return self.audio_cache[cache_key]
            
            # Generate TTS
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            # Save to memory
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            # Cache it
            self.audio_cache[cache_key] = audio_fp
            
            logger.info(f"✅ Generated audio: {language}")
            return audio_fp
            
        except Exception as e:
            logger.error(f"❌ Audio generation failed: {e}")
            return None
    
    def play_alert(self, alert_type, language='english'):
        """Play alert in specified language"""
        try:
            # Get message text
            messages = self.ALERTS.get(language, self.ALERTS['english'])
            text = messages.get(alert_type, messages['drowsy'])
            
            logger.info(f"🔊 Playing alert: {alert_type} in {language}")
            
            # Generate and play audio in background
            thread = threading.Thread(
                target=self._play_audio_background,
                args=(text, language)
            )
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Play alert failed: {e}")
            return False
    
    def _play_audio_background(self, text, language):
        """Background audio playback using Windows Media Player"""
        try:
            audio_fp = self.generate_audio(text, language)
            if audio_fp:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3', dir=self.cache_dir) as temp_file:
                    temp_file.write(audio_fp.read())
                    temp_path = temp_file.name
                
                logger.info(f"🎵 Playing audio: {temp_path}")
                
                # Play using Windows default media player (silent mode)
                subprocess.Popen(
                    ['powershell', '-c', f'(New-Object Media.SoundPlayer "{temp_path}").PlaySync()'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Schedule cleanup after 10 seconds
                def cleanup():
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            logger.info(f"🧹 Cleaned up: {temp_path}")
                    except Exception as e:
                        logger.error(f"Cleanup failed: {e}")
                
                threading.Timer(10.0, cleanup).start()
                
        except Exception as e:
            logger.error(f"❌ Background playback failed: {e}")

# Global instance
voice_service = VoiceAlertService()
