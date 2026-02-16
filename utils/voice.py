import io
import os
import base64
from typing import Tuple
from openai import OpenAI


def get_openai_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    )


def speech_to_text(audio_bytes: bytes) -> Tuple[str, str]:
    try:
        client = get_openai_client()
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        text = response.text.strip() if response.text else ""
        if not text:
            return "", "Could not transcribe audio. Please try recording again."
        return text, ""
    except Exception as e:
        return "", f"Transcription failed: {str(e)}"


def generate_tts_html(text: str) -> str:
    clean_text = text.replace("**", "").replace("---", "").replace("\n", " ").replace("'", "\\'").replace('"', '\\"')
    return f"""
    <div style="margin: 8px 0;">
        <button onclick="
            var utterance = new SpeechSynthesisUtterance('{clean_text}');
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        " style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        ">🔊 Listen to Question</button>
        <button onclick="window.speechSynthesis.cancel();" style="
            background: rgba(255,255,255,0.1);
            color: #c3cfe2;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 14px;
            cursor: pointer;
            margin-left: 8px;
        ">⏹ Stop</button>
    </div>
    """


def auto_speak_tts_html(text: str) -> str:
    clean_text = text.replace("**", "").replace("---", "").replace("\n", " ").replace("'", "\\'").replace('"', '\\"')
    return f"""
    <div style="margin: 8px 0;">
        <button id="listenBtn" onclick="
            var utterance = new SpeechSynthesisUtterance('{clean_text}');
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        " style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        ">🔊 Listen to Question</button>
        <button onclick="window.speechSynthesis.cancel();" style="
            background: rgba(255,255,255,0.1);
            color: #c3cfe2;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 14px;
            cursor: pointer;
            margin-left: 8px;
        ">⏹ Stop</button>
    </div>
    <script>
        (function() {{
            var utterance = new SpeechSynthesisUtterance('{clean_text}');
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        }})();
    </script>
    """
