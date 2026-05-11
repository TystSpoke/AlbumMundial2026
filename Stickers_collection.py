import streamlit as st
import pandas as pd

# Configuración para celular
st.set_page_config(page_title="Álbum 2026 Pro", layout="centered")

# --- PERSISTENCIA DE DATOS (Simulación de DB) ---
# Nota: Para persistencia real, sigue la guía del PDF para conectar Google Sheets
if 'album' not in st.session_state:
    st.session_state.album = set()  # Estampas que ya tienes pegadas
if 'repetidas' not in st.session_state:
    st.session_state.repetidas = {}  # Diccionario: { "MEX 1": 2, "105": 1 }


# --- FUNCIONES LÓGICAS ---
def procesar_intercambio(recibidas, dadas):
    # 1. Procesar lo que recibes (se va al álbum)
    for r in recibidas:
        if r:
            st.session_state.album.add(r.strip().upper())
            # Si la tenías en repetidas y ahora la consigues, opcionalmente podrías quitarla de ahí

    # 2. Procesar lo que das (se quita de repetidas)
    for d in dadas:
        d = d.strip().upper()
        if d in st.session_state.repetidas:
            st.session_state.repetidas[d] -= 1
            if st.session_state.repetidas[d] <= 0:
                del st.session_state.repetidas[d]
    st.balloons()  # Animación de éxito


# --- INTERFAZ DE USUARIO ---
st.title("⚽ Intercambio Mundial 2026")

tabs = st.tabs(["🤝 Modo Intercambio", "📔 Mi Álbum", "♻️ Repetidas"])

# --- TAB 1: MODO INTERCAMBIO (La función que pediste) ---
with tabs[0]:
    st.header("¡Nuevo Trato!")
    st.info("Usa esta sección cuando estés frente a otro coleccionista.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Recibo")
        st.caption("Lo que vas a pegar")
        rec1 = st.text_input("Estampa 1", key="r1")
        rec2 = st.text_input("Estampa 2", key="r2")
        rec3 = st.text_input("Estampa 3", key="r3")

    with col2:
        st.subheader("📤 Doy")
        st.caption("Lo que sale de tu montón")
        da1 = st.text_input("Estampa 1", key="d1")
        da2 = st.text_input("Estampa 2", key="d2")
        da3 = st.text_input("Estampa 3", key="d3")

    if st.button("🤝 CONFIRMAR TRATO HECHO", use_container_width=True):
        recibidas = [rec1, rec2, rec3]
        dadas = [da1, da2, da3]
        procesar_intercambio(recibidas, dadas)
        st.success("Inventario actualizado automáticamente.")

# --- TAB 2: MI ÁLBUM ---
with tabs[1]:
    st.header("📔 Mi Progreso")
    busqueda = st.text_input("🔍 Buscar número:").upper()
    if busqueda:
        if busqueda in st.session_state.album:
            st.success(f"✅ La estampa {busqueda} YA ESTÁ PEGADA.")
        elif busqueda in st.session_state.repetidas:
            st.warning(f"⚠️ La tienes REPETIDA ({st.session_state.repetidas[busqueda]} veces).")
        else:
            st.error(f"❌ TE FALTA la estampa {busqueda}.")

    st.write(f"Total pegadas: **{len(st.session_state.album)}**")
    if st.checkbox("Ver toda mi lista"):
        st.write(sorted(list(st.session_state.album)))

# --- TAB 3: REPETIDAS ---
with tabs[2]:
    st.header("♻️ Mi Pila de Repetidas")

    # Agregar repetida rápido
    new_rep = st.text_input("Añadir repetida (Ej: ARG 10):").upper()
    if st.button("➕ Añadir"):
        if new_rep:
            st.session_state.repetidas[new_rep] = st.session_state.repetidas.get(new_rep, 0) + 1
            st.rerun()

    if st.session_state.repetidas:
        df_rep = pd.DataFrame([
            {"Número": k, "Cantidad": v} for k, v in st.session_state.repetidas.items()
        ])
        st.table(df_rep)
    else:
        st.write("No tienes repetidas registradas.")
