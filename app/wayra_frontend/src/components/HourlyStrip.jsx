import { Fragment } from 'react';
import { dayOf, hourOf, skyOf, tempBackground } from '../utils/weather';
import { SkyIcon, WindArrow } from './WeatherIcon';

// Horizontal strip, one column per hour (meteogram style).
export default function HourlyStrip({ hours }) {
  return (
    <div className="franja tarjeta-elevada">
      <div className="franja-scroll">
        {hours.map((h, i) => {
          const newDay = i === 0 || hourOf(h.hora_lima) === 0;
          return (
            <Fragment key={h.valido_utc}>
              {newDay && <div className="franja-dia">{dayOf(h.hora_lima)}</div>}
              <div className="franja-hora" title={h.semaforo_motivo}>
                <span className="franja-h">{String(hourOf(h.hora_lima)).padStart(2, '0')}h</span>
                <SkyIcon sky={skyOf(h)} size={22} />
                <span className="franja-temp" style={{ background: tempBackground(h.temperatura_c, 0.45) }}>
                  {Math.round(h.temperatura_c)}°
                </span>
                <span className="franja-viento">
                  <WindArrow grados={h.viento_dir_grados} size={13} />
                  {h.viento_kmh}
                </span>
                <span className="franja-lluvia">{h.lluvia_mm ? `${h.lluvia_mm}` : ''}</span>
                <span className={`franja-semaforo semaforo-barra-${h.semaforo}`} />
              </div>
            </Fragment>
          );
        })}
      </div>
      <div className="franja-leyenda">
        <span>Temperatura °C</span>
        <span>Viento km/h (la flecha indica hacia dónde sopla)</span>
        <span>Lluvia mm (Open-Meteo)</span>
        <span>Barra inferior: semáforo</span>
      </div>
    </div>
  );
}
