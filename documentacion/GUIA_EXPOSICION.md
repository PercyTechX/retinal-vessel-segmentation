# Guion para explicar el notebook V2

**Duración orientativa: 11 minutos.** Incluye las pausas para señalar el código y las imágenes. Ensaya con cronómetro para quedar entre 10 y 12 minutos. No necesitas leer cada línea del código.

## 1.- Objetivo y protocolo — 0:00 a 0:40

*Muestra el inicio del notebook.*

En este trabajo buscamos identificar los vasos sanguíneos en imágenes de retina.
El resultado es una máscara. Los vasos aparecen en blanco y el resto, en negro.

Comparamos dos métodos: umbralización adaptativa y crecimiento de regiones.
Los dos usan procesamiento tradicional de imágenes.
No entrenamos un modelo de aprendizaje automático.
La idea es comparar cómo funcionan y explicar sus aciertos y sus errores.

## 2.- Parámetros fijados antes de evaluar — 0:40 a 1:15

*Muestra la configuración. Señala los valores, sin leer todo el archivo.*

Los parámetros controlan las decisiones de cada método.
Para elegirlos usamos seis imágenes de desarrollo.
Después los dejamos fijos y comparamos los métodos en otras 39 imágenes.

Hacemos esto para no cambiar los valores según cada resultado final.
También guardamos la configuración en un archivo.
Así podemos repetir el trabajo y saber qué valores produjeron estas máscaras.

## 3.- Leer imagen, referencia y campo visual — 1:15 a 2:00

*Muestra las tres imágenes: original, referencia y campo visual.*

Usamos 45 imágenes de HRF.
Hay 15 casos sanos, 15 con retinopatía y 15 con glaucoma.

Por cada caso cargamos tres archivos.
La fotografía es la entrada del algoritmo.
La referencia contiene los vasos marcados manualmente.
La usamos para medir la coincidencia de nuestra predicción.

El campo visual indica dónde está la retina.
Permite excluir el fondo negro.
No indica dónde están los vasos.
Antes de continuar, comprobamos que los tres archivos tengan el mismo tamaño.

## 4.- Preparación compartida — 2:00 a 3:00

*Muestra `preparar_imagen`. Señala el canal verde, CLAHE y el suavizado.*

Primero reducimos el ancho de la imagen a 1800 píxeles.
Esto permite trabajar más rápido.
La desventaja es que podemos perder detalle en vasos finos.

Después usamos el canal verde para aprovechar el contraste de los vasos.
Aplicamos CLAHE para resaltar diferencias de intensidad en cada zona.
También usamos un suavizado pequeño para reducir ruido.

Ambos métodos reciben la misma imagen preparada.
Así comparamos sus decisiones sobre una entrada común.

Probamos una corrección adicional de iluminación.
No la dejamos activada.
En desarrollo, el promedio conjunto fue ligeramente mayor sin esa corrección.
Preferimos no añadir ese paso sin una mejora observada.

## 5.- Crecimiento por conectividad 8 — 3:00 a 3:50

*Muestra `crecer_desde_semillas`.*

El crecimiento comienza con semillas.
Son píxeles que cumplen un criterio más exigente de oscuridad local.
Después buscamos otros píxeles que podrían formar parte del vaso.
A estos los llamamos candidatos.

Conservamos los candidatos conectados a una semilla.
Revisamos ocho vecinos, incluidas las diagonales.
Una región sin semillas se descarta.

Esto añade una condición de continuidad.
No basta con que un píxel sea oscuro.
También debe estar conectado a una semilla.
Las semillas salen de la propia imagen, no de la referencia manual.

## 6.- Limpieza y resolución de salida — 3:50 a 4:25

*Muestra `limpiar_y_restaurar`.*

Después eliminamos componentes menores de 45 píxeles en la imagen reducida.
Buscamos quitar puntos aislados.
Esta regla también puede borrar fragmentos reales de vasos.

Quitamos un borde pequeño de la predicción para reducir detecciones del contorno circular.
Pero ese borde sí participa en la evaluación.
Si allí omitimos vasos, cuentan como errores.

Finalmente recuperamos el tamaño original.
La máscara sigue teniendo solo dos valores: fondo y vaso.

## 7.- Dos decisiones de segmentación — 4:25 a 5:30

*Muestra las dos ramas de `segmentar`.*

En el método adaptativo comparamos cada píxel con su entorno.
Si es suficientemente oscuro respecto al promedio local, lo marcamos como vaso.
Usamos una ventana de 47 por 47 y una constante de 10.

La ventana mantiene una escala parecida a la usada en V1, considerando el cambio de resolución.
La constante se eligió entre 6, 8 y 10.
El valor 10 dio el mayor Dice promedio en desarrollo.

En crecimiento usamos dos umbrales.
El valor 16 identifica semillas y el valor 7 admite candidatos.
Esta combinación fue la mejor entre las que probamos para esa preparación.
No significa que sea la mejor para cualquier imagen.

Los dos métodos usan contraste local.
La diferencia principal es que el crecimiento exige conexión con una semilla.

## 8.- Ejecución y pasos intermedios — 5:30 a 6:10

*Muestra el panel de semillas, candidatos y región crecida. Después señala ambas máscaras.*

Aquí podemos seguir el proceso de forma visual.
Las semillas son más restrictivas.
Los candidatos incluyen más estructuras, pero también más ruido.
La región crecida conserva los candidatos conectados a semillas.

Después comparamos ambas predicciones con la referencia.
Vemos vasos recuperados y también diferencias.
Estas imágenes ayudan a entender qué hace cada paso.
También muestran por qué una máscara puede parecer razonable y aun así tener errores.

## 9.- Métricas y comprobación — 6:10 a 7:10

*Muestra `calcular_metricas` y la salida del ejemplo.*

Usamos Dice e IoU para medir cuánto coincide nuestra máscara con la referencia.
Ambos van de cero a uno.
Uno representa una coincidencia perfecta.

Dice relaciona la zona coincidente con el tamaño de ambas máscaras.
IoU compara esa coincidencia con toda la zona marcada por alguna de las dos.
Por eso sus números son diferentes.

Las métricas penalizan dos errores.
Uno es marcar fondo como vaso.
El otro es dejar vasos sin detectar.

Calculamos todo dentro del campo visual original.
También comprobamos que el notebook reproduzca los PNG guardados.
Las cifras de este primer ejemplo pertenecen a una sola imagen.
Ahora veremos los promedios de los 39 casos.

## 10.- Ajuste registrado y resultados finales — 7:10 a 9:00

*Muestra primero la tabla de ajuste. Después ubica la comparación principal y el desglose por grupo.*

La primera tabla registra las opciones probadas con las seis imágenes de desarrollo.
Nos permite justificar los parámetros elegidos.
No elegimos una configuración distinta para cada imagen final.

En la comparación de 39 casos, el adaptativo obtuvo Dice medio de **0,7116**.
Su IoU fue **0,5554**.
El crecimiento obtuvo Dice medio de **0,7152** e IoU de **0,5607**.

El crecimiento tuvo un promedio un poco mayor en V2.
La diferencia de Dice es aproximadamente **0,0036**.
Es pequeña. No podemos decir que siempre sea mejor.
Tampoco significa que haya clasificado correctamente el 71,52 % de todos los píxeles.
Dice mide solapamiento, no ese porcentaje de aciertos.

El desglose por grupo ayuda a entender el promedio.
En casos sanos, el crecimiento alcanzó Dice medio de **0,7807**.
En retinopatía bajó a **0,6478**.
En ese grupo, el adaptativo obtuvo **0,6565**, un valor algo mayor.
Por lo tanto, el método con mejor promedio general no gana en todos los grupos.

Promediamos por imagen para que cada caso tenga el mismo peso.
La tabla también muestra cuánto varían los resultados.
Esto importa porque el promedio no describe por sí solo todas las imágenes.

La interpretación es que ambos métodos recuperan parte de la red vascular.
Pero todavía confunden estructuras y omiten vasos.
Las cifras y las imágenes deben leerse juntas.

## 11.- Ejemplos favorables y difíciles — 9:00 a 10:00

*Muestra los casos `11_h` y `03_dr`. Señala diferencias concretas con la referencia.*

Estos ejemplos muestran dos situaciones distintas.
En `11_h`, el crecimiento obtuvo Dice de **0,8273**.
Se recuperan muchos vasos, aunque la coincidencia no es perfecta.

En `03_dr`, el Dice fue **0,5695**.
Vemos vasos que faltan y zonas marcadas que no coinciden con la referencia.
Otras estructuras también pueden ser oscuras respecto al entorno.
El crecimiento puede conservarlas si están conectadas a una semilla.

Elegimos estos casos por una regla clara.
Son el mayor y el menor Dice del crecimiento entre los 39.
Mostramos ambos métodos en cada imagen.
Así no presentamos solamente un resultado favorable.

## 12.- Reproducir el lote completo — 10:00 a 10:15

*Muestra `recalcular_todo = False`, sin activarlo.*

Esta opción permite volver a generar todas las máscaras.
Son 45 por método: 90 en total.
Para la exposición usamos las salidas ya guardadas.

## 13.- Conclusiones y limitaciones — 10:15 a 11:00

*Muestra las conclusiones del notebook.*

Conseguimos implementar y comparar dos métodos tradicionales.
Podemos explicar sus parámetros y repetir los resultados.
El crecimiento tuvo un promedio ligeramente mayor dentro de V2.
Pero ambos siguen teniendo dificultades con vasos finos y falsas detecciones.

V2 no superó el mejor promedio de V1, que fue **0,7158**.
La elegimos por su relación con las clases y la claridad de sus pasos.

El ajuste usa pocos casos y la división no fue aleatoria.
Además, los 39 casos ya se habían observado en V1.
Por eso esta comparación es exploratoria.
La conclusión se limita a este experimento.

## Para ensayar

- Dedica más tiempo a las tablas y a señalar errores que a leer el código.
- Explica los números despacio. No hace falta leer todas las filas.
- Si superas los 12 minutos, acorta la lectura de la configuración y del ajuste. Conserva la comparación final y las limitaciones.
- Si terminas antes de 10 minutos, usa las imágenes para señalar un vaso recuperado, uno omitido y una falsa detección.
