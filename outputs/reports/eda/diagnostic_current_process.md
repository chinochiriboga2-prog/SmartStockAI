# Diagnóstico del proceso actual

## 1. Estructura y granularidad de los datos
- SKUs únicos analizados: 2094
- Periodo histórico disponible: 2021-01-01 a 2026-02-01
- Granularidad efectiva de la fuente: mensual por SKU
- Observación crítica: la fuente actual no contiene transacciones diarias ni semanales. Por tanto, el EDA se construyó con la mejor granularidad disponible (SKU-mes), y debe documentarse esta limitación para la fase formal del proyecto.

## 2. Calidad de datos
- Registros originales: 129828
- Registros luego de agregación y depuración: 129828
- Registros duplicados eliminados/agregados: 0
- Casos de demanda cero registrada: 81459
- Casos de falta de registro imputada a cero: 0

Interpretación:
- Se diferenció explícitamente entre 'demanda cero' y 'falta de registro', tal como exige el tutor.
- La depuración consistió en agrupar registros repetidos por SKU-fecha y conservar stock final del periodo.

## 3. Justificación de enfoque en Top 50 SKU
- Los 50 SKU de mayor rotación concentran aproximadamente 15.19% de las ventas acumuladas del histórico.
- Esta selección es coherente con el alcance del MVP, que exige una validación piloto sobre productos de mayor relevancia operativa.
- Desde una lógica tipo Pareto, priorizar este subconjunto permite capturar la mayor parte del impacto de negocio en la primera iteración.

## 4. Segmentación de inventario
- Se aplicó clasificación ABC/XYZ para distinguir productos por importancia comercial y previsibilidad.
- Esto permite separar SKU de alta relevancia y alta variabilidad, fundamentales para la toma de decisiones de compra.

## 5. Patrones de demanda
- Mezcla de tipos de demanda observada: {'Lumpy': 0.9971, 'Smooth': 0.0014, 'Erratic': 0.001, 'Intermittent': 0.0005}
- El dataset presenta presencia importante de demanda intermitente y/o variable, lo cual es consistente con un entorno de autopartes.
- Este hallazgo justifica que la gestión manual basada solo en intuición o promedio simple pueda generar sobreinventario o quiebres.

## 6. Línea base operativa actual
- Frecuencia promedio proxy de quiebre de stock: 0.00%
- Nivel de servicio promedio proxy: 100.00%
- Días promedio de inventario proxy: 309.03
- Rotación promedio proxy del inventario: 0.0841

Interpretación:
- Estas métricas son aproximaciones construidas a nivel mensual, por lo que deben reportarse como línea base proxy, no como indicador operacional exacto diario.

## 7. Variables críticas exigidas por revisión
  VARIABLE_CRITICA DISPONIBLE_EN_FUENTE COLUMNAS_POTENCIALES
         Lead Time                   No      No identificada
  Costos Unitarios                   No      No identificada
Stock de Seguridad                   No      No identificada

Interpretación:
- Si Lead Time o Costos Unitarios no están disponibles en la fuente, debe documentarse como una brecha crítica del proceso actual.
- Esto no invalida el EDA, pero sí limita la precisión futura del sistema de reabastecimiento.

## 8. Diagnóstico general del proceso actual
El proceso actual presenta una base histórica suficiente para modelar demanda por SKU, pero con limitaciones relevantes:
1. La granularidad real de la información es mensual, no diaria ni semanal.
2. No todas las variables logísticas críticas están disponibles en la fuente actual.
3. Existe heterogeneidad fuerte entre productos, tanto en ventas como en variabilidad.
4. La demanda intermitente y la concentración de ventas en pocos SKU justifican el enfoque analítico y el uso posterior de IA.
5. La gestión actual puede estar expuesta a decisiones subóptimas por falta de segmentación, baja trazabilidad de quiebres y ausencia de variables clave como lead time y costo unitario.