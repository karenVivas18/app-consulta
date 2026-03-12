import streamlit as st
import re
from datetime import datetime, date

# 1. Configuración de la página
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# --- DATA MAESTRA DE CALENDARIOS (Basada en tus tablas 2026) ---
DATA_MASTER = {
    "PRISMA (Visa/Amex)": [
        {"cierre": date(2026, 1, 8), "prev_c": date(2025, 12, 11), "next_c": date(2026, 2, 5), "prev_e": date(2025, 12, 19), "curr_e": date(2026, 1, 16), "next_e": date(2026, 2, 13), "port": 4},
        {"cierre": date(2026, 1, 15), "prev_c": date(2025, 12, 18), "next_c": date(2026, 2, 12), "prev_e": date(2025, 12, 26), "curr_e": date(2026, 1, 23), "next_e": date(2026, 2, 20), "port": 3},
        {"cierre": date(2026, 1, 22), "prev_c": date(2025, 12, 24), "next_c": date(2026, 2, 19), "prev_e": date(2026, 1, 5), "curr_e": date(2026, 2, 2), "next_e": date(2026, 3, 2), "port": 2},
        {"cierre": date(2026, 1, 29), "prev_c": date(2025, 12, 31), "next_c": date(2026, 2, 26), "prev_e": date(2026, 1, 9), "curr_e": date(2026, 2, 6), "next_e": date(2026, 3, 6), "port": 1},
        {"cierre": date(2026, 2, 5), "prev_c": date(2026, 1, 8), "next_c": date(2026, 3, 5), "prev_e": date(2026, 1, 16), "curr_e": date(2026, 2, 13), "next_e": date(2026, 3, 13), "port": 4},
        {"cierre": date(2026, 3, 5), "prev_c": date(2026, 2, 5), "next_c": date(2026, 4, 9), "prev_e": date(2026, 2, 13), "curr_e": date(2026, 3, 13), "next_e": date(2026, 4, 17), "port": 4},
    ],
    "FISERV (MasterCard)": [
        {"cierre": date(2026, 1, 8), "prev_c": date(2025, 12, 11), "next_c": date(2026, 2, 5), "prev_e": date(2025, 12, 19), "curr_e": date(2026, 1, 16), "next_e": date(2026, 2, 13), "port": 13},
        {"cierre": date(2026, 1, 15), "prev_c": date(2025, 12, 18), "next_c": date(2026, 2, 12), "prev_e": date(2025, 12, 26), "curr_e": date(2026, 1, 23), "next_e": date(2026, 2, 20), "port": 14},
        {"cierre": date(2026, 1, 22), "prev_c": date(2025, 12, 24), "next_c": date(2026, 2, 19), "prev_e": date(2026, 1, 5), "curr_e": date(2026, 2, 2), "next_e": date(2026, 3, 2), "port": 11},
        {"cierre": date(2026, 1, 29), "prev_c": date(2025, 12, 31), "next_c": date(2026, 2, 26), "prev_e": date(2026, 1, 9), "curr_e": date(2026, 2, 6), "next_e": date(2026, 3, 6), "port": 12},
    ]
}

MAPEO_ESTADOS = {
    "ACTIVA": 1, "INACTIVA": 2, "BAJA": 3, "NO INFORMADO": 4,
    "SUSPENDIDO": 5, "RESTRINGIDA": 6, "PAUSADA": 7, "INHABILITADA": 8
}

# 3. Funciones de Lógica
def generar_queries_tramites(texto):
    tipo = re.search(r"TIPO:\s*(TC|TD)", texto, re.I)
    tarjeta = re.search(r"TARJETA:\s*(\d{15,16})", texto, re.I)
    dni = re.search(r"DNI:\s*(\d+)", texto, re.I)
    cc = re.search(r"CC:\s*(\d+)", texto, re.I)
    accion = re.search(r"ACCION:\s*(.*)", texto, re.I)
    if not (tipo and tarjeta and dni and accion): return None, None
    t_tipo, t_num, t_dni = tipo.group(1).upper(), tarjeta.group(1), dni.group(1)
    t_bin, t_last4 = t_num[:6], t_num[-4:]
    t_cc, t_acc = (cc.group(1) if cc else None), accion.group(1).upper()
    joins = "INNER JOIN DEBIT_CARDS DC ON C.ID = DC.CUSTOMER_ID INNER JOIN CARDS T ON DC.CARD_ID = T.ID" if t_tipo == "TD" else \
            "INNER JOIN CREDIT_ACCOUNTS CA ON C.ID = CA.CUSTOMER_ID INNER JOIN CREDIT_CARDS CC ON CA.ID = CC.ACCOUNT_ID INNER JOIN CARDS T ON CC.CARD_ID = T.ID"
    where_sql = f"WHERE C.DOCUMENT = '{t_dni}' AND T.BIN = '{t_bin}' AND T.LAST_DIGITS = '{t_last4}'"
    sql_final = ""
    for nombre, id_estado in MAPEO_ESTADOS.items():
        if nombre in t_acc:
            sql_final += f"-- ESTADO {nombre}\nUPDATE CARDS_STATUS SET STATUS_ID = {id_estado}, UPDATED_AT = CURRENT_TIMESTAMP WHERE CARD_ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n\n"
    if any(x in t_acc for x in ["VIRTUAL", "FALSE"]): sql_final += f"UPDATE CARDS SET PRINTED = 0 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    elif any(x in t_acc for x in ["FISICA", "TRUE"]): sql_final += f"UPDATE CARDS SET PRINTED = 1 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    mongo = f"db.temporary_limit_detail.deleteMany({{ \"document_number\": \"{t_dni}\", \"account_number\": \"{t_cc}\" }});" if t_cc and ("LIMPIAR_MONGO" in t_acc or "AULITRAN" in t_acc) else ""
    return sql_final, mongo

def generar_delete_debit(dni):
    return f"""DELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');"""

def generar_delete_credit_por_cifrado(cifrados_str):
    lineas = cifrados_str.replace("'", "").replace(",", " ").split()
    cifrados = [c.strip() for c in lineas if c.strip()]
    if not cifrados: return "-- ⚠️ Ingresa cifrados válidos."
    lista_sql = ", ".join([f"'{c}'" for c in cifrados])
    return f"DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE \"NUMBER\" IN ({lista_sql}));\nDELETE FROM CREDIT_CARDS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE \"NUMBER\" IN ({lista_sql}));\nDELETE FROM CARDS WHERE \"NUMBER\" IN ({lista_sql});"

def procesar_dump_accounts(texto):
    registros = re.findall(r"VALUES\s*\((.*?)\)\s*;", texto, re.I)
    queries = []
    for reg in registros:
        valores = [v.strip().strip("'") for v in reg.split(",")]
        try: queries.append(f"INSERT INTO M_DUMP_DEBIT_ACCOUNTS (MDUMP_ID, ACCOUNT_TYPE, ACCOUNT_NUMBER, ACCOUNT_STATUS, ACCOUNT_PREFERRED, ACCOUNT_PRIMARY) VALUES ({valores[0]}, '1', '{valores[16]}', '1', '0', '1');")
        except: continue
    return "\n".join(queries)

# --- 4. INTERFAZ ---
st.title("🚀 QA Automation Tool COTA")
tabs = st.tabs(["📝 Trámites", "🔧 Varios", "⚠️ Eliminación", "📦 Dump Masivo", "📅 Settlement & Taxes"])

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
    col_a1, col_a2 = st.columns(2)
    acc_n, acc_s = col_a1.text_input("Nro Cuenta:"), col_a2.selectbox("Estado:", list(MAPEO_ESTADOS.keys()))
    if st.button("Actualizar Cuenta"): st.code(f"UPDATE ACCOUNTS_STATUS SET STATUS_ID={MAPEO_ESTADOS[acc_s]}, UPDATED_AT=CURRENT_TIMESTAMP WHERE ACCOUNT_ID=(SELECT ID FROM CREDIT_ACCOUNTS WHERE \"NUMBER\"='{acc_n}');", "sql")

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
    if st.button("Procesar Dump"): st.code(procesar_dump_accounts(dump_in), "sql")

with tabs[4]:
    st.subheader("📅 Liquidación Inteligente (Excel Logic)")
    col_m1, col_m2, col_m3 = st.columns(3)
    marca = col_m1.selectbox("Marca:", list(DATA_MASTER.keys()))
    acc_s = col_m2.text_input("Cuenta:", placeholder="3142959686")
    bran_s = col_m3.text_input("Branch:", "79")
    
    cal_ref = DATA_MASTER[marca]
    c_selected = st.selectbox("Seleccionar Fecha de CIERRE (Current Closing):", [f["cierre"] for f in cal_ref])
    
    reg = next(item for item in cal_ref if item["cierre"] == c_selected)
    
    f1, f2, f3 = st.columns(3)
    c_cl = f1.date_input("Current Closing", reg["cierre"])
    p_cl = f2.date_input("Previous Closing", reg["prev_c"])
    n_cl = f3.date_input("Next Closing", reg["next_c"])
    
    f4, f5, f6 = st.columns(3)
    c_ex = f4.date_input("Current Expiration", reg["curr_e"])
    p_ex = f5.date_input("Previous Expiration", reg["prev_e"])
    n_ex = f6.date_input("Next Expiration", reg["next_e"])
    
    port_f = st.number_input("Portfolio:", value=reg["port"])

    st.divider()
    st_tax = st.toggle("¿Incluir Impuestos?")
    if st_tax:
        t1, t2, t3 = st.columns(3)
        t_cod, t_des, t_amt = t1.text_input("Tax Code", "2015"), t2.text_input("Desc", "TAX QA"), t3.text_input("Monto", "0")

    if st.button("🚀 Generar Bloque Settlement"):
        if acc_s:
            p_acc, v_dig = acc_s[:9], acc_s[-1]
            suf = "PRISMA" if "PRISMA" in marca else "FISERV"
            p_liq = port_f + 1 if suf == "PRISMA" else port_f
            sql = f"""-- UPDATE {suf}
UPDATE RD_LIQUIDATIONS_USER_{suf} SET CLOSING_DATE_LIQ=TO_DATE('{p_cl}','YYYY-MM-DD'), EXPIRATION_DATE_PREV=TO_DATE('{p_ex}','YYYY-MM-DD'), LIQ_DATE=TO_DATE('{c_cl}','YYYY-MM-DD'), EXPIRATION_DATE=TO_DATE('{c_ex}','YYYY-MM-DD'), PORTFOLIO={p_liq} WHERE ACCOUNT='{acc_s}';
UPDATE RD_SUMMARY_HEADER_{suf} SET CLOSE_DATE_ID=TO_DATE('{c_cl}','YYYY-MM-DD'), NEXT_CLOSE_DATE=TO_DATE('{n_cl}','YYYY-MM-DD'), NEXT_EXPIRATION_DATE=TO_DATE('{n_ex}','YYYY-MM-DD'), PORTFOLIO={port_f} WHERE ACCOUNT_NUMBER_ID='{acc_s}';
INSERT INTO USR_DATACOTAH.RD_LIQUIDATIONS_USER_{suf} (ACCOUNT_NUM, VERIFIER_DIGIT_ACCOUNT, ACCOUNT, BANK_CODE, PORTFOLIO, LIQ_DATE, CLOSING_DATE_LIQ, EXPIRATION_DATE, EXPIRATION_DATE_PREV, PROCESS_DATE) VALUES ({p_acc}, {v_dig}, '{acc_s}', 7, {p_liq}, TO_DATE('{c_cl}','YYYY-MM-DD'), TO_DATE('{p_cl}','YYYY-MM-DD'), TO_DATE('{c_ex}','YYYY-MM-DD'), TO_DATE('{p_ex}','YYYY-MM-DD'), CURRENT_TIMESTAMP);"""
            st.code(sql, "sql")
            if st_tax: st.code(f"INSERT INTO RD_TAX_COMMISSION_DETAIL_OP (ENTITY_CODE, FINANTIAL_ENTITY_CODE, CREDIT_ACCOUNT, BRANCH_OFFICE, TAX_CODE, TAX_DESCRIPTION, AMOUNT, CURRENCY, CLOSE_DATE, CREATE_DATE) VALUES ('007', '007', '{acc_s}', '{bran_s}', '{t_cod}', '{t_des}', {t_amt}, 'ARS', TO_DATE('{c_cl}','YYYY-MM-DD'), CURRENT_TIMESTAMP);", "sql")