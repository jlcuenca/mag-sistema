import { getDb } from '@/lib/db';

export async function GET(request) {
    try {
        const db = getDb();
        const { searchParams } = new URL(request.url);
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '50');
        const ramo = searchParams.get('ramo');
        const tipo = searchParams.get('tipo');
        const agente = searchParams.get('agente');
        const anio = searchParams.get('anio');
        const busqueda = searchParams.get('q');
        const offset = (page - 1) * limit;

        let where = [];
        let params = [];

        if (ramo === 'vida') { where.push('pr.ramo_codigo = 11'); }
        if (ramo === 'gmm') { where.push('pr.ramo_codigo = 34'); }
        if (tipo) { where.push('p.tipo_poliza = ?'); params.push(tipo.toUpperCase()); }
        if (agente) { where.push('a.codigo_agente = ?'); params.push(agente); }
        if (anio) { where.push('p.anio_aplicacion = ?'); params.push(parseInt(anio)); }
        if (busqueda) {
            where.push('(p.poliza_original LIKE ? OR p.asegurado_nombre LIKE ? OR a.codigo_agente LIKE ?)');
            params.push(`%${busqueda}%`, `%${busqueda}%`, `%${busqueda}%`);
        }

        const whereStr = where.length ? `WHERE ${where.join(' AND ')}` : '';

        const total = db.prepare(`
      SELECT COUNT(*) as total
      FROM polizas p
      LEFT JOIN productos pr ON p.producto_id = pr.id
      LEFT JOIN agentes a ON p.agente_id = a.id
      ${whereStr}
    `).get(...params);

        const polizas = db.prepare(`
      SELECT p.*, 
             pr.ramo_codigo, pr.ramo_nombre, pr.plan,
             a.nombre_completo as agente_nombre, a.codigo_agente, a.oficina, a.gerencia, a.territorio
      FROM polizas p
      LEFT JOIN productos pr ON p.producto_id = pr.id
      LEFT JOIN agentes a ON p.agente_id = a.id
      ${whereStr}
      ORDER BY p.fecha_inicio DESC
      LIMIT ? OFFSET ?
    `).all(...params, limit, offset);

        return Response.json({
            data: polizas,
            total: total.total,
            page,
            limit,
            pages: Math.ceil(total.total / limit),
        });
    } catch (err) {
        console.error(err);
        return Response.json({ error: err.message }, { status: 500 });
    }
}

export async function POST(request) {
    try {
        const db = getDb();
        const body = await request.json();

        const stmt = db.prepare(`
      INSERT INTO polizas (
        poliza_original, poliza_estandar, agente_id, producto_id,
        asegurado_nombre, fecha_inicio, fecha_fin,
        prima_total, prima_neta, iva, recargo, suma_asegurada,
        num_asegurados, forma_pago, tipo_pago, status_recibo, gama,
        tipo_poliza, tipo_prima, mystatus, periodo_aplicacion, anio_aplicacion, fuente
      ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    `);

        const result = stmt.run(
            body.poliza_original,
            body.poliza_original?.replace(/^0+(\d)/, '$1'),
            body.agente_id, body.producto_id,
            body.asegurado_nombre, body.fecha_inicio, body.fecha_fin,
            body.prima_total, body.prima_neta, body.iva || 0, body.recargo || 0,
            body.suma_asegurada, body.num_asegurados || 1,
            body.forma_pago, body.tipo_pago, body.status_recibo || 'PAGADA',
            body.gama, body.tipo_poliza, body.tipo_prima,
            body.status_recibo === 'PAGADA' ? 'PAGADA TOTAL' : 'CANCELADA CADUCADA',
            body.fecha_inicio?.substring(0, 7),
            parseInt(body.fecha_inicio?.substring(0, 4) || new Date().getFullYear()),
            'MANUAL'
        );

        return Response.json({ success: true, id: result.lastInsertRowid }, { status: 201 });
    } catch (err) {
        console.error(err);
        return Response.json({ error: err.message }, { status: 500 });
    }
}
