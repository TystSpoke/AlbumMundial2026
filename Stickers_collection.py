import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de la página (Debe ser lo primero)
st.set_page_config(page_title="Álbum 2026 Pro", layout="centered")

# 2. Conexión a Google Sheets
# Así debe quedar tu conexión en el código
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIONES DE BASE DE DATOS ---

def cargar_datos():
    """Lee los datos desde Google Sheets al iniciar la app"""
    try:
        df = conn.read(worksheet="Hoja 1", ttl="0") # ttl=0 para que no use caché y lea datos frescos
        if not df.empty:
            # Cargar estampas pegadas
            coleccion = df[df["Tipo"] == "Colección"]["ID"].tolist()
            st.session_state.album = set(str(x) for x in coleccion)
            
            # Cargar repetidas
            reps = df[df["Tipo"] == "Repetida"]
            st.session_state.repetidas = dict(zip(reps["ID"].astype(str), reps["Cantidad"].astype(int)))
    except Exception:
        # Si la hoja está vacía o hay error, inicializamos estructuras vacías
        if 'album' not in st.session_state: st.session_state.album = set()
        if 'repetidas' not in st.session_state: st.session_state.repetidas = {}

def guardar_cambios():
    """Envía los datos actuales de la memoria a Google Sheets"""
    lista_album = [{"ID": x, "Tipo": "Colección", "Cantidad": 1} for x in st.session_state.album]
    lista_rep = [{"ID": k, "Tipo": "Repetida", "Cantidad": v} for k, v in st.session_state.repetidas.items()]
    
    df_total = pd.DataFrame(lista_album + lista_rep)
    
    if not df_total.empty:
        conn.update(worksheet="Hoja 1", data=df_total)
    else:
        # Si borras todo, creamos un DataFrame vacío con encabezados
        df_vacio = pd.DataFrame(columns=["ID", "Tipo", "Cantidad"])
        conn.update(worksheet="Hoja 1", data=df_vacio)

# --- INICIALIZACIÓN ---
if 'album' not in st.session_state or 'repetidas' not in st.session_state:
    cargar_datos()

# --- FUNCIONES LÓGICAS ---

def procesar_intercambio(recibidas, dadas):
    # 1. Procesar recibidas
    for r in recibidas:
        if r.strip():
            st.session_state.album.add(r.strip().upper())
    
    # 2. Procesar dadas
    for d in dadas:
        d = d.strip().upper()
        if d in st.session_state.repetidas:
            st.session_state.repetidas[d] -= 1
            if st.session_state.repetidas[d] <= 0:
                del st.session_state.repetidas[d]
    
    guardar_cambios()
    st.balloons()

# --- INTERFAZ DE USUARIO ---
st.title("⚽ Collector Pro 2026")

tabs = st.tabs(["🤝 Intercambio", "📔 Mi Álbum", "♻️ Repetidas"])

# TAB 1: MODO INTERCAMBIO
with tabs[0]:
    st.header("¡Nuevo Trato!")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Recibo")
        r1 = st.text_input("Cromo 1", key="r1")
        r2 = st.text_input("Cromo 2", key="r2")
        r3 = st.text_input("Cromo 3", key="r3")
        
    with col2:
        st.subheader("📤 Doy")
        d1 = st.text_input("Cromo 1", key="d1")
        d2 = st.text_input("Cromo 2", key="d2")
        d3 = st.text_input("Cromo 3", key="d3")

    if st.button("🤝 CONFIRMAR TRATO", use_container_width=True):
        procesar_intercambio([r1, r2, r3], [d1, d2, d3])
        st.success("¡Datos guardados en la nube!")

# TAB 2: MI ÁLBUM
with tabs[1]:
    st.header("📔 Mi Progreso")
    busqueda = st.text_input("🔍 Buscar número:").upper()
    if busqueda:
        if busqueda in st.session_state.album:
            st.success(f"✅ Ya la tienes pegada.")
        elif busqueda in st.session_state.repetidas:
            st.warning(f"⚠️ La tienes repetida ({st.session_state.repetidas[busqueda]} veces).")
        else:
            st.error(f"❌ Te falta.")
    
    st.metric("Total pegadas", len(st.session_state.album))
    if st.checkbox("Mostrar lista completa"):
        st.write(sorted(list(st.session_state.album)))

# TAB 3: REPETIDAS
with tabs[2]:
    st.header("♻️ Mis Repetidas")
    
    with st.expander("➕ Añadir manual"):
        new_rep = st.text_input("Número (Ej: MEX 5):").upper()
        if st.button("Guardar Repetida"):
            if new_rep:
                st.session_state.repetidas[new_rep] = st.session_state.repetidas.get(new_rep, 0) + 1
                guardar_cambios()
                st.rerun()

    if st.session_state.repetidas:
        df_rep = pd.DataFrame([{"Número": k, "Cantidad": v} for k, v in st.session_state.repetidas.items()])
        st.table(df_rep)
    else:
        st.write("No tienes repetidas aún.")
