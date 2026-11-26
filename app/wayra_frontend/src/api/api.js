// Single place where the frontend asks for data.
// VITE_USE_MOCK=false in .env.local switches from public/mock/ to the Django API.
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api';

export async function fetchData(route, mockFile) {
  const url = USE_MOCK ? `/mock/${mockFile}` : `${API_BASE}${route}`;
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error ?? `Error ${response.status} al pedir ${url}`);
  }
  return response.json();
}

const query = (params) =>
  new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== '')).toString();

// One function per contract route. Mocks only have the first hour and the default duration.
export const getDestinations = () => fetchData('/destinos', 'destinos.json');
export const getDestination = (code) => fetchData(`/destinos/${code}`, `destino_${code}.json`);
export const getForecast = (code) =>
  fetchData(`/destinos/${code}/pronostico`, `pronostico_${code}.json`);
export const getWindows = (code, hours) =>
  fetchData(`/destinos/${code}/ventanas?${query({ duracion_h: hours })}`, `ventanas_${code}.json`);
export const getGrid = (variable, validUtc, source = 'wayra') =>
  fetchData(
    `/mapa?${query({ variable, valido_utc: validUtc, fuente: source })}`,
    `mapa_${variable}_${source}.json`,
  );
export const getComparison = (validUtc, pointId) =>
  fetchData(
    `/comparador?${query({ valido_utc: validUtc, punto_id: pointId })}`,
    `comparador_${pointId}.json`,
  );
export const getRun = () => fetchData('/ejecucion', 'ejecucion.json');
