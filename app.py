import streamlit as st
import re
from datetime import datetime

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

    joins = "INNER JOIN DEBIT_CARDS DC ON C.ID = DC.CUSTOMER_ID INNER JOIN CARDS T ON DC.CARD_ID = T.ID" if t_tipo == "TD" else \
            "INNER JOIN CREDIT_ACCOUNTS CA ON C.ID = CA.CUSTOMER_ID INNER JOIN CREDIT_CARDS CC ON CA.ID = CC.ACCOUNT_ID INNER JOIN CARDS T ON CC.CARD_ID = T.ID"

    where_sql = f"WHERE C.DOCUMENT = '{t_dni}' AND T.BIN = '{t_bin}' AND T.LAST_DIGITS = '{t_last4}'"
    sql_final = ""

    for nombre, id_estado in MAPEO_ESTADOS.items():
        if nombre in t_acc:
            sql_final += f"-- CAMBIAR ESTADO A {nombre}\nUPDATE CARDS_STATUS SET STATUS_ID = {id_estado}, UPDATED_AT = CURRENT_TIMESTAMP WHERE CARD_ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n\n"
    
    if any(x in t_acc for x in ["VIRTUAL", "FALSE"]):
        sql_final += f"-- DEJAR COMO VIRTUAL\nUPDATE CARDS SET PRINTED = 0 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"
    elif any(x in t_acc for x in ["FISICA", "TRUE"]):
        sql_final += f"-- DEJAR COMO FISICA\nUPDATE CARDS SET PRINTED = 1 WHERE ID IN (SELECT T.ID FROM CUSTOMERS C {joins} {where_sql});\n"

    mongo_final = f"db.temporary_limit_detail.deleteMany({{ \"document_number\": \"{t_dni}\", \"account_number\": \"{t_cc}\" }});" if t_cc and ("LIMPIAR_MONGO" in t_acc or "AULITRAN" in t_acc) else ""
    return sql_final if sql_final else None, mongo_final

def generar_delete_debit(dni):
    return f"""-- DELETE DÉBITO COMPLETO (DNI: {dni})
DELETE FROM DEBIT_CARDS_ACCOUNTS WHERE DEBIT_CARD_ID IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM DEBIT_CARDS WHERE id IN (SELECT dc.id FROM DEBIT_CARDS dc JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');
DELETE FROM CARDS WHERE id IN (SELECT ca.id FROM CARDS ca JOIN DEBIT_CARDS dc ON dc.CARD_ID = ca.id JOIN CUSTOMERS cu ON cu.id = dc.CUSTOMER_ID WHERE cu.DOCUMENT = '{dni}');"""

def generar_delete_credit_por_cifrado(cifrados_str):
    lineas = cifrados_str.replace("'", "").replace(",", " ").split()
    cifrados = [c.strip() for c in lineas if c.strip()]
    if not cifrados: return "-- ⚠️ Ingresa cifrados válidos."
    lista_sql = ", ".join([f"'{c}'" for c in cifrados])
    return f"""-- DELETE TC POR CIFRADO
DELETE FROM CARDS_STATUS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE "NUMBER" IN ({lista_sql}));
DELETE FROM CREDIT_CARDS WHERE CARD_ID IN (SELECT ID FROM CARDS WHERE "NUMBER" IN ({lista_sql}));
DELETE FROM CARDS WHERE "NUMBER" IN ({lista_sql});"""

def procesar_dump_accounts(texto):
    registros = re.findall(r"VALUES\s*\((.*?)\)\s*;", texto, re.I)
    queries = []
    for reg in registros:
        valores = [v.strip().strip("'") for v in reg.split(",")]
        try:
            queries.append(f"INSERT INTO M_DUMP_DEBIT_ACCOUNTS (MDUMP_ID, ACCOUNT_TYPE, ACCOUNT_NUMBER, ACCOUNT_STATUS, ACCOUNT_PREFERRED, ACCOUNT_PRIMARY) VALUES ({valores[0]}, '1', '{valores[16]}', '1', '0', '1');")
        except IndexError: continue
    return "\n".join(queries)

# --- 4. INTERFAZ ---
st.title("🚀 QA Automation Tool COTA")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Trámites", "🔧 Varios", "⚠️ Eliminación", "📦 Dump Masivo", "📅 Settlement & Taxes"])

with tab1:
    input_text = st.text_area("Pegue el mensaje del chat aquí:", height=150)
    if st.button("Generar Queries"):
        sql, mongo = generar_queries_tramites(input_text)
        if sql: st.code(sql, language="sql")
        if mongo: st.code(mongo, language="javascript")

with tab2:
    st.subheader("👤 Cliente & Cuenta")
    col_c1, col_c2, col_c3 = st.columns(3)
    c_nom = col_c1.text_input("Nombre:")
    c_ape = col_c2.text_input("Apellido:")
    c_dni = col_c3.text_input("DNI:")
    if st.button("Update Cliente"):
        st.code(f"UPDATE CUSTOMERS SET NAME='{c_nom.upper()}', SURNAME='{c_ape.upper()}' WHERE DOCUMENT='{c_dni}';", language="sql")
    
    st.divider()
    st.subheader("💳 Estado de Cuenta (ACCOUNTS_STATUS)")
    col_a1, col_a2 = st.columns(2)
    acc_n = col_a1.text_input("Número de Cuenta:")
    acc_s = col_a2.selectbox("Nuevo Estado:", list(MAPEO_ESTADOS.keys()))
    if st.button("Actualizar Cuenta"):
        st.code(f"UPDATE ACCOUNTS_STATUS SET STATUS_ID={MAPEO_ESTADOS[acc_s]}, UPDATED_AT=CURRENT_TIMESTAMP WHERE ACCOUNT_ID=(SELECT ID FROM CREDIT_ACCOUNTS WHERE \"NUMBER\"='{acc_n}');", language="sql")

with tab3:
    st.error("⚠️ ELIMINACIONES PERMANENTES")
    c1, c2 = st.columns(2)
    with c1:
        d_dni = st.text_input("DNI Débito:")
        if st.button("Generar Delete DNI"): st.code(generar_delete_debit(d_dni), language="sql")
    with c2:
        d_cif = st.text_area("Cifrados Crédito:")
        if st.button("Generar Delete CIF"): st.code(generar_delete_credit_por_cifrado(d_cif), language="sql")

with tab4:
    st.subheader("📦 Dump de Cuentas")
    dump_in = st.text_area("Pegue INSERTS de M_DUMP_DEBIT_CARD:", height=200)
    if st.button("Procesar Dump"): st.code(procesar_dump_accounts(dump_in), language="sql")

with tab5:
    st.subheader("📅 Liquidación & Impuestos OP")
    c_s1, c_s2, c_s3 = st.columns(3)
    acc_s = c_s1.text_input("Cuenta (10 dígitos):", placeholder="3142959686")
    port_s = c_s2.number_input("Portfolio:", 1, 9, 2)
    bran_s = c_s3.text_input("Branch:", "79")
    
    f1, f2, f3 = st.columns(3)
    c_cl = f1.date_input("Current Closing (ID)")
    p_cl = f2.date_input("Previous Closing")
    n_cl = f3.date_input("Next Closing")
    
    f4, f5, f6 = st.columns(3)
    c_ex = f4.date_input("Current Expiration")
    p_ex = f5.date_input("Previous Expiration")
    n_ex = f6.date_input("Next Expiration")

    st.divider()
    st_tax = st.toggle("¿Incluir Impuestos (RD_TAX_COMMISSION_DETAIL_OP)?")
    if st_tax:
        t1, t2, t3 = st.columns(3)
        t_cod = t1.text_input("Tax Code:", "2015")
        t_des = t2.text_input("Descripción:", "VISA ADIC - SIN FECHA 2")
        t_amt = t3.text_input("Monto:", "0")

    if st.button("🚀 Generar Bloque Settlement"):
        if acc_s:
            p_acc, v_dig = acc_s[:9], acc_s[-1]
            res = f"""-- UPDATE PRISMA
UPDATE RD_LIQUIDATIONS_USER_PRISMA SET CLOSING_DATE_LIQ=TO_DATE('{p_cl}','YYYY-MM-DD'), EXPIRATION_DATE_PREV=TO_DATE('{p_ex}','YYYY-MM-DD'), LIQ_DATE=TO_DATE('{c_cl}','YYYY-MM-DD'), EXPIRATION_DATE=TO_DATE('{c_ex}','YYYY-MM-DD'), PORTFOLIO={port_s+1} WHERE ACCOUNT={acc_s};
UPDATE RD_SUMMARY_HEADER_PRISMA SET CLOSE_DATE_ID=TO_DATE('{c_cl}','YYYY-MM-DD'), NEXT_CLOSE_DATE=TO_DATE('{n_cl}','YYYY-MM-DD'), NEXT_EXPIRATION_DATE=TO_DATE('{n_ex}','YYYY-MM-DD'), PORTFOLIO={port_s} WHERE ACCOUNT_NUMBER_ID={acc_s};

-- INSERT PRISMA
INSERT INTO USR_DATACOTAH.RD_LIQUIDATIONS_USER_PRISMA (ACCOUNT_NUM, VERIFIER_DIGIT_ACCOUNT, ACCOUNT, BANK_CODE, PORTFOLIO, LIQ_DATE, CLOSING_DATE_LIQ, EXPIRATION_DATE, EXPIRATION_DATE_PREV, PROCESS_DATE) VALUES ({p_acc}, {v_dig}, {acc_s}, 7, {port_s+1}, TO_DATE('{c_cl}','YYYY-MM-DD'), TO_DATE('{p_cl}','YYYY-MM-DD'), TO_DATE('{c_ex}','YYYY-MM-DD'), TO_DATE('{p_ex}','YYYY-MM-DD'), TO_DATE('{c_cl}','YYYY-MM-DD'));
INSERT INTO USR_DATACOTAH.RD_SUMMARY_HEADER_PRISMA (ACCOUNT_NUMBER_ID, FINANTIAL_ENTITY_CODE_ID, REGISTER_INTERNAL_CODE, BANK_CODE, CLOSE_DATE_ID, NEXT_CLOSE_DATE, NEXT_EXPIRATION_DATE, PORTFOLIO) VALUES ({acc_s}, 7, 10, '007', TO_DATE('{c_cl}','YYYY-MM-DD'), TO_DATE('{n_cl}','YYYY-MM-DD'), TO_DATE('{n_ex}','YYYY-MM-DD'), {port_s});"""
            st.code(res, language="sql")
            if st_tax:
                st.code(f"INSERT INTO RD_TAX_COMMISSION_DETAIL_OP (ENTITY_CODE, FINANTIAL_ENTITY_CODE, CREDIT_ACCOUNT, BRANCH_OFFICE, TAX_CODE, TAX_DESCRIPTION, AMOUNT, CURRENCY, CLOSE_DATE, CREATE_DATE) VALUES ('007', '007', '{acc_s}', '{bran_s}', '{t_cod}', '{t_des}', {t_amt}, 'ARS', TO_DATE('{c_cl}','YYYY-MM-DD'), CURRENT_TIMESTAMP);", language="sql")