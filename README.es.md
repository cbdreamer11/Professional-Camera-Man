# Professional Camera Man

**Tu propio equipo de cámara en una pestaña del navegador.** Una pantalla que muestra tu cámara, inicia y detiene la grabación, corre tu teleprompter en el momento justo y te dice —con números, para *tu* cuarto— qué cambiar en tus luces y ajustes para que la imagen se vea como quieres.

🇺🇸 [English README](README.md) · Creado por [Caleb Elizondo](https://github.com/cbdreamer11)

> **Estado, con honestidad.** El adaptador de **Canon (CCAPI)** se construyó y se probó con una Canon EOS R50 V real. Los de Blackmagic, GoPro, Sony, OSC y Personalizado están escritos a partir de la documentación pública de cada fabricante y tienen pruebas automáticas contra cámaras simuladas — **todavía no se han probado con cámaras reales**. La app marca en pantalla cada adaptador como *probado* o *sin probar*. Reportes y correcciones son bienvenidos.

## Qué hace

| | |
|---|---|
| 🎥 **Pantalla de estudio** | Monitor en vivo, botón GRABAR, zoom, enfoque, ISO / apertura / velocidad / balance de blancos, escenas (looks guardados), batería, espacio en tarjeta, aviso si se desconecta el micrófono. Pensada para una tele o monitor junto a la cámara; también sirve en teléfono o tablet. |
| 📜 **Teleprompter** | Sube `.txt`, `.md` o `.docx` (o pega el texto). Velocidad en palabras por minuto, tamaño, modo espejo para el cristal del teleprompter, espacio bajo el lente para leer *a cámara*. El texto `[entre corchetes]` es una indicación: se ve atenuado y no cuenta. Funciona **solo, sin servidor ni cámara** — pruébalo en línea (abajo). |
| 🎬 **Toma con un botón** | GRABAR: corre una cuenta regresiva, la cámara arranca unos segundos antes que el texto (te quedan segundos limpios para editar) y el texto empieza a correr. Otro toque y todo se detiene. |
| 💡 **Asistente de configuración** | Pregunta el **look** (corporativo, podcast, cinematográfico, brillante, tech o "igualar mi foto de referencia"), mide una **foto de referencia** (brillo, de qué lado viene la luz, contraste de mejillas, calidez), pregunta tu **cámara y su API**, y tus **luces y a qué distancia están** — dibuja tu set desde arriba y te dice qué cambiar. |
| 🎯 **Igualar el look** | Mide el monitor en vivo contra tu referencia o estilo: brillo de la cara, mejillas, lado de la luz, calidez. Te dice, por ejemplo: *«La cara está 21% bajo la meta: ≈ +0.8 paso — sube el ISO a ~1600, o acerca la luz principal de 100 a ~75 cm.»* |
| ⚪ **Hoja blanca** | Muestra una hoja blanca, presiona *Medir*: te dice si subir o bajar los Kelvin. |
| 🔌 **Pon la API de tu cámara** | Cada marca es un *adaptador* (un archivo Python pequeño). O describe cualquier cámara con HTTP en un archivo JSON — sin programar. |
| 🖥 **¿Sin API? Sin problema** | Elige «entrada de video»: cualquier webcam, capturadora HDMI, o DJI/GoPro/Sony en modo webcam USB aparece como monitor, con cuadrícula, igualar el look y teleprompter. |

## Inicio rápido (2 minutos)

Necesitas **Python 3.8+**. Nada más: sin dependencias, sin cuentas, nada que instalar con `pip`.

```bash
git clone https://github.com/cbdreamer11/Professional-Camera-Man.git
cd Professional-Camera-Man
./install.sh          # macOS / Linux.  Windows:  py pcm.py
```

Pregunta cómo quieres describir tu estudio (asistente en el navegador o en la terminal) y abre <http://localhost:8770>.

**¿Quieres verlo antes, sin cámara?**

```bash
python3 tests/demo.py        # cámara falsa + un set de ejemplo → http://localhost:8771
```

**¿Solo el teleprompter?** Abre [`web/teleprompter.html`](web/teleprompter.html) en cualquier navegador, o usa la copia en línea: <https://cbdreamer11.github.io/Professional-Camera-Man/teleprompter.html> (tus guiones se quedan en tu navegador; no se sube nada).

## Configurar con Claude (opcional)

Abre la carpeta en [Claude Code](https://claude.com/claude-code) y corre **`/setup-studio`**. Claude te entrevista en lenguaje normal —estilo, foto de referencia, marca y dirección de la cámara, cada luz y a qué distancia está—, escribe tu perfil, prueba la conexión y te explica los consejos. Son las mismas preguntas del asistente y el mismo archivo de perfil.

## Cámaras

| Adaptador | Cómo habla | Estado |
|---|---|---|
| **Canon** EOS R50 V (y otros con CCAPI) | Camera Control API por Wi-Fi | ✅ **probado** en R50 V — [notas y trampas](docs/CANON_CCAPI.md) |
| **Blackmagic** Pocket / URSA | API REST (`/control/api/v1`) | ⚠️ sin probar — de la documentación oficial |
| **GoPro** HERO9+ | Open GoPro HTTP (endpoints del SDK de GoPro) | ⚠️ sin probar — grabar, batería, tiempo de tarjeta, resolución/fps, zoom digital, vista en vivo (requiere `ffmpeg`; la vista en vivo se verificó con un stream simulado) |
| **Sony** (modelos Wi-Fi antiguos) | Camera Remote API (JSON-RPC) | ⚠️ sin probar — los Alpha nuevos necesitan el SDK de Sony, ver [CAMERAS](docs/CAMERAS.md) |
| **OSC** (Ricoh Theta, algunas Insta360…) | Open Spherical Camera | ⚠️ sin probar |
| **Personalizado** | Tu propia descripción en JSON | ⚠️ funciona hasta donde sea correcta tu descripción |
| **Entrada de video** (DJI Osmo, GoPro modo webcam, capturadoras, cualquier webcam) | El acceso a cámara del navegador | ✅ sirve con todo lo que el navegador vea |

## Agrega la API de tu cámara

* **Sin código:** copia [`profiles/custom_api_example.json`](profiles/custom_api_example.json), describe los endpoints de tu cámara y elige «Personalizado» en el asistente.
* **Python:** copia `pcm/adapters/canon_ccapi.py`, cambia lo que envía y deja el archivo en `pcm/adapters/` (o en `data/adapters/` para mantenerlo privado). Se detecta solo.

Guía completa: [docs/ADAPTERS.md](docs/ADAPTERS.md).

## Cómo se calculan los consejos

Práctica estándar convertida en números para *tus* distancias: la regla del obturador de 180° ajustada a una velocidad sin parpadeo para tu frecuencia eléctrica, rangos de ángulo y altura de la luz principal por estilo, ley del inverso del cuadrado para la proporción principal:relleno y para «mueve el relleno a X cm», caída de luz a lo ancho de una cara, aviso de temperaturas de color mezcladas, y revisión de distancia a la cámara y al fondo. Ver [docs/LIGHTING.md](docs/LIGHTING.md). Son *estimaciones*: el panel de Look mide la imagen real.

## Licencia y crédito

[**Professional Camera Man License** — MIT + Atribución](LICENSE). Gratis para uso personal **y comercial**: modifícalo, vende lo que construyas con él. **Una sola condición: conserva visible el crédito «Created by Caleb Elizondo» en la interfaz** (es el footer de cada página, ya incluido). Los nombres de marcas de cámaras son de sus dueños; este proyecto es independiente de todos ellos. Sin garantía.

© 2026 Caleb Elizondo · <https://github.com/cbdreamer11>
