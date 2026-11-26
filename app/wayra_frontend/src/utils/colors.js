// Traffic light: never color alone, always icon + word (RNF005).
export const TRAFFIC_LIGHT = {
  verde: { icon: '✓', label: 'Favorable', color: '#1a7f37', background: '#dafbe1' },
  amarillo: { icon: '!', label: 'Precaución', color: '#7d4e00', background: '#fff1c2' },
  rojo: { icon: '✕', label: 'Desfavorable', color: '#b42318', background: '#fde2e1' },
  gris: { icon: '?', label: 'Sin datos', color: '#57606a', background: '#eaeef2' },
};

// Fixed scales so two maps (GFS and WAYRA) can be compared by eye.
export const SCALES = {
  temperatura: {
    unit: '°C',
    stops: [
      [-15, '#313695'],
      [-5, '#74add1'],
      [0, '#e0f3f8'],
      [5, '#fee090'],
      [15, '#f46d43'],
      [25, '#a50026'],
    ],
  },
  humedad: {
    unit: '%',
    stops: [
      [0, '#fff7ec'],
      [40, '#c6dbef'],
      [70, '#6baed6'],
      [100, '#08306b'],
    ],
  },
  viento: {
    unit: 'km/h',
    stops: [
      [0, '#f7fcf5'],
      [15, '#a1d99b'],
      [30, '#fdae6b'],
      [50, '#e6550d'],
      [70, '#7f0000'],
    ],
  },
};

const hexToRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));

export function colorRgb(variable, value) {
  const stops = SCALES[variable].stops;
  if (value == null || Number.isNaN(value)) return [200, 200, 200];
  if (value <= stops[0][0]) return hexToRgb(stops[0][1]);
  for (let i = 1; i < stops.length; i += 1) {
    const [v1, c1] = stops[i];
    if (value <= v1) {
      const [v0, c0] = stops[i - 1];
      const t = (value - v0) / (v1 - v0);
      const a = hexToRgb(c0);
      const b = hexToRgb(c1);
      return a.map((x, k) => Math.round(x + (b[k] - x) * t));
    }
  }
  return hexToRgb(stops[stops.length - 1][1]);
}

export const VARIABLES = [
  ['temperatura', 'Temperatura'],
  ['humedad', 'Humedad'],
  ['viento', 'Viento'],
];
