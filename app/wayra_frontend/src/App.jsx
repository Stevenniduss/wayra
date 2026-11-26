import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Destination from './pages/Destination';
import Report from './pages/Report';
import MapPage from './pages/MapPage';
import Comparison from './pages/Comparison';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="destino/:code" element={<Destination />} />
          <Route path="destino/:code/reporte" element={<Report />} />
          <Route path="mapa" element={<MapPage />} />
          <Route path="comparador" element={<Comparison />} />
          <Route path="*" element={<p>Esta página no existe.</p>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
