import { TRAFFIC_LIGHT } from '../utils/colors';

export default function TrafficLight({ value, reason, compact = false }) {
  const s = TRAFFIC_LIGHT[value] ?? TRAFFIC_LIGHT.gris;
  return (
    <span className={`semaforo semaforo-${value in TRAFFIC_LIGHT ? value : 'gris'}`} title={reason}>
      <span aria-hidden="true">{s.icon}</span>
      {compact ? <span className="solo-lector">{s.label}</span> : s.label}
    </span>
  );
}
