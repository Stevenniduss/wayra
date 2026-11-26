import { ArrowUp, Cloud, CloudMoon, CloudRain, CloudSun, Moon, Snowflake, Sun } from 'lucide-react';
import { SKY_LABEL, windArrowRotation } from '../utils/weather';

const ICONS = {
  nieve: [Snowflake, 'icono-nieve'],
  lluvia: [CloudRain, 'icono-lluvia'],
  nublado: [Cloud, 'icono-nube'],
  'parcial-dia': [CloudSun, 'icono-sol'],
  'parcial-noche': [CloudMoon, 'icono-luna'],
  'despejado-dia': [Sun, 'icono-sol'],
  'despejado-noche': [Moon, 'icono-luna'],
};

export function SkyIcon({ sky, size = 28 }) {
  const [Icon, className] = ICONS[sky] ?? ICONS.nublado;
  return <Icon size={size} className={className} aria-label={SKY_LABEL[sky]} strokeWidth={1.8} />;
}

export function WindArrow({ grados, size = 16 }) {
  return (
    <ArrowUp
      size={size}
      className="flecha-viento"
      style={{ transform: `rotate(${windArrowRotation(grados)}deg)` }}
      aria-hidden="true"
    />
  );
}
