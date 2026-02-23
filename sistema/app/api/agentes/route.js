import { getDb } from '@/lib/db';

export async function GET(request) {
    try {
        const db = getDb();
        const { searchParams } = new URL(request.url);
        const situacion = searchParams.get('situacion');

        let where = situacion ? `WHERE situacion = '${situacion}'` : '';

        const agentes = db.prepare(`
      SELECT a.*,
        COUNT(p.id) as total_polizas,
        SUM(CASE WHEN p.tipo_poliza = 'NUEVA' AND p.anio_aplicacion = 2025 THEN 1 ELSE 0 END) as polizas_nuevas_2025,
        SUM(CASE WHEN p.tipo_poliza = 'NUEVA' AND p.anio_aplicacion = 2025 THEN p.prima_neta ELSE 0 END) as prima_nueva_2025
      FROM agentes a
      LEFT JOIN polizas p ON p.agente_id = a.id
      ${where}
      GROUP BY a.id
      ORDER BY prima_nueva_2025 DESC
    `).all();

        return Response.json({ data: agentes });
    } catch (err) {
        console.error(err);
        return Response.json({ error: err.message }, { status: 500 });
    }
}
