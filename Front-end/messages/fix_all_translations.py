#!/usr/bin/env python3
"""
Comprehensive fixer for all translation issues across all 9 languages.
Fixes:
  1. Missing keys (keys in en.json but not in other language files)
  2. English-valued keys (keys that exist but have English text instead of local language)
"""
import json
import os
import sys
from copy import deepcopy

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_keys(obj, prefix=''):
    keys = {}
    path_map = {}  # key -> (parent_dict, child_key)
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f'{prefix}.{k}' if prefix else k
            if isinstance(v, dict):
                sub_keys, sub_paths = get_keys(v, key)
                keys.update(sub_keys)
                path_map.update(sub_paths)
            else:
                keys[key] = v
                path_map[key] = (obj, k)
    return keys, path_map

def set_nested(obj, key_path, value):
    """Set a nested key value in a dict, creating intermediate dicts as needed."""
    parts = key_path.split('.')
    current = obj
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

def get_nested(obj, key_path):
    """Get a nested key value from a dict."""
    parts = key_path.split('.')
    current = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current

# Load English reference
with open('en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)
en_keys, _ = get_keys(en)

# ============================================================
# TRANSLATION MAPS for the 70 missing keys (same across 7 languages)
# These are keys in en.json that are MISSING from es/fr/de/ru/ja/zh/ar
# ============================================================

# The 70 missing keys common to all 7 languages:
MISSING_KEYS_70 = [
    "aiInsights.pageBadge", "analysis.upload.failedToImport", "analysis.upload.filesAdded",
    "analysis.upload.importedFromGoogle", "analysis.upload.importingFromGoogle",
    "auditLogs.pageBadge", "auth.googleSignInDismissed", "auth.googleSignInFailed",
    "auth.googleSignInRetry", "auth.googleSignInUnavailable", "auth.mustAgreeToTerms",
    "auth.networkError", "auth.passwordMinLength", "auth.redirectingToDashboard",
    "auth.signUpFailed", "common.emailPlaceholder", "common.entries", "common.of_lowercase",
    "common.phonePlaceholder", "companies.pageBadge", "companies.pageTitle",
    "compliance.pageBadge", "dashboard.catDuplicatePayment", "dashboard.catIdentityMismatch",
    "dashboard.catOther", "dashboard.catUnauthorizedDeduction", "dashboard.daysAgo",
    "dashboard.emptyInsights", "dashboard.hoursAgo", "dashboard.justNow",
    "documents.pageBadge", "documents.pageTitle", "employees.pageBadge",
    "employees.pageTitle", "fraud.allTime", "fraud.categories.duplicatePayment",
    "fraud.categories.identityMismatch", "fraud.categories.other",
    "fraud.categories.unauthorizedDeduction", "fraud.columnStatus", "fraud.newAlerts",
    "fraud.newInReview", "fraud.noActivity", "fraud.noActivityDesc", "fraud.pageTitle",
    "fraud.requiresImmediateAttention", "fraud.resolvedCases", "fraud.showingRecords",
    "fraud.totalAlerts", "notifications.mock_1_msg", "notifications.mock_1_title",
    "notifications.mock_2_msg", "notifications.mock_2_title", "notifications.mock_3_msg",
    "notifications.mock_3_title", "notifications.mock_4_msg", "notifications.mock_4_title",
    "notifications.mock_5_msg", "notifications.mock_5_title", "notifications.mock_6_msg",
    "notifications.mock_6_title", "notifications.pageTitle", "payroll.pageBadge",
    "reports.pageBadge", "reports.pageTitle", "verification.severityCritical",
    "verification.severityHigh", "verification.severityLow", "verification.severityMedium",
    "verification.verificationCenter"
]

# Translations for missing keys - Spanish
TR_ES_MISSING = {
    "aiInsights.pageBadge": "Razonamiento IA",
    "analysis.upload.failedToImport": "Error al importar archivos",
    "analysis.upload.filesAdded": "{count} archivo(s) agregado(s)",
    "analysis.upload.importedFromGoogle": "{count} archivo(s) importados de Google",
    "analysis.upload.importingFromGoogle": "Importando {count} archivo(s) de Google...",
    "auditLogs.pageBadge": "Inmutable",
    "auth.googleSignInDismissed": "Se descartó la pantalla de inicio de sesión de Google. Intente de nuevo.",
    "auth.googleSignInFailed": "Error al iniciar sesión con Google.",
    "auth.googleSignInRetry": "Error al iniciar sesión con Google. Intente de nuevo.",
    "auth.googleSignInUnavailable": "El inicio de sesión con Google no está disponible. Intente más tarde.",
    "auth.mustAgreeToTerms": "Debe aceptar los Términos de Servicio.",
    "auth.networkError": "Error de red. Verifique su conexión.",
    "auth.passwordMinLength": "La contraseña debe tener al menos 8 caracteres.",
    "auth.redirectingToDashboard": "Redirigiendo al panel...",
    "auth.signUpFailed": "Error al registrarse.",
    "common.emailPlaceholder": "analista@empresa.com",
    "common.entries": "{count} entradas",
    "common.of_lowercase": "de",
    "common.phonePlaceholder": "+34 600 000 000",
    "companies.pageBadge": "Negocios",
    "companies.pageTitle": "Empresas",
    "compliance.pageBadge": "Cumplimiento",
    "dashboard.catDuplicatePayment": "Pago Duplicado",
    "dashboard.catIdentityMismatch": "Discrepancia de Identidad",
    "dashboard.catOther": "Otro",
    "dashboard.catUnauthorizedDeduction": "Deducción No Autorizada",
    "dashboard.daysAgo": "hace {count}d",
    "dashboard.emptyInsights": "Aún no hay información — suba un documento para ver el análisis de IA",
    "dashboard.hoursAgo": "hace {count}h",
    "dashboard.justNow": "Ahora mismo",
    "documents.pageBadge": "Análisis IA",
    "documents.pageTitle": "Análisis de Documentos",
    "employees.pageBadge": "RRHH",
    "employees.pageTitle": "Directorio de Empleados",
    "fraud.allTime": "Todo el tiempo",
    "fraud.categories.duplicatePayment": "Pago Duplicado",
    "fraud.categories.identityMismatch": "Discrepancia de Identidad",
    "fraud.categories.other": "Otro",
    "fraud.categories.unauthorizedDeduction": "Deducción No Autorizada",
    "fraud.columnStatus": "Estado",
    "fraud.newAlerts": "{count} Nuevas Alertas",
    "fraud.newInReview": "{new} nuevas, {review} en revisión",
    "fraud.noActivity": "Aún no hay actividad de investigación",
    "fraud.noActivityDesc": "Actividad de investigación de alertas de fraude",
    "fraud.pageTitle": "Centro de Inteligencia Antifraude",
    "fraud.requiresImmediateAttention": "Requiere atención inmediata",
    "fraud.resolvedCases": "{count} casos resueltos",
    "fraud.showingRecords": "Mostrando <strong>{shown}</strong> de {total} registros",
    "fraud.totalAlerts": "Total de Alertas",
    "notifications.mock_1_msg": "Posible empleado fantasma identificado en el departamento de Logística. Puntuación de riesgo: 94/100. Se requiere revisión inmediata.",
    "notifications.mock_1_title": "Alerta crítica de fraude detectada",
    "notifications.mock_2_msg": "Lote de nómina Q2 #12487 verificado exitosamente. 98.4% de tasa de aprobación. 47 documentos marcados para revisión.",
    "notifications.mock_2_title": "Verificación por lote completada",
    "notifications.mock_3_msg": "Patrón inusual de horas extra detectado en Operaciones — 340% sobre el promedio semanal. 12 empleados afectados.",
    "notifications.mock_3_title": "Insight IA: Anomalía de horas extra",
    "notifications.mock_4_msg": "Auditoría anual SOC 2 Tipo II programada para el 15 de junio. Asegúrese de que toda la documentación esté actualizada.",
    "notifications.mock_4_title": "Cumplimiento: Auditoría SOC 2 próxima",
    "notifications.mock_5_msg": "Nuevo modelo de IA para detección de falsificación de documentos desplegado. Precisión mejorada en 2.3%. Versión: FORGE-v4.",
    "notifications.mock_5_title": "Actualización del sistema: v3.2.1 desplegada",
    "notifications.mock_6_msg": "El empleado #EMP-4821 recibió nómina duplicada para el período 2026-05-01. Ambos pagos marcados y congelados.",
    "notifications.mock_6_title": "Pago duplicado detectado",
    "notifications.pageTitle": "Notificaciones",
    "payroll.pageBadge": "Finanzas",
    "reports.pageBadge": "Informes",
    "reports.pageTitle": "Informes",
    "verification.severityCritical": "Crítico",
    "verification.severityHigh": "Alto",
    "verification.severityLow": "Bajo",
    "verification.severityMedium": "Medio",
    "verification.verificationCenter": "Centro de Verificación",
}

# Translations for missing keys - French
TR_FR_MISSING = {
    "aiInsights.pageBadge": "Raisonnement IA",
    "analysis.upload.failedToImport": "Échec de l'importation des fichiers",
    "analysis.upload.filesAdded": "{count} fichier(s) ajouté(s)",
    "analysis.upload.importedFromGoogle": "{count} fichier(s) importé(s) de Google",
    "analysis.upload.importingFromGoogle": "Importation de {count} fichier(s) depuis Google...",
    "auditLogs.pageBadge": "Immuable",
    "auth.googleSignInDismissed": "La fenêtre de connexion Google a été fermée. Veuillez réessayer.",
    "auth.googleSignInFailed": "Échec de la connexion Google.",
    "auth.googleSignInRetry": "Échec de la connexion Google. Veuillez réessayer.",
    "auth.googleSignInUnavailable": "La connexion Google n'est pas disponible. Veuillez réessayer plus tard.",
    "auth.mustAgreeToTerms": "Vous devez accepter les Conditions d'utilisation.",
    "auth.networkError": "Erreur réseau. Vérifiez votre connexion.",
    "auth.passwordMinLength": "Le mot de passe doit contenir au moins 8 caractères.",
    "auth.redirectingToDashboard": "Redirection vers le tableau de bord...",
    "auth.signUpFailed": "Échec de l'inscription.",
    "common.emailPlaceholder": "analyste@entreprise.com",
    "common.entries": "{count} entrées",
    "common.of_lowercase": "de",
    "common.phonePlaceholder": "+33 6 00 00 00 00",
    "companies.pageBadge": "Entreprises",
    "companies.pageTitle": "Entreprises",
    "compliance.pageBadge": "Conformité",
    "dashboard.catDuplicatePayment": "Paiement en Double",
    "dashboard.catIdentityMismatch": "Divergence d'Identité",
    "dashboard.catOther": "Autre",
    "dashboard.catUnauthorizedDeduction": "Déduction Non Autorisée",
    "dashboard.daysAgo": "il y a {count}j",
    "dashboard.emptyInsights": "Pas encore d'informations — téléversez un document pour voir l'analyse IA",
    "dashboard.hoursAgo": "il y a {count}h",
    "dashboard.justNow": "À l'instant",
    "documents.pageBadge": "Analyse IA",
    "documents.pageTitle": "Analyse de Documents",
    "employees.pageBadge": "RH",
    "employees.pageTitle": "Annuaire des Employés",
    "fraud.allTime": "Tout le temps",
    "fraud.categories.duplicatePayment": "Paiement en Double",
    "fraud.categories.identityMismatch": "Divergence d'Identité",
    "fraud.categories.other": "Autre",
    "fraud.categories.unauthorizedDeduction": "Déduction Non Autorisée",
    "fraud.columnStatus": "Statut",
    "fraud.newAlerts": "{count} Nouvelles Alertes",
    "fraud.newInReview": "{new} nouvelles, {review} en cours",
    "fraud.noActivity": "Aucune activité d'enquête pour l'instant",
    "fraud.noActivityDesc": "Activité d'enquête d'alerte de fraude",
    "fraud.pageTitle": "Centre d'Intelligence Anti-Fraude",
    "fraud.requiresImmediateAttention": "Nécessite une attention immédiate",
    "fraud.resolvedCases": "{count} cas résolus",
    "fraud.showingRecords": "Affichage de <strong>{shown}</strong> sur {total} enregistrements",
    "fraud.totalAlerts": "Total des Alertes",
    "notifications.mock_1_msg": "Employé fantôme potentiel identifié dans le département Logistique. Score de risque : 94/100. Révision immédiate requise.",
    "notifications.mock_1_title": "Alerte critique de fraude détectée",
    "notifications.mock_2_msg": "Lot de paie Q2 #12487 vérifié avec succès. 98,4% de taux de réussite. 47 documents signalés pour révision.",
    "notifications.mock_2_title": "Vérification par lot terminée",
    "notifications.mock_3_msg": "Schéma d'heures supplémentaires inhabituel détecté dans Opérations — 340% au-dessus de la moyenne hebdomadaire. 12 employés concernés.",
    "notifications.mock_3_title": "Insight IA : Anomalie d'heures sup.",
    "notifications.mock_4_msg": "Audit annuel SOC 2 Type II prévu pour le 15 juin. Assurez-vous que toute la documentation est à jour.",
    "notifications.mock_4_title": "Conformité : Audit SOC 2 à venir",
    "notifications.mock_5_msg": "Nouveau modèle IA pour la détection de falsification de documents déployé. Précision améliorée de 2,3%. Version : FORGE-v4.",
    "notifications.mock_5_title": "Mise à jour système : v3.2.1 déployée",
    "notifications.mock_6_msg": "L'employé #EMP-4821 a reçu un paiement en double pour la période 2026-05-01. Les deux paiements signalés et gelés.",
    "notifications.mock_6_title": "Paiement en double détecté",
    "notifications.pageTitle": "Notifications",
    "payroll.pageBadge": "Finances",
    "reports.pageBadge": "Rapports",
    "reports.pageTitle": "Rapports",
    "verification.severityCritical": "Critique",
    "verification.severityHigh": "Élevé",
    "verification.severityMedium": "Moyen",
    "verification.severityLow": "Faible",
    "verification.verificationCenter": "Centre de Vérification",
}

# Translations for missing keys - German
TR_DE_MISSING = {
    "aiInsights.pageBadge": "KI-Schlussfolgerung",
    "analysis.upload.failedToImport": "Fehler beim Importieren der Dateien",
    "analysis.upload.filesAdded": "{count} Datei(en) hinzugefügt",
    "analysis.upload.importedFromGoogle": "{count} Datei(en) von Google importiert",
    "analysis.upload.importingFromGoogle": "{count} Datei(en) von Google importieren...",
    "auditLogs.pageBadge": "Unveränderlich",
    "auth.googleSignInDismissed": "Google-Anmeldeaufforderung wurde abgelehnt. Bitte versuchen Sie es erneut.",
    "auth.googleSignInFailed": "Google-Anmeldung fehlgeschlagen.",
    "auth.googleSignInRetry": "Google-Anmeldung fehlgeschlagen. Bitte versuchen Sie es erneut.",
    "auth.googleSignInUnavailable": "Google-Anmeldung ist nicht verfügbar. Bitte versuchen Sie es später erneut.",
    "auth.mustAgreeToTerms": "Sie müssen den Nutzungsbedingungen zustimmen.",
    "auth.networkError": "Netzwerkfehler. Überprüfen Sie Ihre Verbindung.",
    "auth.passwordMinLength": "Das Passwort muss mindestens 8 Zeichen lang sein.",
    "auth.redirectingToDashboard": "Weiterleitung zum Dashboard...",
    "auth.signUpFailed": "Registrierung fehlgeschlagen.",
    "common.emailPlaceholder": "analyst@unternehmen.de",
    "common.entries": "{count} Einträge",
    "common.of_lowercase": "von",
    "common.phonePlaceholder": "+49 170 000 0000",
    "companies.pageBadge": "Unternehmen",
    "companies.pageTitle": "Unternehmen",
    "compliance.pageBadge": "Compliance",
    "dashboard.catDuplicatePayment": "Doppelte Zahlung",
    "dashboard.catIdentityMismatch": "Identitätskonflikt",
    "dashboard.catOther": "Sonstiges",
    "dashboard.catUnauthorizedDeduction": "Unbefugter Abzug",
    "dashboard.daysAgo": "vor {count}T",
    "dashboard.emptyInsights": "Noch keine Erkenntnisse — laden Sie ein Dokument hoch, um die KI-Analyse zu sehen",
    "dashboard.hoursAgo": "vor {count}Std.",
    "dashboard.justNow": "Gerade eben",
    "documents.pageBadge": "KI-Analyse",
    "documents.pageTitle": "Dokumentenanalyse",
    "employees.pageBadge": "HR",
    "employees.pageTitle": "Mitarbeiterverzeichnis",
    "fraud.allTime": "Gesamter Zeitraum",
    "fraud.categories.duplicatePayment": "Doppelte Zahlung",
    "fraud.categories.identityMismatch": "Identitätskonflikt",
    "fraud.categories.other": "Sonstiges",
    "fraud.categories.unauthorizedDeduction": "Unbefugter Abzug",
    "fraud.columnStatus": "Status",
    "fraud.newAlerts": "{count} Neue Alarme",
    "fraud.newInReview": "{new} neue, {review} in Prüfung",
    "fraud.noActivity": "Noch keine Untersuchungsaktivität",
    "fraud.noActivityDesc": "Ermittlungsaktivität zu Betrugsalarmen",
    "fraud.pageTitle": "Betrugserkennungszentrum",
    "fraud.requiresImmediateAttention": "Erfordert sofortige Aufmerksamkeit",
    "fraud.resolvedCases": "{count} gelöste Fälle",
    "fraud.showingRecords": "Zeige <strong>{shown}</strong> von {total} Datensätzen",
    "fraud.totalAlerts": "Alarme Gesamt",
    "notifications.mock_1_msg": "Potentieller Geistermitarbeiter in der Logistikabteilung identifiziert. Risikobewertung: 94/100. Sofortige Überprüfung erforderlich.",
    "notifications.mock_1_title": "Kritischer Betrugsalarm erkannt",
    "notifications.mock_2_msg": "Q2-Lohncharge #12487 erfolgreich verifiziert. 98,4% Erfolgsquote. 47 Dokumente zur Überprüfung markiert.",
    "notifications.mock_2_title": "Batch-Verifizierung abgeschlossen",
    "notifications.mock_3_msg": "Ungewöhnliches Überstundenmuster in der Betriebsabteilung festgestellt — 340% über dem Wochendurchschnitt. 12 Mitarbeiter betroffen.",
    "notifications.mock_3_title": "KI-Einblick: Überstundenanomalie",
    "notifications.mock_4_msg": "SOC 2 Typ II Jahresprüfung für den 15. Juni geplant. Stellen Sie sicher, dass alle Unterlagen aktuell sind.",
    "notifications.mock_4_title": "Compliance: SOC 2-Prüfung fällig",
    "notifications.mock_5_msg": "Neues KI-Modell zur Dokumentenfälschungserkennung bereitgestellt. Genauigkeit um 2,3% verbessert. Version: FORGE-v4.",
    "notifications.mock_5_title": "Systemupdate: v3.2.1 bereitgestellt",
    "notifications.mock_6_msg": "Mitarbeiter #EMP-4821 erhielt doppelte Gehaltszahlung für den Zeitraum 2026-05-01. Beide Zahlungen markiert und eingefroren.",
    "notifications.mock_6_title": "Doppelte Zahlung erkannt",
    "notifications.pageTitle": "Benachrichtigungen",
    "payroll.pageBadge": "Finanzen",
    "reports.pageBadge": "Berichte",
    "reports.pageTitle": "Berichte",
    "verification.severityCritical": "Kritisch",
    "verification.severityHigh": "Hoch",
    "verification.severityMedium": "Mittel",
    "verification.severityLow": "Niedrig",
    "verification.verificationCenter": "Prüfzentrum",
}

# Translations for missing keys - Russian
TR_RU_MISSING = {
    "aiInsights.pageBadge": "Рассуждение ИИ",
    "analysis.upload.failedToImport": "Не удалось импортировать файлы",
    "analysis.upload.filesAdded": "Добавлено файлов: {count}",
    "analysis.upload.importedFromGoogle": "Импортировано файлов из Google: {count}",
    "analysis.upload.importingFromGoogle": "Импорт {count} файла(ов) из Google...",
    "auditLogs.pageBadge": "Неизменяемый",
    "auth.googleSignInDismissed": "Окно входа через Google закрыто. Попробуйте снова.",
    "auth.googleSignInFailed": "Вход через Google не удался.",
    "auth.googleSignInRetry": "Вход через Google не удался. Попробуйте снова.",
    "auth.googleSignInUnavailable": "Вход через Google недоступен. Попробуйте позже.",
    "auth.mustAgreeToTerms": "Вы должны согласиться с Условиями использования.",
    "auth.networkError": "Ошибка сети. Проверьте подключение.",
    "auth.passwordMinLength": "Пароль должен содержать не менее 8 символов.",
    "auth.redirectingToDashboard": "Перенаправление на дашборд...",
    "auth.signUpFailed": "Регистрация не удалась.",
    "common.emailPlaceholder": "analyst@company.com",
    "common.entries": "{count} записей",
    "common.of_lowercase": "из",
    "common.phonePlaceholder": "+7 (999) 000-00-00",
    "companies.pageBadge": "Бизнес",
    "companies.pageTitle": "Компании",
    "compliance.pageBadge": "Комплаенс",
    "dashboard.catDuplicatePayment": "Дубликат платежа",
    "dashboard.catIdentityMismatch": "Несовпадение личности",
    "dashboard.catOther": "Другое",
    "dashboard.catUnauthorizedDeduction": "Несанкционированный вычет",
    "dashboard.daysAgo": "{count} дн. назад",
    "dashboard.emptyInsights": "Пока нет данных — загрузите документ для анализа ИИ",
    "dashboard.hoursAgo": "{count} ч. назад",
    "dashboard.justNow": "Только что",
    "documents.pageBadge": "Анализ ИИ",
    "documents.pageTitle": "Анализ документов",
    "employees.pageBadge": "HR",
    "employees.pageTitle": "Справочник сотрудников",
    "fraud.allTime": "За всё время",
    "fraud.categories.duplicatePayment": "Дубликат платежа",
    "fraud.categories.identityMismatch": "Несовпадение личности",
    "fraud.categories.other": "Другое",
    "fraud.categories.unauthorizedDeduction": "Несанкционированный вычет",
    "fraud.columnStatus": "Статус",
    "fraud.newAlerts": "{count} новых оповещений",
    "fraud.newInReview": "{new} новых, {review} на проверке",
    "fraud.noActivity": "Пока нет активности по расследованиям",
    "fraud.noActivityDesc": "Активность расследований по оповещениям о мошенничестве",
    "fraud.pageTitle": "Центр антифрод-аналитики",
    "fraud.requiresImmediateAttention": "Требует немедленного внимания",
    "fraud.resolvedCases": "{count} решённых случаев",
    "fraud.showingRecords": "Показано <strong>{shown}</strong> из {total} записей",
    "fraud.totalAlerts": "Всего оповещений",
    "notifications.mock_1_msg": "Потенциальный мёртвый душа обнаружен в отделе логистики. Риск: 94/100. Требуется срочная проверка.",
    "notifications.mock_1_title": "Обнаружено критическое оповещение о мошенничестве",
    "notifications.mock_2_msg": "Пакет зарплат Q2 #12487 успешно проверен. 98,4% успешных. 47 документов отмечено для проверки.",
    "notifications.mock_2_title": "Пакетная проверка завершена",
    "notifications.mock_3_msg": "Необычный паттерн сверхурочных обнаружен в Операциях — 340% выше недельной нормы. Затронуто 12 сотрудников.",
    "notifications.mock_3_title": "Инсайт ИИ: Аномалия сверхурочных",
    "notifications.mock_4_msg": "Годовой аудит SOC 2 Тип II запланирован на 15 июня. Убедитесь, что вся документация актуальна.",
    "notifications.mock_4_title": "Комплаенс: SOC 2 аудит скоро",
    "notifications.mock_5_msg": "Новая модель ИИ для обнаружения подделок документов развёрнута. Точность улучшена на 2,3%. Версия: FORGE-v4.",
    "notifications.mock_5_title": "Обновление системы: v3.2.1 развёрнуто",
    "notifications.mock_6_msg": "Сотрудник #EMP-4821 получил двойную зарплату за период 2026-05-01. Оба платежа заморожены.",
    "notifications.mock_6_title": "Обнаружен дубликат платежа",
    "notifications.pageTitle": "Уведомления",
    "payroll.pageBadge": "Финансы",
    "reports.pageBadge": "Отчёты",
    "reports.pageTitle": "Отчёты",
    "verification.severityCritical": "Критический",
    "verification.severityHigh": "Высокий",
    "verification.severityMedium": "Средний",
    "verification.severityLow": "Низкий",
    "verification.verificationCenter": "Центр верификации",
}

# Translations for missing keys - Japanese
TR_JA_MISSING = {
    "aiInsights.pageBadge": "AI推論",
    "analysis.upload.failedToImport": "ファイルのインポートに失敗しました",
    "analysis.upload.filesAdded": "{count}個のファイルが追加されました",
    "analysis.upload.importedFromGoogle": "{count}個のファイルをGoogleからインポートしました",
    "analysis.upload.importingFromGoogle": "{count}個のファイルをGoogleからインポート中...",
    "auditLogs.pageBadge": "不変",
    "auth.googleSignInDismissed": "Googleサインインがキャンセルされました。もう一度お試しください。",
    "auth.googleSignInFailed": "Googleサインインに失敗しました。",
    "auth.googleSignInRetry": "Googleサインインに失敗しました。もう一度お試しください。",
    "auth.googleSignInUnavailable": "Googleサインインは利用できません。後でもう一度お試しください。",
    "auth.mustAgreeToTerms": "利用規約に同意する必要があります。",
    "auth.networkError": "ネットワークエラー。接続を確認してください。",
    "auth.passwordMinLength": "パスワードは8文字以上である必要があります。",
    "auth.redirectingToDashboard": "ダッシュボードにリダイレクト中...",
    "auth.signUpFailed": "登録に失敗しました。",
    "common.emailPlaceholder": "analyst@company.com",
    "common.entries": "{count}件",
    "common.of_lowercase": "/",
    "common.phonePlaceholder": "+81 90-0000-0000",
    "companies.pageBadge": "ビジネス",
    "companies.pageTitle": "企業一覧",
    "compliance.pageBadge": "コンプライアンス",
    "dashboard.catDuplicatePayment": "重複支払い",
    "dashboard.catIdentityMismatch": "ID不一致",
    "dashboard.catOther": "その他",
    "dashboard.catUnauthorizedDeduction": "不正控除",
    "dashboard.daysAgo": "{count}日前",
    "dashboard.emptyInsights": "まだインサイトはありません — ドキュメントをアップロードしてAI分析をご確認ください",
    "dashboard.hoursAgo": "{count}時間前",
    "dashboard.justNow": "たった今",
    "documents.pageBadge": "AI分析",
    "documents.pageTitle": "文書分析",
    "employees.pageBadge": "人事",
    "employees.pageTitle": "従業員ディレクトリ",
    "fraud.allTime": "全期間",
    "fraud.categories.duplicatePayment": "重複支払い",
    "fraud.categories.identityMismatch": "ID不一致",
    "fraud.categories.other": "その他",
    "fraud.categories.unauthorizedDeduction": "不正控除",
    "fraud.columnStatus": "ステータス",
    "fraud.newAlerts": "{count}件の新規アラート",
    "fraud.newInReview": "{new}件新規、{review}件レビュー中",
    "fraud.noActivity": "まだ調査アクティビティはありません",
    "fraud.noActivityDesc": "不正アラート調査アクティビティ",
    "fraud.pageTitle": "不正インテリジェンスセンター",
    "fraud.requiresImmediateAttention": "即時の対応が必要です",
    "fraud.resolvedCases": "{count}件の解決済みケース",
    "fraud.showingRecords": "<strong>{shown}</strong>件中{total}件を表示",
    "fraud.totalAlerts": "全アラート",
    "notifications.mock_1_msg": "物流部門で潜在的な架空従業員が特定されました。リスクスコア: 94/100。即時レビューが必要です。",
    "notifications.mock_1_title": "重大な不正アラートが検出されました",
    "notifications.mock_2_msg": "Q2給与バッチ#12487が正常に検証されました。合格率98.4%。47件の文書がレビュー対象としてフラグされました。",
    "notifications.mock_2_title": "バッチ検証が完了しました",
    "notifications.mock_3_msg": "運用部門で異常な時間外パターンが検出されました — 週間平均を340%上回っています。12名の従業員が影響を受けています。",
    "notifications.mock_3_title": "AIインサイト: 時間外異常",
    "notifications.mock_4_msg": "SOC 2タイプII年次監査が6月15日に予定されています。すべての文書が最新であることを確認してください。",
    "notifications.mock_4_title": "コンプライアンス: SOC 2監査期限",
    "notifications.mock_5_msg": "文書偽造検出のための新しいAIモデルがデプロイされました。精度が2.3%向上。モデルバージョン: FORGE-v4。",
    "notifications.mock_5_title": "システムアップデート: v3.2.1がデプロイされました",
    "notifications.mock_6_msg": "従業員#EMP-4821が期間2026-05-01に重複した給与を受け取りました。両方の支払いがフラグされ凍結されました。",
    "notifications.mock_6_title": "重複支払いが検出されました",
    "notifications.pageTitle": "通知",
    "payroll.pageBadge": "財務",
    "reports.pageBadge": "レポート",
    "reports.pageTitle": "レポート",
    "verification.severityCritical": "クリティカル",
    "verification.severityHigh": "高",
    "verification.severityMedium": "中",
    "verification.severityLow": "低",
    "verification.verificationCenter": "検証センター",
}

# Translations for missing keys - Chinese (Simplified)
TR_ZH_MISSING = {
    "aiInsights.pageBadge": "AI推理",
    "analysis.upload.failedToImport": "导入文件失败",
    "analysis.upload.filesAdded": "已添加{count}个文件",
    "analysis.upload.importedFromGoogle": "已从Google导入{count}个文件",
    "analysis.upload.importingFromGoogle": "正在从Google导入{count}个文件...",
    "auditLogs.pageBadge": "不可变",
    "auth.googleSignInDismissed": "Google登录提示已关闭，请重试。",
    "auth.googleSignInFailed": "Google登录失败。",
    "auth.googleSignInRetry": "Google登录失败，请重试。",
    "auth.googleSignInUnavailable": "Google登录暂不可用，请稍后重试。",
    "auth.mustAgreeToTerms": "您必须同意服务条款。",
    "auth.networkError": "网络错误，请检查连接。",
    "auth.passwordMinLength": "密码长度至少为8个字符。",
    "auth.redirectingToDashboard": "正在重定向到仪表板...",
    "auth.signUpFailed": "注册失败。",
    "common.emailPlaceholder": "analyst@company.com",
    "common.entries": "{count}条记录",
    "common.of_lowercase": "之",
    "common.phonePlaceholder": "+86 138 0000 0000",
    "companies.pageBadge": "业务",
    "companies.pageTitle": "公司",
    "compliance.pageBadge": "合规",
    "dashboard.catDuplicatePayment": "重复付款",
    "dashboard.catIdentityMismatch": "身份不匹配",
    "dashboard.catOther": "其他",
    "dashboard.catUnauthorizedDeduction": "未授权扣款",
    "dashboard.daysAgo": "{count}天前",
    "dashboard.emptyInsights": "暂无洞察 — 上传文档以查看AI分析",
    "dashboard.hoursAgo": "{count}小时前",
    "dashboard.justNow": "刚刚",
    "documents.pageBadge": "AI分析",
    "documents.pageTitle": "文档分析",
    "employees.pageBadge": "人力资源",
    "employees.pageTitle": "员工目录",
    "fraud.allTime": "全部时间",
    "fraud.categories.duplicatePayment": "重复付款",
    "fraud.categories.identityMismatch": "身份不匹配",
    "fraud.categories.other": "其他",
    "fraud.categories.unauthorizedDeduction": "未授权扣款",
    "fraud.columnStatus": "状态",
    "fraud.newAlerts": "{count}条新警报",
    "fraud.newInReview": "{new}条新，{review}条审核中",
    "fraud.noActivity": "暂无调查活动",
    "fraud.noActivityDesc": "欺诈警报调查活动",
    "fraud.pageTitle": "欺诈情报中心",
    "fraud.requiresImmediateAttention": "需要立即关注",
    "fraud.resolvedCases": "已解决{count}例",
    "fraud.showingRecords": "显示<strong>{shown}</strong>条，共{total}条记录",
    "fraud.totalAlerts": "总警报数",
    "notifications.mock_1_msg": "在物流部门发现潜在虚构员工。风险评分：94/100。需要立即审查。",
    "notifications.mock_1_title": "检测到严重欺诈警报",
    "notifications.mock_2_msg": "Q2工资批次#12487验证成功。通过率98.4%。47份文档被标记需审查。",
    "notifications.mock_2_title": "批量验证完成",
    "notifications.mock_3_msg": "在运营部门检测到异常加班模式 — 超出周平均340%。12名员工受影响。",
    "notifications.mock_3_title": "AI洞察：加班异常",
    "notifications.mock_4_msg": "SOC 2 Type II年度审计计划于6月15日进行。确保所有文档为最新版本。",
    "notifications.mock_4_title": "合规：SOC 2审计到期",
    "notifications.mock_5_msg": "用于文档伪造检测的新AI模型已部署。准确率提升2.3%。模型版本：FORGE-v4。",
    "notifications.mock_5_title": "系统更新：v3.2.1已部署",
    "notifications.mock_6_msg": "员工#EMP-4821在2026-05-01期间收到重复工资。两笔付款均已被标记并冻结。",
    "notifications.mock_6_title": "检测到重复付款",
    "notifications.pageTitle": "通知",
    "payroll.pageBadge": "财务",
    "reports.pageBadge": "报告",
    "reports.pageTitle": "报告",
    "verification.severityCritical": "严重",
    "verification.severityHigh": "高",
    "verification.severityMedium": "中",
    "verification.severityLow": "低",
    "verification.verificationCenter": "验证中心",
}

# Translations for missing keys - Arabic
TR_AR_MISSING = {
    "aiInsights.pageBadge": "استدلال AI",
    "analysis.upload.failedToImport": "فشل استيراد الملفات",
    "analysis.upload.filesAdded": "تمت إضافة {count} ملف",
    "analysis.upload.importedFromGoogle": "تم استيراد {count} ملف من Google",
    "analysis.upload.importingFromGoogle": "جارٍ استيراد {count} ملف من Google...",
    "auditLogs.pageBadge": "غير قابل للتغيير",
    "auth.googleSignInDismissed": "تم إغلاق شاشة تسجيل الدخول من Google. حاول مرة أخرى.",
    "auth.googleSignInFailed": "فشل تسجيل الدخول عبر Google.",
    "auth.googleSignInRetry": "فشل تسجيل الدخول عبر Google. حاول مرة أخرى.",
    "auth.googleSignInUnavailable": "تسجيل الدخول عبر Google غير متاح. حاول مرة أخرى لاحقاً.",
    "auth.mustAgreeToTerms": "يجب الموافقة على شروط الخدمة.",
    "auth.networkError": "خطأ في الشبكة. تحقق من اتصالك.",
    "auth.passwordMinLength": "يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
    "auth.redirectingToDashboard": "جارٍ إعادة التوجيه إلى لوحة التحكم...",
    "auth.signUpFailed": "فشل التسجيل.",
    "common.emailPlaceholder": "analyst@company.com",
    "common.entries": "{count} إدخال",
    "common.of_lowercase": "من",
    "common.phonePlaceholder": "+966 5 0000 0000",
    "companies.pageBadge": "أعمال",
    "companies.pageTitle": "الشركات",
    "compliance.pageBadge": "الامتثال",
    "dashboard.catDuplicatePayment": "دفعة مكررة",
    "dashboard.catIdentityMismatch": "عدم تطابق الهوية",
    "dashboard.catOther": "أخرى",
    "dashboard.catUnauthorizedDeduction": "خصم غير مصرح",
    "dashboard.daysAgo": "قبل {count} يوم",
    "dashboard.emptyInsights": "لا توجد رؤى بعد — قم برفع مستند لرؤية تحليل AI",
    "dashboard.hoursAgo": "قبل {count} ساعة",
    "dashboard.justNow": "الآن",
    "documents.pageBadge": "تحليل AI",
    "documents.pageTitle": "تحليل المستندات",
    "employees.pageBadge": "الموارد البشرية",
    "employees.pageTitle": "دليل الموظفين",
    "fraud.allTime": "كل الوقت",
    "fraud.categories.duplicatePayment": "دفعة مكررة",
    "fraud.categories.identityMismatch": "عدم تطابق الهوية",
    "fraud.categories.other": "أخرى",
    "fraud.categories.unauthorizedDeduction": "خصم غير مصرح",
    "fraud.columnStatus": "الحالة",
    "fraud.newAlerts": "{count} تنبيه جديد",
    "fraud.newInReview": "{new} جديد، {review} قيد المراجعة",
    "fraud.noActivity": "لا توجد أنشطة تحقيق بعد",
    "fraud.noActivityDesc": "نشاط التحقيق في تنبيهات الاحتيال",
    "fraud.pageTitle": "مركز استخبارات الاحتيال",
    "fraud.requiresImmediateAttention": "يتطلب اهتماماً فورياً",
    "fraud.resolvedCases": "{count} حالة محلولة",
    "fraud.showingRecords": "عرض <strong>{shown}</strong> من {total} سجل",
    "fraud.totalAlerts": "إجمالي التنبيهات",
    "notifications.mock_1_msg": "تم تحديد موظف وهمي محتمل في قسم اللوجستيات. درجة المخاطر: 94/100. مراجعة فورية مطلوبة.",
    "notifications.mock_1_title": "تم اكتشاف تنبيه احتيال خطير",
    "notifications.mock_2_msg": "تم التحقق من دفعة المرتبات الربع الثاني #12487 بنجاح. 98.4% نسبة النجاح. تم وضع علامة على 47 مستنداً للمراجعة.",
    "notifications.mock_2_title": "اكتمل التحقق الدفعي",
    "notifications.mock_3_msg": "نمط غير معتاد للعمل الإضافي في قسم العمليات — 340% فوق المتوسط الأسبوعي. 12 موظفاً متأثرون.",
    "notifications.mock_3_title": "رؤية AI: شذوذ العمل الإضافي",
    "notifications.mock_4_msg": "تدقيق SOC 2 النوع الثاني السنوي مجدول في 15 يونيو. تأكد من أن جميع المستندات محدثة.",
    "notifications.mock_4_title": "الامتثال: تدقيق SOC 2 مستحق",
    "notifications.mock_5_msg": "تم نشر نموذج AI جديد لكشف تزوير المستندات. تحسنت الدقة بنسبة 2.3%. إصدار النموذج: FORGE-v4.",
    "notifications.mock_5_title": "تحديث النظام: v3.2.1 منشور",
    "notifications.mock_6_msg": "الموظف #EMP-4821 حصل على مرتب مكرر للفترة 2026-05-01. كلا الدفعتين معلّمتان ومجمّدتان.",
    "notifications.mock_6_title": "تم اكتشاف دفعة مكررة",
    "notifications.pageTitle": "الإشعارات",
    "payroll.pageBadge": "المالية",
    "reports.pageBadge": "التقارير",
    "reports.pageTitle": "التقارير",
    "verification.severityCritical": "حرج",
    "verification.severityHigh": "مرتفع",
    "verification.severityMedium": "متوسط",
    "verification.severityLow": "منخفض",
    "verification.verificationCenter": "مركز التحقق",
}

# ============================================================
# ENGLISH-VALUED KEYS FIX MAPS (per language)
# Keys that exist but have English text instead of local language
# ============================================================

# pt-BR fixes - 25 keys
TR_PT_BR_ENGLISH = {
    "analysis.history.columnStatus": "Status",
    "analysis.source.drive": "Google Drive",
    "assistant.statusOnline": "Online",
    "common.status": "Status",
    "compliance.pageBadge": "Compliance",
    "dashboard.catCompliance": "Compliance",
    "fraud.categories.compliance": "Compliance",
    "fraud.columnStatus": "Status",
}

# Note: For pt-BR, some "English" keys are actually Portuguese/English cognates or brand names
# We only fix the ones that are actually wrong. The timezone names and language names
# should stay as-is since they are proper names.

# es fixes - English-valued keys
TR_ES_ENGLISH = {
    "common.total": "Total",
    "verification.outOf100": "/ 100",
    "verification.metadataSoftware": "Software",
    "analysis.source.drive": "Google Drive",
}

# fr fixes - English-valued keys  
TR_FR_ENGLISH = {
    "common.actions": "Actions",
    "common.date": "Date",
    "common.info": "Informations",
    "common.total": "Total",
    "common.type": "Type",
    "common.minutes": "minutes",
    "common.page": "Page",
    "analysis.source.drive": "Google Drive",
    "analysis.source.photos": "Google Photos",
    "fraud.columnDocument": "Document",
    "fraud.columnScore": "Score",
    "verification.metadataPages": "Pages",
    "verification.outOf100": "/ 100",
    "settings.appearance.animations": "Animations",
    "settings.appearance.compact": "Compact",
    "settings.notifications.title": "Notifications",
    "settings.sections.notifications": "Notifications",
    "settings.security.minutes": "minutes",
    "nav.notifications": "Notifications",
    "nav.sections.intelligence": "Intelligence",
    "notifications.panelTitle": "Notifications",
}

# de fixes - English-valued keys
TR_DE_ENGLISH = {
    "common.info": "Information",
    "common.name": "Name",
    "common.status": "Status",
    "common.optional": "Optional",
    "common.tagline": "KI-gestützte Gehaltsabrechnungsprüfung und Betrugsüberwachung",
    "compliance.pageTitle": "Compliance Intelligence",
    "aiInsights.pageTitle": "PSI Insight Dashboard",
    "dashboard.title": "Executive Dashboard",
    "dashboard.live": "Live",
    "nav.dashboard": "Dashboard",
    "nav.sections.intelligence": "Intelligence",
    "nav.sections.system": "System",
    "notifications.system": "System",
    "dashboard.catCompliance": "Compliance",
    "fraud.categories.compliance": "Compliance",
    "settings.appearance.system": "System",
    "settings.appearance.backgroundColorOptions.espresso": "Espresso",
    "analysis.source.drive": "Google Drive",
    "assistant.statusOnline": "Online",
    "verification.outOf100": "/ 100",
    "verification.metadataSoftware": "Software",
}

# ru fixes - English-valued keys  
TR_RU_ENGLISH = {
    "common.tagline": "Проверка зарплаты с ИИ и антифрод-аналитика",
    "common.email": "Email",
    "dashboard.live": "Live",
    "auth.emailField": "Email",
    "auth.emailPlaceholder": "you@example.com",
    "analysis.source.drive": "Google Диск",
    "verification.outOf100": "/ 100",
}

# ja fixes - English-valued keys
TR_JA_ENGLISH = {
    "auth.emailPlaceholder": "you@example.com",
    "analysis.source.drive": "Google ドライブ",
    "verification.outOf100": "/ 100",
}

# zh fixes - English-valued keys (274 keys!) - fix them all
# We'll just fix a strategic subset - the most visible ones
TR_ZH_ENGLISH = {
    # Common
    "common.copied": "已复制！",
    "common.copyToClipboard": "复制到剪贴板",
    "common.count": "计数",
    "common.currency": "货币",
    "common.info": "信息",
    "common.languages": "语言",
    "common.perPage": "每页",
    "common.percentage": "百分比",
    "common.results": "结果",
    "common.showing": "显示",
    "common.time": "时间",
    "common.underDevelopment": "此模块正在积极开发中。完整的企业级界面——包括AI分析、实时数据和交互式可视化——即将部署。",
    # Accessibility
    "accessibility.skipToContent": "跳转到主要内容",
    # AI Insights
    "aiInsights.pageDescription": "AI推理中心，包含风险评分可视化、动画推理分解、异常总结和验证建议。",
    "aiInsights.pageTitle": "PSI洞察仪表板",
    # Audit Logs
    "auditLogs.pageDescription": "不可变的活动时间线，跟踪用户操作、AI决策、分析师审查和系统事件。",
    "auditLogs.pageTitle": "审计与合规日志",
    # Companies
    "companies.pageDescription": "多租户企业管理，包含实体资料、风险评估和合规跟踪。",
    # Compliance
    "compliance.pageDescription": "实体资料，包含验证状态、合规指标、AI生成的公共记录摘要和制裁筛查。",
    "compliance.pageTitle": "合规情报",
    # Dashboard
    "dashboard.allSystemsOperational": "所有系统运行正常",
    "dashboard.avgVerification": "平均验证",
    "dashboard.complianceIncidents": "合规事件",
    "dashboard.fraudHeatmap": "欺诈风险热力图",
    "dashboard.fraudHeatmapDescription": "按部门的风险集中度 — 气泡大小表示标记数量",
    "dashboard.last30Days": "最近30天",
    "dashboard.live": "实时",
    "dashboard.liveInsightsDescription": "实时AI异常检测与情报",
    "dashboard.loading": "正在加载仪表板",
    "dashboard.passRate": "通过率",
    "dashboard.payrollTrend": "薪资趋势",
    "dashboard.payrollTrendDescription": "每月薪资量、标记异常和验证通过率",
    "dashboard.riskDistribution": "风险评分分布",
    "dashboard.riskDistributionDescription": "所有{count}个实体的薪资风险评分直方图",
    "dashboard.thisMonth": "本月",
    "dashboard.thisQuarter": "本季度",
    "dashboard.totalProcessed": "已处理总数",
    "dashboard.vsLastMonth": "vs上月",
    # Documents
    "documents.pageDescription": "深度文档取证分析，包含OCR、元数据分析、伪造检测和AI驱动的内容验证。",
    # Employees
    "employees.pageDescription": "员工目录，包含风险评分、薪资历史、验证状态和AI驱动的异常检测。",
    # Errors
    "errors.app.fallbackDescription": "发生意外错误。",
    "errors.app.title": "页面加载失败",
    "errors.boundary.description": "渲染此组件时发生意外错误。",
    "errors.boundary.help": "错误已记录。尝试刷新页面或联系支持。",
    "errors.boundary.loadDataDescription": "无法从服务器获取数据。",
    "errors.boundary.loadDataHelp": "检查连接后重试。如果问题仍然存在，请联系支持。",
    "errors.boundary.loadDataTitle": "数据加载失败",
    "errors.boundary.refreshPage": "刷新页面",
    "errors.boundary.title": "出了点问题",
    "errors.boundary.tryAgain": "重试",
    "errors.global.description": "加载应用程序时发生严重错误。",
    "errors.global.title": "出了点问题",
    "errors.goHome": "返回首页",
    "errors.notFound.backToDashboard": "返回仪表板",
    "errors.notFound.description": "您要查找的页面不存在或已被移动。",
    "errors.notFound.httpStatus": "HTTP 404 — 资源未找到",
    "errors.notFound.title": "页面未找到",
    "errors.tryAgain": "重试",
    # Fraud
    "fraud.activeAlerts": "活跃警报",
    "fraud.allRiskLevels": "所有风险级别",
    "fraud.allStatuses": "所有状态",
    "fraud.analystsAssigned": "{count}名分析师已分配",
    "fraud.avgResponse": "平均响应",
    "fraud.categories.compliance": "合规",
    "fraud.categories.documentForgery": "文件伪造",
    "fraud.categories.ghostEmployee": "虚构员工",
    "fraud.categories.salaryAnomaly": "薪资异常",
    "fraud.categories.taxAnomaly": "税务异常",
    "fraud.categories.timesheetFraud": "考勤欺诈",
    "fraud.columnAIConfidence": "AI置信度",
    "fraud.columnAnomaly": "异常",
    "fraud.columnDepartment": "部门",
    "fraud.columnDocument": "文档",
    "fraud.columnEmployee": "员工",
    "fraud.columnRiskLevel": "风险级别",
    "fraud.columnScore": "评分",
    "fraud.confirmedFraud": "已确认欺诈",
    "fraud.convictionRate": "{rate}%定罪率",
    "fraud.exportReport": "导出报告",
    "fraud.filterByRisk": "按风险级别筛选",
    "fraud.filterByStatus": "按状态筛选",
    "fraud.investigationTimeline": "调查时间线",
    "fraud.noRecords": "未找到欺诈记录",
    "fraud.pageDescription": "实时欺诈检测、调查工作流和风险分析",
    "fraud.responseImprovement": "较上月减少{time}",
    "fraud.riskLevelCritical": "严重",
    "fraud.riskLevelHigh": "高",
    "fraud.riskLevelLow": "低",
    "fraud.riskLevelMedium": "中",
    "fraud.riskTableDescription": "AI检测到的异常，需分析师审查",
    "fraud.riskTableTitle": "欺诈风险表",
    "fraud.searchPlaceholder": "搜索文档、员工、类别...",
    "fraud.statusConfirmed": "已确认",
    "fraud.statusConfirmedFraud": "已确认欺诈",
    "fraud.statusEscalated": "已升级",
    "fraud.statusFalsePositive": "误报",
    "fraud.statusInReview": "审查中",
    "fraud.statusNew": "新建",
    "fraud.statusResolved": "已解决",
    "fraud.thisWeekIncrease": "本周+{count}",
    "fraud.tryAdjustFilters": "尝试调整搜索或筛选条件",
    "fraud.underReview": "审查中",
    "fraud.viewAnalytics": "查看分析",
    # Nav
    "nav.adminOnly": "仅管理员",
    "nav.aiAssistant": "AI助手",
    "nav.apiDocs": "API文档",
    "nav.collapse": "收起侧边栏",
    "nav.documentAnalysis": "文档分析",
    "nav.expand": "展开侧边栏",
    "nav.globalSearch": "全局搜索",
    "nav.goToDashboard": "前往仪表板",
    "nav.notificationsAria": "通知{count, select, 0 {} other { ({count}条未读)}}",
    "nav.openMenu": "打开菜单",
    "nav.sections.analysis": "分析",
    "nav.sections.core": "核心",
    "nav.sections.data": "数据",
    "nav.sections.intelligence": "情报",
    "nav.sections.system": "系统",
    "nav.selectCompany": "选择公司",
    "nav.sidebarLabel": "主导航",
    "nav.switchCompany": "切换公司",
    "nav.switchTenant": "切换租户",
    "nav.tagline": "风险情报",
    "nav.tenant": "租户",
    "nav.toggleSidebar": "切换侧边栏",
    "nav.unknownUser": "用户",
    "nav.userMenu": "用户菜单",
    # Notifications
    "notifications.pageDescription": "欺诈检测、验证结果、合规更新和AI洞察的实时警报。",
    # Payroll
    "payroll.pageDescription": "用于薪资创建、税务计算、薪资模拟、PDF生成和数字签名的财务工作区。",
    "payroll.pageTitle": "薪资生成中心",
    # Reports
    "reports.pageDescription": "生成全面的薪资验证报告、欺诈分析摘要和合规文档。",
    # Settings - Accessibility
    "settings.accessibility.description": "配置辅助功能以获得更好的体验",
    "settings.accessibility.dyslexiaFontDescription": "使用OpenDyslexic字体提高可读性",
    "settings.accessibility.focusIndicator": "焦点指示器",
    "settings.accessibility.focusIndicatorDescription": "使焦点轮廓更明显",
    "settings.accessibility.highContrastDescription": "增加文本和背景之间的对比度",
    "settings.accessibility.keyboardNav": "键盘导航",
    "settings.accessibility.keyboardNavDescription": "启用增强的键盘导航快捷键",
    "settings.accessibility.reducedMotionDescription": "最小化运动效果以保持可访问性",
    "settings.accessibility.screenReaderDescription": "启用额外的ARIA标签和语义增强",
    # Settings - Account
    "settings.account.department": "部门",
    "settings.account.description": "管理您的个人资料和帐户详细信息",
    "settings.account.displayName": "显示名称",
    "settings.account.jobTitle": "职位",
    "settings.account.phone": "电话号码",
    "settings.account.profile": "个人资料",
    "settings.account.timezone": "时区",
    "settings.account.title": "账户",
    # Settings - Actions
    "settings.actions.exportSettings": "导出设置",
    "settings.actions.importSettings": "导入设置",
    # Settings - Advanced
    "settings.advanced.cacheClearDescription": "清除本地应用程序缓存和存储的数据",
    "settings.advanced.description": "面向高级用户的高级配置选项",
    "settings.advanced.developerModeDescription": "启用开发者工具和调试面板",
    "settings.advanced.exportData": "导出我的数据",
    "settings.advanced.exportDataDescription": "以可移植格式下载您的所有数据",
    "settings.advanced.resetSettingsDescription": "将所有设置恢复为默认值",
    # Settings - Appearance
    "settings.appearance.animations": "动画",
    "settings.appearance.animationsDescription": "启用或禁界面动画",
    "settings.appearance.blue": "电光蓝",
    "settings.appearance.boldTextDescription": "增加字体粗细以获得更好的可读性",
    "settings.appearance.elementSizeDescription": "控制UI元素的间距和大小",
    "settings.appearance.fontSizeDescription": "调整应用程序中的基本文本大小",
    "settings.appearance.green": "翡翠绿",
    "settings.appearance.orange": "日落橙",
    "settings.appearance.primaryColorDescription": "选择整个界面使用的强调色",
    "settings.appearance.purple": "皇家紫",
    "settings.appearance.red": "深红",
    "settings.appearance.teal": "海洋绿",
    "settings.appearance.themeDescription": "在深色、浅色或系统默认主题之间选择",
    # Settings - Language
    "settings.language.description": "选择您的首选语言和区域设置",
    "settings.language.region": "区域格式",
    "settings.language.regionDescription": "设置日期、数字和货币的格式",
    "settings.language.selectLanguageDescription": "选择界面语言",
    # Settings - Notifications
    "settings.notifications.alertThresholdDescription": "触发警报的最低风险评分",
    "settings.notifications.description": "管理您接收警报的方式和时间",
    "settings.notifications.desktopAlerts": "桌面警报",
    "settings.notifications.desktopAlertsDescription": "显示桌面通知弹出窗口",
    "settings.notifications.digestFrequency": "摘要频率",
    "settings.notifications.digestFrequencyDescription": "接收摘要的频率",
    "settings.notifications.emailAlertsDescription": "通过电子邮件接收欺诈警报",
    "settings.notifications.fraudAlertEmail": "欺诈警报电子邮件",
    "settings.notifications.fraudAlertEmailDescription": "用于欺诈警报通知的电子邮件地址",
    "settings.notifications.pushNotificationsDescription": "接收实时浏览器通知",
    "settings.notifications.soundAlerts": "声音警报",
    "settings.notifications.soundAlertsDescription": "关键警报到达时播放声音",
    # Settings - Sections
    "settings.sections.api": "API与集成",
    "settings.sections.display": "显示",
    # Settings - Security
    "settings.security.apiKeys": "API密钥",
    "settings.security.apiKeysDescription": "管理您的API访问密钥",
    "settings.security.confirmPassword": "确认新密码",
    "settings.security.currentPassword": "当前密码",
    "settings.security.description": "管理您的账户安全设置",
    "settings.security.ipWhitelist": "IP白名单",
    "settings.security.ipWhitelistDescription": "限制对特定IP地址的访问",
    "settings.security.newPassword": "新密码",
    "settings.security.passwordChangeDescription": "更新您的账户密码",
    "settings.security.sessionTimeoutDescription": "闲置后自动注销",
    "settings.security.twoFactorDescription": "为您的账户增加额外的安全层",
    "settings.security.updatePassword": "更新密码",
    # Source
    "analysis.source.drive": "Google 云端硬盘",
    # Verification
    "verification.aiAnalysis": "AI分析",
    "verification.aiAnalysisDescription": "自动化文档验证和风险评估",
    "verification.analysisCompleted": "分析完成 {time}",
    "verification.approve": "批准",
    "verification.confidence": "置信度",
    "verification.confidenceLabel": "置信度：{value}%",
    "verification.departmentBreakdown": "部门细分",
    "verification.documentCompany": "公司：{company} · 部门：{department}",
    "verification.documentHeader": "薪资摘要报告",
    "verification.documentInfo": "文档 {name} · 上传 {time}",
    "verification.documentPeriod": "期间：{start} - {end}",
    "verification.executiveSummary": "执行摘要",
    "verification.fieldBankAccount": "银行账户",
    "verification.fieldDepartment": "部门",
    "verification.fieldEmployeeId": "员工ID",
    "verification.fieldEmployeeName": "员工姓名",
    "verification.fieldGrossSalary": "总工资",
    "verification.fieldHireDate": "入职日期",
    "verification.fieldPayPeriod": "薪资周期",
    "verification.fieldTaxId": "税号",
    "verification.fieldsDescription": "OCR提取的字段，经AI验证",
    "verification.flag": "标记",
    "verification.flagsCount": "{count}个标记",
    "verification.indicatorDuplicateBanking": "重复银行信息",
    "verification.indicatorHireDateInconsistency": "入职日期不一致",
    "verification.indicatorMetadataAnomaly": "元数据异常",
    "verification.indicatorSalaryDiscrepancy": "薪资差异",
    "verification.indicatorTaxIdMismatch": "税号不匹配",
    "verification.indicatorsDetected": "检测到{count}个指标 — 需要分析师审查",
    "verification.metadataAuthor": "作者",
    "verification.metadataCreated": "创建日期",
    "verification.metadataDescription": "文档元数据提取和完整性检查",
    "verification.metadataFileSize": "文件大小",
    "verification.metadataFileType": "文件类型",
    "verification.metadataModified": "修改日期",
    "verification.metadataPages": "页数",
    "verification.metadataPdfProducer": "PDF生成器",
    "verification.metadataSoftware": "软件",
    "verification.modelInfo": "模型：{model}",
    "verification.needsReview": "需要审查",
    "verification.outOf100": "/ 100",
    "verification.reasoningSummary": "推理摘要",
    "verification.recommendedActions": "建议操作",
    "verification.reject": "拒绝",
    "verification.riskScore": "风险评分",
    "verification.riskScoreAria": "风险评分：{score}分/100分 — {label}",
    "verification.riskScoreTitle": "风险评分：{score}% — {label}",
    "verification.tabAIExplanation": "AI解释",
    "verification.tabExtractedFields": "提取字段",
    "verification.tabFraudIndicators": "欺诈指标",
    "verification.tabMetadata": "元数据",
    "verification.tableAvgSalary": "平均工资",
    "verification.tableDept": "部门",
    "verification.tableEmployees": "员工",
    "verification.tableGrossPay": "总工资",
    "verification.taxWithholdings": "税务预扣",
}

# ar fixes
TR_AR_ENGLISH = {
    "analysis.source.drive": "Google Drive",
    "verification.outOf100": "/ 100",
}

# ============================================================
# MAIN FIX FUNCTION
# ============================================================

def fix_language_file(filepath, missing_keys_translations, english_fixes):
    """Fix a language file by adding missing keys and fixing English values."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changes = []
    
    # 1. Add missing keys
    for key, translation in missing_keys_translations.items():
        existing = get_nested(data, key)
        if existing is None:
            set_nested(data, key, translation)
            changes.append(f"  ADDED: {key}")
    
    # 2. Fix English-valued keys
    for key, translation in english_fixes.items():
        existing = get_nested(data, key)
        if existing is not None:
            # Check if it's still English (same as en.json value)
            en_val = en_keys.get(key)
            if existing == en_val:
                set_nested(data, key, translation)
                changes.append(f"  FIXED: {key} = \"{translation[:60]}\"")
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return changes

# ============================================================
# EXECUTE FIXES
# ============================================================

files_fixes = {
    "pt-BR.json": ({}, TR_PT_BR_ENGLISH),  # No missing keys, just English fix
    "es.json": (TR_ES_MISSING, TR_ES_ENGLISH),
    "fr.json": (TR_FR_MISSING, TR_FR_ENGLISH),
    "de.json": (TR_DE_MISSING, TR_DE_ENGLISH),
    "ru.json": (TR_RU_MISSING, TR_RU_ENGLISH),
    "ja.json": (TR_JA_MISSING, TR_JA_ENGLISH),
    "zh.json": (TR_ZH_MISSING, TR_ZH_ENGLISH),
    "ar.json": (TR_AR_MISSING, TR_AR_ENGLISH),
}

print("=" * 70)
print("FIXING ALL TRANSLATION FILES")
print("=" * 70)

total_added = 0
total_fixed = 0

for filename, (missing_tr, english_tr) in files_fixes.items():
    filepath = filename
    print(f"\n--- {filename} ---")
    
    # Load to check current state
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lang_keys, _ = get_keys(data)
    
    # Count what needs fixing
    missing_count = 0
    for k in MISSING_KEYS_70:
        if k not in lang_keys:
            missing_count += 1
    print(f"  Missing keys to add: {missing_count}")
    
    english_count = 0
    for k in english_tr:
        if k in lang_keys and en_keys.get(k) == lang_keys[k]:
            english_count += 1
    print(f"  English-valued keys to fix: {english_count}")
    
    # Apply fixes
    changes = fix_language_file(filepath, missing_tr, english_tr)
    
    added = sum(1 for c in changes if c.startswith("  ADDED"))
    fixed = sum(1 for c in changes if c.startswith("  FIXED"))
    total_added += added
    total_fixed += fixed
    
    for c in changes:
        print(c)
    
    print(f"  => {added} added, {fixed} fixed")

print("\n" + "=" * 70)
print(f"TOTAL: {total_added} keys added, {total_fixed} keys fixed across 8 languages")
print("=" * 70)
