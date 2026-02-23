import { getDb } from '@/lib/db';

export async function GET(request) {
    try {
        const db = getDb();
        const { searchParams } = new URL(request.url);
        const periodo = searchParams.get('periodo') || '2025-07';

        // Indicadores AXA para el periodo
        const indicadores = db.prepare(`
      SELECT i.*, a.nombre_completo as agente_nombre
      FROM indicadores_axa i
      LEFT JOIN agentes a ON a.codigo_agente = i.agente_codigo
      WHERE i.periodo = ?
    `).all(periodo);

        // Cruzar con base interna
        const conciliacion = [];
        for (const ind of indicadores) {
            const polizaInterna = db.prepare(`
        SELECT p.*, pr.ramo_codigo, pr.ramo_nombre
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.poliza_estandar = ? OR p.poliza_original = ?
      `).get(ind.poliza, ind.poliza);

            if (polizaInterna) {
                const coincide = polizaInterna.tipo_poliza === 'NUEVA' && ind.es_nueva_axa === 1;
                conciliacion.push({
                    ...ind,
                    poliza_interna: polizaInterna,
                    status: coincide ? 'COINCIDE' : 'DIFERENCIA',
                    tipo_diferencia: !coincide ? `Interno: ${polizaInterna.tipo_poliza}, AXA: ${ind.es_nueva_axa ? 'NUEVA' : 'NO NUEVA'}` : null,
                });
            } else {
                conciliacion.push({
                    ...ind,
                    poliza_interna: null,
                    status: 'SOLO_AXA',
                    tipo_diferencia: 'Póliza en AXA no encontrada en base interna',
                });
            }
        }

        // Resumen
        const resumen = {
            total: conciliacion.length,
            coincide: conciliacion.filter(c => c.status === 'COINCIDE').length,
            diferencia: conciliacion.filter(c => c.status === 'DIFERENCIA').length,
            soloAxa: conciliacion.filter(c => c.status === 'SOLO_AXA').length,
            soloInterno: conciliacion.filter(c => c.status === 'SOLO_INTERNO').length,
            pctCoincidencia: conciliacion.length > 0
                ? Math.round((conciliacion.filter(c => c.status === 'COINCIDE').length / conciliacion.length) * 100)
                : 0,
        };

        const periodos = db.prepare(`SELECT DISTINCT periodo FROM indicadores_axa ORDER BY periodo DESC`).all();

        return Response.json({ conciliacion, resumen, periodos: periodos.map(p => p.periodo) });
    } catch (err) {
        console.error(err);
        return Response.json({ error: err.message }, { status: 500 });
    }
}
