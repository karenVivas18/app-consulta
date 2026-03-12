import streamlit as st
import re
from datetime import datetime, date

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# --- TABLAS DE CONFIGURACIÓN (CALENDARIOS) ---
# He mapeado los datos que pasaste para el año 2026
CALENDARIO_PRISMA = [
    {"cartera": 4, "cierre": date(2026, 1, 8), "vto": date(2026, 1, 16), "prox": date(2026, 2, 5)},
    {"cartera": 3, "cierre": date(2026, 1, 15), "vto": date(2026, 1, 23), "prox": date(2026, 2, 12)},
    {"cartera": 2, "cierre": date(2026, 1, 22), "vto": date(2026, 2, 2), "prox": date(2026, 2, 19)},
    {"cartera": 1, "cierre": date(2026, 1, 29), "vto": date(2026, 2, 6), "prox": date(2026, 2, 26)},
    {"cartera": 4, "cierre": date(2026, 2, 5), "vto": date(2026, 2, 13), "prox": date(2026, 3, 5)},
    {"cartera": 3, "cierre": date(2026, 2, 12), "vto": date(2026, 2, 20), "prox": date(2026, 3, 12)},
    {"cartera": 2, "cierre": date(2026, 2, 19), "vto": date(2026, 3, 2), "prox": date(2026, 3, 19)},
    {"cartera": 1, "cierre": date(2026, 2, 26), "vto": date(2026, 3, 6), "prox": date(2026, 3, 26)},
    {"cartera": 4, "cierre": date(2026, 3, 5), "vto": date(2026, 3, 13), "prox": date(2026, 4, 9)},
    {"cartera": 3, "cierre": date(2026, 3, 12), "vto": date(2026, 3, 20), "prox": date(2026, 4, 16)},
    {"cartera": 2, "cierre": date(2026, 3, 19), "vto": date(2026, 4, 1), "prox": date(2026, 4, 23)},
    {"cartera": 1, "cierre": date(2026, 3, 26), "vto": date(2026, 4, 6), "prox": date(2026, 4, 30)},
]

CALENDARIO_FISERV = [
    {"cartera": 13, "cierre": date(2026, 1, 8), "vto": date(2026, 1, 16), "prox": date(2026, 2, 5)},
    {"cartera": 14, "cierre": date(2026, 1, 15), "vto": date(2026, 1, 23), "prox": date(2026, 2, 12)},
    {"cartera": 11, "cierre": date(2026, 1, 22), "vto": date(2026, 2, 2), "prox": date(2026, 2, 19)},
    {"cartera": 12, "cierre": date(2026, 1, 29), "vto": date(2026, 2, 6), "prox": date(2026, 2, 26)},
    {"cartera": 13, "cierre": date(2026, 2, 5), "vto": date(2026, 2, 13), "prox": date(2026, 3, 5)},
    {"cartera": 14, "cierre": date(2026, 2, 12), "vto": date(2026, 2, 20), "prox": date(2026, 3, 12)},
    {"cartera": 11, "cierre": date(2026, 2, 19), "vto": date(2026, 3, 2), "prox": date(2026, 3, 19)},
    {"cartera": 12, "cierre": date(2026, 2, 26), "vto": date(2026, 3, 6), "prox": date(2026, 3, 26)},
    {"cartera": 13, "cierre": date(2026, 3, 5), "vto": date(2026, 3, 13), "prox": date(2026, 4, 9)},
    {"cartera": 14, "cierre": date(2026, 3, 12), "vto": date(2026, 3, 20), "prox": date(2026, 4, 16)},
    {"cartera": 11, "cierre": date(2026, 3, 19), "vto": date(2026, 4, 1), "prox": date(2026, 4, 23)},
    {"cartera": 12, "cierre": date(2026, 3, 26), "vto": date(2026, 4, 6), "prox": date(2026, 4, 30)},
]

MAPEO_ESTADOS = {
    "ACTIVA": 1, "INACTIVA": 2, "BAJA": 3, "NO INFORMADO": 4,
    "SUSPENDIDO": 5, "RESTRINGIDA": 6, "PAUSADA": 7, "INHABILITADA": 8
}

# --- FUNCIONES DE LÓGICA ---
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

def generar_delete_debit(dni):
    return f"""DELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');"""

def procesar_dump(texto):
    registros = re.findall(r"VALUES\s*\((.*?)\)\s*;", texto, re.I)
    return "\n".join([f"INSERT INTO M_DUMP_DEBIT_ACCOUNTS (MDUMP_ID, ACCOUNT_TYPE, ACCOUNT_NUMBER, ACCOUNT_STATUS, ACCOUNT_PREFERRED, ACCOUNT_PRIMARY) VALUES ({reg.split(',')[0].strip()}, '1', {reg.split(',')[16].strip()}, '1', '0', '1');" for reg in registros if len(reg.split(',')) > 16])

# --- INTERFAZ ---
st.title("🚀 QA Automation Tool COTA")
tabs = st.tabs(["📝 Trámites", "🔧 Varios", "⚠️ Eliminación", "📦 Dump", "📅 Settlement & Taxes"])

with tabs[0]:
    in_t = st.text_area("Mensaje del chat:", height=150)
    if st.button("Generar Trámite"):
        s, m = generar_queries_tramites(in_t)
        if s: st.code(s, "sql")
        if m: st.code(m, "javascript")

with tabs[1]:
    col1, col2, col3 = st.columns(3)
    c_dni = col3.text_input("DNI Cliente:")
    if st.button("Update Nombre/Apellido"):
        st.code(f"UPDATE CUSTOMERS SET NAME='{col1.text_input('Nombre:').upper()}', SURNAME='{col2.text_input('Apellido:').upper()}' WHERE DOCUMENT='{c_dni}';", "sql")
    st.divider()
    acc_n = st.text_input("Cuenta para Estado:", key="acc_v")
    acc_s = st.selectbox("Nuevo Estado:", list(MAPEO_ESTADOS.keys()))
    if st.button("Actualizar Cuenta"):
        st.code(f"UPDATE ACCOUNTS_STATUS SET STATUS_ID={MAPEO_ESTADOS[acc_s]}, UPDATED_AT=CURRENT_TIMESTAMP WHERE ACCOUNT_ID=(SELECT ID FROM CREDIT_ACCOUNTS WHERE \"NUMBER\"='{acc_n}');", "sql")

with tabs[2]:
    d_dni = st.text_input("DNI Débito a Borrar:")
    if st.button("Generar Delete"): st.code(generar_delete_debit(d_dni), "sql")

with tabs[3]:
    dump_in = st.text_area("INSERTS M_DUMP_DEBIT_CARD:", height=150)
    if st.button("Procesar"): st.code(procesar_dump(dump_in), "sql")

with tabs[4]:
    st.subheader("📅 Liquidación Inteligente")
    c_m1, c_m2, c_m3 = st.columns([1, 1, 2])
    marca = c_m1.selectbox("Administradora:", ["PRISMA (Visa/Amex)", "FISERV (MasterCard)"])
    
    if "PRISMA" in marca:
        lista_c, cal_ref = [1, 2, 3, 4], CALENDARIO_PRISMA
        pre_tab, suf = "PRISMA", "PRISMA"
    else:
        lista_c, cal_ref = [11, 12, 13, 14], CALENDARIO_FISERV
        pre_tab, suf = "FISERV", "FISERV"

    nro_c = c_m2.selectbox("Cartera:", lista_c)
    acc_s = c_m3.text_input("Número de Cuenta (Flexible):")

    # Sugerencia automática basada en "hoy" (Marzo 2026)
    hoy = date(2026, 3, 12)
    sug = next((f for f in cal_ref if f["cartera"] == nro_c and f["cierre"] >= hoy), cal_ref[-1])
    
    col_f1, col_f2, col_f3 = st.columns(3)
    c_cl = col_f1.date_input("Current Closing", sug["cierre"])
    p_cl = col_f2.date_input("Previous Closing", date(2026, 2, sug["cierre"].day))
    n_cl = col_f3.date_input("Next Closing", sug["prox"])

    col_f4, col_f5, col_f6 = st.columns(3)
    c_ex = col_f4.date_input("Current Expiration", sug["vto"])
    p_ex = col_f5.date_input("Previous Expiration", date(2026, 2, sug["vto"].day))
    n_ex = col_f6.date_input("Next Expiration", date(2026, 4, sug["vto"].day))

    st.divider()
    st_tax = st.toggle("¿Incluir Impuestos?")
    if st_tax:
        t1, t2, t3 = st.columns(3)
        t_cod, t_amt, t_des = t1.text_input("Tax Code", "2015"), t2.text_input("Monto", "0"), t3.text_input("Desc", "TAX QA")

    if st.button("🚀 Generar Settlement"):
        if acc_s:
            p_acc, v_dig = acc_s[:-1], acc_s[-1]
            sql = f"""-- UPDATE PORTFOLIO Y TABLAS
UPDATE CREDIT_ACCOUNTS SET PORTFOLIO_TYPE_ID = {nro_c} WHERE "NUMBER" = '{acc_s}';
UPDATE RD_LIQUIDATIONS_USER_{suf} SET CLOSING_DATE_LIQ=TO_DATE('{p_cl}','YYYY-MM-DD'), LIQ_DATE=TO_DATE('{c_cl}','YYYY-MM-DD'), EXPIRATION_DATE=TO_DATE('{c_ex}','YYYY-MM-DD') WHERE ACCOUNT='{acc_s}';
UPDATE RD_SUMMARY_HEADER_{suf} SET CLOSE_DATE_ID=TO_DATE('{c_cl}','YYYY-MM-DD'), NEXT_CLOSE_DATE=TO_DATE('{n_cl}','YYYY-MM-DD') WHERE ACCOUNT_NUMBER_ID='{acc_s}';

-- INSERT SETTLEMENT
INSERT INTO USR_DATACOTAH.RD_LIQUIDATIONS_USER_{suf} (ACCOUNT_NUM, VERIFIER_DIGIT_ACCOUNT, ACCOUNT, BANK_CODE, PORTFOLIO, LIQ_DATE, CLOSING_DATE_LIQ, EXPIRATION_DATE, PROCESS_DATE) 
VALUES ({p_acc}, {v_dig}, '{acc_s}', 7, {nro_c if "FISERV" in marca else nro_c+1}, TO_DATE('{c_cl}','YYYY-MM-DD'), TO_DATE('{p_cl}','YYYY-MM-DD'), TO_DATE('{c_ex}','YYYY-MM-DD'), CURRENT_TIMESTAMP);
"""
            st.code(sql, "sql")
            if st_tax:
                st.code(f"INSERT INTO RD_TAX_COMMISSION_DETAIL_OP (ENTITY_CODE, FINANTIAL_ENTITY_CODE, CREDIT_ACCOUNT, BRANCH_OFFICE, TAX_CODE, TAX_DESCRIPTION, AMOUNT, CURRENCY, CLOSE_DATE, CREATE_DATE) VALUES ('007', '007', '{acc_s}', '79', '{t_cod}', '{t_des}', {t_amt}, 'ARS', TO_DATE('{c_cl}','YYYY-MM-DD'), CURRENT_TIMESTAMP);", "sql")