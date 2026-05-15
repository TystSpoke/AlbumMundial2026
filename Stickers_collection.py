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
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(FILE_PATH)
        # Forzamos la decodificación a utf-8-sig para ignorar caracteres raros al inicio
        decoded_content = file_content.decoded_content.decode('utf-8-sig')
        df = pd.read_csv(io.StringIO(decoded_content))

        # LIMPIEZA TOTAL: Quitamos espacios y carácteres raros de los nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]

        st.session_state.file_sha = file_content.sha

        if not df.empty:
            # Filtro para Álbum
            mask_album = df.iloc[:, 1].str.contains("Colecci", case=False, na=False)
            st.session_state.album = set(df[mask_album].iloc[:, 0].astype(str).str.strip())

            # Filtro para Repetidas (con manejo de errores de columna)
            mask_rep = df.iloc[:, 1].str.contains("Repetida", case=False, na=False)
            df_reps = df[mask_rep]

            # Si el archivo tiene las 3 columnas, las lee; si no, pone 1 por defecto
            if df.shape[1] >= 3:
                st.session_state.repetidas = dict(zip(
                    df_reps.iloc[:, 0].astype(str).str.strip(),
                    pd.to_numeric(df_reps.iloc[:, 2], errors='coerce').fillna(1).astype(int)
                ))
            else:
                st.session_state.repetidas = {str(x).strip(): 1 for x in df_reps.iloc[:, 0]}

    except Exception as e:
        # Esto evita el error de "AttributeError" inicializando las variables aunque falle la red
        st.session_state.album = set()
        st.session_state.repetidas = {}
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
        r = r.strip().upper()
        if not r: continue

        if r in st.session_state.album:
            st.session_state.repetidas[r] = st.session_state.repetidas.get(r, 0) + 1
        else:
            st.session_state.album.add(r)

    # 2. Procesar dadas
    for d in dadas:
        d = d.strip().upper()
        if not d: continue

        if d in st.session_state.repetidas:
            st.session_state.repetidas[d] -= 1
            if st.session_state.repetidas[d] <= 0:
                del st.session_state.repetidas[d]
        elif d in st.session_state.album:
            st.session_state.album.remove(d)

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
        txt_recibidas = st.text_area("IDs recibidos (separados por coma o espacio)",
                                     placeholder="CZE 1, MEX 4, USA 18", key="txt_r")

    with col2:
        st.subheader("📤 Doy")
        txt_dadas = st.text_area("IDs entregados (separados por coma o espacio)",
                                 placeholder="BRA 2, ARG 10", key="txt_d")

    if st.button("🤝 CONFIRMAR TRATO", use_container_width=True):
        # 1. Separamos ÚNICAMENTE por comas
        # 2. .strip() elimina espacios sobrantes al inicio/final de cada cromo
        lista_r = [cromo.strip() for cromo in txt_recibidas.split(',') if cromo.strip()]
        lista_d = [cromo.strip() for cromo in txt_dadas.split(',') if cromo.strip()]

        if lista_r or lista_d:
            procesar_intercambio(lista_r, lista_d)
            st.success(f"✅ ¡Trato sincronizado! Procesados {len(lista_r)} recibidos y {len(lista_d)} entregados.")
            st.rerun()  # Refrescamos para ver los cambios
        else:
            st.warning("⚠️ No ingresaste ningún ID.")

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
        new_rep = st.text_input("Número (Ej: MEX 5):").upper().strip()  # <--- Agregar .strip()
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