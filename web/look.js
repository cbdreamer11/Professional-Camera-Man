/* Look measurement: turns a picture (reference photo, or the live monitor) into a few numbers.
   Everything runs in the browser. Brightness is the picture's own 0–255 value (gamma-coded), the same scale the
   recommendations use. Assumes the person sits roughly in the middle of the frame. */
const Look = (() => {
  const cv = document.createElement('canvas');
  const cx = cv.getContext('2d', { willReadFrequently: true });
  const BOX = {                               // fractions of the frame
    face: [0.35, 0.15, 0.65, 0.55],
    left: [0.36, 0.25, 0.49, 0.50],
    right: [0.51, 0.25, 0.64, 0.50],
    card: [0.40, 0.40, 0.60, 0.60],
  };

  function grab(src, maxW = 320) {
    const w0 = src.videoWidth || src.naturalWidth || src.width, h0 = src.videoHeight || src.naturalHeight || src.height;
    if (!w0 || !h0) return null;
    const k = Math.min(1, maxW / w0), w = Math.round(w0 * k), h = Math.round(h0 * k);
    cv.width = w; cv.height = h; cx.drawImage(src, 0, 0, w, h);
    return { px: cx.getImageData(0, 0, w, h).data, w, h };
  }
  function mean(img, box) {
    const x0 = Math.round(box[0] * img.w), y0 = Math.round(box[1] * img.h), x1 = Math.round(box[2] * img.w), y1 = Math.round(box[3] * img.h);
    let r = 0, g = 0, b = 0, l = 0, sat = 0, n = 0;
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
      const i = (y * img.w + x) * 4, R = img.px[i], G = img.px[i + 1], B = img.px[i + 2];
      r += R; g += G; b += B; l += 0.2126 * R + 0.7152 * G + 0.0722 * B;
      const mx = Math.max(R, G, B); sat += mx ? (mx - Math.min(R, G, B)) / mx : 0; n++;
    }
    n = n || 1;
    return { r: r / n, g: g / n, b: b / n, l: l / n, sat: sat / n };
  }
  function analyze(src) {
    const img = grab(src); if (!img) return null;
    const f = mean(img, BOX.face), L = mean(img, BOX.left), R = mean(img, BOX.right);
    const bgL = mean(img, [0, 0, 0.12, 1]), bgR = mean(img, [0.88, 0, 1, 1]);
    const hist = new Uint32Array(256); let tot = 0, sum = 0;
    for (let i = 0; i < img.px.length; i += 16) { const l = Math.round(0.2126 * img.px[i] + 0.7152 * img.px[i + 1] + 0.0722 * img.px[i + 2]); hist[l]++; tot++; sum += l; }
    const pct = q => { let a = 0; for (let i = 0; i < 256; i++) { a += hist[i]; if (a >= tot * q) return i; } return 255; };
    const hi = Math.max(L.l, R.l), lo = Math.max(1, Math.min(L.l, R.l)), ratio = hi / lo;
    return {
      face_luma: Math.round(f.l), luma_mean: Math.round(sum / tot), bg_luma: Math.round((bgL.l + bgR.l) / 2),
      cheek_ratio: +ratio.toFixed(2), bright_side: ratio < 1.04 ? 'even' : (L.l > R.l ? 'left' : 'right'),
      rb_ratio: +(f.r / Math.max(1, f.b)).toFixed(2), saturation: +f.sat.toFixed(2), contrast: +(pct(0.95) / Math.max(1, pct(0.05))).toFixed(1),
    };
  }
  function card(src) { const img = grab(src); if (!img) return null; const m = mean(img, BOX.card); return { r: m.r, g: m.g, b: m.b }; }
  return { analyze, card, BOX };
})();
