# SmartStock AI

## Descripción del problema

SmartStock AI es un prototipo de inteligencia artificial desarrollado para apoyar la toma de decisiones en la gestión de inventarios del sector autopartes. El problema abordado consiste en la dificultad de administrar manualmente un portafolio amplio de productos, lo cual puede generar quiebres de stock, sobreinventario y decisiones poco precisas basadas únicamente en experiencia operativa o archivos de Excel.

En este tipo de negocio, la demanda de productos puede ser irregular, variable o intermitente. Esto hace que la planificación del inventario sea compleja, especialmente cuando existen muchos SKU con diferentes niveles de rotación. Por esta razón, el proyecto busca aplicar análisis de datos y modelos predictivos para mejorar la comprensión del comportamiento de la demanda y apoyar una gestión más técnica del inventario.

## Solución propuesta

El prototipo consiste en una solución de inteligencia artificial desarrollada en Python e integrada con archivos de Excel. Su objetivo es analizar datos históricos de inventario y demanda, aplicar técnicas de clasificación y pronóstico, generar métricas comparativas y exportar resultados que apoyen la toma de decisiones.

La solución permite evaluar el comportamiento de los productos, identificar patrones relevantes, clasificar SKU según criterios de importancia y variabilidad, generar alertas de inventario y analizar resultados mediante reportes, gráficos y técnicas de interpretabilidad.

El sistema busca facilitar una gestión más técnica, trazable y basada en datos, reduciendo la dependencia exclusiva de decisiones manuales o experiencia operativa.

## Requisitos técnicos y dependencias

Para ejecutar el proyecto se requiere:

- Python 3.11
- Visual Studio Code
- GitHub para control de versiones y documentación del repositorio
- Microsoft Excel o una herramienta compatible para revisar los archivos generados
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

### 1. Descargar o clonar el repositorio

Descargar el proyecto desde GitHub o clonarlo en el computador.

### 2. Abrir el proyecto en Visual Studio Code

Abrir la carpeta principal del proyecto en Visual Studio Code.

### 3. Crear el entorno virtual

Desde la terminal, dentro de la carpeta principal del proyecto, ejecutar:

```bash
python -m venv .venv
```

### 4. Activar el entorno virtual

En Windows, ejecutar:

```bash
.venv\Scripts\activate
```

Si el entorno se activó correctamente, debería aparecer `(.venv)` al inicio de la línea de la terminal.

### 5. Instalar las dependencias

Ejecutar:

```bash
pip install -r requirements.txt
```

### 6. Ejecutar el archivo principal

Ejecutar el prototipo principal con:

```bash
python main.py
```

Este archivo ejecuta el flujo principal del sistema y genera los resultados correspondientes.

### 7. Ejecutar el análisis exploratorio de datos

Para generar o revisar los resultados del análisis exploratorio, ejecutar:

```bash
python -m src.eda
```

### 8. Ejecutar el análisis de interpretabilidad

Para ejecutar el componente de interpretabilidad del modelo, ejecutar:

```bash
python -m src.interpretability
```

### 9. Revisar los resultados generados

Los resultados, reportes, métricas, gráficos y archivos finales se encuentran en la carpeta:

```bash
outputs/
```

## Estructura del proyecto

La organización del proyecto responde a una estructura lógica y profesional. De forma simplificada, el repositorio se compone de:

```text
PROYECTO_INVENTARIO/
│
├── data/
│
├── outputs/
│
├── src/
│   ├── abc_xyz.py
│   ├── alerts.py
│   ├── config.py
│   ├── data_loader.py
│   ├── eda.py
│   ├── evaluation.py
│   ├── forecasting.py
│   ├── interpretability.py
│   ├── preprocessing.py
│   └── utils.py
│
├── main.py
├── requirements.txt
└── README.md
```

Descripción de los elementos principales:

- `data/`: carpeta destinada a almacenar los archivos de datos utilizados por el prototipo.
- `outputs/`: carpeta donde se almacenan los resultados generados, reportes, métricas, gráficos y evidencias finales.
- `src/`: carpeta que contiene los módulos principales del sistema.
- `main.py`: archivo principal para ejecutar el flujo completo del prototipo.
- `requirements.txt`: archivo con las librerías necesarias para ejecutar el proyecto.
- `README.md`: documentación técnica del repositorio.
- `.gitignore`: archivo utilizado para excluir elementos innecesarios del repositorio, como entornos virtuales o archivos temporales.

## Explicación general del pipeline

El pipeline general del prototipo SmartStock AI sigue un flujo lógico desde la carga del archivo Excel hasta la exportación de reportes finales.

Las etapas principales son:

1. **Carga de datos:** se importan los datos necesarios desde archivos de Excel relacionados con inventario, ventas o demanda.

2. **Preparación y limpieza de datos:** se revisan, transforman y organizan los datos para que puedan ser utilizados correctamente por el sistema.

3. **Análisis exploratorio de datos:** se identifican patrones relevantes, como productos con mayor rotación, concentración de ventas, variabilidad de demanda, productos críticos y posibles comportamientos de sobreinventario o quiebre de stock.

4. **Clasificación ABC/XYZ:** se clasifican los SKU según su importancia y comportamiento de demanda, permitiendo segmentar los productos de acuerdo con criterios de valor, rotación y variabilidad.

5. **Generación de alertas:** se identifican posibles riesgos relacionados con inventario, tales como quiebres de stock, exceso de inventario o productos con comportamiento irregular.

6. **Modelado y pronóstico:** se aplican técnicas de pronóstico para estimar el comportamiento futuro de la demanda.

7. **Evaluación del modelo:** se calculan métricas de desempeño para comparar resultados y validar la utilidad del modelo.

8. **Interpretabilidad:** se analizan los factores que influyen en los resultados del modelo, incluyendo análisis SHAP cuando corresponde.

9. **Exportación de resultados:** se generan archivos finales, reportes, métricas y gráficos que se almacenan en la carpeta `outputs`.

## Resultados finales del modelo

El prototipo permite analizar el comportamiento de los productos, comparar resultados y generar información útil para apoyar la toma de decisiones en inventarios.

Los resultados obtenidos sirven como base para:

- Identificar productos con riesgo de quiebre de stock.
- Detectar posibles casos de sobreinventario.
- Analizar la variabilidad de la demanda.
- Clasificar productos según criterios ABC/XYZ.
- Revisar métricas de desempeño del modelo.
- Generar reportes finales en Excel.
- Apoyar decisiones operativas y estratégicas dentro del sector autopartes.

La información generada por el prototipo puede ser utilizada para mejorar la planificación del inventario, reducir decisiones basadas únicamente en experiencia operativa y promover una gestión más analítica.

## Evidencias de validación

Las evidencias de validación, resultados generados y archivos de salida se encuentran en la carpeta `outputs`. Estas evidencias permiten demostrar la ejecución del prototipo, el análisis realizado y los resultados obtenidos durante el proceso.

Entre las evidencias consideradas se incluyen:

- Resultados finales del modelo.
- Métricas comparativas.
- Archivos generados por el prototipo.
- Reportes consolidados en Excel.
- Gráficos del análisis exploratorio de datos.
- Evidencias de pruebas finales.
- Resultados del análisis de interpretabilidad.
- Resultados almacenados en la carpeta `outputs`.

## Documentación técnica del repositorio

El repositorio incluye un archivo `README.md` que documenta de forma clara y ordenada los elementos esenciales para comprender y ejecutar el proyecto.

Este archivo contiene:

### Descripción del problema y solución

Se explica que el proyecto aborda la optimización de inventarios y el pronóstico de demanda en una empresa de autopartes. La solución consiste en un prototipo de inteligencia artificial desarrollado en Python e integrado con archivos de Excel.

### Requisitos técnicos y dependencias

Se especifica el uso de Python 3.11 y las librerías necesarias para ejecutar el sistema, instalables mediante el archivo `requirements.txt`.

### Instrucciones de ejecución paso a paso

El README indica cómo:

- Crear el entorno virtual.
- Activar el entorno virtual.
- Instalar dependencias.
- Ejecutar `main.py`.
- Ejecutar `src.eda`.
- Ejecutar `src.interpretability`.
- Ubicar los resultados generados.

### Explicación general del pipeline

También se describe el flujo lógico del sistema desde la carga del archivo Excel hasta la exportación de reportes finales.

## Control de versiones actualizado y demo

La entrega técnica del prototipo se acompaña de una estructura de trabajo organizada y coherente con un control progresivo de versiones del proyecto. Aunque no se implementó una herramienta formal de MLOps, el desarrollo siguió una lógica de evolución ordenada del sistema.

Esto se evidencia en:

- Modularización creciente del código.
- Consolidación del entorno de trabajo.
- Incorporación progresiva de nuevos componentes.
- Generación de outputs estructurados.
- Mejora continua de reportes y anexos.
- Uso de GitHub como repositorio para centralizar el código, la documentación y los archivos principales del prototipo.

La demo del prototipo puede sustentarse mediante:

- Capturas del entorno de ejecución en Visual Studio Code.
- Evidencia del árbol de carpetas del proyecto.
- Capturas del Excel final consolidado.
- Métricas del modelo.
- Gráficos del análisis exploratorio de datos.
- Resultados del análisis SHAP.
- Archivos generados en la carpeta `outputs`.

Esto permite demostrar que el prototipo es ejecutable, comprensible y funcional dentro del alcance definido.

## Referencia a anexos técnicos

Este repositorio funciona como anexo técnico del proyecto, ya que contiene el código fuente, la documentación, las dependencias y las evidencias principales del prototipo desarrollado.

Los anexos técnicos relacionados con el proyecto pueden incluir:

- Código fuente del sistema.
- Reportes generados.
- Resultados del modelo.
- Métricas comparativas.
- Gráficos del EDA.
- Resultados de interpretabilidad.
- Capturas de ejecución.
- Archivos consolidados en Excel.

## Autor

Proyecto desarrollado como prototipo académico de inteligencia artificial aplicado a la optimización de inventarios en el sector autopartes.
