import { useState } from 'react';
import { getWindows } from '../api/api';
import { useApi } from '../utils/useApi';
import { ErrorMessage, Loading } from './Status';
import TrafficLight from './TrafficLight';

const DURATIONS = [4, 6, 8, 12];

// Without a chosen duration the API uses the activity's typical one.
export default function WindowsList({ code }) {
  const [hours, setHours] = useState(null);
  const [showAll, setShowAll] = useState(false);
  const { data, error, loading } = useApi(() => getWindows(code, hours), [code, hours]);

  const list = data?.ventanas ?? [];
  const visible = showAll ? list : list.slice(0, 5);

  return (
    <section>
      <div className="fila-controles">
        <label>
          ¿Cuántas horas dura tu salida?{' '}
          <select value={hours ?? data?.duracion_h ?? 6} onChange={(e) => setHours(Number(e.target.value))}>
            {DURATIONS.map((h) => (
              <option key={h} value={h}>
                {h} horas
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && !data && <Loading />}
      {error && <ErrorMessage error={error} />}
      {data && hours != null && data.duracion_h !== hours && (
        <p className="nota">Con datos de prueba solo se muestran ventanas de {data.duracion_h} horas.</p>
      )}

      <ol className="ventanas">
        {visible.map((v) => (
          <li key={v.inicio_utc} className={`ventana ventana-${v.semaforo}`}>
            <TrafficLight value={v.semaforo} />
            <strong>
              {v.inicio_lima} → {v.fin_lima}
            </strong>
            <span className="motivo">{v.motivo}</span>
          </li>
        ))}
      </ol>
      {list.length > 5 && (
        <button type="button" className="boton-secundario" onClick={() => setShowAll(!showAll)}>
          {showAll ? 'Ver solo las 5 mejores' : `Ver las ${list.length} ventanas`}
        </button>
      )}
    </section>
  );
}
