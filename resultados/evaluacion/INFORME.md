# Resultados de la versión 2

Seis casos para elegir parámetros y 39 para comparar (13 por grupo). La evaluación usa todo el campo visual original, a resolución original. Cada imagen tiene el mismo peso. Los 39 casos ya se habían evaluado en V1: esta es una comparación exploratoria sobre la misma partición, no una prueba independiente nueva.

## Métodos de la versión 2

| Método | Dice medio ± desviación | IoU medio ± desviación |
| --- | --- | --- |
| Umbral adaptativo | 0.7116 ± 0.0587 | 0.5554 ± 0.0698 |
| Crecimiento de regiones | 0.7152 ± 0.0670 | 0.5607 ± 0.0796 |

## Comparación con V1

| Versión | Método | Dice | IoU |
| --- | --- | --- | --- |
| V1 | metodo_morfologico | 0.6901 | 0.5283 |
| V1 | metodo_adaptativo | 0.7158 | 0.5612 |
| V2 | umbral_adaptativo | 0.7116 | 0.5554 |
| V2 | crecimiento_regiones | 0.7152 | 0.5607 |

Diferencia del mejor promedio V2 respecto del mejor V1: -0.0006 de Dice. Es una diferencia descriptiva. Se cambiaron varias decisiones; no permite atribuir el cambio a una sola.

## Desglose por grupo

| Grupo | Método | Dice | IoU |
| --- | --- | --- | --- |
| h | Umbral adaptativo | 0.7666 | 0.6225 |
| dr | Umbral adaptativo | 0.6565 | 0.4904 |
| g | Umbral adaptativo | 0.7118 | 0.5534 |
| h | Crecimiento de regiones | 0.7807 | 0.6411 |
| dr | Crecimiento de regiones | 0.6478 | 0.4816 |
| g | Crecimiento de regiones | 0.7171 | 0.5594 |

## Alcance y limitaciones

- Las semillas se eligen automáticamente desde la imagen, sin anotaciones manuales.
- El crecimiento usa un predicado fijo sobre oscuridad local y conectividad 8. No adapta la media de cada región.
- Ambos métodos comparten evidencia de contraste local; difieren en que el crecimiento exige conexión a semillas.
- Una franja de 3 píxeles de la imagen reducida no recibe predicciones. No se excluye de las métricas.
- Los vasos finos pueden perderse por reescalado o limpieza; el crecimiento puede propagar falsas detecciones.
- Desarrollo es pequeño y no aleatorio. No se demuestra generalización clínica.
- El registro de preparación compartida está en `../ajuste/preparaciones.csv`.

Ejemplos seleccionados por mayor y menor Dice de crecimiento entre los 39 casos:

- `mayor_dice_regiones_11_h.png`: Dice de regiones 0.8273.
- `menor_dice_regiones_03_dr.png`: Dice de regiones 0.5695.
