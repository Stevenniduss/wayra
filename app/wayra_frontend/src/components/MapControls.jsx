export function HourSelect({ hours, value, onChange }) {
  return (
    <label>
      Hora{' '}
      <select value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
        {hours.map((h) => (
          <option key={h.valido_utc} value={h.valido_utc}>
            {h.hora_lima}
          </option>
        ))}
      </select>
    </label>
  );
}
