import { ArrowRight, Mountain, Wind } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDestinations, getForecast } from '../api/api';
import { ErrorMessage, Loading } from '../components/Status';
import TrafficLight from '../components/TrafficLight';
import { SkyIcon } from '../components/WeatherIcon';
import { useApi } from '../utils/useApi';
import { skyOf, tempBackground } from '../utils/weather';

// Card with the current hour of the highest point of the destination.
function DestinationCard({ destination }) {
  const { data } = useApi(() => getForecast(destination.codigo), [destination.codigo]);
  const top = data?.puntos.reduce((a, p) => (p.altitud_real_m > a.altitud_real_m ? p : a), data.puntos[0]);
  const now = top?.horas[0];

  return (
    <Link to={`/destino/${destination.codigo}`} className="tarjeta-destino">
      <div
        className="tarjeta-destino-cielo"
        style={now ? { '--tono': tempBackground(now.temperatura_c, 0.55) } : undefined}
      >
        <Mountain className="tarjeta-destino-montana" size={120} strokeWidth={1} />
        {now ? (
          <>
            <SkyIcon sky={skyOf(now)} size={40} />
            <span className="tarjeta-destino-temp">{Math.round(now.temperatura_c)}°</span>
          </>
        ) : (
          <span className="tarjeta-destino-temp">…</span>
        )}
      </div>
      <div className="tarjeta-destino-cuerpo">
        <span className="etiqueta">{destination.actividad.nombre}</span>
        <h2>{destination.nombre}</h2>
        <p className="detalle">
          {destination.altitud_min_m === destination.altitud_max_m
            ? `${destination.altitud_min_m} m`
            : `${destination.altitud_min_m} – ${destination.altitud_max_m} m`}
        </p>
        {now && (
          <div className="tarjeta-destino-ahora">
            <span>
              <Wind size={15} /> {now.viento_kmh} km/h
            </span>
            <TrafficLight value={now.semaforo} reason={now.semaforo_motivo} />
          </div>
        )}
        {top && <p className="nota">Ahora en {top.nombre}</p>}
        <span className="tarjeta-destino-ir">
          Ver pronóstico <ArrowRight size={15} />
        </span>
      </div>
    </Link>
  );
}

export default function Home() {
  const { data, error, loading } = useApi(getDestinations, []);

  return (
    <>
      <section className="portada">
        <h1>¿A dónde vas?</h1>
        <p>
          Pronóstico por hora en cuadros de 3 km para la Cordillera Blanca. Elige un destino para ver cómo
          estará el clima en cada punto de la ruta y en qué momento conviene salir.
        </p>
      </section>

      {loading && !data && <Loading />}
      {error && <ErrorMessage error={error} />}

      <div className="tarjetas">
        {data?.map((d) => (
          <DestinationCard key={d.codigo} destination={d} />
        ))}
      </div>
    </>
  );
}
