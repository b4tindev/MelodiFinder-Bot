import telebot
import requests
import logging
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time

class BotAyarlari:
    BOT_TOKEN = "8408140773:AAHN8JsGFcRBg0PZ8H0iRoti1YhsPA-3e3Q"
    GEMINI_API_KEY = "AIzaSyAtQbZcxHV-Kk0AaQJKRg0SgijC9e-8TP0"
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    MAKSIMUM_DENEME = 3
    ZAMAN_ASIMI = 30
    
class RuhHaliEmojileri(Enum):
    MUTLU = "😊 Mutlu"
    UZGUN = "😢 Üzgün"
    ENERJIK = "⚡ Enerjik"
    SAKIN = "🧘 Sakin"
    ROMANTIK = "💕 Romantik"
    NOSTALJIK = "🌅 Nostaljik"
    SINIRLI = "😤 Sinirli"
    GENEL = "🎵 Genel"

@dataclass
class ApiYanit:
    basarili: bool
    icerik: Optional[str] = None
    hata: Optional[str] = None

class MelodiFinder:
    
    def __init__(self):
        self.bot = telebot.TeleBot(BotAyarlari.BOT_TOKEN, parse_mode='HTML')
        self.log_ayarla()
        self.komutlari_kaydet()
        
    def log_ayarla(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('melodifinder.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def komutlari_kaydet(self):
        self.bot.message_handler(commands=['start'])(self.basla_komutu)
        self.bot.message_handler(commands=['help'])(self.yardim_komutu)
        self.bot.message_handler(commands=['moods'])(self.ruh_halleri_goster)
        self.bot.message_handler(commands=['hakkinda'])(self.hakkinda_komutu)
        self.bot.message_handler(func=lambda m: True)(self.muzik_istegi_isle)
        
    def basla_komutu(self, mesaj):
        karsilama_metni = """
🎼 <b>MelodiFinder Pro</b> 🎼
<i>Developed by @YourUsername</i>

Merhaba! Ben senin kişisel müzik keşif asistanınım. 

✨ <b>Nasıl Çalışır?</b>
• Ruh halini anlat
• Sana Türkçe şarkılar önerelim
• Her öneride detaylı analiz yapıyorum

🎵 <b>Komutlar:</b>
/help - Yardım menüsü
/moods - Ruh hali örnekleri  
/hakkinda - Geliştirici bilgileri

<i>Şu an nasıl hissediyorsun?</i>
        """
        
        self.bot.reply_to(mesaj, karsilama_metni)
        self.logger.info(f"Yeni kullanıcı: {mesaj.from_user.username or mesaj.from_user.id}")
        
    def yardim_komutu(self, mesaj):
        yardim_metni = """
🆘 <b>MelodiFinder Pro - Yardım</b>

<b>🎯 Nasıl Kullanırım?</b>
Sadece ruh halini yaz! Örneğin:
• "Mutluyum ve dans etmek istiyorum"
• "Hüzünlü hissediyorum"
• "Aşık oldum"

<b>🎨 Özellikler:</b>
✅ AI tabanlı öneriler
✅ Ruh hali analizi
✅ Türkçe müzik odaklı
✅ 3 farklı tarz

<b>💡 İpucu:</b> Detaylı yazdıkça daha iyi öneriler alırsın!
        """
        
        self.bot.reply_to(mesaj, yardim_metni)
        
    def ruh_halleri_goster(self, mesaj):
        ruh_halleri_metni = """
🎭 <b>Ruh Hali Örnekleri</b>

""" + "\n".join([f"• {ruh_hali.value}" for ruh_hali in RuhHaliEmojileri]) + """

<i>Kendi kelimelerinle de ifade edebilirsin!</i>
        """
        
        self.bot.reply_to(mesaj, ruh_halleri_metni)

    def hakkinda_komutu(self, mesaj):
        hakkinda_metni = """
👨‍💻 <b>MelodiFinder Pro</b>

<b>🚀 Geliştirici:</b> @YourUsername
<b>📱 Platform:</b> Telegram Bot API
<b>🤖 AI Engine:</b> Google Gemini 1.5
<b>🎵 Özellik:</b> Türkçe Müzik Önerileri

<b>💡 Vizyon:</b>
Herkesin ruh haline uygun müzik keşfetmesini sağlamak.

<b>🔗 İletişim:</b>
Öneriler için bana yazabilirsiniz!
        """
        
        self.bot.reply_to(mesaj, hakkinda_metni)
    
    def muzik_prompt_olustur(self, kullanici_girisi: str) -> str:
        return f"""
Sen MelodiFinder Pro'nun AI müzik danışmanısın. Kullanıcının ruh haline göre Türkçe şarkı önerileri yapacaksın.

Kullanıcının Ruh Hali: "{kullanici_girisi}"

3 farklı müzik önerisi yap. Her biri şu KESIN formatta olsun:

🎵 <b>Öneri 1</b>
🎭 <b>Ruh Hali:</b> [Analiz]
🎼 <b>Tür:</b> [Müzik türü]
🎤 <b>Şarkı:</b> [Şarkı Adı - Sanatçı]
💫 <b>Neden:</b> [Kısa açıklama]

KURALLAR:
- Sadece Türkçe şarkılar
- Link yok, sadece şarkı adı ve sanatçı
- Her öneri farklı tür
- HTML formatı kullan
        """
    
    def gemini_istek_gonder(self, prompt: str) -> ApiYanit:
        basliklar = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": BotAyarlari.GEMINI_API_KEY
        }

        veri = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 800,
                "topP": 0.95,
                "topK": 40
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            ]
        }

        for deneme in range(BotAyarlari.MAKSIMUM_DENEME):
            try:
                yanit = requests.post(
                    BotAyarlari.GEMINI_URL, 
                    headers=basliklar, 
                    json=veri, 
                    timeout=BotAyarlari.ZAMAN_ASIMI
                )
                
                if yanit.status_code == 200:
                    veri_yanit = yanit.json()
                    if "candidates" in veri_yanit and veri_yanit["candidates"]:
                        icerik = veri_yanit["candidates"][0]["content"]["parts"][0]["text"]
                        return ApiYanit(basarili=True, icerik=icerik)
                    else:
                        return ApiYanit(basarili=False, hata="API'den geçerli yanıt alınamadı")
                else:
                    self.logger.warning(f"API Hatası (Deneme {deneme + 1}): {yanit.status_code}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Zaman aşımı (Deneme {deneme + 1})")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"İstek hatası (Deneme {deneme + 1}): {str(e)}")
            
            if deneme < BotAyarlari.MAKSIMUM_DENEME - 1:
                time.sleep(2 ** deneme)
                
        return ApiYanit(basarili=False, hata="API'ye erişim sağlanamadı")
    
    def muzik_istegi_isle(self, mesaj):
        kullanici_girisi = mesaj.text.strip()
        
        if not kullanici_girisi:
            self.bot.reply_to(mesaj, "🤔 Ruh halini biraz daha anlatabilir misin?")
            return
            
        yukleniyor_mesaji = self.bot.reply_to(mesaj, "🎵 MelodiFinder çalışıyor... ✨")
        
        try:
            prompt = self.muzik_prompt_olustur(kullanici_girisi)
            api_yaniti = self.gemini_istek_gonder(prompt)
            
            if api_yaniti.basarili:
                yanit_metni = f"🎼 <b>MelodiFinder Pro Önerileri</b> 🎼\n\n{api_yaniti.icerik}\n\n💫 <i>Developed by @YourUsername</i>\n🎵 <i>Keyifli dinlemeler!</i>"
                self.bot.edit_message_text(yanit_metni, mesaj.chat.id, yukleniyor_mesaji.message_id)
                
                self.logger.info(f"Başarılı öneri: {mesaj.from_user.username or mesaj.from_user.id}")
                
            else:
                hata_metni = "❌ <b>Üzgünüm!</b>\n\nŞu an önerilerimi hazırlayamıyorum. Lütfen tekrar dener misin?\n\n🎵 <i>MelodiFinder Pro yakında döner!</i>"
                self.bot.edit_message_text(hata_metni, mesaj.chat.id, yukleniyor_mesaji.message_id)
                
                self.logger.error(f"API Hatası: {api_yaniti.hata}")
                
        except Exception as e:
            hata_metni = "⚠️ <b>Beklenmeyen hata</b>\n\nLütfen tekrar dener misin?\n\n💻 <i>@YourUsername ile iletişime geçebilirsin</i>"
            try:
                self.bot.edit_message_text(hata_metni, mesaj.chat.id, yukleniyor_mesaji.message_id)
            except:
                self.bot.reply_to(mesaj, hata_metni)
                
            self.logger.error(f"Genel hata: {str(e)}")
    
    def calistir(self):
        self.logger.info("🎵 MelodiFinder Pro başlatılıyor...")
        
        try:
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            self.logger.critical(f"Bot çalıştırma hatası: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        bot = MelodiFinder()
        bot.calistir()
    except KeyboardInterrupt:
        print("\n🎵 MelodiFinder Pro kapatılıyor...")
    except Exception as e:
        print(f"❌ Kritik hata: {str(e)}")