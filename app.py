import streamlit as st
import re

# 1. Configuración de la página
st.set_page_config(page_title="QA Automation Tool COTA", page_icon="🚀")

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
        sql_final += f"-- DEJAR COMO VIRTUAL\nUPDATE CARDS SET PRINTED = 0 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});"
    elif "FISICA" in t_acc or "TRUE" in t_acc:
        sql_final += f"-- DEJAR COMO FISICA\nUPDATE CARDS SET PRINTED = 1 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});"

    mongo_final = ""
    if "LIMPIAR_MONGO" in t_acc or "AULITRAN" in t_acc:
        if t_cc:
            mongo_final = f"// LIMPIAR AULITRAN\ndb.temporary_limit_detail.deleteMany({{ \"document_number\": \"{t_dni}\", \"account_number\": \"{t_cc}\" }});"
        else:
            mongo_final = "// ⚠️ No se puede generar Mongo: Falta el número de cuenta (CC)."

    return sql_final if sql_final else None, mongo_final if mongo_final else None

def generar_delete_debit(dni):
    return f"""-- 1. Borrar asociaciones de cuentas de débito
DELETE FROM DEBIT_CARDS_ACCOUNTS 
WHERE DEBIT_CARD_ID IN (
    SELECT dc.id FROM DEBIT_CARDS dc
    JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID
    WHERE cu.DOCUMENT = '{dni}'
);

-- 2. Borrar estados de la tarjeta
DELETE FROM CARDS_STATUS 
WHERE CARD_ID IN (
    SELECT ca.id FROM CARDS ca
    JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id
    JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID
    WHERE cu.DOCUMENT = '{dni}'
);

-- 3. Borrar registros en DEBIT_CARDS
DELETE FROM DEBIT_CARDS
WHERE id IN (
    SELECT dc.id FROM DEBIT_CARDS dc
    JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID
    WHERE cu.DOCUMENT = '{dni}'
);

-- 4. Borrar registro base en CARDS
DELETE FROM CARDS
WHERE id IN (
    SELECT ca.id FROM CARDS ca
    JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id
    JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID
    WHERE cu.DOCUMENT = '{dni}'
);

-- 5. Consulta de verificación del cliente
SELECT * FROM CUSTOMERS WHERE DOCUMENT = '{dni}';"""

# --- 3. INTERFAZ CON PESTAÑAS ---
st.title("🚀 QA Automation Tool COTA")

tab1, tab2, tab3 = st.tabs(["📝 Trámites Diarios", "🔧 Varios", "⚠️ Eliminación (Delicado)"])
with tab1:
    st.markdown("Genera updates de estado, virtualidad y MongoDB.")
    input_text = st.text_area("Mensaje del Chat:", height=150, key="tramites")
    if st.button("Generar Queries de Trámite"):
        sql, mongo = generar_queries_tramites(input_text)
        if sql: st.code(sql, language="sql")
        if mongo: 
            st.markdown("**MongoDB (Shell):**")
            st.code(mongo, language="javascript")

with tab2:
    st.subheader("🛠️ Consultas y Updates Rápidos")
    
    # SECCIÓN BRANCH OFFICE
    st.markdown("### 1. Cambio de Branch Office")
    cc_branch = st.text_input("Número de Cuenta (CC):", placeholder="Ej: 123456", key="cc_branch")
    if st.button("Generar Query Branch"):
        if cc_branch:
            st.code(f"UPDATE CREDIT_ACCOUNTS SET BRANCH_OFFICE = 1 WHERE \"NUMBER\" = {cc_branch};", language="sql")
    
    st.divider()

    # SECCIÓN LÍMITES CON JOIN
    st.markdown("### 2. Consulta de Límites (JOIN)")
    st.info("Busca directamente en CREDIT_ACCOUNTS y CREDIT_LIMITS.")
    cc_join = st.text_input("Ingrese CC para Límites:", placeholder="Ej: 999888", key="cc_join")
    
    if st.button("Generar Query de Límites"):
        if cc_join:
            query_join = f"""-- CONSULTAR LÍMITES POR CUENTA (JOIN)
SELECT 
    ca."NUMBER" AS Cuenta, 
    ca.LIMIT_ID, 
    cl.*
FROM CREDIT_ACCOUNTS ca
INNER JOIN CREDIT_LIMITS cl ON ca.LIMIT_ID = cl.ID
WHERE ca."NUMBER" = {cc_join};"""
            st.code(query_join, language="sql")
        else:
            st.warning("Por favor ingrese un número de cuenta.")

with tab3:
    st.error("¡CUIDADO! Operaciones DELETE permanentes para Tarjetas de Débito.")
    dni_input = st.text_input("Ingrese el DNI del cliente:", key="dni_delete")
    if st.button("Generar Bloque de Eliminación"):
        if dni_input:
            st.code(generar_delete_debit(dni_input), language="sql")