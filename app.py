import streamlit as st
import re
from datetime import datetime, date

# 1. Configuración de la página
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# --- DATA MAESTRA DE PORTFOLIOS ---
TABLA_PORTFOLIOS = {
    1: {"DESC": "1ra Semana", "MAESTRO": 1, "PRISMA": 4, "FISERV": 13},
    2: {"DESC": "2da Semana", "MAESTRO": 2, "PRISMA": 3, "FISERV": 14},
    3: {"DESC": "3ra Semana", "MAESTRO": 3, "PRISMA": 2, "FISERV": 11},
    4: {"DESC": "4ta Semana", "MAESTRO": 4, "PRISMA": 1, "FISERV": 12},
}

# Alias para mantener compatibilidad con la lógica existente
MAPEO_PORTFOLIOS = TABLA_PORTFOLIOS

# --- 2. DATA MAESTRA COMPLETA 2026 ---
# p_maestro identifica la semana (1, 2, 3 o 4)
DATA_MASTER = {
    "PRISMA (Visa/Amex)": [
        {"p_maestro": 1, "cierre": date(2026, 1, 8), "curr_e": date(2026, 1, 16), "next_c": date(2026, 2, 5), "prev_c": date(2025, 12, 11), "prev_e": date(2025, 12, 19), "next_e": date(2026, 2, 13)},
        {"p_maestro": 2, "cierre": date(2026, 1, 15), "curr_e": date(2026, 1, 23), "next_c": date(2026, 2, 12), "prev_c": date(2025, 12, 18), "prev_e": date(2025, 12, 26), "next_e": date(2026, 2, 20)},
        {"p_maestro": 3, "cierre": date(2026, 1, 22), "curr_e": date(2026, 2, 2), "next_c": date(2026, 2, 19), "prev_c": date(2025, 12, 24), "prev_e": date(2026, 1, 5), "next_e": date(2026, 3, 2)},
        {"p_maestro": 4, "cierre": date(2026, 1, 29), "curr_e": date(2026, 2, 6), "next_c": date(2026, 2, 26), "prev_c": date(2025, 12, 31), "prev_e": date(2026, 1, 9), "next_e": date(2026, 3, 6)},
        {"p_maestro": 1, "cierre": date(2026, 2, 5), "curr_e": date(2026, 2, 13), "next_c": date(2026, 3, 5), "prev_c": date(2026, 1, 8), "prev_e": date(2026, 1, 16), "next_e": date(2026, 3, 13)},
        {"p_maestro": 2, "cierre": date(2026, 2, 12), "curr_e": date(2026, 2, 20), "next_c": date(2026, 3, 12), "prev_c": date(2026, 1, 15), "prev_e": date(2026, 1, 23), "next_e": date(2026, 3, 20)},
        {"p_maestro": 3, "cierre": date(2026, 2, 19), "curr_e": date(2026, 3, 2), "next_c": date(2026, 3, 19), "prev_c": date(2026, 1, 22), "prev_e": date(2026, 2, 2), "next_e": date(2026, 4, 1)},
        {"p_maestro": 4, "cierre": date(2026, 2, 26), "curr_e": date(2026, 3, 6), "next_c": date(2026, 3, 26), "prev_c": date(2026, 1, 29), "prev_e": date(2026, 2, 6), "next_e": date(2026, 4, 6)},
        {"p_maestro": 1, "cierre": date(2026, 3, 5), "curr_e": date(2026, 3, 13), "next_c": date(2026, 4, 9), "prev_c": date(2026, 2, 5), "prev_e": date(2026, 2, 13), "next_e": date(2026, 4, 17)},
        {"p_maestro": 2, "cierre": date(2026, 3, 12), "curr_e": date(2026, 3, 20), "next_c": date(2026, 4, 16), "prev_c": date(2026, 2, 12), "prev_e": date(2026, 2, 20), "next_e": date(2026, 4, 24)},
        {"p_maestro": 3, "cierre": date(2026, 3, 19), "curr_e": date(2026, 4, 1), "next_c": date(2026, 4, 23), "prev_c": date(2026, 2, 19), "prev_e": date(2026, 3, 2), "next_e": date(2026, 5, 4)},
        {"p_maestro": 4, "cierre": date(2026, 3, 26), "curr_e": date(2026, 4, 6), "next_c": date(2026, 4, 30), "prev_c": date(2026, 2, 26), "prev_e": date(2026, 3, 6), "next_e": date(2026, 5, 8)},
        {"p_maestro": 1, "cierre": date(2026, 4, 9), "curr_e": date(2026, 4, 17), "next_c": date(2026, 5, 7), "prev_c": date(2026, 3, 5), "prev_e": date(2026, 3, 13), "next_e": date(2026, 5, 15)},
        {"p_maestro": 2, "cierre": date(2026, 4, 16), "curr_e": date(2026, 4, 24), "next_c": date(2026, 5, 14), "prev_c": date(2026, 3, 12), "prev_e": date(2026, 3, 20), "next_e": date(2026, 5, 22)},
        {"p_maestro": 3, "cierre": date(2026, 4, 23), "curr_e": date(2026, 5, 4), "next_c": date(2026, 5, 21), "prev_c": date(2026, 3, 19), "prev_e": date(2026, 4, 1), "next_e": date(2026, 6, 1)},
        {"p_maestro": 4, "cierre": date(2026, 4, 30), "curr_e": date(2026, 5, 8), "next_c": date(2026, 5, 28), "prev_c": date(2026, 3, 26), "prev_e": date(2026, 4, 6), "next_e": date(2026, 6, 5)},
        {"p_maestro": 1, "cierre": date(2026, 5, 7), "curr_e": date(2026, 5, 15), "next_c": date(2026, 6, 4), "prev_c": date(2026, 4, 9), "prev_e": date(2026, 4, 17), "next_e": date(2026, 6, 12)},
        {"p_maestro": 2, "cierre": date(2026, 5, 14), "curr_e": date(2026, 5, 22), "next_c": date(2026, 6, 11), "prev_c": date(2026, 4, 16), "prev_e": date(2026, 4, 24), "next_e": date(2026, 6, 19)},
        {"p_maestro": 3, "cierre": date(2026, 5, 21), "curr_e": date(2026, 6, 1), "next_c": date(2026, 6, 18), "prev_c": date(2026, 4, 23), "prev_e": date(2026, 5, 4), "next_e": date(2026, 7, 1)},
        {"p_maestro": 4, "cierre": date(2026, 5, 28), "curr_e": date(2026, 6, 5), "next_c": date(2026, 6, 25), "prev_c": date(2026, 4, 30), "prev_e": date(2026, 5, 8), "next_e": date(2026, 7, 3)},
        {"p_maestro": 1, "cierre": date(2026, 6, 4), "curr_e": date(2026, 6, 12), "next_c": date(2026, 7, 8), "prev_c": date(2026, 5, 7), "prev_e": date(2026, 5, 15), "next_e": date(2026, 7, 17)},
        {"p_maestro": 2, "cierre": date(2026, 6, 11), "curr_e": date(2026, 6, 19), "next_c": date(2026, 7, 16), "prev_c": date(2026, 5, 14), "prev_e": date(2026, 5, 22), "next_e": date(2026, 7, 24)},
        {"p_maestro": 3, "cierre": date(2026, 6, 18), "curr_e": date(2026, 7, 1), "next_c": date(2026, 7, 23), "prev_c": date(2026, 5, 21), "prev_e": date(2026, 6, 1), "next_e": date(2026, 8, 3)},
        {"p_maestro": 4, "cierre": date(2026, 6, 25), "curr_e": date(2026, 7, 3), "next_c": date(2026, 7, 30), "prev_c": date(2026, 5, 28), "prev_e": date(2026, 6, 5), "next_e": date(2026, 8, 7)},
        {"p_maestro": 1, "cierre": date(2026, 7, 8), "curr_e": date(2026, 7, 17), "next_c": date(2026, 8, 6), "prev_c": date(2026, 6, 4), "prev_e": date(2026, 6, 12), "next_e": date(2026, 8, 14)},
        {"p_maestro": 2, "cierre": date(2026, 7, 16), "curr_e": date(2026, 7, 24), "next_c": date(2026, 8, 13), "prev_c": date(2026, 6, 11), "prev_e": date(2026, 6, 19), "next_e": date(2026, 8, 21)},
        {"p_maestro": 3, "cierre": date(2026, 7, 23), "curr_e": date(2026, 8, 3), "next_c": date(2026, 8, 20), "prev_c": date(2026, 6, 18), "prev_e": date(2026, 7, 1), "next_e": date(2026, 9, 1)},
        {"p_maestro": 4, "cierre": date(2026, 7, 30), "curr_e": date(2026, 8, 7), "next_c": date(2026, 8, 27), "prev_c": date(2026, 6, 25), "prev_e": date(2026, 7, 3), "next_e": date(2026, 9, 4)},
        {"p_maestro": 1, "cierre": date(2026, 8, 6), "curr_e": date(2026, 8, 14), "next_c": date(2026, 9, 10), "prev_c": date(2026, 7, 8), "prev_e": date(2026, 7, 17), "next_e": date(2026, 9, 18)},
        {"p_maestro": 2, "cierre": date(2026, 8, 13), "curr_e": date(2026, 8, 21), "next_c": date(2026, 9, 17), "prev_c": date(2026, 7, 16), "prev_e": date(2026, 7, 24), "next_e": date(2026, 9, 25)},
        {"p_maestro": 3, "cierre": date(2026, 8, 20), "curr_e": date(2026, 9, 1), "next_c": date(2026, 9, 24), "prev_c": date(2026, 7, 23), "prev_e": date(2026, 8, 3), "next_e": date(2026, 10, 5)},
        {"p_maestro": 4, "cierre": date(2026, 8, 27), "curr_e": date(2026, 9, 4), "next_c": date(2026, 10, 1), "prev_c": date(2026, 7, 30), "prev_e": date(2026, 7, 3), "next_e": date(2026, 10, 9)},
        {"p_maestro": 1, "cierre": date(2026, 9, 10), "curr_e": date(2026, 9, 18), "next_c": date(2026, 10, 8), "prev_c": date(2026, 8, 6), "prev_e": date(2026, 8, 14), "next_e": date(2026, 10, 16)},
        {"p_maestro": 2, "cierre": date(2026, 9, 17), "curr_e": date(2026, 9, 25), "next_c": date(2026, 10, 15), "prev_c": date(2026, 8, 13), "prev_e": date(2026, 8, 21), "next_e": date(2026, 10, 23)},
        {"p_maestro": 3, "cierre": date(2026, 9, 24), "curr_e": date(2026, 10, 5), "next_c": date(2026, 10, 22), "prev_c": date(2026, 8, 20), "prev_e": date(2026, 9, 1), "next_e": date(2026, 11, 2)},
        {"p_maestro": 4, "cierre": date(2026, 10, 1), "curr_e": date(2026, 10, 9), "next_c": date(2026, 10, 29), "prev_c": date(2026, 8, 27), "prev_e": date(2026, 9, 4), "next_e": date(2026, 11, 9)},
        {"p_maestro": 1, "cierre": date(2026, 10, 8), "curr_e": date(2026, 10, 16), "next_c": date(2026, 11, 5), "prev_c": date(2026, 9, 10), "prev_e": date(2026, 9, 18), "next_e": date(2026, 11, 13)},
        {"p_maestro": 2, "cierre": date(2026, 10, 15), "curr_e": date(2026, 10, 23), "next_c": date(2026, 11, 12), "prev_c": date(2026, 9, 17), "prev_e": date(2026, 9, 25), "next_e": date(2026, 11, 23)},
        {"p_maestro": 3, "cierre": date(2026, 10, 22), "curr_e": date(2026, 11, 2), "next_c": date(2026, 11, 19), "prev_c": date(2026, 9, 24), "prev_e": date(2026, 10, 5), "next_e": date(2026, 12, 1)},
        {"p_maestro": 4, "cierre": date(2026, 10, 29), "curr_e": date(2026, 11, 9), "next_c": date(2026, 11, 26), "prev_c": date(2026, 10, 1), "prev_e": date(2026, 10, 9), "next_e": date(2026, 12, 4)},
        {"p_maestro": 1, "cierre": date(2026, 11, 5), "curr_e": date(2026, 11, 13), "next_c": date(2026, 12, 10), "prev_c": date(2026, 10, 8), "prev_e": date(2026, 10, 16), "next_e": date(2026, 12, 18)},
        {"p_maestro": 2, "cierre": date(2026, 11, 12), "curr_e": date(2026, 11, 23), "next_c": date(2026, 12, 17), "prev_c": date(2026, 10, 15), "prev_e": date(2026, 10, 23), "next_e": date(2026, 12, 28)},
        {"p_maestro": 3, "cierre": date(2026, 11, 19), "curr_e": date(2026, 12, 1), "next_c": date(2026, 12, 24), "prev_c": date(2026, 10, 22), "prev_e": date(2026, 11, 2), "next_e": date(2027, 1, 4)},
        {"p_maestro": 4, "cierre": date(2026, 11, 26), "curr_e": date(2026, 12, 4), "next_c": date(2026, 12, 31), "prev_c": date(2026, 10, 29), "prev_e": date(2026, 11, 9), "next_e": date(2027, 1, 8)},
        {"p_maestro": 1, "cierre": date(2026, 12, 10), "curr_e": date(2026, 12, 18), "next_c": date(2027, 1, 7), "prev_c": date(2026, 11, 5), "prev_e": date(2026, 11, 13), "next_e": date(2027, 1, 15)},
        {"p_maestro": 2, "cierre": date(2026, 12, 17), "curr_e": date(2026, 12, 28), "next_c": date(2027, 1, 14), "prev_c": date(2026, 11, 12), "prev_e": date(2026, 11, 23), "next_e": date(2027, 1, 22)},
        {"p_maestro": 3, "cierre": date(2026, 12, 24), "curr_e": date(2027, 1, 4), "next_c": date(2027, 1, 21), "prev_c": date(2026, 11, 19), "prev_e": date(2026, 12, 1), "next_e": date(2027, 2, 1)},
        {"p_maestro": 4, "cierre": date(2026, 12, 31), "curr_e": date(2027, 1, 8), "next_c": date(2027, 1, 28), "prev_c": date(2026, 11, 26), "prev_e": date(2026, 12, 4), "next_e": date(2027, 2, 5)},
    ],
    "FISERV (MasterCard)": [
        # Se agregan ejemplos para Master que usen el mismo sistema p_maestro
        {"p_maestro": 1, "cierre": date(2026, 1, 8), "curr_e": date(2026, 1, 16), "next_c": date(2026, 2, 5), "prev_c": date(2025, 12, 11), "prev_e": date(2025, 12, 19), "next_e": date(2026, 2, 13)},
        {"p_maestro": 3, "cierre": date(2026, 1, 22), "curr_e": date(2026, 2, 2), "next_c": date(2026, 2, 19), "prev_c": date(2025, 12, 24), "prev_e": date(2026, 1, 5), "next_e": date(2026, 3, 2)},
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

# TAB 1: TRAMITES
with tabs[0]:
    input_text = st.text_area("Mensaje del chat:", height=150)
    if st.button("Generar Trámites"):
        sql, mongo = generar_queries_tramites(input_text)
        if sql: st.code(sql, "sql")
        if mongo: st.code(mongo, "javascript")

# TAB 2: VARIOS (Aquí moví lo que estaba en la 3 por error)
with tabs[1]:
    st.subheader("🛠️ Updates de Cuenta y Branch")
    c1, c2 = st.columns(2)
    with c1:
        cc_br = st.text_input("Cuenta (CC):", key="br_cc")
        val_br = st.text_input("Nuevo Branch:", key="br_val")
        if st.button("Update Branch"):
            st.code(f"UPDATE CREDIT_ACCOUNTS SET BRANCH_OFFICE = {val_br} WHERE \"NUMBER\" = '{cc_br}';", "sql")
    with c2:
        cc_lim = st.text_input("CC para Límites:", key="lim_cc")
        if st.button("Ver Límites (SQL)"):
            st.code(f"SELECT ca.\"NUMBER\", cl.* FROM CREDIT_ACCOUNTS ca INNER JOIN CREDIT_LIMITS cl ON ca.LIMIT_ID = cl.ID WHERE ca.\"NUMBER\" = '{cc_lim}';", "sql")
    
    st.divider()
    st.subheader("💵 Dólar Manual")
    f_d, p_d, s_d = st.columns(3)
    f_rate = f_d.date_input("Fecha:")
    p_rate = p_d.text_input("Compra:", "1420")
    s_rate = s_d.text_input("Venta:", "1470")
    if st.button("Generar SQL Dólar"):
        st.code(f"UPDATE DOLLAR_EXCHANGE_RATES SET PURCHASE={p_rate}, SELLING={s_rate} WHERE DATE_RATE=TO_DATE('{f_rate}','YYYY-MM-DD');", "sql")

# TAB 3: ELIMINACIÓN (Recuperada)
with tabs[2]:
    st.subheader("⚠️ Limpieza de Datos (DELETE)")
    col_del1, col_del2 = st.columns(2)
    
    with col_del1:
        st.markdown("#### 💳 Débito (por DNI)")
        dni_del = st.text_input("DNI del Cliente:")
        if st.button("Limpiar Débito"):
            sql_del = f"""DELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni_del}');
DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni_del}');
DELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni_del}');
DELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni_del}');"""
            st.code(sql_del, "sql")

    with col_del2:
        st.markdown("#### 💳 Crédito (por Cifrado)")
        cif_del = st.text_area("Cifrados (separados por espacio):")
        if st.button("Limpiar Crédito"):
            cifrados = [f"'{c.strip()}'" for c in cif_del.split() if c.strip()]
            if cifrados:
                lista = ", ".join(cifrados)
                sql_cif = f"DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE \"NUMBER\" IN ({lista}));\nDELETE FROM CREDIT_CARDS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE \"NUMBER\" IN ({lista}));\nDELETE FROM CARDS WHERE \"NUMBER\" IN ({lista});"
                st.code(sql_cif, "sql")

# TAB 4: SETTLEMENT (Con la lógica de portafolios corregida)
with tabs[3]:
    st.subheader("📅 Generador de Settlement")
    marca = st.selectbox("Marca:", list(DATA_MASTER.keys()))
    acc_s = st.text_input("Número de Cuenta:", placeholder="429214619")
    
    cal_ref = DATA_MASTER[marca]
    c_selected = st.selectbox("Fecha de Cierre:", options=[f["cierre"] for f in cal_ref], format_func=lambda x: x.strftime("%d/%m/%Y"))
    reg = next(item for item in cal_ref if item["cierre"] == c_selected)
    
    # Montos
    m1, m2 = st.columns(2)
    base_p = m1.number_input("Monto Pesos:", value=0.0)
    base_d = m2.number_input("Monto Dólares:", value=0.0)

    if st.button("🚀 Generar SQL Full Settlement"):
        m_key = "PRISMA" if "PRISMA" in marca else "FISERV"
        sem_id = reg["p_maestro"]
        
        # IDs según tu regla
        id_proc = MAPEO_PORTFOLIOS[sem_id][m_key]
        id_maestro = MAPEO_PORTFOLIOS[sem_id]["MAESTRO"]
        
        sql_set = f"""-- 1. DÓLAR
DELETE FROM DOLLAR_EXCHANGE_RATES WHERE DATE_RATE = TO_DATE('{reg['curr_e']}','YYYY-MM-DD');
INSERT INTO DOLLAR_EXCHANGE_RATES (DATE_RATE, PURCHASE, SELLING, PROCESS_DATE) 
VALUES (TO_DATE('{reg['curr_e']}','YYYY-MM-DD'), 1420, 1470, CURRENT_TIMESTAMP);

-- 2. LIQUIDACIÓN (Usa ID Proc: {id_proc})
UPDATE RD_LIQUIDATIONS_USER_{m_key} 
SET CLOSING_DATE_LIQ=TO_DATE('{reg['prev_c']}','YYYY-MM-DD'), 
    LIQ_DATE=TO_DATE('{reg['cierre']}','YYYY-MM-DD'), 
    EXPIRATION_DATE=TO_DATE('{reg['curr_e']}','YYYY-MM-DD'), 
    PORTFOLIO={id_proc}, 
    LIQ_AUS_BALANCE={base_p}, 
    LAST_LIQ_USD_AMOUNT={base_d} 
WHERE ACCOUNT='{acc_s}';

-- 3. HEADER (Usa ID Proc: {id_proc})
UPDATE RD_SUMMARY_HEADER_{m_key} 
SET CLOSE_DATE_ID=TO_DATE('{reg['cierre']}','YYYY-MM-DD'), 
    NEXT_CLOSE_DATE=TO_DATE('{reg['next_c']}','YYYY-MM-DD'), 
    PORTFOLIO={id_proc} 
WHERE ACCOUNT_NUMBER_ID='{acc_s}';

-- 4. MAESTRO (Usa ID Maestro: {id_maestro})
UPDATE CREDIT_ACCOUNTS SET PORTFOLIO_TYPE_ID = {id_maestro} WHERE "NUMBER" = '{acc_s}';"""
        st.code(sql_set, "sql")
with tabs[4]:
    st.subheader("🚀 Generador de SQL: Settlement & Dólar")
    
    col1, col2 = st.columns(2)
    marca = col1.selectbox("Marca:", list(DATA_MASTER.keys()), key="set_marca")
    acc_s = col2.text_input("Número de Cuenta:", placeholder="429214619", key="set_acc")
    
    cal_ref = DATA_MASTER[marca]
    c_selected = st.selectbox("Fecha de Cierre:", 
                              options=[f["cierre"] for f in cal_ref], 
                              format_func=lambda x: x.strftime("%d/%m/%Y"),
                              key="set_close")
    
    # Buscamos los datos de la fecha seleccionada
    reg = next(item for item in cal_ref if item["cierre"] == c_selected)
    
    # Inputs de fechas (editables)
    f_c1, f_c2, f_c3 = st.columns(3)
    c_cl = f_c1.date_input("Cierre Actual", reg["cierre"])
    p_cl = f_c2.date_input("Cierre Anterior", reg["prev_c"])
    n_cl = f_c3.date_input("Próximo Cierre", reg["next_c"])
    
    f_e1, f_e2, f_e3 = st.columns(3)
    c_ex = f_e1.date_input("Vto Actual", reg["curr_e"])
    p_ex = f_e2.date_input("Vto Anterior", reg["prev_e"])
    n_ex = f_e3.date_input("Próximo Vto", reg["next_e"])
    
    st.divider()
    
    # Montos y Dólar
    st.subheader("💰 Datos de Deuda y Tipo de Cambio")
    m_col1, m_col2 = st.columns(2)
    base_p = m_col1.number_input("Monto Pesos (LIQ_AUS_BALANCE):", value=0.0)
    base_d = m_col2.number_input("Monto Dólares (LAST_LIQ_USD_AMOUNT):", value=0.0)
    
    d_col1, d_col2 = st.columns(2)
    buy_rate = d_col1.number_input("Dólar Compra:", value=1470.0)
    sell_rate = d_col2.number_input("Dólar Venta:", value=1420.0)

    if st.button("Generar Scripts SQL"):
        if not acc_s:
            st.warning("⚠️ Por favor ingresa una cuenta.")
        else:
            # Lógica de Portafolios
            marca_key = "PRISMA" if "PRISMA" in marca else "FISERV"
            semana_id = reg["p_maestro"]
            
            p_procesadora = TABLA_PORTFOLIOS[semana_id][marca_key]
            p_maestro = TABLA_PORTFOLIOS[semana_id]["MAESTRO"]
            desc_semana = TABLA_PORTFOLIOS[semana_id]["DESC"]
            
            sql_final = f"""-- COTIZACION DÓLAR PARA VENCIMIENTO {c_ex}
DELETE FROM DOLLAR_EXCHANGE_RATES WHERE DATE_RATE = TO_DATE('{c_ex}','YYYY-MM-DD');
INSERT INTO DOLLAR_EXCHANGE_RATES (DATE_RATE, PURCHASE, SELLING, PROCESS_DATE) 
VALUES (TO_DATE('{c_ex}','YYYY-MM-DD'), {buy_rate}, {sell_rate}, CURRENT_TIMESTAMP);

-- ACTUALIZACIÓN DE SETTLEMENT ({desc_semana})
-- Tabla Liquidaciones (Usa ID Procesadora: {p_procesadora})
UPDATE RD_LIQUIDATIONS_USER_{marca_key} 
SET CLOSING_DATE_LIQ=TO_DATE('{p_cl}','YYYY-MM-DD'), 
    LIQ_DATE=TO_DATE('{c_cl}','YYYY-MM-DD'), 
    EXPIRATION_DATE=TO_DATE('{c_ex}','YYYY-MM-DD'), 
    PORTFOLIO={p_procesadora}, 
    LIQ_AUS_BALANCE={base_p}, 
    LAST_LIQ_USD_AMOUNT={base_d} 
WHERE ACCOUNT='{acc_s}';

-- Tabla Resumen Cabecera (Usa ID Maestro: {p_maestro})
UPDATE RD_SUMMARY_HEADER_{marca_key} 
SET CLOSE_DATE_ID=TO_DATE('{c_cl}','YYYY-MM-DD'), 
    NEXT_CLOSE_DATE=TO_DATE('{n_cl}','YYYY-MM-DD'), 
    PORTFOLIO={p_maestro} 
WHERE ACCOUNT_NUMBER_ID='{acc_s}';

-- Tabla Maestro de Cuentas (Usa ID Maestro: {p_maestro})
UPDATE CREDIT_ACCOUNTS 
SET PORTFOLIO_TYPE_ID = {p_maestro} 
WHERE "NUMBER" = '{acc_s}';"""
            
            st.code(sql_final, "sql")
with tabs[5]:
    st.subheader("💰 Simulator: Calculadora de Deuda Dinámica")
    st.info("Configura la base y los movimientos para predecir el resultado de la API.")
    
    # --- CONFIGURACIÓN INICIAL ---
    col_acc1, col_acc2, col_acc3 = st.columns(3)
    marca_sim = col_acc1.selectbox("Marca Tarjeta:", ["PRISMA", "FISERV"], key="sim_marca")
    acc_sim = col_acc2.text_input("Número de Cuenta:", value="413864350", key="sim_acc")
    cotiz_v = col_acc3.number_input("Cotización Dólar Venta:", value=2150.0, step=1.0)

    st.divider()

    # --- COLUMNAS DE INPUTS ---
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("### 🏦 1. Valores Base (Settlement)")
        b_pesos = st.number_input("Deuda Pesos Base:", value=55000.0)
        b_dolar = st.number_input("Deuda Dólares Base:", value=34.0)
        
        if st.button("🚀 Generar SQL Update Base"):
            if marca_sim == "FISERV":
                sql_b = f"UPDATE RD_LIQUIDATIONS_FISERV SET ACTUAL_DOLAR_BALANCE = {b_dolar}, ARP_ACTUAL_BALANCE = {b_pesos} WHERE ACCOUNT_NUMBER = {acc_sim};"
            else:
                sql_b = f"UPDATE RD_LIQUIDATIONS_USER_PRISMA SET LAST_LIQ_USD_AMOUNT = {b_dolar}, LIQ_AUS_BALANCE = {b_pesos} WHERE ACCOUNT = {acc_sim};"
            st.code(sql_b, "sql")

    with col_der:
        st.markdown("### 💸 2. Movimiento & Fecha de Cierre")
        m_monto = st.number_input("Monto del Movimiento:", value=0.0)
        m_tipo = st.selectbox("Operación:", ["PAGO (Resta Deuda)", "CONSUMO (Suma Deuda)"])
        m_moneda = st.selectbox("Moneda:", ["ARS", "USD"])
        
        # AQUÍ ESTÁ EL CAMBIO: Se pide el Close Date para los Inserts
        f_cie_mov = st.date_input("Fecha Cierre Destino (Close Date):", value=date(2026, 3, 19))
        
        if st.button("🚀 Generar SQL Insert Movimiento"):
            ent_cod = "007" if marca_sim == "PRISMA" else "027"
            # Formateamos la fecha seleccionada para el SQL
            f_str = f_cie_mov.strftime('%d/%m/%Y')
            f_iso = f_cie_mov.strftime('%Y-%m-%d')
            
            if "PAGO" in m_tipo:
                sql_m = f"""-- INSERT PAGO CON CLOSE_DATE DINÁMICO
INSERT INTO PAYMENTS_OP_LIGHT (ID,ENTITY_CODE,FINANTIAL_ENTITY_CODE,CREDIT_ACCOUNT,BRANCH_OFFICE,TRANSACTION_DATE,OPERATION_DATE,EXTERNAL_PAYMENT_CODE,AMOUNT1,CURRENCY,PORTFOLIO,CLOSE_DATE,CANAL,ORIGIN_TRANSACTION,CREATE_DATE,OPERATION_ID)
VALUES((SELECT MAX(ID) +1 FROM PAYMENTS_OP_LIGHT),'{ent_cod}','{ent_cod}','{acc_sim}','040',to_date('{f_str}','DD/MM/RRRR'),to_date('{f_str}','DD/MM/RRRR'),'2500','{m_monto}','{m_moneda}','1',to_date('{f_str}','DD/MM/RRRR'),null,'{marca_sim}',to_timestamp('{f_str}','DD/MM/RRRR'),SYS_GUID());"""
            else:
                sql_m = f"""-- INSERT CONSUMO CON CLOSE_DATE DINÁMICO
INSERT INTO PURCHASE_TC_OP_LIGHT (CARD_NUMBER, PURCHASE_DATE, MERCHANT_NAME, AMOUNT, CURRENCY, CLOSE_DATE, ORIGIN_TRANSACTION, ACCOUNT_NUMBER, PROCESS_DATE) 
VALUES ('000000', CURRENT_DATE, 'MOVIMIENTO QA COTA', {m_monto}, '{m_moneda}', to_date('{f_str}','DD/MM/RRRR'), '{marca_sim}', '{acc_sim}', CURRENT_TIMESTAMP);"""
            st.code(sql_m, "sql")

    st.divider()

    # --- LÓGICA DE CÁLCULO ---
    factor = -1 if "PAGO" in m_tipo else 1
    final_p = b_pesos + (m_monto if m_moneda == "ARS" else 0) * factor
    final_d = b_dolar + (m_monto if m_moneda == "USD" else 0) * factor
    total_pesificado = final_p + (final_d * cotiz_v)

    # --- RESULTADOS FINALES ---
    st.markdown("### 🎯 Resultado Esperado en API (Actual Debt)")
    
    res_p1, res_p2 = st.columns(2)
    res_p1.metric("DEUDA PESOS BASE", f"{b_pesos:,.2f} ARS")
    res_p2.metric("DEUDA PESOS FINAL (pesos_debt)", f"{final_p:,.2f} ARS", delta=f"{(final_p - b_pesos):,.2f}")

    res_d1, res_d2 = st.columns(2)
    res_d1.metric("DEUDA DÓLARES BASE", f"{b_dolar:,.2f} USD")
    res_d2.metric("DEUDA DÓLARES FINAL (dollar_debt)", f"{final_d:,.2f} USD", delta=f"{(final_d - b_dolar):,.2f}")

    st.divider()
    
    final_a, final_b = st.columns(2)
    with final_a:
        st.subheader("TOTAL DEUDA PESOS")
        st.title(f"{total_pesificado:,.2f} ARS")
        st.caption(f"Cálculo: {final_p:,.2f} + ({final_d:,.2f} USD * {cotiz_v})")
        
    with final_b:
        st.subheader("TOTAL DEUDA DÓLARES")
        st.title(f"{final_d:,.2f} USD")

    # Botón para la cotización
    if st.button("💵 Generar Rate Dólar (Para esta Expiration)"):
        f_exp = f_cie_mov.strftime('%Y-%m-%d')
        sql_rate = f"""DELETE FROM DOLLAR_EXCHANGE_RATES WHERE DATE_RATE = TO_DATE('{f_exp}','YYYY-MM-DD');
INSERT INTO DOLLAR_EXCHANGE_RATES (DATE_RATE, PURCHASE, SELLING, PROCESS_DATE) VALUES (TO_DATE('{f_exp}','YYYY-MM-DD'), {cotiz_v - 50}, {cotiz_v}, CURRENT_TIMESTAMP);"""
        st.code(sql_rate, "sql")

with tabs[6]:
    st.subheader("📋 Protocolo de Mensaje")
    st.code("""SOLICITUD DE DEUDA QA
- CUENTA: [Nro]
- MARCA: [VISA/AMEX/MASTER]
- TIPO: [PAGO/CONSUMO]
- MONTO: [Valor]
- MONEDA: [ARS/USD]
- CIERRE: [Fecha]""", language="text")
