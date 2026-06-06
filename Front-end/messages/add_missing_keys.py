import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Keys to add with their translations for each locale
new_keys = {
    'auditLogs': {
        'emptyTimelineDescription': {
            'en': 'No events have been recorded yet. Timeline will populate as activities occur.',
            'pt-BR': 'Nenhum evento registrado ainda. A linha do tempo será preenchida conforme as atividades ocorrerem.',
            'es': 'Aún no se han registrado eventos. La línea de tiempo se completará a medida que ocurran actividades.',
            'fr': 'Aucun événement enregistré pour le moment. La chronologie se remplira au fur et à mesure des activités.',
            'de': 'Noch keine Ereignisse aufgezeichnet. Der Zeitverlauf wird gefüllt, sobald Aktivitäten auftreten.',
            'ru': 'События еще не записаны. Временная шкала будет заполняться по мере выполнения действий.',
            'ja': 'まだイベントは記録されていません。アクティビティが発生するとタイムラインが表示されます。',
            'zh': '尚未记录任何事件。时间线将随着活动的发生而填充。',
            'ar': 'لم يتم تسجيل أي أحداث بعد. سيتم ملء الجدول الزمني مع حدوث الأنشطة.',
        },
        'activityHeatmapEmpty': {
            'en': 'Activity data will appear here over time.',
            'pt-BR': 'Os dados de atividade aparecerão aqui com o tempo.',
            'es': 'Los datos de actividad aparecerán aquí con el tiempo.',
            'fr': 'Les données d\'activité apparaîtront ici au fil du temps.',
            'de': 'Aktivitätsdaten werden hier mit der Zeit angezeigt.',
            'ru': 'Данные об активности будут отображаться здесь со временем.',
            'ja': 'アクティビティデータは時間の経過とともにここに表示されます。',
            'zh': '活动数据将随时间显示在此处。',
            'ar': 'ستظهر بيانات النشاط هنا بمرور الوقت.',
        },
        'noPatterns': {
            'en': 'No suspicious patterns detected',
            'pt-BR': 'Nenhum padrão suspeito detectado',
            'es': 'No se detectaron patrones sospechosos',
            'fr': 'Aucun motif suspect détecté',
            'de': 'Keine verdächtigen Muster erkannt',
            'ru': 'Подозрительных закономерностей не обнаружено',
            'ja': '不審なパターンは検出されませんでした',
            'zh': '未检测到可疑模式',
            'ar': 'لم يتم اكتشاف أنماط مشبوهة',
        },
        'emptyPatternsDescription': {
            'en': 'No suspicious patterns detected yet. Patterns will appear as the system processes data.',
            'pt-BR': 'Nenhum padrão suspeito detectado ainda. Os padrões aparecerão à medida que o sistema processar os dados.',
            'es': 'Aún no se detectaron patrones sospechosos. Los patrones aparecerán a medida que el sistema procese datos.',
            'fr': 'Aucun motif suspect détecté pour le moment. Les motifs apparaîtront au fur et à mesure que le système traite les données.',
            'de': 'Noch keine verdächtigen Muster erkannt. Muster werden angezeigt, sobald das System Daten verarbeitet.',
            'ru': 'Подозрительных закономерностей пока не обнаружено. Закономерности появятся по мере обработки данных системой.',
            'ja': '不審なパターンはまだ検出されていません。システムがデータを処理するにつれてパターンが表示されます。',
            'zh': '尚未检测到可疑模式。模式将在系统处理数据时出现。',
            'ar': 'لم يتم اكتشاف أنماط مشبوهة بعد. ستظهر الأنماط أثناء معالجة النظام للبيانات.',
        },
    },
    'reports': {
        'noDataAvailable': {
            'en': 'No data available yet. Reports will populate as documents are analyzed.',
            'pt-BR': 'Nenhum dado disponível ainda. Os relatórios serão preenchidos à medida que os documentos forem analisados.',
            'es': 'Aún no hay datos disponibles. Los informes se completarán a medida que se analicen los documentos.',
            'fr': 'Aucune donnée disponible pour le moment. Les rapports se rempliront au fur et à mesure de l\'analyse des documents.',
            'de': 'Noch keine Daten verfügbar. Berichte werden gefüllt, sobald Dokumente analysiert werden.',
            'ru': 'Данные пока недоступны. Отчеты будут заполняться по мере анализа документов.',
            'ja': 'まだデータはありません。ドキュメントが分析されるとレポートが表示されます。',
            'zh': '尚无可用数据。报告将在文档分析后填充。',
            'ar': 'لا توجد بيانات متاحة بعد. سيتم ملء التقارير أثناء تحليل المستندات.',
        },
        'notAvailable': {
            'en': 'N/A',
            'pt-BR': 'N/D',
            'es': 'N/D',
            'fr': 'N/D',
            'de': 'N/V',
            'ru': 'Н/Д',
            'ja': 'N/A',
            'zh': 'N/A',
            'ar': 'غير متاح',
        },
    },
}

locales = ['pt-BR', 'es', 'fr', 'de', 'ru', 'ja', 'zh', 'ar']

# Add to each locale file
for code in locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    changes = 0
    
    # Add auditLogs keys
    for key, translations in new_keys['auditLogs'].items():
        if key not in data.get('auditLogs', {}):
            if 'auditLogs' not in data:
                data['auditLogs'] = {}
            data['auditLogs'][key] = translations[code]
            print(f'  ADDED auditLogs.{key} to {code}: "{translations[code][:50]}..."')
            changes += 1
    
    # Add reports keys
    for key, translations in new_keys['reports'].items():
        if key not in data.get('reports', {}):
            if 'reports' not in data:
                data['reports'] = {}
            data['reports'][key] = translations[code]
            print(f'  ADDED reports.{key} to {code}: "{translations[code][:50]}..."')
            changes += 1
    
    if changes > 0:
        with open(f'{code}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f'  -> Saved {code}.json ({changes} changes)\n')
    else:
        print(f'  {code}: No changes needed\n')

print("=" * 60)
print("VERIFICATION")
print("=" * 60)

# Verify all keys now exist
all_ok = True
for code in ['en'] + locales:
    with open(f'{code}.json', 'rb') as f:
        data = json.load(f)
    
    for ns in ['auditLogs', 'reports']:
        for key in new_keys[ns].keys():
            if key not in data.get(ns, {}):
                print(f'  MISSING [{code}]: {ns}.{key}')
                all_ok = False
            else:
                val = data[ns][key]
                if not val or len(str(val)) == 0:
                    print(f'  EMPTY [{code}]: {ns}.{key}')
                    all_ok = False

if all_ok:
    print('\n*** ALL 6 KEYS NOW EXIST IN ALL 9 LOCALES ***')
else:
    print('\n*** SOME KEYS STILL MISSING ***')
