import { skyOf, tempBackground } from '../utils/weather';
import TrafficLight from './TrafficLight';
import { SkyIcon, WindArrow } from './WeatherIcon';

export default function ForecastTable({ hours }) {
  return (
    <div className="tabla-scroll">
      <table className="tabla">
        <thead>
          <tr>
            <th>Hora</th>
            <th aria-label="Cielo" />
            <th>Estado</th>
            <th>Temp.</th>
            <th>Sensación</th>
            <th>Rocío</th>
            <th>Humedad</th>
            <th>Viento</th>
            <th>Lluvia*</th>
          </tr>
        </thead>
        <tbody>
          {hours.map((h) => (
            <tr key={h.valido_utc}>
              <td>{h.hora_lima}</td>
              <td>
                <SkyIcon sky={skyOf(h)} size={20} />
              </td>
              <td>
                <TrafficLight value={h.semaforo} reason={h.semaforo_motivo} />
              </td>
              <td>
                <span className="celda-temp" style={{ background: tempBackground(h.temperatura_c) }}>
                  {h.temperatura_c} °C{h.bajo_cero && ' ❄'}
                </span>
              </td>
              <td>{h.sensacion_termica_c} °C</td>
              <td>{h.punto_rocio_c} °C</td>
              <td>
                <span className="barra-humedad" style={{ '--pct': `${h.humedad_pct}%` }}>
                  {h.humedad_pct} %
                </span>
                {h.humedad_elevada && ' · alta'}
              </td>
              <td>
                <WindArrow grados={h.viento_dir_grados} size={14} /> {h.viento_kmh} km/h{' '}
                {h.viento_dir_texto ?? ''}
              </td>
              <td>{h.lluvia_mm == null ? '—' : `${h.lluvia_mm} mm`}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="nota">
        Pasa el cursor sobre el estado para ver el motivo. *La lluvia viene de Open-Meteo (GFS), no del
        modelo WAYRA.
      </p>
    </div>
  );
}
