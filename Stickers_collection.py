import streamlit as st
import pandas as pd
from github import Github
import io

# 1. Configuración de la página
st.set_page_config(page_title="Álbum 2026 Pro", layout="centered")

# 2. Configuración de GitHub (Desde Secrets)
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = "TystSpoke/AlbumMundial2026"  # <--- CAMBIA ESTO por tu Usuario/NombreDelRepo
FILE_PATH = "datos.csv"


# --- FUNCIONES DE BASE DE DATOS (GITHUB CSV) ---

def cargar_datos():
    """Lee el CSV desde GitHub con las columnas ID, Tipo y Cantidad"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(FILE_PATH)
        decoded_content = file_content.decoded_content.decode()
        df = pd.read_csv(io.StringIO(decoded_content))

        st.session_state.file_sha = file_content.sha

        if not df.empty:
            # Filtra los que son parte de tu colección personal
            coleccion = df[df["Tipo"] == "Colección"]["ID"].tolist()
            st.session_state.album = set(str(x) for x in coleccion)

            # Filtra las repetidas y guarda su cantidad
            reps = df[df["Tipo"] == "Repetida"]
            st.session_state.repetidas = dict(zip(reps["ID"].astype(str), reps["Cantidad"].astype(int)))
        else:
            st.session_state.album = set()
            st.session_state.repetidas = {}
    except Exception as e:
        st.error(f"Error de sincronización: {e}")

def guardar_cambios():
    """Actualiza el archivo CSV en GitHub haciendo un commit automático"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)

        # Preparamos los datos
        lista_album = [{"ID": x, "Tipo": "Colección", "Cantidad": 1} for x in st.session_state.album]
        lista_rep = [{"ID": k, "Tipo": "Repetida", "Cantidad": v} for k, v in st.session_state.repetidas.items()]

        df_total = pd.DataFrame(lista_album + lista_rep)
        csv_string = df_total.to_csv(index=False)

        # Subimos a GitHub
        repo.update_file(
            FILE_PATH,
            "Actualización de cromos desde App",
            csv_string,
            st.session_state.file_sha
        )

        # Actualizamos el SHA para el siguiente cambio
        new_content = repo.get_contents(FILE_PATH)
        st.session_state.file_sha = new_content.sha

    except Exception as e:
        st.error(f"No se pudo guardar en GitHub: {e}")


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
        st.success("¡Trato sincronizado con GitHub!")

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