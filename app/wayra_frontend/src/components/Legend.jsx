import { SCALES } from '../utils/colors';

export default function Legend({ variable }) {
  const { unit, stops } = SCALES[variable];
  const min = stops[0][0];
  const max = stops[stops.length - 1][0];
  const gradient = stops
    .map(([v, c]) => `${c} ${(((v - min) / (max - min)) * 100).toFixed(0)}%`)
    .join(', ');

  return (
    <div className="leyenda">
      <div className="leyenda-barra" style={{ background: `linear-gradient(to right, ${gradient})` }} />
      <div className="leyenda-valores">
        {stops.map(([v]) => (
          <span key={v}>{v}</span>
        ))}
      </div>
      <small>{unit}</small>
    </div>
  );
}
