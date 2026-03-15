"""
Internationalization (i18n) support for the GitLab Guide chatbot.
Provides translations for static UI labels across supported languages.
"""

SUPPORTED_LANGUAGES: list[str] = ["English", "French", "Spanish", "German", "Japanese"]

TRANSLATIONS: dict[str, dict[str, str]] = {
    "English": {
        "sidebar_title": "GitLab Guide",
        "try_asking": "Try asking",
        "clear_chat": "Clear Chat History",
        "recent_questions": "Recent Questions",
        "people_also_asked": "People also asked",
        "bookmarks": "Bookmarks",
        "export_markdown": "Export as Markdown",
        "export_pdf": "Export as PDF",
        "role_label": "Your Role",
        "font_size_label": "Font Size",
        "language_label": "Language",
        "feedback_prompt": "What could be improved?",
        "onboarding_banner_title": "Welcome to GitLab Guide!",
        "onboarding_banner_body": "Take a quick tour to learn the most important things about working at GitLab.",
        "start_tour": "Start Tour",
        "skip_tour": "Skip",
        "next_question": "Next",
    },
    "French": {
        "sidebar_title": "Guide GitLab",
        "try_asking": "Essayez de demander",
        "clear_chat": "Effacer l'historique",
        "recent_questions": "Questions récentes",
        "people_also_asked": "Les gens ont aussi demandé",
        "bookmarks": "Favoris",
        "export_markdown": "Exporter en Markdown",
        "export_pdf": "Exporter en PDF",
        "role_label": "Votre rôle",
        "font_size_label": "Taille de police",
        "language_label": "Langue",
        "feedback_prompt": "Qu'est-ce qui pourrait être amélioré ?",
        "onboarding_banner_title": "Bienvenue dans GitLab Guide !",
        "onboarding_banner_body": "Faites une visite rapide pour découvrir les points essentiels du travail chez GitLab.",
        "start_tour": "Commencer la visite",
        "skip_tour": "Passer",
        "next_question": "Suivant",
    },
    "Spanish": {
        "sidebar_title": "Guía de GitLab",
        "try_asking": "Intenta preguntar",
        "clear_chat": "Borrar historial",
        "recent_questions": "Preguntas recientes",
        "people_also_asked": "La gente también preguntó",
        "bookmarks": "Marcadores",
        "export_markdown": "Exportar como Markdown",
        "export_pdf": "Exportar como PDF",
        "role_label": "Tu rol",
        "font_size_label": "Tamaño de fuente",
        "language_label": "Idioma",
        "feedback_prompt": "¿Qué se podría mejorar?",
        "onboarding_banner_title": "¡Bienvenido a GitLab Guide!",
        "onboarding_banner_body": "Haz un recorrido rápido para aprender lo más importante sobre trabajar en GitLab.",
        "start_tour": "Iniciar recorrido",
        "skip_tour": "Omitir",
        "next_question": "Siguiente",
    },
    "German": {
        "sidebar_title": "GitLab-Leitfaden",
        "try_asking": "Versuche zu fragen",
        "clear_chat": "Chatverlauf löschen",
        "recent_questions": "Letzte Fragen",
        "people_also_asked": "Andere fragten auch",
        "bookmarks": "Lesezeichen",
        "export_markdown": "Als Markdown exportieren",
        "export_pdf": "Als PDF exportieren",
        "role_label": "Deine Rolle",
        "font_size_label": "Schriftgröße",
        "language_label": "Sprache",
        "feedback_prompt": "Was könnte verbessert werden?",
        "onboarding_banner_title": "Willkommen beim GitLab-Leitfaden!",
        "onboarding_banner_body": "Mache eine kurze Tour, um die wichtigsten Dinge über die Arbeit bei GitLab zu erfahren.",
        "start_tour": "Tour starten",
        "skip_tour": "Überspringen",
        "next_question": "Weiter",
    },
    "Japanese": {
        "sidebar_title": "GitLab ガイド",
        "try_asking": "質問してみましょう",
        "clear_chat": "チャット履歴を消去",
        "recent_questions": "最近の質問",
        "people_also_asked": "他の人も質問しています",
        "bookmarks": "ブックマーク",
        "export_markdown": "Markdownとしてエクスポート",
        "export_pdf": "PDFとしてエクスポート",
        "role_label": "あなたの役割",
        "font_size_label": "フォントサイズ",
        "language_label": "言語",
        "feedback_prompt": "改善できる点は何ですか？",
        "onboarding_banner_title": "GitLab ガイドへようこそ！",
        "onboarding_banner_body": "GitLab での働き方について最も重要なことを学ぶために、簡単なツアーをご覧ください。",
        "start_tour": "ツアーを開始",
        "skip_tour": "スキップ",
        "next_question": "次へ",
    },
}


def t(key: str, lang: str) -> str:
    """
    Look up a translation key for the given language.

    Falls back to English if the key is missing for the requested language.
    Falls back to the key string itself if the English translation is also missing.
    Never raises an exception.
    """
    lang_dict = TRANSLATIONS.get(lang, {})
    if key in lang_dict:
        return lang_dict[key]
    # Fallback to English
    english_dict = TRANSLATIONS.get("English", {})
    if key in english_dict:
        return english_dict[key]
    # Final fallback: return the key itself
    return key
