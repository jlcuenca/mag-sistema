import { getDb } from '@/lib/db';

export async function GET(request) {
    try {
        const db = getDb();
        const { searchParams } = new URL(request.url);
        const anio = parseInt(searchParams.get('anio') || new Date().getFullYear());
        const ramo = searchParams.get('ramo'); // 'vida', 'gmm', o null

        // KPIs principales
        let whereClause = `WHERE p.anio_aplicacion = ?`;
        const params = [anio];

        const polizasBase = db.prepare(`
      SELECT p.*, pr.ramo_codigo, pr.ramo_nombre, pr.plan, pr.gama as prod_gama,
             a.nombre_completo as agente_nombre, a.oficina, a.gerencia, a.territorio
      FROM polizas p
      LEFT JOIN productos pr ON p.producto_id = pr.id
      LEFT JOIN agentes a ON p.agente_id = a.id
      ${whereClause}
    `).all(...params);

        const nuevasVida = polizasBase.filter(p => p.ramo_codigo === 11 && p.tipo_poliza === 'NUEVA' && p.tipo_prima === 'BASICA');
        const nuevasGmm = polizasBase.filter(p => p.ramo_codigo === 34 && p.tipo_poliza === 'NUEVA');
        const subsVida = polizasBase.filter(p => p.ramo_codigo === 11 && p.tipo_poliza === 'SUBSECUENTE');
        const subsGmm = polizasBase.filter(p => p.ramo_codigo === 34 && p.tipo_poliza === 'SUBSECUENTE');
        const canceladas = polizasBase.filter(p => p.status_recibo !== 'PAGADA');

        // Producción mensual
        const produccionMensual = db.prepare(`
      SELECT periodo_aplicacion as periodo,
             SUM(CASE WHEN pr.ramo_codigo = 11 AND p.tipo_poliza = 'NUEVA' THEN 1 ELSE 0 END) as polizas_vida,
             SUM(CASE WHEN pr.ramo_codigo = 34 AND p.tipo_poliza = 'NUEVA' THEN 1 ELSE 0 END) as polizas_gmm,
             SUM(CASE WHEN pr.ramo_codigo = 11 AND p.tipo_poliza = 'NUEVA' THEN p.prima_neta ELSE 0 END) as prima_vida,
             SUM(CASE WHEN pr.ramo_codigo = 34 AND p.tipo_poliza = 'NUEVA' THEN p.prima_neta ELSE 0 END) as prima_gmm
      FROM polizas p
      LEFT JOIN productos pr ON p.producto_id = pr.id
      WHERE p.anio_aplicacion = ?
      GROUP BY periodo_aplicacion
      ORDER BY periodo_aplicacion
    `).all(anio);

        // Top agentes
        const topAgentes = db.prepare(`
      SELECT a.nombre_completo, a.codigo_agente, a.oficina,
             COUNT(CASE WHEN p.tipo_poliza = 'NUEVA' THEN 1 END) as polizas_nuevas,
             SUM(CASE WHEN p.tipo_poliza = 'NUEVA' THEN p.prima_neta ELSE 0 END) as prima_total
      FROM polizas p
      LEFT JOIN agentes a ON p.agente_id = a.id
      WHERE p.anio_aplicacion = ?
      GROUP BY a.id
      ORDER BY prima_total DESC
      LIMIT 10
    `).all(anio);

        // Distribución por gama GMM
        const distribucionGama = db.prepare(`
      SELECT p.gama, COUNT(*) as total, SUM(p.prima_neta) as prima
      FROM polizas p
      LEFT JOIN productos pr ON p.producto_id = pr.id
      WHERE pr.ramo_codigo = 34 AND p.anio_aplicacion = ? AND p.gama IS NOT NULL
      GROUP BY p.gama
    `).all(anio);

        // Metas
        const meta = db.prepare(`SELECT * FROM metas WHERE anio = ? AND periodo IS NULL`).get(anio);

        return Response.json({
            kpis: {
                polizasNuevasVida: nuevasVida.length,
                primaNuevaVida: nuevasVida.reduce((s, p) => s + (p.prima_neta || 0), 0),
                polizasNuevasGmm: nuevasGmm.length,
                aseguradosNuevosGmm: nuevasGmm.reduce((s, p) => s + (p.num_asegurados || 1), 0),
                primaNuevaGmm: nuevasGmm.reduce((s, p) => s + (p.prima_neta || 0), 0),
                primaSubsecuenteVida: subsVida.reduce((s, p) => s + (p.prima_neta || 0), 0),
                primaSubsecuenteGmm: subsGmm.reduce((s, p) => s + (p.prima_neta || 0), 0),
                polizasCanceladas: canceladas.length,
                totalPolizas: polizasBase.length,
                metaVida: meta?.meta_polizas_vida || 0,
                metaGmm: meta?.meta_polizas_gmm || 0,
                metaPrimaVida: meta?.meta_prima_vida || 0,
                metaPrimaGmm: meta?.meta_prima_gmm || 0,
            },
            produccionMensual,
            topAgentes,
            distribucionGama,
        });
    } catch (err) {
        console.error(err);
        return Response.json({ error: err.message }, { status: 500 });
    }
}
