import { useState } from 'react';
import { getComparison, getGrid } from '../api/api';
import GridMap, { gridBounds } from '../components/GridMap';
import Legend from '../components/Legend';
import { ErrorMessage, Loading } from '../components/Status';
import { useApi } from '../utils/useApi';
import { HourSelect } from '../components/MapControls';
import { VARIABLES } from '../utils/colors';

const ROWS = [
  ['temperatura_c', 'Temperatura', '°C'],
  ['humedad_pct', 'Humedad', '%'],
  ['viento_kmh', 'Viento', 'km/h'],
];

export default function Comparison() {
  const [variable, setVariable] = useState('temperatura');
  const [hour, setHour] = useState(null);
  const [pointId, setPointId] = useState(null);

  const wayra = useApi(() => getGrid(variable, hour, 'wayra'), [variable, hour]);
  const gfs = useApi(() => getGrid(variable, hour, 'gfs'), [variable, hour]);
  const points = wayra.data?.destinos ?? [];
  const selected = pointId ?? points[0]?.punto_id;
  const numbers = useApi(
    () => (selected ? getComparison(hour, selected) : Promise.resolve(null)),
    [hour, selected],
  );

  if (wayra.loading && !wayra.data) return <Loading />;
  if (wayra.error || gfs.error) return <ErrorMessage error={wayra.error ?? gfs.error} />;

  return (
    <>
      <h1>GFS frente a WAYRA</h1>
      <p className="subtitulo">
        El mismo momento con el modelo global (cuadros de unos 28 km) y con WAYRA (cuadros de unos
        3 km). Los dos mapas usan la misma escala de colores.
      </p>

      <div className="fila-controles">
        <label>
          Variable{' '}
          <select value={variable} onChange={(e) => setVariable(e.target.value)}>
            {VARIABLES.map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <HourSelect
          hours={wayra.data.horas_disponibles}
          value={hour ?? wayra.data.valido_utc}
          onChange={setHour}
        />
        <label>
          Punto{' '}
          <select value={selected ?? ''} onChange={(e) => setPointId(Number(e.target.value))}>
            {points.map((p) => (
              <option key={p.punto_id} value={p.punto_id}>
                {p.nombre} · {p.punto}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="comparador">
        <section>
          <h2>GFS · {gfs.data?.resolucion_km ?? 28} km</h2>
          {gfs.data ? <GridMap grid={gfs.data} height={380} selectedPoint={selected} viewBounds={gridBounds(wayra.data)} /> : <Loading />}
        </section>
        <section>
          <h2>WAYRA · {wayra.data.resolucion_km} km</h2>
          <GridMap grid={wayra.data} height={380} selectedPoint={selected} />
        </section>
      </div>
      <Legend variable={variable} />

      {numbers.error && <ErrorMessage error={numbers.error} />}
      {numbers.data && (
        <>
          <h2>
            {numbers.data.punto.destino} · {numbers.data.punto.nombre} · {numbers.data.hora_lima}
          </h2>
          <table className="tabla tabla-corta">
            <thead>
              <tr>
                <th />
                <th>GFS</th>
                <th>WAYRA</th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map(([key, label, unit]) => (
                <tr key={key}>
                  <td>{label}</td>
                  <td>
                    {numbers.data.gfs[key]} {unit}
                  </td>
                  <td>
                    {numbers.data.wayra[key]} {unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}
