import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from utils.config import get_token, TELEGRAM_MAX_MSG
from utils.i18n import I18N, t, get_user_lang, USER_LANG
from utils.asr_translate import transcribe_file, translate_text, flag_for_lang
from utils.emotions import detect_emotions, format_emotions
from utils.asr_translate import detect_lang_text, translate_text


class BotApp:
    """
    Telegram bot application (OOP style).
    Encapsulates app creation, handlers, and utilities.
    """

    def __init__(self) -> None:
        self.token = get_token()
        self.app: Application = Application.builder().token(self.token).build()
        self._setup_logging()
        self._register_handlers()

    # ---------- Setup ----------
    def _setup_logging(self) -> None:
        logging.basicConfig(
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            level=logging.INFO,
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initialized BotApp")

    def _register_handlers(self) -> None:
        # Commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_cmd))
        self.app.add_handler(CommandHandler("about", self.about))
        self.app.add_handler(CommandHandler("lang", self.lang_cmd))

        # Language selection callbacks
        self.app.add_handler(
            CallbackQueryHandler(self.on_setlang, pattern=r"^setlang:(es|en)$")
        )

        # Voice
        self.app.add_handler(MessageHandler(filters.VOICE, self.on_voice))

        # Text echo
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo_text)
        )

        # Unknown commands
        self.app.add_handler(MessageHandler(filters.COMMAND, self.unknown))

        # Errors
        self.app.add_error_handler(self.error_handler)

    # ---------- Utilities ----------
    @staticmethod
    def _split_telegram_message(text: str, limit: int = TELEGRAM_MAX_MSG) -> List[str]:
        """Split long text for Telegram."""
        parts = []
        while len(text) > limit:
            cut = text.rfind("\n", 0, limit)
            if cut == -1:
                cut = text.rfind(" ", 0, limit)
            if cut == -1:
                cut = limit
            parts.append(text[:cut])
            text = text[cut:].lstrip()
        if text:
            parts.append(text)
        return parts

    # ---------- Command handlers ----------
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            t(user.id, "welcome", telegram_lang_code=user.language_code)
        )

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            t(user.id, "help", telegram_lang_code=user.language_code)
        )

    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            t(user.id, "about", telegram_lang_code=user.language_code)
        )

    async def lang_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show inline keyboard to select language."""
        user = update.effective_user
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🇪🇸 Español", callback_data="setlang:es"),
                    InlineKeyboardButton(
                        "🇬🇧 English", callback_data="setlang:en"),
                ]
            ]
        )
        await update.message.reply_text(
            t(user.id, "choose_lang", telegram_lang_code=user.language_code),
            reply_markup=kb,
        )

    async def on_setlang(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection via callback."""
        query = update.callback_query
        await query.answer()
        user = query.from_user
        data = query.data or ""
        if data.startswith("setlang:"):
            lang = data.split(":", 1)[1]
            if lang in ("es", "en"):
                USER_LANG[user.id] = lang
                await query.edit_message_text(
                    t(user.id, "lang_set", telegram_lang_code=user.language_code)
                )

    # ---------- Voice handler ----------

    async def on_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        user = update.effective_user
        file_id = msg.voice.file_id
        tg_file = await context.bot.get_file(file_id)

        # Download voice note to a temp file
        with TemporaryDirectory() as td:
            audio_path = Path(td) / "audio.ogg"
            await tg_file.download_to_drive(str(audio_path))
            text, lang, prob = transcribe_file(audio_path)

        if not text:
            await msg.reply_text(
                t(user.id, "no_transcription",
                  telegram_lang_code=user.language_code)
            )
            return

        # UI language preference (for i18n output of emotions)
        user_lang_ui = get_user_lang(user.id, user.language_code)

        # 1) Translate first (en<->es depending on detected speech lang)
        translated, target_lang = translate_text(lang, text)

        # 2) Choose which text to feed into GoEmotions (expects English)
        if target_lang == "es":
            # Source was English -> keep original English transcription
            emotion_text = text
        elif target_lang == "en":
            # Source was Spanish -> use English translation (fallback to original if empty)
            emotion_text = translated or text
        else:
            # Unknown/unchanged language -> safest fallback
            emotion_text = text

        # 3) Detect emotions on the chosen text
        emotions = detect_emotions(emotion_text, top_k=3, threshold=0.30)
        emo_str = format_emotions(
            emotions, ui_lang=user_lang_ui) if emotions else "neutral 😐"

        # 4) Send transcription
        header = t(
            user.id,
            "transcription_header",
            flag=flag_for_lang(lang),
            lang=lang,
            conf=f"{prob:.0f}",
            telegram_lang_code=user.language_code,
        )
        parts = self._split_telegram_message(text)
        await msg.reply_text(header + parts[0])
        for p in parts[1:]:
            await msg.reply_text(p)

        # 5) Send translation if applicable
        if target_lang != "same" and translated:
            flag_t = "🇬🇧" if target_lang == "en" else "🇪🇸" if target_lang == "es" else "🌐"
            t_header = t(
                user.id,
                "translation_header",
                flag=flag_t,
                src=lang,
                tgt=target_lang,
                telegram_lang_code=user.language_code,
            )
            t_parts = self._split_telegram_message(translated)
            await msg.reply_text(t_header + t_parts[0])
            for p in t_parts[1:]:
                await msg.reply_text(p)
        else:
            await msg.reply_text(
                t(user.id, "translation_skipped",
                  telegram_lang_code=user.language_code)
            )

        # 6) Send emotions summary
        await msg.reply_text(
            t(user.id, "emotion_header", emo=emo_str,
              telegram_lang_code=user.language_code)
        )

    async def echo_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        user = update.effective_user
        text = msg.text

        detected_lang = detect_lang_text(text)

        # If language is not supported → stop early
        if detected_lang not in ("en", "es"):
            await msg.reply_text("no procesadas (se omite análisis).")
            return

        # Translate between en <-> es
        translated, target_lang = translate_text(detected_lang, text)

        # Choose text for emotion detection (GoEmotions requires English)
        if detected_lang == "en":
            emotion_text = text  # already English
        elif detected_lang == "es":
            emotion_text = translated or text  # use translation into English
        else:
            emotion_text = text  # safe fallback

        # Detect emotions
        user_lang_ui = get_user_lang(user.id, user.language_code)
        emotions = detect_emotions(emotion_text, top_k=3, threshold=0.30)
        emo_str = format_emotions(
            emotions, ui_lang=user_lang_ui) if emotions else "neutral 😐"

        # 1) Show original text
        flag_src = "🇬🇧" if detected_lang == "en" else "🇪🇸"
        header = t(
            user.id,
            "you_wrote",
            flag=flag_src,
            lang=detected_lang,
            telegram_lang_code=user.language_code,
        )
        await msg.reply_text(f"{header}{text}")

        # 2) Show translation if applicable
        if target_lang != "same" and translated:
            flag_tgt = "🇬🇧" if target_lang == "en" else "🇪🇸"
            t_header = t(
                user.id,
                "translation_header",
                flag=flag_tgt,
                src=detected_lang,
                tgt=target_lang,
                telegram_lang_code=user.language_code,
            )
            await msg.reply_text(f"{t_header}{translated}")

        # 3) Show emotions
        await msg.reply_text(
            t(user.id, "emotion_header", emo=emo_str,
              telegram_lang_code=user.language_code)
        )

    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            t(user.id, "unknown_cmd", telegram_lang_code=user.language_code)
        )

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        # Log but do not crash the app
        self.logger.exception("Unhandled exception: %s", update)

    # ---------- Run ----------
    def run(self) -> None:
        self.logger.info("Bot running with i18n (OOP)…")
        self.app.run_polling()


if __name__ == "__main__":
    BotApp().run()
