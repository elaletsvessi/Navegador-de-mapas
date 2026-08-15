import streamlit as st
import requests
import folium
import time
from streamlit_folium import st_folium

st.set_page_config(page_title="Calculadora de Rutas", layout="wide")

st.title("🗺️ Trazador de Rutas Rápidas")
st.write("Ingresa tu punto de partida y tu destino para encontrar el mejor camino.")

# Función para convertir texto a coordenadas (Limitada a San Luis Potosí y blindada)
def obtener_coordenadas(direccion):
    url = "https://nominatim.openstreetmap.org/search"
    
    # ¡AQUÍ ESTÁ EL TRUCO! Le inyectamos la ciudad y estado a su búsqueda
    direccion_completa = f"{direccion}, San Luis Potosí, México"
    
    # Arregla espacios y acentos para mejorar la búsqueda automáticamente
    parametros = {
        "q": direccion_completa,
        "format": "json",
        "limit": 1,
        "countrycodes": "mx"
    }
    headers = {"User-Agent": "ProyectoRutas_UASLP/1.0"}
    
    try:
        respuesta = requests.get(url, params=parametros, headers=headers)
        
        # Verificamos (Código 200) antes de intentar leer el JSON
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if len(datos) > 0:
                return float(datos[0]['lat']), float(datos[0]['lon'])
        else:
            st.error(f"El servidor de mapas está ocupado (Error {respuesta.status_code}). Intenta en un segundo.")
            
    except Exception as e:
        st.error(f"Hubo un problema de conexión: {e}")
        
    return None, None

# Interfaz de búsqueda
col1, col2 = st.columns(2)
with col1:
    origen_txt = st.text_input("📍 Punto de Partida", placeholder="Ej. Parque de Morales")
with col2:
    destino_txt = st.text_input("🏁 Destino", placeholder="Ej. Plaza San Luis")

# Se crea una variable en la memoria de Streamlit para controlar cuándo mostrar el mapa
if "mostrar_mapa" not in st.session_state:
    st.session_state.mostrar_mapa = False

# Cuando se presiona el botón, guardamos los datos y activamos la visualización del mapa
if st.button("Calcular Ruta", type="primary"):
    if origen_txt and destino_txt:
        st.session_state.origen = origen_txt
        st.session_state.destino = destino_txt
        st.session_state.mostrar_mapa = True
    else:
        st.warning("Por favor, llena ambos campos.")

# Si la memoria dice que mostremos el mapa, lo dibujamos fuera del botón
if st.session_state.mostrar_mapa:
    
    with st.spinner("Buscando el punto de partida... 📍"):
        lat1, lon1 = obtener_coordenadas(st.session_state.origen)
        
    # Esperamos 1.5 segundos para no saturar al servidor y evitar que nos metan a la cárcel (Error 429)
    time.sleep(1.5)
    
    with st.spinner("Buscando el destino... 🏁"):
        lat2, lon2 = obtener_coordenadas(st.session_state.destino)
        
    if lat1 and lat2:
        with st.spinner("Trazando la mejor ruta... 🚗"):
            
            # Petición a OSRM para trazar el camino
            url_ruta = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
            res_ruta = requests.get(url_ruta).json()
            
            if res_ruta.get("code") == "Ok":
                ruta_geojson = res_ruta["routes"][0]["geometry"]
                distancia_km = res_ruta["routes"][0]["distance"] / 1000
                tiempo_min = res_ruta["routes"][0]["duration"] / 60
                
                st.success(f"✅ Ruta encontrada: **{distancia_km:.2f} km** | Tiempo estimado: **{tiempo_min:.0f} minutos**")
                
                # --- DIBUJAR EL MAPA ---
                # Usamos "CartoDB positron" para un mapa más limpio y moderno
                mapa = folium.Map(location=[(lat1+lat2)/2, (lon1+lon2)/2], tiles="CartoDB positron")
                
                # Colocamos los pines
                folium.Marker([lat1, lon1], tooltip="Origen", icon=folium.Icon(color="green")).add_to(mapa)
                folium.Marker([lat2, lon2], tooltip="Destino", icon=folium.Icon(color="red", icon="flag")).add_to(mapa)
                
                # Trazamos la línea de la ruta
                folium.GeoJson(ruta_geojson, name="Ruta").add_to(mapa)
                
                # Ajustamos la cámara para que se vean ambos puntos perfectamente sin importar la distancia
                mapa.fit_bounds([[lat1, lon1], [lat2, lon2]])
                
                # Renderizamos el mapa en la pantalla
                # Creamos 3 columnas invisibles (margen izquierdo, centro gigante, margen derecho)
                espacio_izq, contenedor_mapa, espacio_der = st.columns([1, 10, 1])
                
                with contenedor_mapa:
                    # Lo hacemos más alto (700) y le decimos que use todo el ancho disponible del centro
                    st_folium(mapa, height=700, use_container_width=True)
            else:
                st.error("No se pudo encontrar una ruta de manejo entre estos dos puntos.")
    else:
        st.error("No pude encontrar uno de los lugares en San Luis Potosí. ¡Intenta ser un poco más específico!")