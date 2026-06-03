# -*- coding: utf-8 -*-
"""
Add Google Drive i18n section to all language files.
"""
import json
import os

DRIVE_EN = {
    "title": "Upload from Google Drive",
    "description": "Sign in with Google to browse and import your Drive documents",
    "connecting": "Connecting to Google...",
    "importing": "Importing {count} file(s)...",
    "imported": "{count} file(s) imported",
    "importSuccess": "Files ready for analysis",
    "failedToImport": "Failed to import files",
    "tokenExpired": "Session expired. Please try again.",
    "pleaseWait": "Do not close this page",
    "tryAgain": "Try again or use device upload",
    "errorTitle": "Connection failed",
    "notConfigured": "Google Drive is not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID in .env.local",
    "someSkipped": "Imported {count} file(s). Maximum file limit reached.",
}

TRANSLATIONS = {
    "pt-BR": {
        "title": "Upload do Google Drive",
        "description": "Faça login com o Google para navegar e importar seus documentos do Drive",
        "connecting": "Conectando ao Google...",
        "importing": "Importando {count} arquivo(s)...",
        "imported": "{count} arquivo(s) importado(s)",
        "importSuccess": "Arquivos prontos para análise",
        "failedToImport": "Falha ao importar arquivos",
        "tokenExpired": "Sessão expirada. Tente novamente.",
        "pleaseWait": "Não feche esta página",
        "tryAgain": "Tente novamente ou use upload do dispositivo",
        "errorTitle": "Conexão falhou",
        "notConfigured": "Google Drive não configurado. Defina NEXT_PUBLIC_GOOGLE_CLIENT_ID no .env.local",
        "someSkipped": "{count} arquivo(s) importado(s). Limite máximo atingido.",
    },
    "es": {
        "title": "Subir desde Google Drive",
        "description": "Inicia sesión con Google para explorar e importar tus documentos de Drive",
        "connecting": "Conectando con Google...",
        "importing": "Importando {count} archivo(s)...",
        "imported": "{count} archivo(s) importado(s)",
        "importSuccess": "Archivos listos para análisis",
        "failedToImport": "Error al importar archivos",
        "tokenExpired": "Sesión expirada. Inténtalo de nuevo.",
        "pleaseWait": "No cierres esta página",
        "tryAgain": "Inténtalo de nuevo o usa subida desde dispositivo",
        "errorTitle": "Conexión fallida",
        "notConfigured": "Google Drive no configurado. Define NEXT_PUBLIC_GOOGLE_CLIENT_ID en .env.local",
        "someSkipped": "{count} archivo(s) importado(s). Límite máximo alcanzado.",
    },
    "fr": {
        "title": "Importer depuis Google Drive",
        "description": "Connectez-vous avec Google pour parcourir et importer vos documents Drive",
        "connecting": "Connexion à Google...",
        "importing": "Import de {count} fichier(s)...",
        "imported": "{count} fichier(s) importé(s)",
        "importSuccess": "Fichiers prêts pour analyse",
        "failedToImport": "Échec de l'import des fichiers",
        "tokenExpired": "Session expirée. Veuillez réessayer.",
        "pleaseWait": "Ne fermez pas cette page",
        "tryAgain": "Réessayez ou utilisez le téléchargement depuis l'appareil",
        "errorTitle": "Échec de la connexion",
        "notConfigured": "Google Drive non configuré. Définissez NEXT_PUBLIC_GOOGLE_CLIENT_ID dans .env.local",
        "someSkipped": "{count} fichier(s) importé(s). Limite maximale atteinte.",
    },
    "de": {
        "title": "Von Google Drive hochladen",
        "description": "Melden Sie sich bei Google an, um Ihre Drive-Dokumente zu durchsuchen und zu importieren",
        "connecting": "Verbindung zu Google wird hergestellt...",
        "importing": "{count} Datei(en) werden importiert...",
        "imported": "{count} Datei(en) importiert",
        "importSuccess": "Dateien bereit für die Analyse",
        "failedToImport": "Fehler beim Importieren der Dateien",
        "tokenExpired": "Sitzung abgelaufen. Bitte versuchen Sie es erneut.",
        "pleaseWait": "Schließen Sie diese Seite nicht",
        "tryAgain": "Versuchen Sie es erneut oder laden Sie vom Gerät hoch",
        "errorTitle": "Verbindung fehlgeschlagen",
        "notConfigured": "Google Drive nicht konfiguriert. Setzen Sie NEXT_PUBLIC_GOOGLE_CLIENT_ID in .env.local",
        "someSkipped": "{count} Datei(en) importiert. Maximale Anzahl erreicht.",
    },
    "ru": {
        "title": "Загрузить из Google Диска",
        "description": "Войдите в Google, чтобы просматривать и импортировать документы с Диска",
        "connecting": "Подключение к Google...",
        "importing": "Импорт {count} файла(ов)...",
        "imported": "{count} файла(ов) импортировано",
        "importSuccess": "Файлы готовы к анализу",
        "failedToImport": "Не удалось импортировать файлы",
        "tokenExpired": "Сессия истекла. Попробуйте снова.",
        "pleaseWait": "Не закрывайте эту страницу",
        "tryAgain": "Попробуйте снова или используйте загрузку с устройства",
        "errorTitle": "Ошибка подключения",
        "notConfigured": "Google Диск не настроен. Укажите NEXT_PUBLIC_GOOGLE_CLIENT_ID в .env.local",
        "someSkipped": "Импортировано {count} файла(ов). Достигнут лимит.",
    },
    "ja": {
        "title": "Google ドライブからアップロード",
        "description": "Google にサインインして Drive のドキュメントを参照・インポート",
        "connecting": "Google に接続中...",
        "importing": "{count} ファイルをインポート中...",
        "imported": "{count} ファイルをインポートしました",
        "importSuccess": "分析準備完了",
        "failedToImport": "ファイルのインポートに失敗しました",
        "tokenExpired": "セッションの有効期限が切れました。もう一度お試しください。",
        "pleaseWait": "このページを閉じないでください",
        "tryAgain": "もう一度試すか、デバイスからアップロードしてください",
        "errorTitle": "接続に失敗しました",
        "notConfigured": "Google ドライブが設定されていません。.env.local で NEXT_PUBLIC_GOOGLE_CLIENT_ID を設定してください",
        "someSkipped": "{count} ファイルをインポートしました。最大ファイル数に達しました。",
    },
    "zh": {
        "title": "从 Google 云端硬盘上传",
        "description": "登录 Google 以浏览和导入您的云端硬盘文档",
        "connecting": "正在连接 Google...",
        "importing": "正在导入 {count} 个文件...",
        "imported": "已导入 {count} 个文件",
        "importSuccess": "文件已准备好进行分析",
        "failedToImport": "文件导入失败",
        "tokenExpired": "会话已过期，请重试。",
        "pleaseWait": "请勿关闭此页面",
        "tryAgain": "请重试或使用设备上传",
        "errorTitle": "连接失败",
        "notConfigured": "Google 云端硬盘未配置。请在 .env.local 中设置 NEXT_PUBLIC_GOOGLE_CLIENT_ID",
        "someSkipped": "已导入 {count} 个文件，已达到最大文件限制。",
    },
    "ar": {
        "title": "رفع من Google Drive",
        "description": "سجل دخولك إلى Google لتصفح واستيراد مستندات Drive الخاصة بك",
        "connecting": "جاري الاتصال بـ Google...",
        "importing": "جاري استيراد {count} ملف...",
        "imported": "تم استيراد {count} ملف",
        "importSuccess": "الملفات جاهزة للتحليل",
        "failedToImport": "فشل استيراد الملفات",
        "tokenExpired": "انتهت الجلسة. حاول مرة أخرى.",
        "pleaseWait": "لا تغلق هذه الصفحة",
        "tryAgain": "حاول مرة أخرى أو استخدم الرفع من الجهاز",
        "errorTitle": "فشل الاتصال",
        "notConfigured": "Google Drive غير مهيأ. قم بتعيين NEXT_PUBLIC_GOOGLE_CLIENT_ID في .env.local",
        "someSkipped": "تم استيراد {count} ملف. تم الوصول إلى الحد الأقصى.",
    },
}

def main():
    msgs_dir = os.path.join(os.path.dirname(__file__))
    for fname in sorted(os.listdir(msgs_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(msgs_dir, fname)
        lang = fname.replace(".json", "")

        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)

        # Determine drive data for this language
        if lang == "en":
            drive_data = DRIVE_EN
        else:
            drive_data = TRANSLATIONS.get(lang, DRIVE_EN)

        analysis = d.get("analysis", {})
        keys = list(analysis.keys())

        # Insert drive between 'source' and 'pipeline'
        if "source" in keys and "pipeline" in keys:
            new_analysis = {}
            for k in keys:
                new_analysis[k] = analysis[k]
                if k == "source":
                    new_analysis["drive"] = drive_data
            d["analysis"] = new_analysis
        else:
            # Fallback: append at end
            analysis["drive"] = drive_data
            d["analysis"] = analysis

        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)

        print(f"OK {lang}: drive section added")

    print("\nAll language files updated!")

if __name__ == "__main__":
    main()
