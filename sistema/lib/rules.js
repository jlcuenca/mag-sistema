/**
 * Motor de reglas de negocio para clasificación de pólizas MAG-AXA
 */

export const UMBRAL_COMISION_BASICA = 0.021; // 2.1% — configurable

/**
 * REGLA 1: Clasificación Nueva vs. Subsecuente
 */
export function clasificarPoliza(poliza, anioAnalisis) {
    const year = parseInt(poliza.fecha_inicio?.substring(0, 4));

    if (poliza.ramo_codigo === 34) {
        // GMM
        if (year === anioAnalisis && poliza.status_recibo === 'PAGADA') {
            return { tipo_poliza: 'NUEVA', es_nueva: true };
        } else if (year === anioAnalisis - 1) {
            return { tipo_poliza: 'SUBSECUENTE', es_nueva: false };
        }
        return { tipo_poliza: 'NO_APLICA', es_nueva: false };
    }

    if (poliza.ramo_codigo === 11) {
        // VIDA
        const pct = poliza.prima_neta > 0 ? (poliza.comision || 0) / poliza.prima_neta : 0;
        const tipo_prima = pct >= UMBRAL_COMISION_BASICA ? 'BASICA' : 'EXCEDENTE';

        if (tipo_prima === 'BASICA') {
            if (year === anioAnalisis && poliza.status_recibo === 'PAGADA') {
                return { tipo_poliza: 'NUEVA', tipo_prima, pct_comision: pct, es_nueva: true };
            } else if (year === anioAnalisis - 1) {
                return { tipo_poliza: 'SUBSECUENTE', tipo_prima, pct_comision: pct, es_nueva: false };
            }
        }
        return { tipo_poliza: 'NO_APLICA', tipo_prima, pct_comision: pct, es_nueva: false };
    }

    return { tipo_poliza: 'NO_APLICA', es_nueva: false };
}

/**
 * REGLA 4: Alerta frontera de año (pagos 2-5 enero)
 */
export function alertaFronteraAnio(fechaPago) {
    if (!fechaPago) return false;
    const d = new Date(fechaPago);
    return d.getMonth() === 0 && d.getDate() >= 2 && d.getDate() <= 5;
}

/**
 * REGLA 5: Detección de reexpediciones
 */
export function esReexpedicion(numPoliza) {
    const match = numPoliza?.match(/(\d+[A-Z]*)(\d{2})$/);
    if (!match) return false;
    return parseInt(match[2]) > 0;
}

export function normalizarPoliza(num) {
    if (!num) return num;
    // Quitar ceros iniciales no significativos numéricos
    return num.replace(/^0+(\d)/, '$1');
}

/**
 * REGLA 6: MYSTATUS
 */
export function calcularMyStatus(statusRecibo) {
    switch (statusRecibo) {
        case 'CANC/X F.PAGO': return 'CANCELADA CADUCADA';
        case 'CANC/X SUSTITUCION': return 'CANCELADA NO TOMADA';
        case 'PAGADA': return 'PAGADA TOTAL';
        default: return '';
    }
}

/**
 * Calcular KPIs para dashboard
 */
export function calcularKPIs(polizas, anio = new Date().getFullYear()) {
    const nuevasVida = polizas.filter(p =>
        p.tipo_poliza === 'NUEVA' && p.ramo_codigo === 11 && p.tipo_prima === 'BASICA' && p.anio_aplicacion === anio
    );
    const nuevasGmm = polizas.filter(p =>
        p.tipo_poliza === 'NUEVA' && p.ramo_codigo === 34 && p.anio_aplicacion === anio
    );
    const subsVida = polizas.filter(p => p.tipo_poliza === 'SUBSECUENTE' && p.ramo_codigo === 11 && p.anio_aplicacion === anio);
    const subsGmm = polizas.filter(p => p.tipo_poliza === 'SUBSECUENTE' && p.ramo_codigo === 34 && p.anio_aplicacion === anio);

    return {
        polizasNuevasVida: nuevasVida.length,
        primaNuevaVida: nuevasVida.reduce((s, p) => s + (p.prima_neta || 0), 0),
        polizasNuevasGmm: nuevasGmm.length,
        aseguradosNuevosGmm: nuevasGmm.reduce((s, p) => s + (p.num_asegurados || 1), 0),
        primaNuevaGmm: nuevasGmm.reduce((s, p) => s + (p.prima_neta || 0), 0),
        primaSubsecuenteVida: subsVida.reduce((s, p) => s + (p.prima_neta || 0), 0),
        primaSubsecuenteGmm: subsGmm.reduce((s, p) => s + (p.prima_neta || 0), 0),
        canceladasVida: polizas.filter(p => p.ramo_codigo === 11 && p.status_recibo !== 'PAGADA').length,
        canceladasGmm: polizas.filter(p => p.ramo_codigo === 34 && p.status_recibo !== 'PAGADA').length,
    };
}
