import streamlit as st
import re

# 1. Configuración de la página
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# 2. Diccionarios y lógica
MAPEO_ESTADOS = {
    "ACTIVA": 1, "INACTIVA": 2, "BAJA": 3, "NO INFORMADO": 4,
    "SUSPENDIDO": 5, "RESTRINGIDA": 6, "PAUSADA": 7, "INHABILITADA": 8
}

def generar_queries_tramites(texto):
    tipo = re.search(r"TIPO:\s*(TC|TD)", texto, re.I)
    tarjeta = re.search(r"TARJETA:\s*(\d{15,16})", texto, re.I)
    dni = re.search(r"DNI:\s*(\d+)", texto, re.I)
    cc = re.search(r"CC:\s*(\d+)", texto, re.I)
    accion = re.search(r"ACCION:\s*(.*)", texto, re.I)

    if not (tipo and tarjeta and dni and accion):
        return None, None

    t_tipo, t_num, t_dni = tipo.group(1).upper(), tarjeta.group(1), dni.group(1)
    t_bin, t_last4 = t_num[:6], t_num[-4:]
    t_cc = cc.group(1) if cc else None
    t_acc = accion.group(1).upper()

    if t_tipo == "TD":
        joins = "INNER JOIN DEBIT_CARDS DC ON C.ID = DC.CUSTOMER_ID INNER JOIN CARDS T ON DC.CARD_ID = T.ID"
    else:
        joins = "INNER JOIN CREDIT_ACCOUNTS CA ON C.ID = CA.CUSTOMER_ID INNER JOIN CREDIT_CARDS CC ON CA.ID = CC.ACCOUNT_ID INNER JOIN CARDS T ON CC.CARD_ID = T.ID"

    where_sql = f"WHERE C.DOCUMENT = '{t_dni}' AND T.BIN = '{t_bin}' AND T.LAST_DIGITS = '{t_last4}'"
    sql_final = ""

    for nombre, id_estado in MAPEO_ESTADOS.items():
        if nombre in t_acc:
            sql_final += f"-- CAMBIAR ESTADO A {nombre}\nUPDATE CARDS_STATUS SET STATUS_ID = {id_estado}, UPDATED_AT = CURRENT_TIMESTAMP WHERE CARD_ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n\n"
    
    if "VIRTUAL" in t_acc or "FALSE" in t_acc:
        sql_final += f"-- DEJAR COMO VIRTUAL\nUPDATE CARDS SET PRINTED = 0 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    elif "FISICA" in t_acc or "TRUE" in t_acc:
        sql_final += f"-- DEJAR COMO FISICA\nUPDATE CARDS SET PRINTED = 1 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"

    mongo_final = ""
    if "LIMPIAR_MONGO" in t_acc or "AULITRAN" in t_acc:
        if t_cc:
            mongo_final = f"// LIMPIAR AULITRAN\ndb.temporary_limit_detail.deleteMany({{ \"document_number\": \"{t_dni}\", \"account_number\": \"{t_cc}\" }});"
        else:
            mongo_final = "// ⚠️ No se puede generar Mongo: Falta el número de cuenta (CC)."

    return sql_final if sql_final else None, mongo_final if mongo_final else None

def generar_delete_debit(dni):
    return f"""-- 1. Borrar asociaciones de cuentas de débito\nDELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\n\n-- 2. Borrar estados de la tarjeta\nDELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\n\n-- 3. Borrar registros en DEBIT_CARDS\nDELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\n\n-- 4. Borrar registro base en CARDS\nDELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\n\n-- 5. Verificación\nSELECT * FROM CUSTOMERS WHERE DOCUMENT = '{dni}';"""

# --- 3. INTERFAZ ---
st.title("🚀 QA Automation Tool COTA")

tab1, tab2, tab3 = st.tabs(["📝 Trámites Diarios", "🔧 Varios & Settlement", "⚠️ Eliminación"])

with tab1:
    input_text = st.text_area("Mensaje del Chat:", height=150)
    if st.button("Generar Queries de Trámite"):
        sql, mongo = generar_queries_tramites(input_text)
        if sql: st.code(sql, language="sql")
        if mongo: st.code(mongo, language="javascript")

with tab2:
    # FILA 1: BRANCH Y LÍMITES
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏦 Branch Office")
        c1, c2 = st.columns(2)
        cc_br = c1.text_input("Cuenta (CC):", key="br_cc")
        val_br = c2.text_input("Nuevo Branch:", key="br_val")
        if st.button("Generar Update Branch"):
            st.code(f"UPDATE CREDIT_ACCOUNTS SET BRANCH_OFFICE = {val_br} WHERE \"NUMBER\" = {cc_br};", language="sql")

    with col2:
        st.subheader("📊 Consulta Límites")
        cc_lim = st.text_input("CC para ver Límites:", key="lim_cc")
        if st.button("Generar JOIN Límites"):
            st.code(f"SELECT ca.\"NUMBER\", cl.* FROM CREDIT_ACCOUNTS ca INNER JOIN CREDIT_LIMITS cl ON ca.LIMIT_ID = cl.ID WHERE ca.\"NUMBER\" = {cc_lim};", language="sql")

    st.divider()

    # FILA 2: EXCHANGE RATE (DÓLAR)
    st.subheader("💵 Dollar Exchange Rates")
    st.info("Si la fecha no existe, usa el INSERT. Si ya existe, usa el UPDATE.")
    c_f, c_p, c_s = st.columns(3)
    f_rate = c_f.date_input("Fecha del Rate:")
    p_rate = c_p.text_input("Purchase Price:", value="200")
    s_rate = c_s.text_input("Selling Price:", value="1200")
    
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Generar UPDATE Dólar"):
        st.code(f"UPDATE DOLLAR_EXCHANGE_RATES SET PURCHASE = {p_rate}, SELLING = {s_rate} WHERE DATE_RATE = TO_DATE('{f_rate}', 'YYYY-MM-DD');", language="sql")
    if col_btn2.button("Generar INSERT Dólar (Si es nuevo)"):
        st.code(f"INSERT INTO DOLLAR_EXCHANGE_RATES (ID, DATE_RATE, PURCHASE, SELLING, CREATED_AT) VALUES (NEXTVAL('DOLLAR_EXCHANGE_RATES_ID_SEQ'), TO_DATE('{f_rate}', 'YYYY-MM-DD'), {p_rate}, {s_rate}, CURRENT_TIMESTAMP);", language="sql")

    st.divider()

    # FILA 3: SETTLEMENT / LIQUIDACIONES
    st.subheader("💳 Liquidaciones (Settlement)")
    cc_liq = st.text_input("Número de Cuenta para Liquidación:", key="liq_cc")
    m_usd = st.text_input("Monto USD (Dólares):", value="0", key="liq_usd")
    m_ars = st.text_input("Monto ARS (Pesos):", value="0", key="liq_ars")
    
    col_v, col_m = st.columns(2)
    if col_v.button("Update PRISMA (Visa/Amex)"):
        st.code(f"UPDATE RD_LIQUIDATIONS_USER_PRISMA SET LAST_LIQ_USD_AMOUNT = {m_usd}, LIQ_AUS_BALANCE = {m_ars} WHERE ACCOUNT IN ({cc_liq});", language="sql")
    if col_m.button("Update FISERV (Mastercard)"):
        st.code(f"UPDATE RD_LIQUIDATIONS_FISERV SET ACTUAL_DOLAR_BALANCE = {m_usd}, ARP_ACTUAL_BALANCE = {m_ars} WHERE ACCOUNT_NUMBER = {cc_liq};", language="sql")

with tab3:
    dni_input = st.text_input("DNI para borrar Débito:")
    if st.button("Generar DELETE"):
        st.code(generar_delete_debit(dni_input), language="sql")