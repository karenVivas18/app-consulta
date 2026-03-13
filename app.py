import streamlit as st
import re
from datetime import datetime, date

# 1. Configuración de la página
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# --- DATA MAESTRA DE CALENDARIOS ---
DATA_MASTER = {
    "PRISMA (Visa/Amex)": [
        {"cierre": date(2026, 1, 8), "prev_c": date(2025, 12, 11), "next_c": date(2026, 2, 5), "prev_e": date(2025, 12, 19), "curr_e": date(2026, 1, 16), "next_e": date(2026, 2, 13), "port": 4},
        {"cierre": date(2026, 1, 15), "prev_c": date(2025, 12, 18), "next_c": date(2026, 2, 12), "prev_e": date(2025, 12, 26), "curr_e": date(2026, 1, 23), "next_e": date(2026, 2, 20), "port": 3},
        {"cierre": date(2026, 1, 22), "prev_c": date(2025, 12, 24), "next_c": date(2026, 2, 19), "prev_e": date(2026, 1, 5), "curr_e": date(2026, 2, 2), "next_e": date(2026, 3, 2), "port": 2},
        {"cierre": date(2026, 1, 29), "prev_c": date(2025, 12, 31), "next_c": date(2026, 2, 26), "prev_e": date(2026, 1, 9), "curr_e": date(2026, 2, 6), "next_e": date(2026, 3, 6), "port": 1},
        {"cierre": date(2026, 2, 5), "prev_c": date(2026, 1, 8), "next_c": date(2026, 3, 5), "prev_e": date(2026, 1, 16), "curr_e": date(2026, 2, 13), "next_e": date(2026, 3, 13), "port": 4},
        {"cierre": date(2026, 2, 19), "prev_c": date(2026, 1, 22), "next_c": date(2026, 3, 19), "prev_e": date(2026, 2, 2), "curr_e": date(2026, 3, 2), "next_e": date(2026, 4, 1), "port": 2},
        {"cierre": date(2026, 3, 5), "prev_c": date(2026, 2, 5), "next_c": date(2026, 4, 9), "prev_e": date(2026, 2, 13), "curr_e": date(2026, 3, 13), "next_e": date(2026, 4, 17), "port": 4},
    ],
    "FISERV (MasterCard)": [
        {"cierre": date(2026, 1, 8), "prev_c": date(2025, 12, 11), "next_c": date(2026, 2, 5), "prev_e": date(2025, 12, 19), "curr_e": date(2026, 1, 16), "next_e": date(2026, 2, 13), "port": 13},
        {"cierre": date(2026, 1, 22), "prev_c": date(2025, 12, 24), "next_c": date(2026, 2, 19), "prev_e": date(2026, 1, 5), "curr_e": date(2026, 2, 2), "next_e": date(2026, 3, 2), "port": 11},
    ]
}

ENTIDADES = {"VISA": "007", "AMEX": "607", "MASTER": "027"}
MAPEO_ESTADOS = {"ACTIVA": 1, "INACTIVA": 2, "BAJA": 3, "NO INFORMADO": 4, "SUSPENDIDO": 5, "RESTRINGIDA": 6, "PAUSADA": 7, "INHABILITADA": 8}

# --- FUNCIONES DE LÓGICA ---
def generar_queries_tramites(texto):
    tipo = re.search(r"TIPO:\s*(TC|TD)", texto, re.I); tarjeta = re.search(r"TARJETA:\s*(\d{15,16})", texto, re.I)
    dni = re.search(r"DNI:\s*(\d+)", texto, re.I); cc = re.search(r"CC:\s*(\d+)", texto, re.I); accion = re.search(r"ACCION:\s*(.*)", texto, re.I)
    if not (tipo and tarjeta and dni and accion): return None, None
    t_tipo, t_num, t_dni = tipo.group(1).upper(), tarjeta.group(1), dni.group(1)
    t_bin, t_last4 = t_num[:6], t_num[-4:]; t_cc, t_acc = (cc.group(1) if cc else None), accion.group(1).upper()
    joins = "INNER JOIN DEBIT_CARDS DC ON C.ID = DC.CUSTOMER_ID INNER JOIN CARDS T ON DC.CARD_ID = T.ID" if t_tipo == "TD" else \
            "INNER JOIN CREDIT_ACCOUNTS CA ON C.ID = CA.CUSTOMER_ID INNER JOIN CREDIT_CARDS CC ON CA.ID = CC.ACCOUNT_ID INNER JOIN CARDS T ON CC.CARD_ID = T.ID"
    where_sql = f"WHERE C.DOCUMENT = '{t_dni}' AND T.BIN = '{t_bin}' AND T.LAST_DIGITS = '{t_last4}'"
    sql_final = ""
    for nombre, id_estado in MAPEO_ESTADOS.items():
        if nombre in t_acc: sql_final += f"-- ESTADO {nombre}\nUPDATE CARDS_STATUS SET STATUS_ID = {id_estado}, UPDATED_AT = CURRENT_TIMESTAMP WHERE CARD_ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n\n"
    if any(x in t_acc for x in ["VIRTUAL", "FALSE"]): sql_final += f"UPDATE CARDS SET PRINTED = 0 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    elif any(x in t_acc for x in ["FISICA", "TRUE"]): sql_final += f"UPDATE CARDS SET PRINTED = 1 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    mongo = f"db.temporary_limit_detail.deleteMany({{ \"document_number\": \"{t_dni}\", \"account_number\": \"{t_cc}\" }});" if t_cc and ("LIMPIAR_MONGO" in t_acc or "AULITRAN" in t_acc) else ""
    return sql_final, mongo

def generar_delete_debit(dni):
    return f"DELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nDELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nDELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nDELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');"

def generar_delete_credit_por_cifrado(cifrados_str):
    cifrados = [c.strip() for c in cifrados_str.replace("'", "").replace(",", " ").split() if c.strip()]
    if not cifrados: return "-- ⚠️ Ingresa cifrados válidos."
    lista_sql = ", ".join([f"'{c}'" for c in cifrados])
    return f"DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE \"NUMBER\" IN ({lista_sql}));\nDELETE FROM CREDIT_CARDS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE \"NUMBER\" IN ({lista_sql}));\nDELETE FROM CARDS WHERE \"NUMBER\" IN ({lista_sql});"

# --- INTERFAZ ---
st.title("🚀 QA Automation Tool COTA")
tabs = st.tabs(["📝 Trámites", "🔧 Varios", "⚠️ Eliminación", "📦 Dump", "📅 Settlement", "💰 Simulator", "📋 Protocolo"])

with tabs[0]:
    input_text = st.text_area("Mensaje del chat:", height=150)
    if st.button("Generar Trámites"):
        sql, mongo = generar_queries_tramites(input_text)
        if sql: st.code(sql, "sql")
        if mongo: st.code(mongo, "javascript")

with tabs[1]:
    st.subheader("👤 Cliente & Cuenta")
    col_c1, col_c2, col_c3 = st.columns(3)
    c_nom, c_ape, c_dni = col_c1.text_input("Nombre:"), col_c2.text_input("Apellido:"), col_c3.text_input("DNI:")
    if st.button("Update Cliente"): st.code(f"UPDATE CUSTOMERS SET NAME='{c_nom.upper()}', SURNAME='{c_ape.upper()}' WHERE DOCUMENT='{c_dni}';", "sql")
    st.divider()
    acc_n, acc_st = st.columns(2)
    a_n = acc_n.text_input("Nro Cuenta:")
    a_s = acc_st.selectbox("Estado:", list(MAPEO_ESTADOS.keys()))
    if st.button("Actualizar Cuenta"): st.code(f"UPDATE ACCOUNTS_STATUS SET STATUS_ID={MAPEO_ESTADOS[a_s]}, UPDATED_AT=CURRENT_TIMESTAMP WHERE ACCOUNT_ID=(SELECT ID FROM CREDIT_ACCOUNTS WHERE \"NUMBER\"='{a_n}');", "sql")

with tabs[2]:
    st.error("⚠️ ELIMINACIONES PERMANENTES")
    c1, c2 = st.columns(2)
    with c1:
        d_dni = st.text_input("DNI Débito:")
        if st.button("Borrar Débito"): st.code(generar_delete_debit(d_dni), "sql")
    with c2:
        d_cif = st.text_area("Cifrados Crédito:")
        if st.button("Borrar Crédito (CIF)"): st.code(generar_delete_credit_por_cifrado(d_cif), "sql")

with tabs[3]:
    dump_in = st.text_area("INSERTS de M_DUMP_DEBIT_CARD:", height=200)
    if st.button("Procesar Dump"): st.code(re.sub(r"VALUES\s*\((.*?)\)\s*;", lambda m: f"INSERT INTO M_DUMP_DEBIT_ACCOUNTS (MDUMP_ID, ACCOUNT_TYPE, ACCOUNT_NUMBER, ACCOUNT_STATUS, ACCOUNT_PREFERRED, ACCOUNT_PRIMARY) VALUES ({m.group(1).split(',')[0].strip()}, '1', {m.group(1).split(',')[16].strip()}, '1', '0', '1');", dump_in, flags=re.I), "sql")

with tabs[4]:
    st.subheader("📅 Liquidación & Cotización")
    col_m1, col_m2 = st.columns(2)
    marca = col_m1.selectbox("Marca:", list(DATA_MASTER.keys()))
    acc_s = col_m2.text_input("Cuenta (Settlement):", placeholder="413864350")
    
    cal_ref = DATA_MASTER[marca]
    c_selected = st.selectbox("Cierre (Current Closing):", [f["cierre"] for f in cal_ref])
    reg = next(item for item in cal_ref if item["cierre"] == c_selected)
    
    f1, f2, f3 = st.columns(3)
    c_cl, p_cl, n_cl = f1.date_input("Current Closing", reg["cierre"]), f2.date_input("Previous Closing", reg["prev_c"]), f3.date_input("Next Closing", reg["next_c"])
    f4, f5, f6 = st.columns(3)
    c_ex, p_ex, n_ex = f4.date_input("Current Expiration", reg["curr_e"]), f5.date_input("Prev Expiration", reg["prev_e"]), f6.date_input("Next Expiration", reg["next_e"])
    
    st.divider()
    st.subheader("💵 Configuración de Deuda Base & Dólar")
    d_col1, d_col2 = st.columns(2)
    base_p = d_col1.number_input("Pesos Base (LIQ_AUS_BALANCE):", value=0.0)
    base_d = d_col2.number_input("Dólares Base (LAST_LIQ_USD_AMOUNT):", value=0.0)
    
    x_col1, x_col2 = st.columns(2)
    buy_rate = x_col1.number_input("Buying Rate (Compra):", value=2100.0)
    sell_rate = x_col2.number_input("Selling Rate (Venta):", value=2150.0)

    if st.button("🚀 Generar Bloque Settlement + Dólar"):
        suf = "PRISMA" if "PRISMA" in marca else "FISERV"
        p_liq = reg["port"] + (1 if suf=="PRISMA" else 0)
        sql = f"""-- COTIZACION DÓLAR PARA EXPIRATION
DELETE FROM DOLLAR_EXCHANGE_RATES WHERE DATE_RATE = TO_DATE('{c_ex}','YYYY-MM-DD');
INSERT INTO DOLLAR_EXCHANGE_RATES (DATE_RATE, PURCHASE, SELLING, PROCESS_DATE) VALUES (TO_DATE('{c_ex}','YYYY-MM-DD'), {buy_rate}, {sell_rate}, CURRENT_TIMESTAMP);

-- SETTLEMENT BASE
UPDATE RD_LIQUIDATIONS_USER_{suf} SET CLOSING_DATE_LIQ=TO_DATE('{p_cl}','YYYY-MM-DD'), LIQ_DATE=TO_DATE('{c_cl}','YYYY-MM-DD'), EXPIRATION_DATE=TO_DATE('{c_ex}','YYYY-MM-DD'), PORTFOLIO={p_liq}, LIQ_AUS_BALANCE={base_p}, LAST_LIQ_USD_AMOUNT={base_d} WHERE ACCOUNT='{acc_s}';
UPDATE RD_SUMMARY_HEADER_{suf} SET CLOSE_DATE_ID=TO_DATE('{c_cl}','YYYY-MM-DD'), NEXT_CLOSE_DATE=TO_DATE('{n_cl}','YYYY-MM-DD'), PORTFOLIO={reg['port']} WHERE ACCOUNT_NUMBER_ID='{acc_s}';"""
        st.code(sql, "sql")

with tabs[5]:
    st.subheader("💰 Simulador de Deuda Actual")
    col_v1, col_v2 = st.columns(2)
    m_mov = col_v1.selectbox("Marca:", ["VISA", "AMEX", "MASTER"])
    a_mov = col_v2.text_input("Cuenta:", key="acc_mov_v")
    
    tipo_mov = st.radio("Tipo:", ["PAGO (Resta)", "CONSUMO (Suma)"], horizontal=True)
    m_c1, m_c2, m_c3 = st.columns(3)
    monto_mov = m_c1.number_input("Monto Movimiento:", value=0.0)
    mon_mov = m_c2.selectbox("Moneda:", ["ARS", "USD"])
    f_cie_mov = m_c3.date_input("Cierre Destino:", value=date(2026, 2, 19))

    if st.button("🚀 Generar Movimiento"):
        ent = ENTIDADES[m_mov]; ori = "FISERV" if m_mov == "MASTER" else "PRISMA"
        if tipo_mov == "PAGO (Resta)":
            sql_m = f"INSERT INTO PAYMENTS_OP_LIGHT (ID, ENTITY_CODE, FINANTIAL_ENTITY_CODE, CREDIT_ACCOUNT, BRANCH_OFFICE, TRANSACTION_DATE, OPERATION_DATE, EXTERNAL_PAYMENT_CODE, AMOUNT1, CURRENCY, PORTFOLIO, CLOSE_DATE, ORIGIN_TRANSACTION, CREATE_DATE, OPERATION_ID) VALUES ((SELECT MAX(ID)+1 FROM PAYMENTS_OP_LIGHT), '{ent}', '{ent}', '{a_mov}', '040', CURRENT_DATE, CURRENT_DATE, '2500', {monto_mov}, '{mon_mov}', 2, TO_DATE('{f_cie_mov}','YYYY-MM-DD'), '{ori}', CURRENT_TIMESTAMP, SYS_GUID());"
        else:
            sql_m = f"INSERT INTO PURCHASE_TC_OP_LIGHT (CARD_NUMBER, PURCHASE_DATE, MERCHANT_NAME, AMOUNT, CURRENCY, CLOSE_DATE, ORIGIN_TRANSACTION, ACCOUNT_NUMBER, PROCESS_DATE) VALUES ('000000', CURRENT_DATE, 'MOV QA', {monto_mov}, '{mon_mov}', TO_DATE('{f_cie_mov}','YYYY-MM-DD'), '{ori}', '{a_mov}', CURRENT_TIMESTAMP);"
        st.code(sql_m, "sql")
    
    st.divider()
    st.subheader("🎯 Resultado Esperado en API")
    # Cálculo lógica
    calc_pesos = base_p + (monto_mov if tipo_mov=="CONSUMO (Suma)" and mon_mov=="ARS" else 0) - (monto_mov if tipo_mov=="PAGO (Resta)" and mon_mov=="ARS" else 0)
    calc_dolar = base_d + (monto_mov if tipo_mov=="CONSUMO (Suma)" and mon_mov=="USD" else 0) - (monto_mov if tipo_mov=="PAGO (Resta)" and mon_mov=="USD" else 0)
    total_en_pesos = calc_pesos + (calc_dolar * sell_rate)

    st.write(f"**Deuda en Pesos (`pesos_debt`):** {calc_pesos:,.2f} ARS")
    st.write(f"**Deuda en Dólares (`dollar_debt`):** {calc_dolar:,.2f} USD")
    st.success(f"**TOTAL DEUDA (PESOS + USD * RATE):** {total_en_pesos:,.2f} ARS")

with tabs[6]:
    st.subheader("📋 Protocolo de Mensaje")
    st.code("""SOLICITUD DE DEUDA QA
- CUENTA: [Nro]
- MARCA: [VISA/AMEX/MASTER]
- TIPO: [PAGO/CONSUMO]
- MONTO: [Valor]
- MONEDA: [ARS/USD]
- CIERRE: [Fecha]""", language="text")