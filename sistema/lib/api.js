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
