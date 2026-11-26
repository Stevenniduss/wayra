import { Link, useParams } from 'react-router-dom';
import { getForecast, getWindows } from '../api/api';
import { ErrorMessage, Loading } from '../components/Status';
import TrafficLight from '../components/TrafficLight';
import { TRAFFIC_LIGHT } from '../utils/colors';
import { useApi } from '../utils/useApi';

function summary(point) {
  const h = point.horas;
  return {
    minTemp: Math.min(...h.map((x) => x.temperatura_c)),
    minFeels: Math.min(...h.map((x) => x.sensacion_termica_c)),
    maxWind: Math.max(...h.map((x) => x.viento_kmh)),
    hoursRed: h.filter((x) => x.semaforo === 'rojo').length,
  };
}

function shareText(forecast, windows) {
  const lines = [`WAYRA · ${forecast.nombre} (${forecast.actividad})`];
  lines.push(`Pronóstico con GFS del ${forecast.ejecucion.gfs_inicio_lima} (hora de Lima)`);
  lines.push('Mejores horarios para salir:');
  windows.slice(0, 3).forEach((v) => {
    lines.push(`- ${v.inicio_lima} → ${v.fin_lima}: ${TRAFFIC_LIGHT[v.semaforo].label}`);
  });
  forecast.puntos.forEach((p) => {
    const s = summary(p);
    lines.push(`${p.nombre}: mín. ${s.minTemp} °C, viento hasta ${s.maxWind} km/h`);
  });
  lines.push('Ayuda para planificar, no es un aviso oficial.');
  return lines.join('\n');
}

export default function Report() {
  const { code } = useParams();
  const forecast = useApi(() => getForecast(code), [code]);
  const windows = useApi(() => getWindows(code), [code]);

  if ((forecast.loading && !forecast.data) || (windows.loading && !windows.data)) return <Loading />;
  if (forecast.error || windows.error) return <ErrorMessage error={forecast.error ?? windows.error} />;

  const f = forecast.data;
  const best = windows.data.ventanas.slice(0, 3);
  const whatsapp = `https://wa.me/?text=${encodeURIComponent(shareText(f, windows.data.ventanas))}`;

  return (
    <article className="reporte">
      <p className="migas no-imprimir">
        <Link to={`/destino/${code}`}>← Volver a {f.nombre}</Link>
      </p>
      <h1>
        {f.nombre} <small>{f.actividad}</small>
      </h1>
      <p>
        Pronóstico WAYRA con la corrida GFS del {f.ejecucion.gfs_inicio_lima} (hora de Lima)
        {f.ejecucion.es_respaldo && ' · datos de respaldo'}.
      </p>

      <h2>Mejores horarios ({windows.data.duracion_h} horas)</h2>
      <ol className="ventanas">
        {best.map((v) => (
          <li key={v.inicio_utc} className={`ventana ventana-${v.semaforo}`}>
            <TrafficLight value={v.semaforo} />
            <strong>
              {v.inicio_lima} → {v.fin_lima}
            </strong>
            <span className="motivo">{v.motivo}</span>
          </li>
        ))}
      </ol>

      <h2>Por punto de la ruta</h2>
      <table className="tabla">
        <thead>
          <tr>
            <th>Punto</th>
            <th>Altitud</th>
            <th>Temp. mín.</th>
            <th>Sensación mín.</th>
            <th>Viento máx.</th>
            <th>Horas en rojo</th>
          </tr>
        </thead>
        <tbody>
          {f.puntos.map((p) => {
            const s = summary(p);
            return (
              <tr key={p.punto_id}>
                <td>{p.nombre}</td>
                <td>
                  {p.altitud_real_m} m{p.es_estimado && ' (estimado)'}
                </td>
                <td>{s.minTemp} °C</td>
                <td>{s.minFeels} °C</td>
                <td>{s.maxWind} km/h</td>
                <td>{s.hoursRed}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="acciones no-imprimir">
        <button type="button" className="boton" onClick={() => window.print()}>
          Imprimir o guardar PDF
        </button>
        <a className="boton boton-whatsapp" href={whatsapp} target="_blank" rel="noreferrer">
          Compartir por WhatsApp
        </a>
      </div>
    </article>
  );
}
