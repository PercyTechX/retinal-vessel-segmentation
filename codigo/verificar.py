"""Revisar el crecimiento, las métricas y las máscaras."""

import csv
import numpy as np

from datos import (BASE, METODOS, calcular_metricas, leer_caso, leer_imagen,
                   leer_json, listar_casos)
from metodos import crecer_desde_semillas


def comprobar(condicion, mensaje):
    """Avisar si una comprobación falla."""
    if not condicion:
        raise ValueError(mensaje)


def verificar_ejemplos():
    """Probar semillas y vecinos con ejemplos pequeños."""
    candidatos = np.zeros((7, 7), bool)
    candidatos[1, 1] = candidatos[2, 2] = candidatos[3, 3] = candidatos[0, 6] = True
    semillas = np.zeros_like(candidatos)
    semillas[1, 1] = True
    crecimiento = crecer_desde_semillas(semillas, candidatos)
    comprobar(crecimiento.sum() == 3 and crecimiento[3, 3] and not crecimiento[0, 6],
              'El crecimiento debe seguir diagonales y rechazar componentes sin semillas.')
    comprobar(not np.any(crecer_desde_semillas(np.zeros_like(semillas), candidatos)),
              'Sin semillas el crecimiento debe ser vacío.')
    referencia = np.array([[1, 1], [0, 0]], bool)
    prediccion = np.array([[1, 0], [1, 0]], bool)
    campo = np.ones_like(referencia)
    metricas = calcular_metricas(prediccion, referencia, campo)
    comprobar(metricas['dice'] == 0.5 and metricas['iou'] == 1 / 3,
              'El ejemplo conocido debe dar Dice 0,5 e IoU 1/3.')
    comprobar(calcular_metricas(referencia, referencia, campo)['dice'] == 1,
              'La coincidencia perfecta debe dar Dice 1.')
    # Comprobamos que el fondo exterior no afecte las métricas.
    campo[1, 0] = False
    comprobar(calcular_metricas(prediccion, referencia, campo)['falsos_positivos'] == 0,
              'La evaluación debe excluir el exterior del campo visual.')


def principal():
    verificar_ejemplos()
    destino = BASE / 'resultados/evaluacion'
    seleccion = leer_json(destino / 'seleccion.json')
    comprobar(seleccion == leer_json(BASE / 'resultados/ajuste/seleccion.json'),
              'La selección evaluada debe coincidir con la elegida en desarrollo.')
    parametros = seleccion['experimento']
    with (destino / 'metricas.csv').open() as archivo:
        filas = list(csv.DictReader(archivo))
    rutas = listar_casos()
    esperados = {(ruta.stem, metodo) for ruta in rutas for metodo in METODOS}
    comprobar(len(filas) == 90 and {(f['caso'], f['metodo']) for f in filas} == esperados,
              'Se esperan 90 filas sin duplicados ni casos faltantes.')
    registros = {(f['caso'], f['metodo']): f for f in filas}

    # Revisamos las máscaras guardadas y recalculamos sus métricas.
    for ruta in rutas:
        _, referencia, campo = leer_caso(ruta)
        for metodo in METODOS:
            mascara = leer_imagen(BASE / 'predicted_masks' / metodo / f'{ruta.stem}.png')
            comprobar(mascara.shape == referencia.shape, f'Tamaño incorrecto: {ruta.stem}')
            comprobar(np.all((mascara == 0) | (mascara == 255)), f'Máscara no binaria: {ruta.stem}')
            comprobar(not np.any(mascara[~campo]), f'Predicción exterior: {ruta.stem}')
            metricas = calcular_metricas(mascara > 0, referencia, campo)
            fila = registros[ruta.stem, metodo]
            for nombre in ['dice', 'iou']:
                comprobar(abs(metricas[nombre] - float(fila[nombre])) < 1e-12,
                          f'Métrica incompatible con PNG: {ruta.stem}, {metodo}, {nombre}')
            particion = 'desarrollo' if ruta.stem in parametros['casos_desarrollo'] else 'evaluacion'
            comprobar(fila['particion'] == particion, f'Partición incorrecta: {ruta.stem}')
    for metodo in METODOS:
        comprobar(len(list((BASE / 'predicted_masks' / metodo).glob('*.png'))) == 45,
                  f'Se requieren 45 máscaras para {metodo}')
    mensaje = ('Correcto: crecimiento por 8 vecinos y rechazo de regiones sin semillas; '
               'métricas conocidas; 90 máscaras binarias al tamaño original; '
               'exterior nulo; métricas recalculadas desde PNG; particiones y selección comprobadas.\n')
    (destino / 'VERIFICACION.txt').write_text(mensaje, encoding='utf-8')
    print(mensaje, flush=True)


if __name__ == '__main__':
    principal()
