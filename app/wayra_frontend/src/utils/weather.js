import { colorRgb } from './colors';

// "26/11 14:00" -> 14
export const hourOf = (horaLima) => Number(horaLima.slice(6, 8));
export const dayOf = (horaLima) => horaLima.slice(0, 5);

const isDay = (horaLima) => {
  const h = hourOf(horaLima);
  return h >= 6 && h < 18;
};

// Icon for an hour. Rain comes from Open-Meteo, the rest from WAYRA.
export function skyOf(hour) {
  if (hour.lluvia_mm != null && hour.lluvia_mm >= 0.5) {
    return hour.bajo_cero ? 'nieve' : 'lluvia';
  }
  if (hour.humedad_pct >= 90) return 'nublado';
  if (hour.humedad_pct >= 75) return isDay(hour.hora_lima) ? 'parcial-dia' : 'parcial-noche';
  return isDay(hour.hora_lima) ? 'despejado-dia' : 'despejado-noche';
}

export const SKY_LABEL = {
  nieve: 'Nieve posible',
  lluvia: 'Lluvia posible',
  nublado: 'Muy húmedo / nublado',
  'parcial-dia': 'Parcialmente húmedo',
  'parcial-noche': 'Parcialmente húmedo',
  'despejado-dia': 'Seco',
  'despejado-noche': 'Seco',
};

// Soft background for a temperature cell; works in both themes.
export function tempBackground(t, alpha = 0.35) {
  const [r, g, b] = colorRgb('temperatura', t);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Arrow points to where the wind goes (API gives where it comes from).
export const windArrowRotation = (grados) => (grados == null ? 0 : (grados + 180) % 360);
