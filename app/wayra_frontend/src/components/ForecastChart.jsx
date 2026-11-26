import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useTheme } from '../theme/ThemeContext';

const PALETTE = {
  light: { grid: '#e3e8ef', axis: '#5b6576', tooltip: '#ffffff', text: '#1b2433' },
  dark: { grid: '#263246', axis: '#8b98ad', tooltip: '#162032', text: '#e6ecf5' },
};

export default function ForecastChart({ hours }) {
  const { theme } = useTheme();
  const c = PALETTE[theme];
  const axis = { fontSize: 12, fill: c.axis };
  const tooltip = {
    contentStyle: { background: c.tooltip, border: `1px solid ${c.grid}`, borderRadius: 10, color: c.text },
    labelStyle: { color: c.text, fontWeight: 600 },
  };

  return (
    <div className="graficos">
      <h3>Temperatura y sensación térmica</h3>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={hours} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="grad-temp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f97316" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={c.grid} vertical={false} />
          <XAxis dataKey="hora_lima" minTickGap={40} tick={axis} stroke={c.grid} />
          <YAxis unit="°" tick={axis} width={44} stroke={c.grid} />
          <Tooltip {...tooltip} />
          <Legend />
          <ReferenceLine
            y={0}
            stroke="#38bdf8"
            strokeDasharray="4 4"
            label={{ value: '0 °C', fontSize: 11, fill: '#38bdf8' }}
          />
          <Area
            type="monotone"
            dataKey="temperatura_c"
            name="Temperatura (°C)"
            stroke="#f97316"
            fill="url(#grad-temp)"
            strokeWidth={2.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="sensacion_termica_c"
            name="Sensación (°C)"
            stroke="#a78bfa"
            dot={false}
            strokeWidth={2}
            strokeDasharray="5 3"
          />
        </ComposedChart>
      </ResponsiveContainer>

      <h3>Viento y humedad</h3>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={hours} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="grad-hum" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={c.grid} vertical={false} />
          <XAxis dataKey="hora_lima" minTickGap={40} tick={axis} stroke={c.grid} />
          <YAxis yAxisId="v" tick={axis} width={44} stroke={c.grid} />
          <YAxis yAxisId="h" orientation="right" domain={[0, 100]} unit="%" tick={axis} width={44} stroke={c.grid} />
          <Tooltip {...tooltip} />
          <Legend />
          <Area
            yAxisId="h"
            type="monotone"
            dataKey="humedad_pct"
            name="Humedad (%)"
            stroke="#3b82f6"
            fill="url(#grad-hum)"
            strokeWidth={2}
            dot={false}
          />
          <Bar yAxisId="v" dataKey="viento_kmh" name="Viento (km/h)" fill="#14b8a6" radius={[3, 3, 0, 0]} maxBarSize={10} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
