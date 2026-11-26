import { LoaderCircle, TriangleAlert } from 'lucide-react';

export function Loading({ text = 'Cargando…' }) {
  return (
    <p className="estado">
      <LoaderCircle size={18} className="girando" /> {text}
    </p>
  );
}

export function ErrorMessage({ error }) {
  return (
    <p className="estado estado-error" role="alert">
      <TriangleAlert size={18} /> No se pudo cargar la información. {error?.message}
    </p>
  );
}
