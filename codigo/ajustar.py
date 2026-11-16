"""Elegir parámetros con los casos de desarrollo."""

from itertools import product
from statistics import mean

from datos import (BASE, METODOS, calcular_metricas, guardar_csv, guardar_json,
                   leer_caso, leer_json, listar_casos)
from metodos import preparar_imagen, segmentar


def crear_candidatos(experimento):
    """Preparar las opciones del ajuste."""
    candidatos = []
    for correccion in experimento['correcciones_a_comparar']:
        for constante in experimento['constantes_a_comparar']:
            candidatos.append({'id': f'adaptativo_{int(correccion)}_{constante}',
                               'metodo': METODOS[0], 'corregir_iluminacion': correccion,
                               'configuracion': {'constante': constante}})
        for bajo, alto in product(experimento['umbrales_bajos_a_comparar'],
                                  experimento['umbrales_altos_a_comparar']):
            candidatos.append({'id': f'regiones_{int(correccion)}_{bajo}_{alto}',
                               'metodo': METODOS[1], 'corregir_iluminacion': correccion,
                               'configuracion': {'umbral_bajo': bajo, 'umbral_alto': alto}})
    return candidatos


def principal():
    experimento = leer_json(BASE / 'configuracion/experimento.json')
    candidatos = crear_candidatos(experimento)
    rutas = [ruta for ruta in listar_casos() if ruta.stem in experimento['casos_desarrollo']]
    if len(rutas) != 6:
        raise ValueError('Se requieren seis casos de desarrollo.')
    # Guardamos las opciones que vamos a probar.
    destino = BASE / 'resultados/ajuste'
    guardar_json(destino / 'busqueda.json', {'experimento': experimento, 'candidatos': candidatos})
    filas = []
    for ruta in rutas:
        imagen, referencia, campo = leer_caso(ruta)
        for correccion in experimento['correcciones_a_comparar']:
            etapas = preparar_imagen(imagen, campo, experimento, correccion)
            for candidato in candidatos:
                if candidato['corregir_iluminacion'] != correccion:
                    continue
                prediccion, _ = segmentar(etapas, campo, experimento, candidato['metodo'],
                                         candidato['configuracion'])
                metricas = calcular_metricas(prediccion, referencia, campo)
                filas.append({'caso': ruta.stem, 'candidato': candidato['id'],
                              'metodo': candidato['metodo'], 'corregir_iluminacion': correccion,
                              'dice': metricas['dice'], 'iou': metricas['iou']})
        print(f"Desarrollo completado: {ruta.stem} ({len(candidatos)} configuraciones)", flush=True)

    # Elegimos el mejor resultado de cada método.
    resumen = []
    for candidato in candidatos:
        registros = [fila for fila in filas if fila['candidato'] == candidato['id']]
        resumen.append({'candidato': candidato['id'], 'metodo': candidato['metodo'],
                        'corregir_iluminacion': candidato['corregir_iluminacion'],
                        'dice_promedio': mean(f['dice'] for f in registros),
                        'iou_promedio': mean(f['iou'] for f in registros)})
    ganadores = {}
    preparaciones = []
    for correccion in experimento['correcciones_a_comparar']:
        ganadores[correccion] = {}
        for metodo in METODOS:
            mejor = max((fila for fila in resumen if fila['metodo'] == metodo
                         and fila['corregir_iluminacion'] == correccion), key=lambda f: f['dice_promedio'])
            ganadores[correccion][metodo] = mejor
        preparaciones.append({'corregir_iluminacion': correccion,
                              'dice_promedio_de_ambos': mean(f['dice_promedio'] for f in ganadores[correccion].values())})
    # Usamos la misma preparación para ambos métodos.
    # Si hay empate, elegimos la opción más sencilla.
    elegida = max(preparaciones, key=lambda f: f['dice_promedio_de_ambos'])['corregir_iluminacion']
    seleccion = {'experimento': experimento, 'corregir_iluminacion': elegida, 'metodos': {}}
    for metodo in METODOS:
        identificador = ganadores[elegida][metodo]['candidato']
        seleccion['metodos'][metodo] = next(c['configuracion'] for c in candidatos if c['id'] == identificador)
    guardar_csv(destino / 'comparaciones.csv', filas)
    guardar_csv(destino / 'resumen.csv', resumen)
    guardar_csv(destino / 'preparaciones.csv', preparaciones)
    guardar_json(BASE / 'configuracion/seleccion.json', seleccion)
    guardar_json(destino / 'seleccion.json', seleccion)
    print(f'Corrección de iluminación elegida: {elegida}', flush=True)
    print(seleccion['metodos'], flush=True)


if __name__ == '__main__':
    principal()
