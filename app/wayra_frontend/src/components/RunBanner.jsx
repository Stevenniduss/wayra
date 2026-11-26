import { Clock, DatabaseBackup, TriangleAlert } from 'lucide-react';
import { getRun } from '../api/api';
import { useApi } from '../utils/useApi';

export default function RunBanner() {
  const { data, error } = useApi(getRun, []);

  if (error) {
    return (
      <div className="aviso aviso-rojo">
        <TriangleAlert size={16} /> Todavía no hay un pronóstico disponible.
      </div>
    );
  }
  if (!data) return null;

  return (
    <>
      <div className="aviso">
        <Clock size={16} />
        <span>
          Corrida GFS del <strong>{data.gfs_inicio_lima}</strong> (hora de Lima) · hace {data.antiguedad_h} h ·{' '}
          {data.horizonte_h} h hacia adelante
        </span>
        <span className="aviso-chip">modelo {data.modelo_version}</span>
      </div>
      {data.desactualizada && (
        <div className="aviso aviso-amarillo">
          <TriangleAlert size={16} /> Este pronóstico tiene más de 12 horas. Revisa de nuevo más tarde.
        </div>
      )}
      {data.es_respaldo && (
        <div className="aviso aviso-amarillo">
          <DatabaseBackup size={16} /> Se muestran datos de respaldo guardados, no la última descarga.
        </div>
      )}
    </>
  );
}
