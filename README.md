# SmartStock AI

## Descripción del problema

SmartStock AI es un prototipo de inteligencia artificial desarrollado para apoyar la toma de decisiones en la gestión de inventarios del sector autopartes. El problema abordado consiste en la dificultad de administrar manualmente un portafolio amplio de productos, lo cual puede generar quiebres de stock, sobreinventario y decisiones poco precisas basadas únicamente en experiencia operativa o archivos de Excel.

En este tipo de negocio, la demanda de productos puede ser irregular, variable o intermitente. Esto hace que la planificación del inventario sea compleja, especialmente cuando existen muchos SKU con diferentes niveles de rotación. Por esta razón, el proyecto busca aplicar análisis de datos y modelos predictivos para mejorar la comprensión del comportamiento de la demanda y apoyar una gestión más técnica del inventario.

## Solución propuesta

El prototipo utiliza técnicas de análisis de datos y modelado predictivo para evaluar el comportamiento histórico de la demanda, comparar modelos de pronóstico y generar resultados que apoyen la optimización del inventario.

La solución busca facilitar una gestión más técnica, trazable y basada en datos. A través del pipeline desarrollado, se procesan los datos disponibles, se analizan patrones relevantes, se entrenan modelos de pronóstico y se generan resultados que permiten apoyar decisiones relacionadas con inventario, demanda, sobreinventario y posibles quiebres de stock.

## Requisitos técnicos y dependencias

Para ejecutar el proyecto se requiere:

- Python 3.10 o superior
- Visual Studio Code
- GitHub para control de versiones y documentación del repositorio
- Librerías incluidas en el archivo `requirements.txt`

Las dependencias necesarias del proyecto se encuentran registradas en el archivo:

```bash
requirements.txt
```

## Instalación de dependencias

Para instalar las dependencias necesarias, se debe ejecutar el siguiente comando en la terminal, dentro de la carpeta principal del proyecto:

```bash
pip install -r requirements.txt
```

## Instrucciones de ejecución paso a paso

Para ejecutar el prototipo SmartStock AI, seguir los siguientes pasos:

1. Descargar o clonar el repositorio desde GitHub.
2. Abrir la carpeta del proyecto en Visual Studio Code.
3. Verificar que Python esté instalado correctamente en el computador.
4. Abrir una terminal dentro de la carpeta principal del proyecto.
5. Instalar las dependencias necesarias con el siguiente comando:

```bash
pip install -r requirements.txt
```

6. Ejecutar el archivo principal del proyecto con el siguiente comando:

```bash
python main.py
```

7. Revisar los resultados generados en la carpeta `outputs`.

## Estructura del proyecto

El repositorio está organizado de la siguiente manera:

```text
SmartStockAI/
│
├── main.py
├── README.md
├── requirements.txt
├── src/
├── outputs/
└── .gitignore
```

Descripción de los elementos principales:

- `main.py`: archivo principal para ejecutar el prototipo.
- `src/`: carpeta que contiene los módulos, scripts y funciones del proyecto.
- `outputs/`: carpeta donde se almacenan resultados, métricas, gráficos o evidencias generadas.
- `requirements.txt`: archivo con las librerías necesarias para ejecutar el proyecto.
- `README.md`: documentación técnica del prototipo.
- `.gitignore`: archivo utilizado para excluir elementos innecesarios del repositorio, como entornos virtuales o archivos temporales.

## Explicación general del pipeline

El pipeline general del prototipo SmartStock AI sigue las siguientes etapas:

1. **Carga de datos:** se importan los datos necesarios para el análisis del comportamiento de la demanda e inventario.

2. **Preparación y limpieza de datos:** se revisan, transforman y organizan los datos para que puedan ser utilizados correctamente por el modelo.

3. **Análisis exploratorio de datos:** se identifican patrones relevantes en la información, como productos con mayor rotación, variabilidad de la demanda, concentración de ventas y posibles comportamientos de sobreinventario o quiebre de stock.

4. **Modelado predictivo:** se aplican modelos de pronóstico para estimar el comportamiento futuro de la demanda.

5. **Comparación de modelos:** se evalúa el desempeño de los modelos utilizados mediante métricas de error y comparación de resultados.

6. **Validación de resultados:** se revisan las métricas obtenidas para determinar qué modelo presenta un mejor desempeño frente a la información analizada.

7. **Generación de evidencias:** los resultados finales, métricas, gráficos o archivos de salida se almacenan en la carpeta `outputs`.

## Resultados finales del modelo

El prototipo permite comparar modelos de pronóstico y seleccionar una alternativa adecuada para apoyar la toma de decisiones en inventarios. Los resultados obtenidos sirven como base para identificar productos con posibles riesgos de quiebre de stock, sobreinventario o comportamiento irregular de demanda.

La información generada por el prototipo puede ser utilizada como apoyo para mejorar la planificación del inventario, reducir decisiones basadas únicamente en experiencia operativa y promover una gestión más analítica dentro del sector autopartes.

## Evidencias de validación

Las evidencias de validación, resultados generados y archivos de salida se encuentran en la carpeta `outputs`. Estas evidencias permiten demostrar la ejecución del prototipo, el análisis realizado y los resultados obtenidos durante el proceso.

Entre las evidencias consideradas se incluyen:

- Resultados finales del modelo.
- Métricas comparativas.
- Archivos generados por el prototipo.
- Evidencias de pruebas finales.
- Resultados almacenados en la carpeta `outputs`.
