import { Droplets, Thermometer, Wind } from 'lucide-react';
import { SKY_LABEL, skyOf } from '../utils/weather';
import TrafficLight from './TrafficLight';
import { SkyIcon, WindArrow } from './WeatherIcon';

// First hour of the forecast, shown big like the "now" block of weather sites.
export default function NowPanel({ point }) {
  const h = point.horas[0];
  if (!h) return null;
  const sky = skyOf(h);

  return (
    <section className="ahora tarjeta-elevada">
      <div className="ahora-principal">
        <SkyIcon sky={sky} size={64} />
        <div>
          <div className="ahora-temp">{Math.round(h.temperatura_c)}°</div>
          <div className="ahora-cielo">{SKY_LABEL[sky]}</div>
        </div>
      </div>

      <div className="ahora-datos">
        <div>
          <Thermometer size={18} />
          <span>Sensación</span>
          <strong>{h.sensacion_termica_c} °C</strong>
        </div>
        <div>
          <Wind size={18} />
          <span>Viento</span>
          <strong>
            {h.viento_kmh} km/h <WindArrow grados={h.viento_dir_grados} /> {h.viento_dir_texto}
          </strong>
        </div>
        <div>
          <Droplets size={18} />
          <span>Humedad</span>
          <strong>{h.humedad_pct} %</strong>
        </div>
        <div>
          <Droplets size={18} className="icono-rocio" />
          <span>Punto de rocío</span>
          <strong>{h.punto_rocio_c} °C</strong>
        </div>
      </div>

      <div className="ahora-pie">
        <span>
          {point.nombre} · {point.altitud_real_m} m · {h.hora_lima}
        </span>
        <TrafficLight value={h.semaforo} reason={h.semaforo_motivo} />
      </div>
      <p className="ahora-motivo">{h.semaforo_motivo}</p>
    </section>
  );
}
