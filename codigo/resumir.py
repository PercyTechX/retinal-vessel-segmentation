"""Resumir resultados y compararlos con V1."""

import csv
from statistics import mean, stdev

from datos import BASE, METODOS, guardar_csv, leer_caso, leer_imagen, listar_casos
from ejecutar import crear_panel
import cv2
import matplotlib.pyplot as plt

NOMBRES = {'umbral_adaptativo': 'Umbral adaptativo', 'crecimiento_regiones': 'Crecimiento de regiones'}


def principal():
    destino = BASE / 'resultados/evaluacion'
    with (destino / 'metricas.csv').open() as archivo:
        filas = list(csv.DictReader(archivo))
    for fila in filas:
        for metrica in ['dice', 'iou']:
            fila[metrica] = float(fila[metrica])

    # Resumimos desarrollo y evaluación por separado.
    resumen = []
    for particion in ['desarrollo', 'evaluacion']:
        for metodo in METODOS:
            for grupo in ['todos', 'h', 'dr', 'g']:
                registros = [f for f in filas if f['particion'] == particion and f['metodo'] == metodo
                             and (grupo == 'todos' or f['grupo'] == grupo)]
                resumen.append({'particion': particion, 'metodo': metodo, 'grupo': grupo,
                                'cantidad': len(registros),
                                'dice_promedio': mean(f['dice'] for f in registros),
                                'dice_desviacion': stdev(f['dice'] for f in registros),
                                'iou_promedio': mean(f['iou'] for f in registros),
                                'iou_desviacion': stdev(f['iou'] for f in registros)})
    guardar_csv(destino / 'resumen.csv', resumen)

    # Leemos los resultados anteriores para compararlos.
    comparacion = []
    referencia_v1 = BASE / 'referencias/version_1/resumen.csv'
    if not referencia_v1.is_file():
        referencia_v1 = BASE.parent / 'version_1/resultados/evaluacion/resumen.csv'
    with referencia_v1.open() as archivo:
        for fila in csv.DictReader(archivo):
            if fila['particion'] == 'evaluacion' and fila['grupo'] == 'todos':
                comparacion.append({'version': 'V1', 'metodo': fila['metodo'],
                                    'dice_promedio': float(fila['dice_promedio']),
                                    'iou_promedio': float(fila['iou_promedio'])})
    principales = [f for f in resumen if f['particion'] == 'evaluacion' and f['grupo'] == 'todos']
    for fila in principales:
        comparacion.append({'version': 'V2', 'metodo': fila['metodo'],
                            'dice_promedio': fila['dice_promedio'], 'iou_promedio': fila['iou_promedio']})
    guardar_csv(destino / 'comparacion_versiones.csv', comparacion)

    # Graficamos los resultados de cada método.
    figura, ejes = plt.subplots(1, 2, figsize=(11, 4))
    valores = [[f['dice'] for f in filas if f['particion'] == 'evaluacion'
                and f['metodo'] == metodo] for metodo in METODOS]
    ejes[0].boxplot(valores, tick_labels=['Adaptativo V2', 'Regiones V2'])
    ejes[0].set(title='Variación de Dice en 39 casos', ylim=(0, 1), ylabel='Dice')
    etiquetas = ['V1 morfológico', 'V1 adaptativo', 'V2 adaptativo', 'V2 regiones']
    ejes[1].bar(etiquetas, [f['dice_promedio'] for f in comparacion], color=['#8596a6', '#8596a6', '#167d8d', '#167d8d'])
    ejes[1].set(title='Comparación descriptiva sobre los mismos casos', ylim=(0, 1), ylabel='Dice medio')
    ejes[1].tick_params(axis='x', labelrotation=20)
    figura.tight_layout()
    figura.savefig(destino / 'comparacion_versiones.png', dpi=150)
    plt.close(figura)

    # Mostramos el mejor y el peor caso del crecimiento.
    registros = [f for f in filas if f['particion'] == 'evaluacion' and f['metodo'] == 'crecimiento_regiones']
    rutas = {p.stem: p for p in listar_casos()}
    ejemplos = [('mayor_dice_regiones', max(registros, key=lambda f: f['dice'])),
                ('menor_dice_regiones', min(registros, key=lambda f: f['dice']))]
    for etiqueta, fila in ejemplos:
        caso = fila['caso']
        imagen, referencia, _ = leer_caso(rutas[caso])
        contenidos = [('Original', cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)), ('Referencia manual', referencia)]
        contenidos += [(NOMBRES[m], leer_imagen(BASE / 'predicted_masks' / m / f'{caso}.png') > 0)
                       for m in METODOS]
        crear_panel(contenidos, destino / f'{etiqueta}_{caso}.png', columnas=2)

    # Guardamos las cifras y sus limitaciones en el informe.
    texto = ['# Resultados de la versión 2', '',
             'Seis casos para elegir parámetros y 39 para comparar (13 por grupo). '
             'La evaluación usa todo el campo visual original, a resolución original. '
             'Cada imagen tiene el mismo peso. Los 39 casos ya se habían evaluado '
             'en V1: esta es una comparación exploratoria sobre la misma partición, '
             'no una prueba independiente nueva.', '',
             '## Métodos de la versión 2', '',
             '| Método | Dice medio ± desviación | IoU medio ± desviación |',
             '| --- | --- | --- |']
    for fila in principales:
        texto.append(f"| {NOMBRES[fila['metodo']]} | {fila['dice_promedio']:.4f} ± {fila['dice_desviacion']:.4f} | "
                     f"{fila['iou_promedio']:.4f} ± {fila['iou_desviacion']:.4f} |")
    texto += ['', '## Comparación con V1', '', '| Versión | Método | Dice | IoU |', '| --- | --- | --- | --- |']
    for fila in comparacion:
        texto.append(f"| {fila['version']} | {fila['metodo']} | {fila['dice_promedio']:.4f} | {fila['iou_promedio']:.4f} |")
    mejor_anterior = max(f['dice_promedio'] for f in comparacion if f['version'] == 'V1')
    mejor_actual = max(f['dice_promedio'] for f in comparacion if f['version'] == 'V2')
    texto += ['', f'Diferencia del mejor promedio V2 respecto del mejor V1: {mejor_actual - mejor_anterior:+.4f} de Dice. '
              'Es una diferencia descriptiva. Se cambiaron varias decisiones; no permite atribuir el cambio a una sola.', '',
              '## Desglose por grupo', '', '| Grupo | Método | Dice | IoU |', '| --- | --- | --- | --- |']
    for fila in resumen:
        if fila['particion'] == 'evaluacion' and fila['grupo'] != 'todos':
            texto.append(f"| {fila['grupo']} | {NOMBRES[fila['metodo']]} | {fila['dice_promedio']:.4f} | {fila['iou_promedio']:.4f} |")
    texto += ['', '## Alcance y limitaciones', '',
              '- Las semillas se eligen automáticamente desde la imagen, sin anotaciones manuales.',
              '- El crecimiento usa un predicado fijo sobre oscuridad local y conectividad 8. No adapta la media de cada región.',
              '- Ambos métodos comparten evidencia de contraste local; difieren en que el crecimiento exige conexión a semillas.',
              '- Una franja de 3 píxeles de la imagen reducida no recibe predicciones. No se excluye de las métricas.',
              '- Los vasos finos pueden perderse por reescalado o limpieza; el crecimiento puede propagar falsas detecciones.',
              '- Desarrollo es pequeño y no aleatorio. No se demuestra generalización clínica.',
              '- El registro de preparación compartida está en `../ajuste/preparaciones.csv`.', '',
              'Ejemplos seleccionados por mayor y menor Dice de crecimiento entre los 39 casos:', '']
    for etiqueta, fila in ejemplos:
        texto.append(f"- `{etiqueta}_{fila['caso']}.png`: Dice de regiones {fila['dice']:.4f}.")
    (destino / 'INFORME.md').write_text('\n'.join(texto) + '\n', encoding='utf-8')
    print('\n'.join(texto), flush=True)


if __name__ == '__main__':
    principal()
