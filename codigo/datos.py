"""Leer datos y guardar resultados."""

from pathlib import Path
import csv
import json

import cv2
import numpy as np

BASE = Path(__file__).resolve().parents[1]
# Buscamos los datos dentro del paquete.
# Si no están aquí, usamos los datos compartidos.
DATOS = BASE / 'datos' / 'HRF'
if not DATOS.is_dir():
    DATOS = BASE.parent / 'datos_compartidos' / 'HRF'
METODOS = ('umbral_adaptativo', 'crecimiento_regiones')


def leer_json(ruta):
    """Leer un archivo JSON."""
    return json.loads(ruta.read_text(encoding='utf-8'))


def guardar_json(ruta, contenido):
    """Guardar un archivo JSON."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def guardar_csv(ruta, filas):
    """Guardar una tabla CSV."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open('w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def listar_casos():
    """Buscar y comprobar los 45 casos."""
    rutas = sorted(p for p in (DATOS / 'images').iterdir() if p.suffix.lower() == '.jpg')
    esperados = {f'{numero:02}_{grupo}' for numero in range(1, 16) for grupo in ('h', 'dr', 'g')}
    if len(rutas) != 45 or {p.stem for p in rutas} != esperados:
        raise ValueError('HRF debe contener los 45 casos esperados sin duplicados.')
    return rutas


def leer_imagen(ruta, color=False):
    """Leer una imagen y avisar si falla."""
    imagen = cv2.imread(str(ruta), cv2.IMREAD_COLOR if color else cv2.IMREAD_GRAYSCALE)
    if imagen is None:
        raise ValueError(f'No se pudo leer {ruta}')
    return imagen


def leer_caso(ruta):
    """Cargar la imagen, la referencia y el campo visual."""
    imagen = leer_imagen(ruta, color=True)
    referencia = leer_imagen(DATOS / 'manual1' / f'{ruta.stem}.tif') > 0
    campo = leer_imagen(DATOS / 'mask' / f'{ruta.stem}_mask.tif') > 0
    if imagen.shape[:2] != referencia.shape or referencia.shape != campo.shape:
        raise ValueError(f'Dimensiones incompatibles en {ruta.stem}')
    if not np.any(referencia) or not np.any(campo):
        raise ValueError(f'Referencia o campo vacío en {ruta.stem}')
    return imagen, referencia, campo


def calcular_metricas(prediccion, referencia, campo):
    """Calcular Dice e IoU dentro del campo original."""
    predicha, real = prediccion[campo], referencia[campo]
    vp = int(np.count_nonzero(predicha & real))
    fp = int(np.count_nonzero(predicha & ~real))
    fn = int(np.count_nonzero(~predicha & real))
    denominador_dice, denominador_iou = 2 * vp + fp + fn, vp + fp + fn
    return {'dice': 2 * vp / denominador_dice if denominador_dice else 1.0,
            'iou': vp / denominador_iou if denominador_iou else 1.0,
            'verdaderos_positivos': vp, 'falsos_positivos': fp, 'falsos_negativos': fn}
