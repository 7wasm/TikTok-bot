import os
import asyncio
import subprocess
import requests
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ملاحظة: يجب وضع التوكن الخاص بك هنا
BOT_TOKEN = "8086447530:AAFSUFZeICxq1_kZ7mAAGCL-dig63EFiMfU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! أرسل لي رابط بث TikTok المباشر أو اسم المستخدم (مثال: @username) وسأقوم بتسجيله لك."
    )

def get_live_url(identifier):
    """
    محاولة الحصول على رابط البث المباشر باستخدام yt-dlp
    """
    if not identifier.startswith("http"):
        url = f"https://www.tiktok.com/@{identifier.replace('@', '')}/live"
    else:
        url = identifier

    try:
        # استخدام yt-dlp للحصول على رابط البث المباشر (m3u8)
        command = [
            "yt-dlp",
            "--get-url",
            "--format", "best",
            url
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except Exception as e:
        print(f"Error getting URL: {e}")
        return None

async def record_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    identifier = update.message.text.strip()
    await update.message.reply_text(f"جاري التحقق من البث لـ: {identifier}...")

    live_url = get_live_url(identifier)
    
    if not live_url:
        await update.message.reply_text("عذراً، لم أتمكن من العثور على بث مباشر نشط لهذا الحساب أو الرابط غير صحيح.")
        return

    # يمكن للمستخدم إرسال "الرابط مدة_الثواني" لتحديد المدة
    parts = identifier.split()
    duration = "60" # القيمة الافتراضية
    if len(parts) > 1 and parts[1].isdigit():
        duration = parts[1]
        identifier = parts[0]

    await update.message.reply_text(f"تم العثور على البث! جاري بدء التسجيل لمدة {duration} ثانية...")

    # اسم الملف
    filename = f"tiktok_live_{int(asyncio.get_event_loop().time())}.mp4"
    filepath = os.path.join("/home/ubuntu/", filename)

    # استخدام ffmpeg للتسجيل
    ffmpeg_command = [
        "ffmpeg",
        "-i", live_url,
        "-c", "copy",
        "-t", duration, 
        filepath
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await update.message.reply_text("التسجيل جارٍ الآن...")
        stdout, stderr = await process.communicate()

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            await update.message.reply_text("تم الانتهاء من التسجيل! جاري إرسال الملف...")
            await update.message.reply_video(video=open(filepath, 'rb'), caption="إليك تسجيل البث المباشر.")
            # حذف الملف بعد الإرسال لتوفير المساحة
            os.remove(filepath)
        else:
            await update.message.reply_text("فشل التسجيل. قد يكون البث قد انتهى أو حدث خطأ في الاتصال.")
            if os.path.exists(filepath):
                os.remove(filepath)

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التسجيل: {str(e)}")

if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("الرجاء وضع BOT_TOKEN الصحيح في الكود.")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), record_tiktok))
        print("البوت يعمل الآن...")
        app.run_polling()
