import { useMemo, useState } from 'react';
import { CircleMarker, ImageOverlay, MapContainer, Popup, TileLayer, Tooltip, useMapEvents } from 'react-leaflet';
import { colorRgb } from '../utils/colors';

const TOPO_URL = 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png';
const TOPO_ATTRIBUTION =
  'Mapa: © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, SRTM | Estilo: © <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)';

// The API gives cell centers; the image has to cover half a cell more on each side.
function cellSize(grid) {
  return {
    lat: (grid.lat_norte - grid.lat_sur) / (grid.filas - 1),
    lon: (grid.lon_este - grid.lon_oeste) / (grid.columnas - 1),
  };
}

export function gridBounds(grid) {
  const d = cellSize(grid);
  return [
    [grid.lat_sur - d.lat / 2, grid.lon_oeste - d.lon / 2],
    [grid.lat_norte + d.lat / 2, grid.lon_este + d.lon / 2],
  ];
}

// One pixel per cell. Row 0 is south, so it goes at the bottom of the image.
function gridImage(grid) {
  const canvas = document.createElement('canvas');
  canvas.width = grid.columnas;
  canvas.height = grid.filas;
  const ctx = canvas.getContext('2d');
  const image = ctx.createImageData(grid.columnas, grid.filas);
  grid.valores.forEach((row, r) => {
    row.forEach((value, c) => {
      const i = ((grid.filas - 1 - r) * grid.columnas + c) * 4;
      const [red, green, blue] = colorRgb(grid.variable, value);
      image.data.set([red, green, blue, 255], i);
    });
  });
  ctx.putImageData(image, 0, 0);
  return canvas.toDataURL();
}

function CellValue({ grid }) {
  const [picked, setPicked] = useState(null);
  useMapEvents({
    click(e) {
      const d = cellSize(grid);
      const r = Math.round((e.latlng.lat - grid.lat_sur) / d.lat);
      const c = Math.round((e.latlng.lng - grid.lon_oeste) / d.lon);
      const value = grid.valores[r]?.[c];
      setPicked(value == null ? null : { latlng: e.latlng, value });
    },
  });
  if (!picked) return null;
  return (
    <Popup position={picked.latlng} eventHandlers={{ remove: () => setPicked(null) }}>
      {picked.value} {grid.unidad}
    </Popup>
  );
}

// viewBounds lets two maps open on the same area (comparator).
export default function GridMap({ grid, height = 460, selectedPoint, viewBounds }) {
  const url = useMemo(() => gridImage(grid), [grid]);
  const bounds = useMemo(() => gridBounds(grid), [grid]);

  return (
    <MapContainer bounds={viewBounds ?? bounds} style={{ height }} className="mapa" scrollWheelZoom={false}>
      <TileLayer url={TOPO_URL} attribution={TOPO_ATTRIBUTION} maxZoom={15} />
      <ImageOverlay key={url} url={url} bounds={bounds} opacity={0.6} />
      {grid.destinos.map((p) => (
        <CircleMarker
          key={p.punto_id}
          center={[p.lat, p.lon]}
          radius={p.punto_id === selectedPoint ? 8 : 5}
          pathOptions={{ color: '#111', weight: 2, fillColor: '#fff', fillOpacity: 1 }}
        >
          <Tooltip>
            {p.nombre} · {p.punto}
          </Tooltip>
        </CircleMarker>
      ))}
      <CellValue grid={grid} />
    </MapContainer>
  );
}
