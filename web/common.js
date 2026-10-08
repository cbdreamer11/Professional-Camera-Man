/* Professional Camera Man — shared bits: language, API helper, toast, credit footer. */
const PCM = (() => {
  const CREDIT = 'Created by Caleb Elizondo';
  const CREDIT_URL = 'https://github.com/cbdreamer11';

  const DICT = {
    en: {
      app: 'Professional Camera Man', studio: 'Studio', setup: 'Setup', teleprompter: 'Teleprompter',
      rec: 'REC', stop: 'STOP', cancel: 'CANCEL', ready: 'Ready', no_camera: 'No camera', connecting: 'Connecting to the camera…',
      connect_hint: 'Turn it on and enable its network/remote control. Details in Setup.', recording: 'Recording',
      zoom: 'Zoom (hold)', wide: '− Wide', tele: 'Tele +', focus: 'Focus', af: 'AF',
      iso: 'ISO', aperture: 'Aperture', shutter: 'Shutter', wb: 'White bal.', kelvin: 'Kelvin',
      grid: 'Grid', look: 'Look', release: 'Release camera', take: 'Take camera', source_cam: 'Camera feed', source_vid: 'Video input',
      pick_video: 'Choose a video input', no_video: 'No video input found (or permission denied).', scenes: 'Scenes',
      save_scene: '+ Save scene', scene_name: 'Scene name', save: 'Save', delete: 'Delete', close: 'Close', apply_rec: 'Apply recommended',
      advanced: 'Advanced settings', saved: 'Saved', applied: 'Applied', failed: 'Failed',
      battery: 'Battery', storage: 'Storage', left: 'left', free_of: '{a} free of {b}', status: 'Status', lens: 'Lens',
      mic_dropped: '⚠ The external microphone disconnected', mic_ext: '🎙 External microphone connected', mic_int: 'Internal microphone (no external one detected)',
      untested: 'This adapter has not been tested on real hardware yet.', tested: 'Tested on real hardware',
      your_studio: 'Your studio', edit_setup: 'Edit setup', no_profile: 'No setup yet — run the wizard.', style: 'Look',
      advice: 'Advice for your set', nothing_to_fix: 'Nothing to fix.', look_title: 'Look match', look_vs_ref: 'Reference photo', look_vs_style: 'Style target',
      look_face: 'Face brightness', look_cheek: 'Cheek ratio (light vs shadow side)', look_warm: 'Warmth (R/B)', look_side: 'Lit from',
      look_measuring: 'Measuring the box in the monitor — sit in the middle of the frame.', look_on: 'Measure', look_off: 'Stop',
      left_s: 'left', right_s: 'right', even: 'even', white_card: 'White card', white_card_help: 'Hold a white sheet in the box and press Measure.',
      measure: 'Measure', wc_neutral: 'Neutral. White balance is right.', wc_blue: 'Bluish ({p}%): raise Kelvin ≈ +{k} K and measure again.',
      wc_red: 'Reddish ({p}%): lower Kelvin ≈ {k} K and measure again.', wc_apply: 'Apply',
      too_dark: 'Face is {p}% under the target: ≈ +{s} stop. Raise ISO to ~{iso}, or move the key light from {d0} to ~{d1} cm.',
      too_bright: 'Face is {p}% over the target: ≈ −{s} stop. Lower ISO to ~{iso}, dim the key light, or move it back to ~{d1} cm.',
      face_ok: 'Face brightness is inside the target.',
      cheek_high: 'Too much contrast between cheeks. Add fill (or bring it closer), or move the key closer to the camera axis.',
      cheek_low: 'Very flat. Swing the key light farther off axis or lower the fill.', cheek_ok: 'Cheek contrast is inside the target.',
      countdown_cancel: 'Tap REC again to cancel', cam_starts: 'Camera starts in {n}', text_starts: '● Recording · text starts in {n}',
      busy: 'The camera cannot record right now (memory card inserted? still on its menu?)',
      server_off: 'The studio server is not running.', reference: 'Reference',
      scripts: 'Scripts', open: 'Open', edit: 'Edit', add_files: 'Add files', paste_new: 'Paste a script', drop_here: 'Drop .txt, .md or .docx files here — or click to choose',
      words: 'words', min: 'min', untitled: 'Untitled', title: 'Title', text: 'Text', export_lib: 'Export library', import_lib: 'Import library',
      speed: 'Speed (wpm)', font: 'Text size', mirror: 'Mirror', restart: 'Restart', play: '▶ Play', pause: '⏸ Pause', list: '☰ List',
      lens_gap: 'Gap under the lens (% of screen)', width: 'Text width (%)', countdown: 'Countdown (s)', settings: 'Settings',
      pdf_hint: 'PDF is not supported: export it as .docx or .txt, or paste the text.', empty_lib: 'No scripts yet. Add a file or paste one.',
      brackets_hint: 'Tip: text in [square brackets] is shown dimmed and is not counted as spoken words.',
      confirm_delete: 'Delete this script?', imported: 'Imported {n} script(s)', read_error: 'Could not read {f}',
      hotkeys: 'Space play/pause · ↑↓ speed · A/Z text size · M mirror · Home restart · Esc list',
      started_with: 'Open source — free to use. Keep the credit.', done: 'Done', wiz_next: 'Next', wiz_back: 'Back', wiz_finish: 'Save and open the studio',
    },
    es: {
      app: 'Professional Camera Man', studio: 'Estudio', setup: 'Configuración', teleprompter: 'Teleprompter',
      rec: 'GRABAR', stop: 'DETENER', cancel: 'CANCELAR', ready: 'Lista', no_camera: 'Sin cámara', connecting: 'Conectando con la cámara…',
      connect_hint: 'Enciéndela y activa su red/control remoto. Detalles en Configuración.', recording: 'Grabando',
      zoom: 'Zoom (mantén)', wide: '− Abrir', tele: 'Cerrar +', focus: 'Enfoque', af: 'AF',
      iso: 'ISO', aperture: 'Apertura', shutter: 'Velocidad', wb: 'Balance', kelvin: 'Kelvin',
      grid: 'Cuadrícula', look: 'Look', release: 'Soltar cámara', take: 'Tomar cámara', source_cam: 'Señal de la cámara', source_vid: 'Entrada de video',
      pick_video: 'Elige una entrada de video', no_video: 'No hay entradas de video (o se negó el permiso).', scenes: 'Escenas',
      save_scene: '+ Guardar escena', scene_name: 'Nombre de la escena', save: 'Guardar', delete: 'Borrar', close: 'Cerrar', apply_rec: 'Aplicar lo recomendado',
      advanced: 'Ajustes avanzados', saved: 'Guardado', applied: 'Aplicado', failed: 'Falló',
      battery: 'Batería', storage: 'Almacenamiento', left: 'restante', free_of: '{a} libres de {b}', status: 'Estado', lens: 'Lente',
      mic_dropped: '⚠ Se desconectó el micrófono externo', mic_ext: '🎙 Micrófono externo conectado', mic_int: 'Micrófono interno (no se detecta uno externo)',
      untested: 'Este adaptador todavía no se ha probado con una cámara real.', tested: 'Probado con una cámara real',
      your_studio: 'Tu estudio', edit_setup: 'Editar configuración', no_profile: 'Aún no hay configuración — corre el asistente.', style: 'Look',
      advice: 'Consejos para tu set', nothing_to_fix: 'Nada que corregir.', look_title: 'Igualar el look', look_vs_ref: 'Foto de referencia', look_vs_style: 'Meta del estilo',
      look_face: 'Brillo de la cara', look_cheek: 'Relación entre mejillas (luz vs sombra)', look_warm: 'Calidez (R/B)', look_side: 'Luz desde',
      look_measuring: 'Midiendo el recuadro del monitor — siéntate en el centro del cuadro.', look_on: 'Medir', look_off: 'Parar',
      left_s: 'izquierda', right_s: 'derecha', even: 'pareja', white_card: 'Hoja blanca', white_card_help: 'Pon una hoja blanca en el recuadro y presiona Medir.',
      measure: 'Medir', wc_neutral: 'Neutral. El balance de blancos está bien.', wc_blue: 'Azulada ({p}%): sube Kelvin ≈ +{k} K y mide otra vez.',
      wc_red: 'Rojiza ({p}%): baja Kelvin ≈ {k} K y mide otra vez.', wc_apply: 'Aplicar',
      too_dark: 'La cara está {p}% bajo la meta: ≈ +{s} paso. Sube el ISO a ~{iso}, o acerca la luz principal de {d0} a ~{d1} cm.',
      too_bright: 'La cara está {p}% sobre la meta: ≈ −{s} paso. Baja el ISO a ~{iso}, atenúa la luz principal o aléjala a ~{d1} cm.',
      face_ok: 'El brillo de la cara está dentro de la meta.',
      cheek_high: 'Demasiado contraste entre mejillas. Agrega relleno (o acércalo), o acerca la luz principal al eje de la cámara.',
      cheek_low: 'Se ve muy plano. Abre más la luz principal respecto al eje o baja el relleno.', cheek_ok: 'El contraste entre mejillas está dentro de la meta.',
      countdown_cancel: 'Toca GRABAR otra vez para cancelar', cam_starts: 'La cámara graba en {n}', text_starts: '● Grabando · el texto arranca en {n}',
      busy: 'La cámara no puede grabar ahora (¿tiene tarjeta? ¿está en su menú?)',
      server_off: 'El servidor del estudio no está corriendo.', reference: 'Referencia',
      scripts: 'Guiones', open: 'Abrir', edit: 'Editar', add_files: 'Subir archivos', paste_new: 'Pegar un guion', drop_here: 'Suelta aquí archivos .txt, .md o .docx — o haz clic para elegirlos',
      words: 'palabras', min: 'min', untitled: 'Sin título', title: 'Título', text: 'Texto', export_lib: 'Exportar biblioteca', import_lib: 'Importar biblioteca',
      speed: 'Velocidad (ppm)', font: 'Tamaño del texto', mirror: 'Espejo', restart: 'Inicio', play: '▶ Iniciar', pause: '⏸ Pausa', list: '☰ Lista',
      lens_gap: 'Espacio bajo el lente (% de pantalla)', width: 'Ancho del texto (%)', countdown: 'Cuenta regresiva (s)', settings: 'Ajustes',
      pdf_hint: 'No se admite PDF: expórtalo a .docx o .txt, o pega el texto.', empty_lib: 'Aún no hay guiones. Sube un archivo o pega uno.',
      brackets_hint: 'Tip: el texto entre [corchetes] se ve atenuado y no cuenta como palabras habladas.',
      confirm_delete: '¿Borrar este guion?', imported: 'Se importaron {n} guion(es)', read_error: 'No se pudo leer {f}',
      hotkeys: 'Espacio inicia/pausa · ↑↓ velocidad · A/Z tamaño · M espejo · Inicio reinicia · Esc lista',
      started_with: 'Código abierto — úsalo gratis. Conserva el crédito.', done: 'Listo', wiz_next: 'Siguiente', wiz_back: 'Atrás', wiz_finish: 'Guardar y abrir el estudio',
    },
  };

  let lang = 'en';
  try { lang = localStorage.getItem('pcm_lang') || ((navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en'); } catch (e) {}
  const t = (k, vars) => {
    let s = (DICT[lang] && DICT[lang][k]) || DICT.en[k] || k;
    if (vars) for (const v in vars) s = s.replaceAll('{' + v + '}', vars[v]);
    return s;
  };
  function setLang(l) {
    lang = l === 'es' ? 'es' : 'en';
    try { localStorage.setItem('pcm_lang', lang); } catch (e) {}
    document.documentElement.lang = lang; translate();
  }
  function translate(root) {
    (root || document).querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    (root || document).querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  }

  async function api(method, path, body) {
    const r = await fetch(path, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    let d = {}; try { d = await r.json(); } catch (e) {}
    if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
    return d;
  }

  function toast(msg, ok) {
    let el = document.getElementById('toast');
    if (!el) { el = document.createElement('div'); el.id = 'toast'; document.body.appendChild(el); }
    el.textContent = msg; el.className = 'show' + (ok ? ' ok' : '');
    clearTimeout(el._h); el._h = setTimeout(() => { el.className = ''; }, 3800);
  }

  /* The credit footer. The licence requires keeping it visible (see LICENSE). */
  function footer() {
    if (document.getElementById('credit')) return;
    const f = document.createElement('footer');
    f.id = 'credit';
    f.innerHTML = '<a href="' + CREDIT_URL + '" target="_blank" rel="noopener">' + CREDIT + '</a>';
    document.body.appendChild(f);
  }

  document.documentElement.lang = lang;
  document.addEventListener('DOMContentLoaded', () => { translate(); footer(); });
  return { t, setLang, get lang() { return lang; }, translate, api, toast, footer, CREDIT, CREDIT_URL };
})();
