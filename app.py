import streamlit as st
import re
from datetime import datetime, date

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# --- TABLAS DE CONFIGURACIÓN (CALENDARIOS 2026) ---
CALENDARIO_PRISMA = [
    {"cierre": date(2026, 1, 8), "vto": date(2026, 1, 16), "prox_c": date(2026, 2, 5), "port": 4},
    {"cierre": date(2026, 1, 15), "vto": date(2026, 1, 23), "prox_c": date(2026, 2, 12), "port": 3},
    {"cierre": date(2026, 1, 22), "vto": date(2026, 2, 2), "prox_c": date(2026, 2, 19), "port": 2},
    {"cierre": date(2026, 1, 29), "vto": date(2026, 2, 6), "prox_c": date(2026, 2, 26), "port": 1},
    {"cierre": date(2026, 2, 5), "vto": date(2026, 2, 13), "prox_c": date(2026, 3, 5), "port": 4},
    {"cierre": date(2026, 2, 12), "vto": date(2026, 2, 20), "prox_c": date(2026, 3, 12), "port": 3},
    {"cierre": date(2026, 2, 19), "vto": date(2026, 3, 2), "prox_c": date(2026, 3, 19), "port": 2},
    {"cierre": date(2026, 2, 26), "vto": date(2026, 3, 6), "prox_c": date(2026, 3, 26), "port": 1},
    {"cierre": date(2026, 3, 5), "vto": date(2026, 3, 13), "prox_c": date(2026, 4, 9), "port": 4},
    {"cierre": date(2026, 3, 12), "vto": date(2026, 3, 20), "prox_c": date(2026, 4, 16), "port": 3},
    {"cierre": date(2026, 3, 19), "vto": date(2026, 4, 1), "prox_c": date(2026, 4, 23), "port": 2},
    {"cierre": date(2026, 3, 26), "vto": date(2026, 4, 6), "prox_c": date(2026, 4, 30), "port": 1},
]

CALENDARIO_FISERV = [
    {"cierre": date(2026, 1, 8), "vto": date(2026, 1, 16), "prox_c": date(2026, 2, 5), "port": 13},
    {"cierre": date(2026, 1, 15), "vto": date(2026, 1, 23), "prox_c": date(2026, 2, 12), "port": 14},
    {"cierre": date(2026, 1, 22), "vto": date(2026, 2, 2), "prox_c": date(2026, 2, 19), "port": 11},
    {"cierre": date(2026, 1, 29), "vto": date(2026, 2, 6), "prox_c": date(2026, 2, 26), "port": 12},
    {"cierre": date(2026, 2, 5), "vto": date(2026, 2, 13), "prox_c": date(2026, 3, 5), "port": 13},
    {"cierre": date(2026, 2, 12), "vto": date(2026, 2, 20), "prox_c": date(2026, 3, 12), "port": 14},
    {"cierre": date(2026, 2, 19), "vto": date(2026, 3, 2), "prox_c": date(2026, 3, 19), "port": 11},
    {"cierre": date(2026, 2, 26), "vto": date(2026, 3, 6), "prox_c": date(2026, 3, 26), "port": 12},
    {"cierre": date(2026, 3, 5), "vto": date(2026, 3, 13), "prox_c": date(2026, 4, 9), "port": 13},
    {"cierre": date(2026, 3, 12), "vto": date(2026, 3, 20), "prox_c": date(2026, 4, 16), "port": 14},
    {"cierre": date(2026, 3, 19), "vto": date(2026, 4, 1), "prox_c": date(2026, 4, 23), "port": 11},
    {"cierre": date(2026, 3, 26), "vto": date(2026, 4, 6), "prox_c": date(2026, 4, 30), "port": 12},
]

MAPEO_ESTADOS = {
    "ACTIVA": 1, "INACTIVA": 2, "BAJA": 3, "NO INFORMADO": 4,
    "SUSPENDIDO": 5, "RESTRINGIDA": 6, "PAUSADA": 7, "INHABILITADA": 8
}

# --- FUNCIONES ---
def generar_queries_tramites(texto):
    tipo = re.search(r"TIPO:\s*(TC|TD)", texto, re.I)
    tarjeta = re.search(r"TARJETA:\s*(\d{15,16})", texto, re.I)
    dni = re.search(r"DNI:\s*(\d+)", texto, re.I)
    cc = re.search(r"CC:\s*(\d+)", texto, re.I)
    accion = re.search(r"ACCION:\s*(.*)", texto, re.I)
    if not (tipo and tarjeta and dni and accion): return None, None
    t_tipo, t_num, t_dni, t_acc = tipo.group(1).upper(), tarjeta.group(1), dni.group(1), accion.group(1).upper()
    t_bin, t_last4, t_cc = t_num[:6], t_num[-4:], cc.group(1) if cc else None
    joins = "INNER JOIN DEBIT_CARDS DC ON C.ID = DC.CUSTOMER_ID INNER JOIN CARDS T ON DC.CARD_ID = T.ID" if t_tipo == "TD" else \
            "INNER JOIN CREDIT_ACCOUNTS CA ON C.ID = CA.CUSTOMER_ID INNER JOIN CREDIT_CARDS CC ON CA.ID = CC.ACCOUNT_ID INNER JOIN CARDS T ON CC.CARD_ID = T.ID"
    where_sql = f"WHERE C.DOCUMENT = '{t_dni}' AND T.BIN = '{t_bin}' AND T.LAST_DIGITS = '{t_last4}'"
    sql_final = ""
    for nombre, id_estado in MAPEO_ESTADOS.items():
        if nombre in t_acc:
            sql_final += f"-- ESTADO {nombre}\nUPDATE CARDS_STATUS SET STATUS_ID = {id_estado}, UPDATED_AT = CURRENT_TIMESTAMP WHERE CARD_ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n\n"
    if any(x in t_acc for x in ["VIRTUAL", "FALSE"]): sql_final += f"UPDATE CARDS SET PRINTED = 0 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    elif any(x in t_acc for x in ["FISICA", "TRUE"]): sql_final += f"UPDATE CARDS SET PRINTED = 1 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    mongo = f"db.temporary_limit_detail.deleteMany({{ \"document_number\": \"{t_dni}\", \"account_number\": \"{t_cc}\" }});" if t_cc and ("LIMPIAR" in t_acc or "AULITRAN" in t_acc) else ""
    return sql_final, mongo

# --- INTERFAZ ---
tabs = st.tabs(["📝 Trámites", "🔧 Varios", "⚠️ Eliminación", "📦 Dump", "📅 Settlement & Taxes"])

with tabs[0]:
    in_t = st.text_area("Mensaje del chat:", height=150)
    if st.button("Generar Trámite"):
        s, m = generar_queries_tramites(in_t)
        if s: st.code(s, "sql")
        if m: st.code(m, "javascript")

with tabs[1]:
    col1, col2, col3 = st.columns(3)
    dni_v = col3.text_input("DNI Cliente:", key="dni_v")
    if st.button("Update Nombre/Apellido"):
        st.code(f"UPDATE CUSTOMERS SET NAME='{col1.text_input('Nombre:').upper()}', SURNAME='{col2.text_input('Apellido:').upper()}' WHERE DOCUMENT='{dni_v}';", "sql")
    st.divider()
    acc_v = st.text_input("Nro Cuenta para Estado:", key="acc_v")
    est_v = st.selectbox("Nuevo Estado:", list(MAPEO_ESTADOS.keys()))
    if st.button("Actualizar Cuenta"):
        st.code(f"UPDATE ACCOUNTS_STATUS SET STATUS_ID={MAPEO_ESTADOS[est_v]}, UPDATED_AT=CURRENT_TIMESTAMP WHERE ACCOUNT_ID=(SELECT ID FROM CREDIT_ACCOUNTS WHERE \"NUMBER\"='{acc_v}');", "sql")

with tabs[2]:
    st.subheader("🗑️ Eliminación de Productos")
    del_dni = st.text_input("DNI del Cliente a limpiar:")
    
    col_del1, col_del2 = st.columns(2)
    if col_del1.button("Borrar Débito (DNI)"):
        st.code(f"""DELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{del_dni}');
DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{del_dni}');
DELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{del_dni}');
DELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{del_dni}');""", "sql")

    if col_del2.button("Borrar Crédito (DNI)"):
        st.code(f"""DELETE FROM CREDIT_CARDS WHERE ACCOUNT_ID IN (SELECT id FROM CREDIT_ACCOUNTS WHERE CUSTOMER_ID IN (SELECT id FROM CUSTOMERS WHERE DOCUMENT = '{del_dni}'));
DELETE FROM ACCOUNTS_STATUS WHERE ACCOUNT_ID IN (SELECT id FROM CREDIT_ACCOUNTS WHERE CUSTOMER_ID IN (SELECT id FROM CUSTOMERS WHERE DOCUMENT = '{del_dni}'));
DELETE FROM CREDIT_ACCOUNTS WHERE CUSTOMER_ID IN (SELECT id FROM CUSTOMERS WHERE DOCUMENT = '{del_dni}');""", "sql")

with tabs[3]:
    dump_in = st.text_area("Pega VALUES de M_DUMP_DEBIT_CARD:", height=150)
    if st.button("Procesar"):
        registros = re.findall(r"VALUES\s*\((.*?)\)\s*;", dump_in, re.I)
        res = [f"INSERT INTO M_DUMP_DEBIT_ACCOUNTS (MDUMP_ID, ACCOUNT_TYPE, ACCOUNT_NUMBER, ACCOUNT_STATUS, ACCOUNT_PREFERRED, ACCOUNT_PRIMARY) VALUES ({r.split(',')[0].strip()}, '1', {r.split(',')[16].strip()}, '1', '0', '1');" for r in registros if len(r.split(',')) > 16]
        st.code("\n".join(res), "sql")

with tabs[4]:
    st.subheader("📅 Liquidación Inteligente (Calendarios)")
    c1, c2 = st.columns(2)
    marca = c1.selectbox("Marca:", ["PRISMA", "FISERV"])
    acc_s = c2.text_input("Cuenta:")
    
    cal_ref = CALENDARIO_PRISMA if marca == "PRISMA" else CALENDARIO_FISERV
    lista_cierres = [f["cierre"] for f in cal_ref]
    c_selected = st.selectbox("Seleccionar Fecha de Cierre:", lista_cierres)
    
    reg = next(item for item in cal_ref if item["cierre"] == c_selected)
    st.info(f"Sugerencia de Cartera: {reg['port']}")

    f1, f2, f3 = st.columns(3)
    curr_c = f1.date_input("Current Closing", reg["cierre"])
    prev_c = f2.date_input("Previous Closing", date(2026, curr_c.month - 1, curr_c.day) if curr_c.month > 1 else date(2025, 12, curr_c.day))
    next_c = f3.date_input("Next Closing", reg["prox_c"])

    f4, f5, f6 = st.columns(3)
    curr_e = f4.date_input("Current Expiration", reg["vto"])
    prev_e = f5.date_input("Prev Expiration", date(2026, curr_e.month - 1, curr_e.day) if curr_e.month > 1 else date(2025, 12, curr_e.day))
    next_e = f6.date_input("Next Expiration", date(2026, curr_e.month + 1, curr_e.day) if curr_e.month < 12 else date(2027, 1, curr_e.day))

    port_f = st.number_input("Portfolio:", value=reg["port"])

    if st.button("🚀 Generar Settlement"):
        suf = "PRISMA" if marca == "PRISMA" else "FISERV"
        p_acc, v_dig = acc_s[:-1], acc_s[-1]
        p_liq = port_f + 1 if suf == "PRISMA" else port_f
        sql = f"""UPDATE CREDIT_ACCOUNTS SET PORTFOLIO_TYPE_ID = {port_f} WHERE "NUMBER" = '{acc_s}';
UPDATE RD_LIQUIDATIONS_USER_{suf} SET CLOSING_DATE_LIQ=TO_DATE('{prev_c}','YYYY-MM-DD'), LIQ_DATE=TO_DATE('{curr_c}','YYYY-MM-DD'), EXPIRATION_DATE=TO_DATE('{curr_e}','YYYY-MM-DD'), PORTFOLIO={p_liq} WHERE ACCOUNT='{acc_s}';
UPDATE RD_SUMMARY_HEADER_{suf} SET CLOSE_DATE_ID=TO_DATE('{curr_c}','YYYY-MM-DD'), NEXT_CLOSE_DATE=TO_DATE('{next_c}','YYYY-MM-DD') WHERE ACCOUNT_NUMBER_ID='{acc_s}';
INSERT INTO USR_DATACOTAH.RD_LIQUIDATIONS_USER_{suf} (ACCOUNT_NUM, VERIFIER_DIGIT_ACCOUNT, ACCOUNT, BANK_CODE, PORTFOLIO, LIQ_DATE, CLOSING_DATE_LIQ, EXPIRATION_DATE, PROCESS_DATE) 
VALUES ({p_acc}, {v_dig}, '{acc_s}', 7, {p_liq}, TO_DATE('{curr_c}','YYYY-MM-DD'), TO_DATE('{prev_c}','YYYY-MM-DD'), TO_DATE('{curr_e}','YYYY-MM-DD'), CURRENT_TIMESTAMP);"""
        st.code(sql, "sql")