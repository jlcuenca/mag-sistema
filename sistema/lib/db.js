import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const DB_PATH = path.join(process.cwd(), 'data', 'mag.db');

let _db = null;

export function getDb() {
    if (_db) return _db;

    // Crear directorio si no existe
    const dir = path.dirname(DB_PATH);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');

    initSchema(_db);
    seedData(_db);

    return _db;
}

function initSchema(db) {
    db.exec(`
    CREATE TABLE IF NOT EXISTS agentes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      codigo_agente TEXT UNIQUE NOT NULL,
      nombre_completo TEXT NOT NULL,
      rol TEXT DEFAULT 'Agente',
      situacion TEXT DEFAULT 'ACTIVO',
      fecha_alta TEXT,
      fecha_cancelacion TEXT,
      territorio TEXT,
      oficina TEXT,
      gerencia TEXT,
      promotor TEXT,
      nombre_promotoria TEXT DEFAULT 'MAG',
      centro_costos TEXT,
      telefono TEXT,
      email TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS productos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ramo_codigo INTEGER NOT NULL,
      ramo_nombre TEXT NOT NULL,
      plan TEXT,
      gama TEXT,
      registro_cnsf TEXT,
      UNIQUE(ramo_codigo, plan, gama)
    );

    CREATE TABLE IF NOT EXISTS polizas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      poliza_original TEXT NOT NULL,
      poliza_estandar TEXT NOT NULL,
      version INTEGER DEFAULT 0,
      solicitud TEXT,
      archivo_pdf TEXT,
      agente_id INTEGER REFERENCES agentes(id),
      producto_id INTEGER REFERENCES productos(id),
      asegurado_nombre TEXT,
      contratante_nombre TEXT,
      rfc TEXT,
      codigo_postal TEXT,
      telefono TEXT,
      email TEXT,
      num_asegurados INTEGER DEFAULT 1,
      fecha_emision TEXT,
      fecha_inicio TEXT NOT NULL,
      fecha_fin TEXT,
      moneda TEXT DEFAULT 'MN',
      prima_total REAL,
      prima_neta REAL,
      iva REAL,
      recargo REAL,
      derecho_poliza REAL,
      suma_asegurada REAL,
      deducible REAL,
      coaseguro REAL,
      forma_pago TEXT,
      tipo_pago TEXT,
      status_recibo TEXT,
      plazo_pago TEXT,
      tope REAL,
      zona TEXT,
      red TEXT,
      tabulador TEXT,
      maternidad TEXT,
      cobertura TEXT,
      gama TEXT,
      es_nueva INTEGER,
      tipo_poliza TEXT,
      tipo_prima TEXT,
      pct_comision REAL,
      poliza_padre_id INTEGER REFERENCES polizas(id),
      es_reexpedicion INTEGER DEFAULT 0,
      mystatus TEXT,
      periodo_aplicacion TEXT,
      anio_aplicacion INTEGER,
      fuente TEXT DEFAULT 'EXCEL_IMPORT',
      notas TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_polizas_estandar ON polizas(poliza_estandar);
    CREATE INDEX IF NOT EXISTS idx_polizas_agente ON polizas(agente_id);
    CREATE INDEX IF NOT EXISTS idx_polizas_fecha_inicio ON polizas(fecha_inicio);
    CREATE INDEX IF NOT EXISTS idx_polizas_tipo ON polizas(tipo_poliza);
    CREATE INDEX IF NOT EXISTS idx_polizas_periodo ON polizas(periodo_aplicacion);

    CREATE TABLE IF NOT EXISTS indicadores_axa (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      periodo TEXT NOT NULL,
      fecha_recepcion TEXT,
      poliza TEXT,
      agente_codigo TEXT,
      ramo TEXT,
      num_asegurados INTEGER,
      polizas_equivalentes REAL,
      prima_primer_anio REAL,
      antiguedad_axa TEXT,
      fecha_inicio_vigencia TEXT,
      es_nueva_axa INTEGER,
      reconocimiento_antiguedad INTEGER,
      encontrada_en_base INTEGER,
      diferencia_clasificacion TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS conciliaciones (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      periodo TEXT NOT NULL,
      fecha_conciliacion TEXT DEFAULT (datetime('now')),
      poliza_id INTEGER REFERENCES polizas(id),
      indicador_axa_id INTEGER REFERENCES indicadores_axa(id),
      status TEXT,
      tipo_diferencia TEXT,
      clasificacion_interna TEXT,
      clasificacion_axa TEXT,
      prima_interna REAL,
      prima_axa REAL,
      resuelto INTEGER DEFAULT 0,
      notas_resolucion TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS metas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      anio INTEGER NOT NULL,
      periodo TEXT,
      agente_id INTEGER REFERENCES agentes(id),
      meta_polizas_vida INTEGER,
      meta_prima_vida REAL,
      meta_polizas_gmm INTEGER,
      meta_asegurados_gmm INTEGER,
      meta_prima_gmm REAL,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS importaciones (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      tipo TEXT NOT NULL,
      archivo_nombre TEXT,
      registros_procesados INTEGER,
      registros_nuevos INTEGER,
      registros_actualizados INTEGER,
      registros_error INTEGER,
      errores_detalle TEXT,
      usuario TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    );
  `);
}

function seedData(db) {
    // Solo seedear si no hay datos
    const count = db.prepare('SELECT COUNT(*) as c FROM agentes').get();
    if (count.c > 0) return;

    // Agentes
    const agentes = [
        { codigo: '47968', nombre: 'GARCÍA LÓPEZ, ROBERTO', rol: 'Agente', situacion: 'ACTIVO', fecha_alta: '2018-03-15', territorio: 'Zona Norte', oficina: 'CDMX Norte', gerencia: 'Gerencia A', promotor: 'MAG Principal', cc: '56991' },
        { codigo: '627523', nombre: 'MARTÍNEZ SOTO, PATRICIA', rol: 'Agente', situacion: 'ACTIVO', fecha_alta: '2019-07-22', territorio: 'Zona Sur', oficina: 'CDMX Sur', gerencia: 'Gerencia B', promotor: 'MAG Principal', cc: '606266' },
        { codigo: '385201', nombre: 'HERNÁNDEZ RUIZ, CARLOS', rol: 'Agente Senior', situacion: 'ACTIVO', fecha_alta: '2017-01-10', territorio: 'Zona Centro', oficina: 'CDMX Centro', gerencia: 'Gerencia A', promotor: 'MAG Principal', cc: '57834' },
        { codigo: '492011', nombre: 'TORRES VEGA, ANA LAURA', rol: 'Agente', situacion: 'ACTIVO', fecha_alta: '2020-11-05', territorio: 'Zona Oriente', oficina: 'CDMX Oriente', gerencia: 'Gerencia C', promotor: 'MAG Principal', cc: '61204' },
        { codigo: '731804', nombre: 'RAMÍREZ CASTILLO, MIGUEL', rol: 'Agente', situacion: 'ACTIVO', fecha_alta: '2021-04-18', territorio: 'Zona Norte', oficina: 'CDMX Norte', gerencia: 'Gerencia A', promotor: 'MAG Principal', cc: '58902' },
        { codigo: '203847', nombre: 'FLORES MENDOZA, DIANA', rol: 'Agente', situacion: 'CANCELADO', fecha_alta: '2016-09-30', fecha_cancelacion: '2024-06-01', territorio: 'Zona Sur', oficina: 'CDMX Sur', gerencia: 'Gerencia B', promotor: 'MAG Principal', cc: '55410' },
        { codigo: '918273', nombre: 'JIMÉNEZ REYES, OSCAR', rol: 'Agente Senior', situacion: 'ACTIVO', fecha_alta: '2015-02-14', territorio: 'Zona Centro', oficina: 'CDMX Centro', gerencia: 'Gerencia B', promotor: 'MAG Principal', cc: '59301' },
        { codigo: '564738', nombre: 'MORALES PAREDES, LUCÍA', rol: 'Agente', situacion: 'ACTIVO', fecha_alta: '2022-08-20', territorio: 'Zona Oriente', oficina: 'CDMX Oriente', gerencia: 'Gerencia C', promotor: 'MAG Principal', cc: '62105' },
    ];

    const insertAgente = db.prepare(`
    INSERT INTO agentes (codigo_agente, nombre_completo, rol, situacion, fecha_alta, fecha_cancelacion, territorio, oficina, gerencia, promotor, centro_costos)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

    for (const a of agentes) {
        insertAgente.run(a.codigo, a.nombre, a.rol, a.situacion, a.fecha_alta, a.fecha_cancelacion || null, a.territorio, a.oficina, a.gerencia, a.promotor, a.cc);
    }

    // Productos
    const productos = [
        { ramo: 11, nombre: 'VIDA', plan: 'VIDA Y AHORRO', gama: null, cnsf: 'CNSF-S0048-0440-2011' },
        { ramo: 11, nombre: 'VIDA', plan: 'MI PROYECTO R', gama: null, cnsf: 'CNSF-S0048-0440-2011' },
        { ramo: 34, nombre: 'GASTOS MEDICOS MAYORES INDIVIDUAL', plan: 'FLEX PLUS', gama: 'ZAFIRO', cnsf: 'CNSF-S0048-0327-2024' },
        { ramo: 34, nombre: 'GASTOS MEDICOS MAYORES INDIVIDUAL', plan: 'FLEX PLUS', gama: 'DIAMANTE', cnsf: 'CNSF-S0048-0327-2024' },
        { ramo: 34, nombre: 'GASTOS MEDICOS MAYORES INDIVIDUAL', plan: 'FLEX PLUS', gama: 'ESMERALDA', cnsf: 'CNSF-S0048-0427-2024' },
        { ramo: 34, nombre: 'GASTOS MEDICOS MAYORES INDIVIDUAL', plan: 'FLEX PLUS', gama: 'RUBI', cnsf: 'CNSF-S0048-0427-2024' },
    ];

    const insertProd = db.prepare(`INSERT OR IGNORE INTO productos (ramo_codigo, ramo_nombre, plan, gama, registro_cnsf) VALUES (?,?,?,?,?)`);
    for (const p of productos) insertProd.run(p.ramo, p.nombre, p.plan, p.gama, p.cnsf);

    // Pólizas de ejemplo — VIDA (30 pólizas)
    const vidaPolizas = generateVidaPolizas(db);
    // Pólizas de ejemplo — GMM (80 pólizas)
    const gmmPolizas = generateGmmPolizas(db);

    const insertPoliza = db.prepare(`
    INSERT INTO polizas (
      poliza_original, poliza_estandar, agente_id, producto_id,
      asegurado_nombre, rfc, fecha_inicio, fecha_fin, fecha_emision,
      moneda, prima_total, prima_neta, iva, recargo, suma_asegurada,
      deducible, coaseguro, num_asegurados, forma_pago, tipo_pago,
      status_recibo, gama, es_nueva, tipo_poliza, tipo_prima,
      pct_comision, mystatus, periodo_aplicacion, anio_aplicacion, fuente
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
  `);

    for (const p of [...vidaPolizas, ...gmmPolizas]) {
        insertPoliza.run(
            p.poliza_original, p.poliza_estandar, p.agente_id, p.producto_id,
            p.asegurado_nombre, p.rfc, p.fecha_inicio, p.fecha_fin, p.fecha_emision,
            p.moneda || 'MN', p.prima_total, p.prima_neta, p.iva || 0, p.recargo || 0,
            p.suma_asegurada, p.deducible || null, p.coaseguro || null,
            p.num_asegurados || 1, p.forma_pago, p.tipo_pago,
            p.status_recibo, p.gama || null, p.es_nueva ? 1 : 0,
            p.tipo_poliza, p.tipo_prima || null, p.pct_comision || null,
            p.mystatus, p.periodo_aplicacion, p.anio_aplicacion, 'EXCEL_IMPORT'
        );
    }

    // Metas 2025
    const insertMeta = db.prepare(`INSERT INTO metas (anio, periodo, meta_polizas_vida, meta_prima_vida, meta_polizas_gmm, meta_asegurados_gmm, meta_prima_gmm) VALUES (?,?,?,?,?,?,?)`);
    const meses = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06', '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12'];
    for (const m of meses) {
        insertMeta.run(2025, m, 4, 120000, 20, 25, 480000);
    }
    insertMeta.run(2025, null, 48, 1440000, 240, 300, 5760000);

    // Indicadores AXA de ejemplo (julio 2025)
    const insertInd = db.prepare(`INSERT INTO indicadores_axa (periodo, fecha_recepcion, poliza, agente_codigo, ramo, num_asegurados, polizas_equivalentes, prima_primer_anio, es_nueva_axa, reconocimiento_antiguedad, encontrada_en_base) VALUES (?,?,?,?,?,?,?,?,?,?,?)`);
    insertInd.run('2025-07', '2025-08-25', '0076384A', '47968', 'VIDA', 1, 1.0, 28077, 1, 0, 1);
    insertInd.run('2025-07', '2025-08-25', '10007U00', '627523', 'GMM', 2, null, 24568, 1, 0, 1);
    insertInd.run('2025-07', '2025-08-25', '10015Z00', '385201', 'GMM', 1, null, 18500, 1, 0, 0);
    insertInd.run('2025-07', '2025-08-25', '0088921B', '47968', 'VIDA', 1, 0.8, 22400, 1, 0, 1);

    console.log('✅ Base de datos inicializada con datos de ejemplo');
}

function generateVidaPolizas(db) {
    const agentes = db.prepare('SELECT id, codigo_agente FROM agentes WHERE situacion = ?').all('ACTIVO');
    const prodVida = db.prepare('SELECT id FROM productos WHERE ramo_codigo = 11').all();
    const nombres = [
        'SALAZAR CASTILLO, JUAN FRANCISCO', 'GUTIÉRREZ MORENO, ELENA', 'VÁZQUEZ LUNA, PEDRO ANTONIO',
        'ORTIZ DÍAZ, CARMEN PATRICIA', 'REYES SANTOS, FERNANDO', 'MENDOZA ÁVILA, SOFÍA',
        'CASTILLO ROJAS, ALEJANDRO', 'LUNA HERRERA, VALERIA', 'SANTOS MEDINA, EDUARDO',
        'ESPINOZA CAMPOS, MARIELA', 'RIVAS FUENTES, DANIEL', 'PAREDES GÓMEZ, CLAUDIA',
        'ACOSTA VARGAS, MANUEL', 'DELGADO RÍOS, ISABEL', 'CERVANTES MORA, RICARDO',
        'PACHECO IBARRA, ANDREA', 'GUERRERO SOLÍS, ARTURO', 'MONTES AGUILAR, GABRIELA',
        'PEÑA CONTRERAS, SERGIO', 'LARA SANDOVAL, NATALIA', 'ROJAS CORONA, VÍCTOR',
        'AGUILAR ESTRADA, MÓNICA', 'CARRILLO TEJEDA, HUGO', 'MIRANDA BONILLA, VERÓNICA',
        'VILLAREAL CUÉLLAR, RUBÉN', 'SÁNCHEZ BETANCOURT, LORENA', 'BRAVO MONTOYA, JAIME',
        'FUENTES ESPINOSA, CRISTINA', 'MEDINA QUIROZ, PABLO', 'ALVARADO PIÑA, SUSANA',
    ];
    const formasPago = ['MENSUAL', 'ANUAL', 'SEMESTRAL', 'TRIMESTRAL'];
    const tipos = ['CARGO AUTOMATICO', 'Tarjeta', 'Agente'];
    const polizas = [];

    for (let i = 0; i < 30; i++) {
        const agente = agentes[i % agentes.length];
        const prod = prodVida[i % prodVida.length];
        const year = i < 10 ? 2024 : (i < 22 ? 2025 : 2026);
        const month = String((i % 12) + 1).padStart(2, '0');
        const day = String(Math.min(28, (i % 27) + 1)).padStart(2, '0');
        const fechaInicio = `${year}-${month}-${day}`;
        const fechaFin = `${year + 30}-${month}-${day}`;
        const primaNeta = 15000 + (i * 1800);
        const comision = primaNeta * (i % 3 === 0 ? 0.025 : 0.018); // básica vs excedente
        const pctCom = comision / primaNeta;
        const esBasica = pctCom >= 0.021;
        const esNueva = year >= 2025;
        const formaIdx = i % formasPago.length;
        const recargo = formasPago[formaIdx] === 'MENSUAL' ? primaNeta * 0.05 : 0;

        polizas.push({
            poliza_original: `${String(76384 + i).padStart(7, '0')}A`,
            poliza_estandar: `${76384 + i}A`,
            agente_id: agente.id,
            producto_id: prod.id,
            asegurado_nombre: nombres[i],
            rfc: `RFC${String(i).padStart(8, '0')}`,
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
            fecha_emision: fechaInicio,
            prima_total: primaNeta + recargo,
            prima_neta: primaNeta,
            iva: 0,
            recargo,
            suma_asegurada: 1000000 + (i * 100000),
            forma_pago: formasPago[formaIdx],
            tipo_pago: tipos[i % tipos.length],
            status_recibo: i % 8 === 0 ? 'CANC/X F.PAGO' : 'PAGADA',
            es_nueva: esNueva && esBasica ? 1 : 0,
            tipo_poliza: esNueva && esBasica ? 'NUEVA' : (esNueva && !esBasica ? 'NO_APLICA' : 'SUBSECUENTE'),
            tipo_prima: esBasica ? 'BASICA' : 'EXCEDENTE',
            pct_comision: pctCom,
            mystatus: i % 8 === 0 ? 'CANCELADA CADUCADA' : 'PAGADA TOTAL',
            periodo_aplicacion: `${year}-${month}`,
            anio_aplicacion: year,
        });
    }
    return polizas;
}

function generateGmmPolizas(db) {
    const agentes = db.prepare('SELECT id, codigo_agente FROM agentes WHERE situacion = ?').all('ACTIVO');
    const gamas = ['ZAFIRO', 'DIAMANTE', 'ESMERALDA', 'RUBI'];
    const prodGmm = db.prepare('SELECT id, gama FROM productos WHERE ramo_codigo = 34').all();
    const nombres = [
        'CARRASCO RIVERA, VERENICE', 'DOMÍNGUEZ ÁNGEL, RAÚL', 'TRUJILLO SOTO, JESSICA',
        'CAMPOS NORIEGA, ARMANDO', 'OLVERA TAPIA, ADRIANA', 'GARZA FUENTES, RODRIGO',
        'NÚÑEZ TELLO, LILIANA', 'VALDEZ CISNEROS, BENJAMÍN', 'ARREDONDO MEZA, BEATRIZ',
        'QUIÑONES PADILLA, ALFREDO', 'BARRERA LEIVA, MARIANA', 'CIENFUEGOS RUEDA, ARTURO',
        'SOTO FIGUEROA, KARINA', 'MEJÍA COLÍN, SALVADOR', 'PORTILLO OCHOA, DIANA',
        'ALARCÓN VIDAL, ERNESTO', 'TOVAR NÁJERA, FERNANDA', 'ROMO LEAL, GREGORIO',
        'PONCE SERRANO, ALEJANDRA', 'GALINDO REINA, ÓSCAR', 'UREÑA TÉLLEZ, CLAUDIA',
        'ESPINO BADILLO, MAURICIO', 'CANTÚ GUERRERO, SARA', 'VILLANUEVA MONTES, RAFAEL',
        'INFANTE SANDOVAL, PILAR', 'CORONADO BLANCO, IGNACIO', 'OJEDA VÁZQUEZ, NORA',
        'BERNAL PALOMINO, HÉCTOR', 'ZAVALA GÓMEZ, ESTHER', 'CANO PACHECO, JULIO',
        'LUNA FUENTES, REBECA', 'MEZA ÁNGEL, TOMÁS', 'NIETO PÉREZ, ALICIA',
        'BUSTOS HERRERA, ENRIQUE', 'PALOMINO LARA, VERÓNICA', 'SALINAS ROBLES, JORGE',
        'BECERRA MUÑIZ, LORENA', 'OCHOA RÍOS, SAMUEL', 'NAVARRO CALVA, GABRIELA',
        'RÍOS MEDRANO, IVÁN', 'LEIVA CASTILLO, SILVIA', 'MONTOYA BERNAL, ÁNGEL',
        'CÁRDENAS ORTEGA, FABIOLA', 'ESCOBAR LUNA, ESTEBAN', 'QUIROZ SILVA, MARISOL',
        'TAPIA AGUILERA, GUSTAVO', 'IBARRA CORTÉS, AURORA', 'SERRANO FUENTES, CRISTÓBAL',
        'TÉLLEZ MORA, NORMA', 'BONILLA ROJAS, MARCOS', 'SILVA CAMPOS, LETICIA',
        'AGUILERA NAVA, AURELIO', 'FUENTES MORA, CECILIA', 'CASTAÑEDA RÍOS, BENJAMÍN',
        'MORAN DÍAZ, PATRICIA', 'FIGUEROA SALAS, ANTONIO', 'SANDOVAL REYES, BLANCA',
        'SOLÍS HERNÁNDEZ, GERARDO', 'NAVA GUTIÉRREZ, ROSA', 'PAREDES TÉLLEZ, FELIPE',
        'PALACIOS BERNAL, DANIELA', 'GUERRERO CANO, RAMÓN', 'SOSA SERRANO, YOLANDA',
        'VELASCO FUENTES, LÁZARO', 'PULIDO ÁVILA, MIRIAM', 'MORENO TRUJILLO, JONÁS',
        'HERRERA ESPINO, ROCÍO', 'DURÁN PALOMINO, JORGE', 'RUIZ ORTEGA, ELSA',
        'ESPINOSA VALDEZ, MARIO', 'CERVANTES GALINDO, ANA KAREN', 'MOLINA CANTÚ, ISRAEL',
        'MEJÍA CORONADO, LAURA', 'NORIEGA CÁRDENAS, RUBÉN', 'PEDRAZA OCHOA, HILDA',
        'VEGA BUSTOS, SIXTO', 'OROZCO NAVARRO, MARGARITA', 'ARENAS RÍOS, ERNESTO',
    ];
    const formasPago = ['MENSUAL', 'ANUAL', 'TRIMESTRAL'];
    const tipos = ['Tarjeta', 'CARGO AUTOMATICO', 'Agente'];
    const tabuladores = ['CEDRO', 'FRESNO', 'ROBLE'];
    const zonas = ['Zona 1', 'Zona 3', 'Zona 6', 'Zona 11'];
    const polizas = [];

    for (let i = 0; i < 80; i++) {
        const agente = agentes[i % agentes.length];
        const gamaIdx = i % gamas.length;
        const prod = prodGmm.find(p => p.gama === gamas[gamaIdx]) || prodGmm[0];
        const year = i < 20 ? 2024 : (i < 65 ? 2025 : 2026);
        const month = String((i % 12) + 1).padStart(2, '0');
        const day = String(Math.min(28, (i % 25) + 1)).padStart(2, '0');
        const fechaInicio = `${year}-${month}-${day}`;
        const fechaFin = `${year + 1}-${month}-${day}`;
        const primaNeta = 8000 + (i * 350);
        const iva = primaNeta * 0.16;
        const recargo = primaNeta * 0.09;
        const numAseg = (i % 4) + 1;
        const esNueva = year >= 2025;

        polizas.push({
            poliza_original: `${String(10007 + i).padStart(5, '0')}U00`,
            poliza_estandar: `${10007 + i}U00`,
            agente_id: agente.id,
            producto_id: prod.id,
            asegurado_nombre: nombres[i % nombres.length],
            rfc: null,
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin,
            fecha_emision: fechaInicio,
            prima_total: primaNeta + iva + recargo,
            prima_neta: primaNeta,
            iva,
            recargo,
            suma_asegurada: 10000000 + (gamaIdx * 10000000),
            deducible: 50000 + (gamaIdx * 10000),
            coaseguro: 10,
            num_asegurados: numAseg,
            forma_pago: formasPago[i % formasPago.length],
            tipo_pago: tipos[i % tipos.length],
            status_recibo: i % 10 === 0 ? 'CANC/X F.PAGO' : 'PAGADA',
            gama: gamas[gamaIdx],
            es_nueva: esNueva ? 1 : 0,
            tipo_poliza: esNueva ? 'NUEVA' : 'SUBSECUENTE',
            tipo_prima: null,
            pct_comision: null,
            mystatus: i % 10 === 0 ? 'CANCELADA CADUCADA' : 'PAGADA TOTAL',
            periodo_aplicacion: `${year}-${month}`,
            anio_aplicacion: year,
        });
    }
    return polizas;
}
