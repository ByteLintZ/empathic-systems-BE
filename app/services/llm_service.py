import logging
import time
import random
import asyncio
from typing import Optional, List, Dict
import os
from datetime import datetime
from dotenv import load_dotenv
import httpx

load_dotenv()

class LLMService:
    def __init__(self):
        # Load primary API key
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            logging.error("[LLMService] GROQ_API_KEY not found! Please check your .env")
            
        if self.api_key:
            logging.info(f"[LLMService] Loaded Groq API key ending in: ...{self.api_key[-6:]}")

        # Groq OpenAI-compatible endpoint
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Groq's blazingly fast models
        self.models = [
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        
        # Tracking for logging
        self.last_used_model = None
        
        logging.info(f"LLMService initialized with Groq API and {len(self.models)} models")

    def get_educational_system_prompt(self, emotion: str, subject: Optional[str] = None) -> str:
        """Get educational system prompt based on emotion and subject"""
        base_prompt = (
            "Kamu adalah EduBot 🚀, mentor AI yang super asik, enerjik, dan punya otak engineering yang tajam! "
            "PENTING: Kamu memiliki maksimal 1000 token. Buat jawabanmu terstruktur, gampang dibaca (gunakan bullet points/bold), dan langsung ke inti logika. "
            "\nKarakteristik & Gaya Bahasamu:\n"
            "✨ Vibe-mu seperti Tech Lead atau Kating (Kakak Tingkat) yang lagi mentoring juniornya: santai, suportif, dan seru!\n"
            "🧠 Kamu benci hafalan buta. Kamu selalu ngajak siswa memecahkan masalah pakai 'engineering logic', debugging, atau fundamental thinking.\n"
            "💡 Gunakan analogi dari dunia teknologi, game, atau sistem dunia nyata yang masuk akal.\n"
            "🤗 Empatimu aktif: validasi perasaan mereka dengan semangat, lalu ajak mereka 'berantem' ngalahin problemnya bareng-bareng.\n"
            "\nAturan:\n"
            "- Gunakan emoji secukupnya untuk ngasih energi positif (nggak over/alay).\n"
            "- Bahasa Indonesia gaul/santai tapi tetap sopan dan jelas.\n"
        )
        
        if subject:
            subject_prompts = {
                'matematika': '🔢 Buatmu, matematika bukan rumus ngebosenin, melainkan bahasa pemrograman alam semesta. Ajak siswa melihat polanya!',
                'fisika': '⚛️ Jelaskan fisika kayak kita lagi nge-reverse engineer cara kerja alam semesta!',  
                'kimia': '🧪 Bahas kimia layaknya meracik arsitektur sistem dari tingkat molekuler.',
                'biologi': '🌿 Bedah biologi sebagai sistem algoritma kehidupan yang paling kompleks dan keren.',
                'sejarah': '📚 Ceritakan sejarah sebagai analisis sebab-akibat dan data dari masa lalu yang ngebentuk sistem hari ini.',
                'bahasa': '📝 Lihat bahasa sebagai protokol komunikasi canggih untuk mentransfer ide di otak ke orang lain.',
                'geografi': '🌍 Petakan geografi sebagai interaksi dinamis antara spasial dan sistem lingkungan.',
            }
            base_prompt += f"\n{subject_prompts.get(subject.lower(), '🔥 Kamu sangat antusias membahas bidang ' + subject + ' ini!')}\n"
        
        emotion_templates = {
            "Senang": (
                "Konteks: Siswa lagi hype dan paham materinya 🎉\n"
                "Instruksi:\n"
                "- Ikut hype! Puji keberhasilan mereka (misal: 'Nice catch!', 'Logika kamu jalan banget!').\n"
                "- Kasih fun fact atau tantang mereka dengan satu level kompleksitas yang lebih tinggi buat mancing rasa penasarannya."
            ),
            "Netral": (
                "Konteks: Siswa lagi mode fokus 💻\n"
                "Instruksi:\n"
                "- Langsung bedah materinya dengan sistematis dan asik.\n"
                "- Kasih framework berpikirnya, jangan cuma ngasih jawaban instan."
            ),
            "Bingung": (
                "Konteks: Siswa lagi nge-bug atau stuck 🌀\n"
                "Instruksi:\n"
                "- Validasi kebingungan mereka dengan santai (wajar kalau otak lagi 'loading').\n"
                "- Ajak 'debug' bareng dari dasar. Pecah masalahnya (breakdown) jadi komponen kecil.\n"
                "- Lempar pertanyaan pancingan biar mereka nemu logikanya sendiri."
            ),
            "Frustrasi": (
                "Konteks: Siswa kena mental block/frustrasi 😤\n"
                "Instruksi:\n"
                "- Tunjukkan empati yang membangkitkan semangat! (misal: 'Wah, materi ini emang boss fight yang alot!').\n"
                "- Ajak tarik napas bentar (step back).\n"
                "- Ubah angle pendekatannya. Kalau cara A gagal, tawarkan cara B pakai analogi yang jauh lebih simpel."
            ),
            "Marah": (
                "Konteks: Siswa kesal dengan materi/tugas 😠\n"
                "Instruksi:\n"
                "- Tetap cool, suportif, dan jadi *safe space* buat mereka marah.\n"
                "- Jangan ceramah. Akui kalau materinya emang ngeselin, lalu pelan-pelan arahkan fokus buat 'ngalahin' masalah utamanya secara taktis."
            ),
        }
        
        return base_prompt + "\n" + emotion_templates.get(emotion, emotion_templates["Netral"])
    
    async def create_empathetic_response(self, user_message: str, emotion: str, confidence: float, 
                                         context_messages: Optional[List[Dict]] = None, 
                                         conversation_subject: Optional[str] = None) -> str:
        """Create educational empathetic response using Groq API"""
        
        messages = [
            {
                "role": "system",
                "content": self.get_educational_system_prompt(emotion, conversation_subject)
            }
        ]
        
        if context_messages:
            messages.extend(context_messages[:-1])
            
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        logging.info(f"🎭 EMOTION: {emotion} (confidence: {confidence:.3f}) - User: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        
        # Simplified retry config since we only have 1 reliable key now
        max_retries = 3 
        base_delay = 1.0
        selected_model = self.models[0] # Defaulting to Llama-3.3-70b as primary
        
        request_start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.8,
            "top_p": 0.9
        }

        for attempt in range(max_retries):
            try:
                attempt_start_time = time.time()
                logging.info(f"🚀 ATTEMPT {attempt + 1}/{max_retries}: Groq model={selected_model}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(self.api_url, headers=headers, json=payload)
                
                attempt_duration = time.time() - attempt_start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        ai_response = data["choices"][0]["message"]["content"].strip()
                        total_duration = time.time() - request_start_time
                        
                        self.last_used_model = selected_model
                        
                        logging.info(f"✅ SUCCESS: {selected_model} "
                                   f"({attempt_duration:.2f}s attempt, {total_duration:.2f}s total) "
                                   f"- Response: {len(ai_response)} chars")
                        
                        return self._enhance_educational_response(ai_response, emotion, confidence)
                    else:
                        logging.warning(f"❌ EMPTY: {selected_model} returned empty response")
                        if attempt == max_retries - 1: return self._get_fallback_response(emotion, user_message)
                        
                elif response.status_code == 429: # Rate limit hit on Groq
                    delay = base_delay * (2 ** attempt)
                    logging.warning(f"🚫 RATE LIMITED: Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    if attempt == max_retries - 1: return self._get_rate_limit_fallback(emotion)
                        
                else:
                    error_text = response.text[:200] + "..." if len(response.text) > 200 else response.text
                    logging.error(f"❌ HTTP {response.status_code}: {selected_model} "
                                f"({attempt_duration:.2f}s) - {error_text}")
                    if attempt == max_retries - 1: return self._get_fallback_response(emotion, user_message)
                    await asyncio.sleep(1) # Brief pause before retrying a 5xx error
                    
            except httpx.TimeoutException:
                logging.warning(f"Timeout, retrying... (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1: return self._get_timeout_fallback(emotion)
                await asyncio.sleep(base_delay)
                
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                if attempt == max_retries - 1: return self._get_fallback_response(emotion, user_message)
                await asyncio.sleep(base_delay)
        
        return self._get_fallback_response(emotion, user_message)
    
    def _enhance_educational_response(self, response: str, emotion: str, confidence: float) -> str:
        """Enhance response with educational elements"""
        if confidence > 0.85:
            emotion_emoji = {
                "Senang": "😊", "Netral": "🤖", "Bingung": "🤔", 
                "Frustrasi": "😤", "Marah": "😠"
            }.get(emotion, "🤖")
            response += f"\n\n{emotion_emoji} *Aku bisa merasakan kamu sedang {emotion.lower()} nih!*"
        
        learning_tips = {
            "Senang": "\n\n💡 **Tips**: Manfaatkan semangat positif ini untuk mempelajari topik baru!",
            "Bingung": "\n\n💡 **Tips**: Tidak apa-apa bingung, itu artinya otak kamu sedang bekerja keras!",
            "Frustrasi": "\n\n💡 **Tips**: Istirahat sebentar, lalu coba dengan pendekatan yang berbeda ya!",
            "Marah": "\n\n💡 **Tips**: Tarik nafas dalam-dalam, mari kita selesaikan ini bersama-sama."
        }
        
        if emotion in learning_tips and confidence > 0.7:
            response += learning_tips[emotion]
            
        return response
    
    def _get_fallback_response(self, emotion: str, user_message: str) -> str:
        fallbacks = {
            "Senang": "🎉 Wah, senang banget denger semangat kamu! Aku siap membantu kamu belajar lebih banyak lagi. Ada yang ingin kamu tanyakan? 😊",
            "Netral": "📚 Halo! Aku EduBot, siap membantu kamu belajar dengan cara yang menyenangkan. Apa yang ingin kita pelajari hari ini? 🤖",
            "Bingung": "🤔 Aku paham kamu merasa bingung. Gak masalah kok! Mari kita pecahkan masalah ini step by step. Bisa ceritakan lebih detail tentang apa yang membingungkan? 💡",
            "Frustrasi": "😤 Aku tahu perasaan frustrasi itu tidak enak. Tapi ingat, setiap ahli pernah jadi pemula! Mari kita coba pendekatan yang lebih mudah ya. Kamu pasti bisa! 💪",
            "Marah": "😠 Aku paham kamu sedang kesal. Mari kita ambil nafas sejenak dan fokus menyelesaikan masalah ini bersama-sama. Aku di sini untuk membantu kamu. 🤝"
        }
        base_response = fallbacks.get(emotion, fallbacks["Netral"])
        
        if any(keyword in user_message.lower() for keyword in ['matematika', 'math', 'hitung']):
            base_response += "\n\n🔢 Oh, ini tentang matematika ya? Aku suka banget sama matematika!"
        elif any(keyword in user_message.lower() for keyword in ['fisika', 'physics']):
            base_response += "\n\n⚛️ Fisika nih! Seru banget, kita bisa bahas eksperimen dan rumus-rumus keren!"
        elif any(keyword in user_message.lower() for keyword in ['sejarah', 'history']):
            base_response += "\n\n📚 Sejarah! Aku punya banyak cerita menarik dari masa lalu!"
            
        return base_response
    
    def _get_rate_limit_fallback(self, emotion: str) -> str:
        rate_limit_responses = {
            "Senang": "🎉 Maaf, servernya agak sibuk nih karena banyak teman yang antusias belajar seperti kamu! Tapi aku tetap senang banget bisa chat sama kamu. Coba lagi sebentar ya! 😊",
            "Netral": "🤖 Server sedang sibuk melayani banyak siswa yang sedang belajar. Silakan coba lagi dalam beberapa saat. Terima kasih atas kesabarannya! 📚",
            "Bingung": "🤔 Waduh, servernya lagi rame nih karena banyak yang bertanya seperti kamu! Jangan khawatir, coba tanya lagi sebentar ya. Aku pasti bantu jawab kebingungan kamu! 💡",
            "Frustrasi": "😤 Aku tahu ini bikin frustasi, server lagi sibuk banget. Tapi tenang, coba lagi sebentar dan aku pasti jawab dengan semangat! Kamu pasti bisa mengatasi ini! 💪",
            "Marah": "😠 Maaf ya kalau ini bikin kesal. Server sedang sibuk tapi aku tetap di sini untuk membantu. Mohon bersabar sebentar, aku akan segera membantu kamu! 🤝"
        }
        return rate_limit_responses.get(emotion, rate_limit_responses["Netral"])
    
    def _get_timeout_fallback(self, emotion: str) -> str:
        timeout_responses = {
            "Senang": "🎉 Wah, semangatmu luar biasa! Tapi koneksinya agak lambat nih. Coba tanya lagi ya, aku pasti jawab dengan antusias! 😊",
            "Netral": "🤖 Koneksi agak lambat saat ini. Silakan ulangi pertanyaan kamu, aku siap membantu! 📚",
            "Bingung": "🤔 Hmm, sepertinya ada gangguan koneksi yang bikin proses jadi lambat. Jangan khawatir, coba lagi ya! Aku tetap siap bantu! 💡",
            "Frustrasi": "😤 Aku paham frustrasimu karena koneksi lambat. Tapi jangan menyerah! Coba lagi dan kita selesaikan bersama! 💪",
            "Marah": "😠 Maaf koneksinya bermasalah dan bikin kesal. Aku tetap di sini untuk membantu, coba lagi sebentar ya! 🤝"
        }
        return timeout_responses.get(emotion, timeout_responses["Netral"])

# Global instance
llm_service = LLMService()