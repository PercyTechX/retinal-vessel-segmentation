"""Aplicar los métodos y guardar sus resultados."""

import os
from time import perf_counter

import cv2
import numpy as np

from datos import (BASE, METODOS, calcular_metricas, guardar_csv, guardar_json,
                   leer_caso, leer_json, listar_casos)
from metodos import preparar_imagen, segmentar

os.environ.setdefault('MPLCONFIGDIR', str(BASE / '.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def guardar_imagen(ruta, imagen):
    """Guardar la imagen y comprobar que no falle."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if imagen.dtype == bool:
        imagen = imagen.astype(np.uint8) * 255
    if not cv2.imwrite(str(ruta), imagen):
        raise OSError(f'No se pudo escribir {ruta}')


def crear_panel(contenidos, ruta, columnas=3):
    """Mostrar varias imágenes en una figura."""
    filas = (len(contenidos) + columnas - 1) // columnas
    figura, ejes = plt.subplots(filas, columnas, figsize=(5 * columnas, 3.8 * filas), squeeze=False)
    for eje in ejes.flat:
        eje.axis('off')
    for eje, (titulo, imagen) in zip(ejes.flat, contenidos):
        eje.imshow(imagen, cmap='gray')
        eje.set_title(titulo)
    figura.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(ruta, dpi=140)
    plt.close(figura)


def principal():
    # Cargamos los parámetros elegidos.
    seleccion = leer_json(BASE / 'configuracion/seleccion.json')
    parametros = seleccion['experimento']
    destino = BASE / 'resultados/evaluacion'
    guardar_json(destino / 'seleccion.json', seleccion)
    filas = []
    for ruta in listar_casos():
        imagen, referencia, campo = leer_caso(ruta)
        inicio = perf_counter()
        etapas = preparar_imagen(imagen, campo, parametros, seleccion['corregir_iluminacion'])
        segundos_preparacion = perf_counter() - inicio
        salidas, intermedias = {}, {}
        for metodo in METODOS:
            inicio = perf_counter()
            prediccion, pasos = segmentar(etapas, campo, parametros, metodo, seleccion['metodos'][metodo])
            segundos_metodo = perf_counter() - inicio
            salidas[metodo], intermedias[metodo] = prediccion, pasos
            metricas = calcular_metricas(prediccion, referencia, campo)
            filas.append({'caso': ruta.stem, 'grupo': ruta.stem.split('_')[1],
                          'particion': 'desarrollo' if ruta.stem in parametros['casos_desarrollo'] else 'evaluacion',
                          'metodo': metodo, **metricas, 'segundos_preparacion': segundos_preparacion,
                          'segundos_segmentacion_limpieza_restauracion': segundos_metodo})
            guardar_imagen(BASE / 'predicted_masks' / metodo / f'{ruta.stem}.png', prediccion)

        # Mostramos un caso de desarrollo de cada grupo.
        if ruta.stem in {'01_h', '01_g', '01_dr'}:
            carpeta = BASE / 'resultados/etapas' / ruta.stem
            for nombre in ['verde', 'corregida', 'preparada']:
                guardar_imagen(carpeta / f'{nombre}.png', etapas[nombre])
            for metodo, pasos in intermedias.items():
                for nombre, paso in pasos.items():
                    guardar_imagen(carpeta / f'{nombre}.png', paso)
            crear_panel([
                ('Original', cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)),
                ('Canal verde', etapas['verde']),
                ('Imagen preparada', etapas['preparada']),
                ('Semillas automáticas', intermedias['crecimiento_regiones']['semillas']),
                ('Candidatos para crecer', intermedias['crecimiento_regiones']['candidatos']),
                ('Región crecida (antes de limpiar)', intermedias['crecimiento_regiones']['region_crecida']),
            ], carpeta / 'proceso.png')
            crear_panel([
                ('Original', cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)), ('Referencia manual', referencia),
                ('Umbral adaptativo', salidas['umbral_adaptativo']),
                ('Crecimiento de regiones', salidas['crecimiento_regiones'])
            ], carpeta / 'comparacion.png', columnas=2)
        print(f'Guardado: {ruta.stem}', flush=True)
    guardar_csv(destino / 'metricas.csv', filas)


if __name__ == '__main__':
    principal()
