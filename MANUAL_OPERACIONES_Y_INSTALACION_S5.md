================================================================================
         MANUAL DE OPERACION E INSTALACION - COMMAND CENTER FODA S5             
                     ESTADO MAYOR DE OPERACIONES // E.M.O.                      
================================================================================

Este manual detalla los pasos para la instalación técnica del entorno, la configuración del modelo de lenguaje local (Ollama) y la guía de operación del Command Center FODA S5.



================================================================================
                    PARTE I: MANUAL DE INSTALACION Y DESPLIEGUE                           
================================================================================

>> 1. REQUISITOS PREVIOS DEL SISTEMA
   1. Sistema Operativo: macOS, Linux o Windows.
   2. Python: Versión 3.8 a 3.12 instalada.
   3. Memoria RAM: 8 GB mínimo (16 GB recomendado para Ollama local).

>> 2. CLONACION O PREPARACION DE CARPETA
   Asegúrese de estar en el directorio de trabajo del proyecto:
   
   cd /Users/beto/Desktop/FODA
   

>> 3. METODO AUTOMATICO SIMPLIFICADO (RECOMENDADO)
   Se ha integrado un script launcher inteligente llamado run_foda_s5.py que automatiza toda la configuración. Al ejecutarlo:
   1. Verifica e instala de forma automática todas las dependencias listadas en requirements.txt.
   2. Escanea si el puerto de Ollama está activo y descarga (ollama pull) el modelo llama3 en segundo plano si no está disponible localmente.
   3. Inicia el servidor Streamlit en el puerto local.

   [!] Ejecución del método automático:
   Configure y active su entorno virtual, y ejecute el launcher:
   [En macOS/Linux]
   python3 -m venv stratcom_env
   source stratcom_env/bin/activate
   python run_foda_s5.py

   [En Windows]
   python -m venv stratcom_env
   stratcom_env\Scripts\activate
   python run_foda_s5.py



================================================================================
            PARTE II: INSTALACION PASO A PASO (METODO MANUAL ALTERNATIVO)       
================================================================================

>> 1. CONFIGURACION DEL ENTORNO VIRTUAL (VENV)
   Si desea realizar el despliegue manualmente:
   [En macOS/Linux]
   python3 -m venv stratcom_env
   source stratcom_env/bin/activate

   [En Windows]
   python -m venv stratcom_env
   stratcom_env\Scripts\activate

>> 2. INSTALACION DE DEPENDENCIAS PYTHON
   Con el entorno virtual activo, instale las librerías indicadas en el archivo requirements.txt:
   pip install --upgrade pip
   pip install -r requirements.txt

>> 3. CONFIGURACION DE INTELIGENCIA ARTIFICIAL LOCAL (OLLAMA)
   1. Descargar Ollama: Visite ollama.com y descargue la aplicación correspondiente a su OS.
   2. Iniciar Ollama: Abra la aplicación en su máquina.
   3. Descargar el modelo Llama3: En su terminal ejecute:
       ollama pull llama3

>> 4. DESPLIEGUE DE LA APLICACION
   Para iniciar el panel interactivo de Streamlit de forma manual:
   streamlit run main.py



================================================================================
                    PARTE III: GUIA DE OPERACION TACTICA                        
================================================================================

La herramienta está diseñada alrededor de una barra de control y seis pestañas equidistantes:

>> 1. PANEL DE CONTROL LATERAL (CONTROL DE ACCESO Y ARCHIVO)
   La barra lateral izquierda actúa como el centro de administración y seguridad del sistema. Desde aquí se definen las autorizaciones del operador y se administran los registros históricos.
   1. Perfil del Operador (Roles): Determina el nivel de privilegios funcionales:
       1.1. Comandante: Habilita la formulación, asignación y marcado de directivas operacionales en el Plan de Acción.
       1.2. Analista: Autoriza la edición de matrices FODA, la participación en votaciones estratégicas y la generación de reportes automáticos de IA.
       1.3. Observador: Modo de visualización pasiva. Restringe la interacción, inhabilitando la edición, adición/eliminación de factores, la votación CAME y la creación de directivas.
    2. Archivo de Misiones (Recovery): Se conecta de forma persistente a una base de datos local SQLite. Permite consultar análisis previos indexados por fecha, hora y rol. Al presionar RESTAURAR HISTÓRICO, las matrices activas se sobrescriben con los datos históricos guardados, forzando la recalculación en cascada de todo el tablero.
    3. Seguridad Operacional y de Red: 
        3.1. Ejecución 100% en Bucle Local: La aplicación web se ejecuta en la dirección de bucle local (http://localhost:8501). Esto significa que el puerto no está expuesto a la red externa ni a internet a menos que tú lo configures explícitamente en el router.
        3.2. Privacidad Absoluta de la IA (Ollama Local): A diferencia de otras soluciones que envían tu información a servidores externos (como OpenAI o Claude) a través de Internet siendo vulnerables a intercepciones "Man-in-the-Middle", tu motor de IA corre de forma local en tu máquina (localhost:11434). Ningún dato estratégico sale del equipo físico.
        3.3. Prevención de Inyección de Código e Inyección SQL: En la base de datos SQLite, las consultas son parametrizadas (se usan placeholders), lo que neutraliza por completo cualquier intento de inyección de código SQL malicioso a través de los formularios. Los factores ingresados por el usuario se sanitizan mediante expresiones regulares neutralizando caracteres de control y scripts maliciosos.
        3.4. Empaquetado de Seguridad (.exe): El empaquetado en un ejecutable cerrado (.exe) dentro de un binario ejecutable comprimido. Esto es un nivel de seguridad: Alto. El usuario solo ve el archivo ejecutable "FODA_S5.exe" siendo imposible leer o modificar el código fuente original.


>> 2. PESTAÑA MATRICES PONDERADAS
   Es la base de datos de entrada del sistema, dividida en factores internos (Fortalezas y Debilidades) y externos (Oportunidades y Amenazas).
   1. Metodología de ponderación FODA: Consta de tres fases:
       1.1. Asignación de Peso (Importancia): A cada factor se le otorga un peso ponderado entre 0.0 y 1.0, dependiendo de su relevancia para la organización, sumando siempre un total de 1.0 (no deberá ser superior a este valor, en cada cuadrante Ej. 1.0 Fortalezas; 1.0 Oportunidades; 1.0 Debilidades; 1.0 Amenazas).
       1.2. Calificación (Desempeño): Se evalúa la situación actual de cada factor respecto a la empresa. Se utiliza una escala de 1.0 a 5.0, donde 5.0 es una respuesta superior y 1.0 deficiente.
       1.3. Cálculo del Total Ponderado: Se multiplica el peso de cada factor por su calificación. Los factores con los totales más altos son aquellos que requieren atención o inversión prioritaria.
   2. Carga y Mapeo NLP Inteligente: A través del cargador de archivos, el operador puede subir archivos CSV o Excel (.xlsx). El sistema ejecuta un mapeo semántico NLP avanzado para identificar automáticamente qué columnas corresponden a cada cuadrante del FODA (incluso si tienen nombres informales o abreviados), cargando la información en segundos.
   3. Edición en Tiempo Real sin Latencia: Las tablas interactivas permiten alterar descripciones de factores, pesos ponderados y calificaciones sin interferencias ni pérdida de foco. Las calificaciones operan en una escala de 1.0 (mínimo) a 5.0 (máximo). Las filas se pueden agregar o eliminar dinámicamente usando los controles interactivos integrados en cada tabla.
    4. Auditoría y Autonormalización MEFI y MEFE: Las funciones de autonormalización de la Matriz de Evaluación de Factores Internos (MEFI) y la Matriz de Evaluación de Factores Externos (MEFE) tienen el propósito de auditar, corregir y balancear matemáticamente los pesos asignados a los factores de las matrices FODA para que cumplan estrictamente con las reglas metodológicas de planeación estratégica.
        4.1. Auditoría de Cumplimiento Metodológico: El sistema fiscaliza de forma constante que la suma de ponderaciones de cada ámbito de la matriz sume exactamente 1.00, por ejemplo:
            4.1.1. Ámbito Interno (MEFI): Suma de Pesos de Fortalezas (F) + Suma de Pesos de Debilidades (D) = 1.00.
            4.1.2. Ámbito Externo (MEFE): Suma de Pesos de Oportunidades (O) + Suma de Pesos de Amenazas (A) = 1.00.
        4.2. Corrección Proporcional: En caso de desbalance, se activan alertas rojas y botones de AUTONORMALIZAR MATRIZ que distribuyen proporcionalmente los pesos de manera matemática automática.

>> 3. PESTAÑA DIAGNÓSTICO ESTRATÉGICO
   Convierte los datos crudos en inteligencia de posicionamiento geográfico/operacional.
   1. Plano de Posicionamiento Vectorial: Muestra un plano cartesiano interactivo de cuatro cuadrantes donde se grafica el vector resultante (X, Y) derivado de los pesos y calificaciones. Su cuadrante define el enfoque operativo recomendado: Ofensivo (FO), Adaptativo (DO), Defensivo (FA) o de Supervivencia (DA).
   2. Métricas de Balance: Integra un gráfico de radar que mapea visualmente la distribución de fuerzas de cada factor, facilitando al Estado Mayor la detección de asimetrías o brechas tácticas de forma inmediata.

>> 4. PESTAÑA ANÁLISIS CAUSA-EFECTO
   El Diagrama de Ishikawa (espina de pescado) se genera 100% de forma dinámica y automática a partir de la información activa que ingresas en las matrices FODA.
   1. La Cabeza del Pescado (El Efecto): Se actualiza sola según el Estado Estratégico actual calculado del vector resultante (ej. DOMINIO TOTAL, SUPERVIVENCIA CRÍTICA, etc.).
   2. Las Espinas del Pescado (Las Causas):
       2.1. Espina de ENTORNO: Toma automáticamente hasta 3 de las Amenazas ingresadas en la matriz FODA.
       2.2. Espinas de TECNOLOGÍA, PERSONAL y PROCESOS: El sistema analiza el texto de tus Debilidades y las clasifica usando palabras clave en tiempo real:
           2.2.1. Tecnología: Si la debilidad contiene palabras como sistema, software, ciber, red, base de datos, tecnología, etc.
           2.2.2. Personal: Si contiene palabras como personal, capacitación, humano, operador, entrenamiento, líder, etc.
           2.2.3. Procesos: Cualquier otra debilidad de la matriz que no caiga en las anteriores se asigna a esta categoría por defecto.

>> 5. PESTAÑA ANÁLISIS DE RIESGO & ESTRÉS
   Modela la viabilidad de la misión bajo escenarios adversos o simulaciones estocásticas.
   1. Prueba de Estrés: Deslizadores de hostilidad y pérdida de recursos que alteran los vectores reales simulando situaciones de degradación crítica.
   2. Simulación Monte Carlo (1000 iteraciones): Proyecta una nube de dispersión de 1,000 caminos posibles para calcular probabilísticamente el éxito de la misión. Si la probabilidad de éxito disminuye a rangos peligrosos, el semáforo de alerta global cambia dinámicamente.

>> 6. PESTAÑA INFORME IA & EXPORTACIÓN
   Genera documentación formal clasificada y exportaciones de alta fidelidad.
    1. Motor de Inteligencia Artificial (Ollama + Llama3): A partir de las matrices activas, redacta un informe militar clasificado y estructurado (SITUACIÓN GENERAL, AMENAZAS, RIESGOS y LÍNEAS DE ACCIÓN), parafraseado y sin emojis. Los rubros de Amenazas, Riesgos y Líneas de Acción se numeran automáticamente con números arábigos estándar (1., 2., 3., etc.) sin ceros a la izquierda, con sangría alineada y texto justificado. Asimismo, el texto de "🔵 SITUACIÓN GENERAL" se presenta de forma justificada en prosa.
   2. Exportación en PDF y Excel: El botón de exportación genera un PDF horizontal optimizado para HUD o un archivo de Excel consolidando los datos en 7 pestañas estructuradas.

>> 7. PESTAÑA MANDO Y BITÁCORA
   Facilita el control de la reunión táctica en tiempo real:
   1. Mando Compartido (Votación CAME): Permite a los analistas emitir votos en favor de las estrategias recomendadas. El consenso y la visualización de porcentajes de decisión se ajustan dinámicamente al total de votantes elegidos en el selector (1 a 25), con barras de progreso de alta estética.
   2. Plan de Acción Directivo: Lista de tareas y directivas de control exclusivo del Comandante.
       2.1. Roles tácticos en el Plan de Acción: El ingreso de directivas y tareas en el plan de acción es exclusivo para el rol de Comandante. Por defecto, cuando abres la herramienta, tu perfil se inicializa como Analista (lo que te permite modificar matrices, votar y generar reportes de IA, pero no formular directivas).
       2.2. Cómo habilitar los controles de ingreso de directivas:
           2.2.1. Ve a la barra lateral izquierda (debajo de la imagen táctica).
           2.2.2. Localiza el selector con el título "Perfil del Operador".
           2.2.3. Cambia tu perfil de Analista a Comandante.
           2.2.4. ¡Listo! Vuelve a la pestaña MANDO Y BITÁCORA y verás que en la sección derecha (ACTION_PLAN) ha aparecido el campo de entrada "Nueva Acción Directiva" y el botón "AÑADIR ACCIÓN".
   3. Bitácora del Turno (Audit Log): Registro inmutable de eventos del sistema (modificaciones, votos, normalizaciones) para auditorías de operaciones.

>> 8. ALERTA HUD 100% DINÁMICA (FÓRMULA DE RIESGO REAL)
   ¿Qué función tiene?: Evalúa algorítmicamente en tiempo real la viabilidad de la misión basándose en la probabilidad de éxito de las simulaciones y el nivel de hostilidad de los factores:
   1. VERDE (Normal): Probabilidad de éxito > 70% sin amenazas de alto nivel. Indica una postura táctica segura.
   2. AMARILLO (Precaución): Probabilidad de éxito entre 40% y 70%. Requiere monitoreo constante y preparación de planes de mitigación.
   3. ROJO (Crítico): Probabilidad de éxito < 40%, o si se califica alguna amenaza en la Matriz A con rango severo (>= 4.5), o estrés de simulación crítico (> 20.0). Demanda una acción inmediata de re-evaluación o retirada.
