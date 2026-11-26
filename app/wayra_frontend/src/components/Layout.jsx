import { CloudSun, GitCompareArrows, Map as MapIcon, Mountain, TriangleAlert } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';
import RunBanner from './RunBanner';
import ThemeToggle from './ThemeToggle';

export default function Layout() {
  return (
    <div className="app">
      <header className="cabecera no-imprimir">
        <NavLink to="/" className="marca">
          <Mountain size={22} />
          <span>
            WAYRA <small>Clima de montaña</small>
          </span>
        </NavLink>
        <nav>
          <NavLink to="/" end>
            <CloudSun size={17} /> Destinos
          </NavLink>
          <NavLink to="/mapa">
            <MapIcon size={17} /> Mapa
          </NavLink>
          <NavLink to="/comparador">
            <GitCompareArrows size={17} /> GFS vs WAYRA
          </NavLink>
        </nav>
        <ThemeToggle />
      </header>

      <main className="contenido">
        <div className="no-imprimir">
          <RunBanner />
        </div>
        <Outlet />
      </main>

      <footer className="limitaciones">
        <TriangleAlert size={18} />
        <p>
          <strong>Antes de salir:</strong> WAYRA es una ayuda para planificar, no un aviso oficial. No
          pronostica lluvia (la que se muestra viene de Open-Meteo), avalanchas ni el estado de la ruta.
          Consulta siempre a SENAMHI, a tu guía y al parque.
        </p>
      </footer>
    </div>
  );
}
