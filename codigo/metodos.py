"""Métodos de segmentación de V2."""

import cv2
import numpy as np


def preparar_imagen(imagen, campo_original, parametros, corregir_iluminacion):
    """Preparar la imagen para ambos métodos."""
    # Reducimos la imagen al ancho de trabajo.
    alto, ancho = imagen.shape[:2]
    escala = min(1.0, parametros['ancho_procesamiento'] / ancho)
    tamano = (round(ancho * escala), round(alto * escala))
    reducida = cv2.resize(imagen, tamano, interpolation=cv2.INTER_AREA)
    campo = cv2.resize(campo_original.astype(np.uint8), tamano,
                       interpolation=cv2.INTER_NEAREST).astype(bool)
    verde = reducida[:, :, 1]

    # Corregimos la iluminación solo si la opción está activada.
    # El fondo negro no participa en el cálculo.
    fondo = None
    if corregir_iluminacion:
        sigma = parametros['sigma_iluminacion']
        pesos = cv2.GaussianBlur(campo.astype(np.float32), (0, 0), sigma)
        suma = cv2.GaussianBlur(verde.astype(np.float32) * campo, (0, 0), sigma)
        fondo = suma / np.maximum(pesos, 1e-6)
        corregida = np.clip(verde.astype(np.float32) - fondo + 128, 0, 255).astype(np.uint8)
    else:
        corregida = verde.copy()
    corregida[~campo] = int(np.median(corregida[campo]))

    # Mejoramos el contraste y suavizamos el ruido.
    contraste = cv2.createCLAHE(clipLimit=parametros['contraste_clahe'],
                               tileGridSize=(8, 8)).apply(corregida)
    preparada = cv2.GaussianBlur(contraste, (3, 3), 0)
    preparada[~campo] = int(np.median(preparada[campo]))

    # Quitamos un borde pequeño para evitar detecciones del contorno.
    # Los vasos omitidos en ese borde sí cuentan como errores.
    margen = parametros['margen_campo']
    elemento = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * margen + 1, 2 * margen + 1))
    campo_interior = cv2.erode(campo.astype(np.uint8), elemento).astype(bool)
    ventana = parametros['ventana_local']
    promedio = cv2.GaussianBlur(preparada.astype(np.float32), (ventana, ventana), 0)
    oscuridad_local = promedio - preparada.astype(np.float32)
    return {'verde': verde, 'fondo': fondo, 'corregida': corregida,
            'preparada': preparada, 'oscuridad_local': oscuridad_local,
            'campo_interior': campo_interior}


def crecer_desde_semillas(semillas, candidatos):
    """Conservar candidatos conectados a semillas por ocho vecinos."""
    # Nos quedamos con las regiones que tienen alguna semilla.
    candidatos = candidatos.astype(bool)
    semillas = semillas.astype(bool) & candidatos
    cantidad, etiquetas = cv2.connectedComponents(candidatos.astype(np.uint8), connectivity=8)
    conservar = np.zeros(cantidad, dtype=bool)
    conservar[np.unique(etiquetas[semillas])] = True
    conservar[0] = False
    return conservar[etiquetas]


def limpiar_y_restaurar(mascara, campo_interior, campo_original, parametros):
    """Quitar puntos pequeños y recuperar el tamaño original."""
    mascara = (mascara & campo_interior).astype(np.uint8)
    cantidad, etiquetas, estadisticas, _ = cv2.connectedComponentsWithStats(mascara, connectivity=8)
    conservar = np.zeros(cantidad, dtype=bool)
    conservar[1:] = estadisticas[1:, cv2.CC_STAT_AREA] >= parametros['area_minima']
    limpia = conservar[etiquetas].astype(np.uint8)
    alto, ancho = campo_original.shape
    original = cv2.resize(limpia, (ancho, alto), interpolation=cv2.INTER_NEAREST).astype(bool)
    return original & campo_original


def segmentar(etapas, campo_original, parametros, metodo, configuracion):
    """Aplicar el método elegido."""
    campo = etapas['campo_interior']
    if metodo == 'umbral_adaptativo':
        # Marcamos los píxeles oscuros respecto a su entorno.
        mascara = cv2.adaptiveThreshold(
            etapas['preparada'], 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, parametros['ventana_local'], configuracion['constante']) > 0
        intermedias = {'umbral_inicial': mascara & campo}
    elif metodo == 'crecimiento_regiones':
        # Separamos las semillas de los posibles vasos.
        # Después conservamos los candidatos conectados a semillas.
        bajo, alto = configuracion['umbral_bajo'], configuracion['umbral_alto']
        if bajo >= alto:
            raise ValueError('El umbral de semillas debe superar al de candidatos.')
        semillas = (etapas['oscuridad_local'] >= alto) & campo
        candidatos = (etapas['oscuridad_local'] >= bajo) & campo
        mascara = crecer_desde_semillas(semillas, candidatos)
        intermedias = {'semillas': semillas, 'candidatos': candidatos, 'region_crecida': mascara}
    else:
        raise ValueError(f'Método desconocido: {metodo}')
    prediccion = limpiar_y_restaurar(mascara, campo, campo_original, parametros)
    return prediccion, intermedias
