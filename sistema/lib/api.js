/**
 * URL base del backend FastAPI (Python).
 * En desarrollo apunta a localhost:8000
 * En producción cambiar a la URL del servidor.
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Helper para hacer fetches a la API FastAPI
 */
export async function apiFetch(path, options = {}) {
    const url = `${API_URL}${path}`;
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `Error ${res.status}`);
    }
    return res.json();
}

/**
 * Formatea números como pesos MXN
 */
export function fmt(n) {
    if (!n && n !== 0) return '$0';
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}

export const MESES = {
    '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr',
    '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago',
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic',
};

/**
 * URLs base para documentos PDF (solicitudes y pólizas).
 * Configurable vía variables de entorno o por defecto al servidor de cartera.
 */
export const DOC_BASE_URL = process.env.NEXT_PUBLIC_DOC_BASE_URL
    || 'http://54.184.22.19:7070/cartera-0.1/static/archivos';

/**
 * Construye la URL del PDF de una solicitud.
 * Ej: getSolicitudDocUrl('1715626') → .../solicitudes/1715626.pdf
 */
export function getSolicitudDocUrl(numSolicitud) {
    if (!numSolicitud) return null;
    const num = String(numSolicitud).trim();
    return `${DOC_BASE_URL}/solicitudes/${num}.pdf`;
}

/**
 * Construye la URL del PDF de una póliza.
 * Ej: getPolizaDocUrl('19715626') → .../19715626.pdf
 */
export function getPolizaDocUrl(numPoliza) {
    if (!numPoliza) return null;
    const num = String(numPoliza).trim();
    return `${DOC_BASE_URL}/${num}.pdf`;
}
