import { CalendarClock, ChartLine, FileText, MountainSnow, Table, ThermometerSnowflake } from 'lucide-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getForecast } from '../api/api';
import ForecastChart from '../components/ForecastChart';
import ForecastTable from '../components/ForecastTable';
import HourlyStrip from '../components/HourlyStrip';
import NowPanel from '../components/NowPanel';
import { ErrorMessage, Loading } from '../components/Status';
import TrafficLight from '../components/TrafficLight';
import WindowsList from '../components/WindowsList';
import { useApi } from '../utils/useApi';

const ZONES = { valle: 'Valle', campo_base: 'Campo base', zona_alta: 'Zona alta' };
const TABS = [
  ['ventanas', 'Mejores horarios', CalendarClock],
  ['tabla', 'Hora por hora', Table],
  ['grafico', 'Gráficos', ChartLine],
];

// Worst color of the next hours, to show next to each point.
const SEVERITY = { verde: 0, amarillo: 1, gris: 2, rojo: 3 };
const worst = (hours) =>
  hours.reduce((a, h) => (SEVERITY[h.semaforo] > SEVERITY[a.semaforo] ? h : a), hours[0]);

export default function Destination() {
  const { code } = useParams();
  const { data, error, loading } = useApi(() => getForecast(code), [code]);
  const [pointIndex, setPointIndex] = useState(0);
  const [tab, setTab] = useState('ventanas');

  if (loading && !data) return <Loading />;
  if (error) return <ErrorMessage error={error} />;

  const point = data.puntos[pointIndex] ?? data.puntos[0];
  const freezing = data.isoterma_0c.find((x) => x.altitud_m != null);

  return (
    <>
      <p className="migas">
        <Link to="/">Destinos</Link> / {data.nombre}
      </p>
      <div className="titulo-con-accion">
        <h1>
          {data.nombre} <small>{data.actividad}</small>
        </h1>
        <Link className="boton" to={`/destino/${code}/reporte`}>
          <FileText size={16} /> Reporte para compartir
        </Link>
      </div>

      <div className="puntos">
        {data.puntos.map((p, i) => {
          const w = p.horas.length ? worst(p.horas.slice(0, 12)) : null;
          return (
            <button
              type="button"
              key={p.punto_id}
              className={`punto ${i === pointIndex ? 'activo' : ''}`}
              onClick={() => setPointIndex(i)}
            >
              <span className="punto-zona">{ZONES[p.zona] ?? p.zona}</span>
              <strong>{p.nombre}</strong>
              <span className="punto-altura">
                {p.altitud_real_m} m{p.es_estimado && ' · estimado'}
              </span>
              {w && <TrafficLight value={w.semaforo} reason="Peor estado de las próximas 12 horas" />}
            </button>
          );
        })}
      </div>

      <div className="resumen">
        <NowPanel point={point} />
        <div className="resumen-lateral">
          {freezing && (
            <div className="dato tarjeta-elevada">
              <MountainSnow size={26} className="icono-nieve" />
              <div>
                <span>Altura de congelamiento (0 °C)</span>
                <strong>{freezing.altitud_m.toLocaleString('es-PE')} m</strong>
                <small>a las {freezing.hora_lima}</small>
              </div>
            </div>
          )}
          <div className="dato tarjeta-elevada">
            <ThermometerSnowflake size={26} className="icono-lluvia" />
            <div>
              <span>Paso de bajo cero a sobre cero</span>
              <strong>{point.transicion_termica.hora_lima ?? point.transicion_termica.texto}</strong>
            </div>
          </div>
          {point.es_estimado && (
            <p className="nota nota-caja">
              Este punto está a {Math.abs(point.diferencia_m)} m de la altura del cuadro del modelo (
              {point.altitud_celda_m} m). La temperatura se corrigió por altura y es una estimación.
            </p>
          )}
        </div>
      </div>

      <h2 className="seccion">Próximas 48 horas · {point.nombre}</h2>
      <HourlyStrip hours={point.horas} />

      <div className="pestanas" role="tablist">
        {TABS.map(([id, label, Icon]) => (
          <button
            type="button"
            role="tab"
            key={id}
            aria-selected={tab === id}
            className={tab === id ? 'activo' : ''}
            onClick={() => setTab(id)}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      <div className="panel tarjeta-elevada">
        {tab === 'ventanas' && <WindowsList code={code} />}
        {tab === 'tabla' && <ForecastTable hours={point.horas} />}
        {tab === 'grafico' && <ForecastChart hours={point.horas} />}
      </div>
    </>
  );
}
