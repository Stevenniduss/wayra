import { useState } from 'react';
import { getGrid } from '../api/api';
import GridMap from '../components/GridMap';
import Legend from '../components/Legend';
import { ErrorMessage, Loading } from '../components/Status';
import { HourSelect } from '../components/MapControls';
import { VARIABLES } from '../utils/colors';
import { useApi } from '../utils/useApi';

export default function MapPage() {
  const [variable, setVariable] = useState('temperatura');
  const [hour, setHour] = useState(null);
  const { data, error, loading } = useApi(() => getGrid(variable, hour), [variable, hour]);

  return (
    <>
      <h1>Mapa de la Cordillera Blanca</h1>
      <p className="subtitulo">
        Cada cuadro mide unos 3 km. Toca el mapa para ver el valor de ese cuadro.
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
        {data && (
          <HourSelect hours={data.horas_disponibles} value={hour ?? data.valido_utc} onChange={setHour} />
        )}
        {loading && data && <span className="nota">Actualizando…</span>}
      </div>

      {loading && !data && <Loading />}
      {error && <ErrorMessage error={error} />}
      {data && (
        <>
          <GridMap grid={data} />
          <Legend variable={variable} />
          <p className="nota">
            {data.hora_lima} (hora de Lima) · mínimo {data.min} {data.unidad}, máximo {data.max}{' '}
            {data.unidad}
          </p>
        </>
      )}
    </>
  );
}
