"""A reproducible comparison of the previous draft and the audited calculation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def calculate_audit():
    data = json.loads((ROOT / 'calculated.json').read_text())
    baseline = json.loads((ROOT / 'calculation_baseline_r12.json').read_text())
    rows = []
    keys = ['output_kwh', 'chemical_kwh', 'wmtc_equiv', 'utility_equiv',
            'end_soc', 't_peak', 'stop_reason', 'available_fraction']
    for row in data['rows']:
        scenarios = {}
        for scenario, result in row['simulations'].items():
            previous = baseline['rows'].get(row['id'], {}).get(scenario)
            scenarios[scenario] = None if result is None else {
                **{key: result[key] for key in keys},
                'previous_output_kwh': None if previous is None else previous['output_kwh'],
                'previous_wmtc_equiv': None if previous is None else previous['wmtc_equiv'],
                'delta_wmtc_km': None if previous is None else result['wmtc_equiv'] - previous['wmtc_equiv'],
            }
        rows.append(dict(id=row['id'], model=row['model'], name=row['name'],
                         nominal_kwh_per_block=row['energy'], cells_per_block=row['n'],
                         nominal_wmtc_km_per_block=row['nominal_wmtc'],
                         voltage_basis=row['voltage_basis'], scenarios=scenarios))
    audit = dict(release='20261001-r13', baseline=baseline['release'],
                 baseline_description=baseline['description'],
                 method='Rnom=Nblocks*E_nom/(8.9/80); Rscenario=E_terminal/(8.9/80). The BRP ratio uses stated battery energy, not measured terminal consumption; no WMTC speed trace.',
                 wmtc_index_kwh_km=data['assumptions']['wmtc_index_kwh_km'],
                 utility_index_kwh_km=data['assumptions']['utility_index_kwh_km'],
                 corrected_curve_extraction=['rs60_5A', 'amprius50q_10A'],
                 low_current_method='Use available complete 1 A curves, interpolate in Ah/current; below the lowest measured current, extrapolate only the voltage drop using DCIR.',
                 uncertainty='Approximate JPEG integration; differences of a few percent are not a reliable rank. Generic OCV models and missing DCIR remain explicitly labelled.',
                 configurations=len(rows), scenarios_per_configuration=36, rows=rows)
    (ROOT / 'dist/calculation_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    return audit

def section(escape):
    audit = json.loads((ROOT / 'dist/calculation_audit.json').read_text())
    def number(value, digits=2):
        return '—' if value is None else f'{value:.{digits}f}'.replace('.', ',')
    cells = []
    for row in audit['rows']:
        result = row['scenarios']['2_5_mixed']
        values = [row['name'], number(row['nominal_kwh_per_block']),
                  number(2 * row['nominal_wmtc_km_per_block'], 1),
                  number(None if result is None else result['previous_wmtc_equiv'], 1),
                  number(None if result is None else result['output_kwh']),
                  number(None if result is None else result['wmtc_equiv'], 1),
                  number(None if result is None else result['end_soc'], 1),
                  'Нет DCIR / применимого рейтинга тока' if result is None else result['stop_reason']]
        cells.append('<tr>' + ''.join('<td>' + escape(v) + '</td>' for v in values) + '</tr>')
    headers = ['Сборка', 'Номинал / блок, кВт·ч', 'Номинальный эквивалент пары, км',
               'Прежний сценарий, км', 'Выдано парой, кВт·ч', 'Исправленный сценарий, км', 'SOC в конце, %', 'Завершение']
    return '<section class="section" id="wmtc-audit"><div class="wrap"><p class="eyebrow">Проверка расчётов · 1 октября 2026</p><h2>WMTC: номинальная и выданная энергия</h2><p>Индекс BRP: 8,9 / 80 = 0,11125 кВт·ч/км. Номинальный эквивалент = число блоков × Eном / индекс; сценарный = Eвыданная / индекс. Первый не учитывает резерв и потери. Второй учитывает выбранную нагрузку, SOC, 3,0 В и ограничения, но не воспроизводит скоростной цикл WMTC. Полезная энергия BRP неизвестна: пересчёт энергии с клемм по этому индексу остаётся условным.</p><p>Исправлены обрывы оцифровки RS60 при 5 А и INR21700/50Q при 10 А. Ранее модель отбрасывала имеющиеся кривые при 1 А и переносила 5–10 А на малые токи только через DCIR; теперь использует доступную низкотоковую кривую. Для двух блоков умеренного сценария это около 1 А/яч. на основном участке. Повторного вычитания DCIR из измеренного напряжения нет.</p><p>Linkdata 65P: 9,734 кВт·ч/блок; номинальный эквивалент пары 175,0 км. Reliance RS60: 8,761 кВт·ч/блок; номинальный эквивалент пары 157,5 км. Сценарные числа ниже, потому что часть энергии остаётся за резервом и отсечкой. Малые различия сопоставимы с погрешностью JPEG и не доказывают преимущество партии.</p><p>Таблица: два одинаковых блока, умеренный сценарий, начало 95% SOC / 25 °C, G=5 Вт/К на блок. «Прежний» — локальный черновик перед этим аудитом. Пустые поля означают нехватку данных. <a href="calculation_audit.json">Скачать аудит всех 33 конфигураций и 36 сочетаний режима (JSON)</a>.</p><div class="table-wrap"><table><thead><tr>' + ''.join('<th>' + escape(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(cells) + '</tbody></table></div></div></section>'

if __name__ == '__main__':
    result = calculate_audit()
    print('Calculation audit:', result['configurations'], 'configurations, 36 scenarios each')
