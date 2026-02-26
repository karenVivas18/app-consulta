import streamlit as st
import re

# 1. Configuración de la página
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀", layout="wide")

# 2. Diccionarios de mapeo
MAPEO_ESTADOS = {
    "ACTIVA": 1, 
    "INACTIVA": 2, 
    "BAJA": 3, 
    "NO INFORMADO": 4,
    "SUSPENDIDO": 5, 
    "RESTRINGIDA": 6, 
    "PAUSADA": 7, 
    "INHABILITADA": 8
}

# 3. Funciones de Lógica
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
    return f"""-- DELETE DÉBITO COMPLETO\nDELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nDELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nDELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nDELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');\nSELECT * FROM CUSTOMERS WHERE DOCUMENT = '{dni}';"""

def generar_delete_credit_por_cifrado(cifrados_str):
    lineas = cifrados_str.replace("'", "").replace(",", " ").split()
    cifrados = [c.strip() for c in lineas if c.strip()]
    if not cifrados: return "-- ⚠️ Ingresa cifrados válidos."
    lista_sql = ", ".join([f"'{c}'" for c in cifrados])
    return f"""-- DELETE TC POR CIFRADO\nDELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE "NUMBER" IN ({lista_sql}));\nDELETE FROM CREDIT_CARDS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE "NUMBER" IN ({lista_sql}));\nDELETE FROM CARDS WHERE "NUMBER" IN ({lista_sql});\nSELECT * FROM CARDS WHERE "NUMBER" IN ({lista_sql});"""

# --- 4. INTERFAZ ---
st.title("🚀 QA Automation Tool COTA")

tab1, tab2, tab3 = st.tabs(["📝 Trámites Diarios", "🔧 Varios & Settlement", "⚠️ Eliminación"])

with tab1:
    st.markdown("### Generador de Trámites Rápidos")
    input_text = st.text_area("Pegue el mensaje del chat aquí:", height=150)
    if st.button("Generar Queries de Trámite"):
        sql, mongo = generar_queries_tramites(input_text)
        if sql: st.code(sql, language="sql")
        if mongo: st.code(mongo, language="javascript")

with tab2:
    # --- SECCIÓN: DATOS DEL CLIENTE ---
    st.subheader("👤 Datos del Cliente")
    col_n, col_a, col_d, col_g = st.columns(4)
    c_name = col_n.text_input("Nombre:", key="cust_name")
    c_surname = col_a.text_input("Apellido:", key="cust_surname")
    c_dni = col_d.text_input("DNI:", key="cust_dni")
    c_gender = col_g.selectbox("Género:", ["M", "F", "X"], key="cust_gen")
    if st.button("Generar Update Cliente"):
        if c_name and c_surname and c_dni:
            st.code(f"UPDATE CUSTOMERS SET NAME = '{c_name.upper()}', SURNAME = '{c_surname.upper()}' WHERE DOCUMENT = '{c_dni}' AND GENDER = '{c_gender}';", language="sql")

    st.divider()

    # --- SECCIÓN: ESTADO DE CUENTA ---
    st.subheader("💳 Estado de Cuenta (ACCOUNTS_STATUS)")
    col_acc_1, col_acc_2 = st.columns(2)
    acc_num = col_acc_1.text_input("Número de Cuenta (CC):", key="acc_num_val")
    acc_status = col_acc_2.selectbox("Estado Deseado:", list(MAPEO_ESTADOS.keys()), key="acc_state_val")
    if st.button("Generar Update Estado Cuenta"):
        if acc_num:
            id_st = MAPEO_ESTADOS[acc_status]
            st.code(f"-- CAMBIO A {acc_status}\nUPDATE ACCOUNTS_STATUS SET STATUS_ID = {id_st}, UPDATED_AT = CURRENT_TIMESTAMP WHERE ACCOUNT_ID = (SELECT ID FROM CREDIT_ACCOUNTS WHERE \"NUMBER\" = '{acc_num}');", language="sql")

    st.divider()

    # --- SECCIÓN: BRANCH Y LÍMITES ---
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.subheader("🏦 Branch Office")
        cc_br = st.text_input("CC para Branch:", key="br_cc")
        val_br = st.text_input("Nuevo valor Branch:", key="br_val")
        if st.button("Generar Update Branch"):
            st.code(f"UPDATE CREDIT_ACCOUNTS SET BRANCH_OFFICE = {val_br} WHERE \"NUMBER\" = '{cc_br}';", language="sql")
    with col_b2:
        st.subheader("📊 Consulta Límites")
        cc_lim = st.text_input("CC para Límites:", key="lim_cc")
        if st.button("Generar JOIN Límites"):
            st.code(f"SELECT ca.\"NUMBER\", cl.* FROM CREDIT_ACCOUNTS ca INNER JOIN CREDIT_LIMITS cl ON ca.LIMIT_ID = cl.ID WHERE ca.\"NUMBER\" = '{cc_lim}';", language="sql")

    st.divider()

    # --- SECCIÓN: DÓLAR ---
    st.subheader("💵 Dollar Exchange Rates")
    c_f, c_p, c_s = st.columns(3)
    f_rate = c_f.date_input("Fecha Rate:")
    p_rate = c_p.text_input("Purchase Price:", value="200")
    s_rate = c_s.text_input("Selling Price:", value="1200")
    col_d1, col_d2 = st.columns(2)
    if col_d1.button("Generar UPDATE Dólar"):
        st.code(f"UPDATE DOLLAR_EXCHANGE_RATES SET PURCHASE = {p_rate}, SELLING = {s_rate} WHERE DATE_RATE = TO_DATE('{f_rate}', 'YYYY-MM-DD');", language="sql")
    if col_d2.button("Generar INSERT Dólar"):
        st.code(f"INSERT INTO DOLLAR_EXCHANGE_RATES (ID, DATE_RATE, PURCHASE, SELLING, CREATED_AT) VALUES (NEXTVAL('DOLLAR_EXCHANGE_RATES_ID_SEQ'), TO_DATE('{f_rate}', 'YYYY-MM-DD'), {p_rate}, {s_rate}, CURRENT_TIMESTAMP);", language="sql")

    st.divider()

    # --- SECCIÓN: SETTLEMENT ---
    st.subheader("💳 Liquidaciones (Settlement)")
    cc_liq = st.text_input("Cuenta para Liquidación:", key="liq_cc")
    m_usd = st.text_input("Monto USD:", value="0")
    m_ars = st.text_input("Monto ARS:", value="0")
    btn_p, btn_f = st.columns(2)
    if btn_p.button("Update PRISMA (Visa/Amex)"):
        st.code(f"UPDATE RD_LIQUIDATIONS_USER_PRISMA SET LAST_LIQ_USD_AMOUNT = {m_usd}, LIQ_AUS_BALANCE = {m_ars} WHERE ACCOUNT IN ({cc_liq});", language="sql")
    if btn_f.button("Update FISERV (Master)"):
        st.code(f"UPDATE RD_LIQUIDATIONS_FISERV SET ACTUAL_DOLAR_BALANCE = {m_usd}, ARP_ACTUAL_BALANCE = {m_ars} WHERE ACCOUNT_NUMBER = {cc_liq};", language="sql")

with tab3:
    st.error("⚠️ ZONA DE ELIMINACIÓN PERMANENTE")
    col_del_1, col_del_2 = st.columns(2)
    with col_del_1:
        st.subheader("❌ Débito (DNI)")
        dni_del = st.text_input("DNI del cliente:", key="del_dni")
        if st.button("Generar Delete Débito"):
            st.code(generar_delete_debit(dni_del), language="sql")
    with col_del_2:
        st.subheader("❌ Crédito (Cifrados)")
        cif_del = st.text_area("Pegue números cifrados:", height=100)
        if st.button("Generar Delete Crédito"):
            st.code(generar_delete_credit_por_cifrado(cif_del), language="sql")