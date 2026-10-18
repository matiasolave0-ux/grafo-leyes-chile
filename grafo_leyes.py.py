import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import io

# 1. Configuración general (Uso de toda la pantalla)
st.set_page_config(layout="wide", page_title="Análisis de Redes Legales")

st.sidebar.title("📊 Resumen de la Red")
st.sidebar.write("Sube el archivo Excel con las leyes separadas por hojas.")

archivo_excel = st.sidebar.file_uploader("Cargar Excel (.xlsx)", type=["xlsx"])

if archivo_excel is not None:
    # 2. Leer TODAS las hojas del excel
    diccionario_hojas = pd.read_excel(archivo_excel, sheet_name=None)
    
    G = nx.MultiDiGraph()
    
    # 3. Asignar colores por Ley
    colores = ['#ff4b4b', '#4b8bff', '#4bff6a', '#ffb04b', '#9d4bff', '#00ced1']
    leyes = list(diccionario_hojas.keys())
    color_map = {leyes[i]: colores[i % len(colores)] for i in range(len(leyes))}
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎨 Leyenda de Leyes")
    for ley, color in color_map.items():
        st.sidebar.markdown(f"<span style='color:{color}; font-weight:bold;'>■</span> {ley}", unsafe_allow_html=True)
    
    # 4. Construir el grafo iterando por cada hoja
    
    # Diccionario para fusionar nombres rebeldes
    homologacion = {
        "GORE": "GOBIERNO REGIONAL",
        "GOBIERNOS REGIONALES": "GOBIERNO REGIONAL",
        "GOBIERNO REGIONAL (GORE)": "GOBIERNO REGIONAL",
        "EL PRESIDENTE": "PRESIDENTE DE LA REPÚBLICA",
        "PRESIDENTE": "PRESIDENTE DE LA REPÚBLICA",
        "CONSEJEROS REGIONALES": "CONSEJO REGIONAL",
        "CONSEJO REGIONAL (CORE)": "CONSEJO REGIONAL",
        "MINISTERIOS": "MINISTERIOS SECTORIALES"
    }

    for nombre_hoja, df in diccionario_hojas.items():
        df.columns = df.columns.str.strip()
        
        if 'Institución A' not in df.columns or 'Institución B' not in df.columns:
            continue 
            
        # Rellena los espacios vacíos (celdas combinadas) hacia abajo
        df['Institución A'] = df['Institución A'].ffill()
        df['Institución B'] = df['Institución B'].ffill()
        
        color_ley = color_map[nombre_hoja]
        
        for index, row in df.iterrows():
            origen_raw = str(row['Institución A'])
            destino_raw = str(row['Institución B'])
            
            # Limpieza básica de espacios y mayúsculas
            origen = " ".join(origen_raw.split()).upper()
            destino = " ".join(destino_raw.split()).upper()
            
            # Homologación de nombres duplicados
            origen = homologacion.get(origen, origen)
            destino = homologacion.get(destino, destino)
            
            # Filtrar filas vacías o nulas
            if origen == "NAN" or destino == "NAN" or origen == "NONE" or destino == "NONE":
                continue
            
            if not G.has_node(origen):
                G.add_node(origen, title=origen_raw, label=origen)
            if not G.has_node(destino):
                G.add_node(destino, title=destino_raw, label=destino)
            
            orden = row.get('Orden legal', 'Sin dato')
            tipo = row.get('Tipo de mandato', 'Sin dato')
            mandato = row.get('Mandato explícito', 'Sin dato')
            
            # --- LECTURA DE INTENSIDAD NUMÉRICA ---
            try:
                valor_celda = row.get('Intensidad', 2)
                if pd.isna(valor_celda):
                    intensidad_num = 2
                else:
                    intensidad_num = int(float(valor_celda))
            except:
                intensidad_num = 2
                
            # Asignación de grosor visual y etiqueta
            if intensidad_num >= 3:
                grosor = 7
                etiqueta_intensidad = "Mayor (Nivel 3)"
            elif intensidad_num <= 1:
                grosor = 1
                etiqueta_intensidad = "Diminuta (Nivel 1)"
            else:
                grosor = 3
                etiqueta_intensidad = "Mediana (Nivel 2)"
                
            info = f"<b>Ley:</b> {nombre_hoja}<br><b>Orden Legal:</b> {orden}<br><b>Tipo:</b> {tipo}<br><b>Intensidad:</b> {etiqueta_intensidad}<br><br>{mandato}"
            
            # Conexión final
            G.add_edge(origen, destino, title=info, label=str(tipo), color=color_ley, ley=nombre_hoja, width=grosor)
            
    # 5. Proporcionalidad de los Nodos (Tamaño según conexiones)
    for nodo in G.nodes():
        G.nodes[nodo]['value'] = G.degree(nodo) + 1 
        
    # --- Métricas y Auditoría ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Métricas Generales")
    st.sidebar.write(f"**Nodos (Instituciones):** {G.number_of_nodes()}")
    st.sidebar.write(f"**Aristas (Interacciones):** {G.number_of_edges()}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Auditoría de Actores")
    st.sidebar.write("Revisa esta lista alfabética. Si ves dos nombres parecidos, agrégalos al diccionario de homologación en el código.")
    actores_ordenados = sorted(list(G.nodes()))
    st.sidebar.dataframe(pd.DataFrame({"Instituciones Detectadas": actores_ordenados}), use_container_width=True)

    # --- 6. Visualización Central (Grafo Interactivo ampliado) ---
    st.title("Mapa de Interacciones Legales")
    st.write("💡 **Tip:** Pasa el cursor sobre la esquina superior derecha del cuadro blanco del grafo; aparecerá un ícono de flechas ⤢ para ponerlo en pantalla completa aquí mismo.")
    
    net = Network(height='800px', width='100%', directed=True, bgcolor='#ffffff', font_color='#333333')
    net.from_nx(G)
    
    # Físicas y flechas dinámicas para evitar superposición
    net.set_options("""
    var options = {
      "configure": {
        "enabled": true,
        "filter": ["physics"]
      },
      "nodes": {
        "font": { "size": 11, "face": "arial", "color": "#2c3e50" },
        "scaling": { "min": 14, "max": 50, "label": { "enabled": true, "min": 9, "max": 14 } }
      },
      "edges": {
        "font": { "size": 8, "color": "#7f8c8d", "align": "middle" },
        "smooth": { "type": "dynamic" } 
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -32000,
          "centralGravity": 0.4,
          "springLength": 280,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 1
        },
        "solver": "barnesHut"
      }
    }
    """)
    
    path_html = "grafo_temporal.html"
    net.save_graph(path_html)
    
    with open(path_html, 'r', encoding='utf-8') as f:
        source_code = f.read()
        
    components.html(source_code, height=850)
    
    # --- 7. Motor de Descargas (HTML, PNG, PDF) ---
    st.markdown("---")
    st.subheader("📥 Descargar Grafo")
    st.success("Para presentaciones, te recomendamos descargar el **Grafo Interactivo (HTML)**. Puedes abrirlo haciendo doble clic, presionar F11 en tu navegador y exponer en pantalla completa moviendo los nodos en vivo.")
    
    col_html, col_png, col_pdf = st.columns(3)
    
    # Botón HTML
    col_html.download_button(
        label="🌐 Descargar Grafo Interactivo (HTML)", 
        data=source_code, 
        file_name="grafo_leyes_interactivo.html", 
        mime="text/html"
    )

    # Gráfico estático
    fig, ax = plt.subplots(figsize=(24, 18)) 
    pos = nx.kamada_kawai_layout(G)
    node_sizes = [(G.degree(n) + 1) * 350 for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, node_color='#eaeff2', edgecolors='#95a5a6', alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=6, font_weight="bold", font_color="#2c3e50")
    
    for nombre_hoja, color in color_map.items():
        edges_ley = [(u, v, d) for u, v, d in G.edges(data=True) if d.get('ley') == nombre_hoja]
        
        if edges_ley:
            edgelist = [(u, v) for u, v, d in edges_ley]
            edge_widths = [d.get('width', 3) * 0.6 for u, v, d in edges_ley]
            
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=edgelist, edge_color=color, alpha=0.6, 
                                   width=edge_widths, arrowsize=10, connectionstyle='arc3, rad=0.2')
        
    ax.axis('off')
    plt.tight_layout()
    
    buf_png = io.BytesIO()
    fig.savefig(buf_png, format="png", dpi=300)
    buf_png.seek(0)
    
    buf_pdf = io.BytesIO()
    fig.savefig(buf_pdf, format="pdf")
    buf_pdf.seek(0)
    
    col_png.download_button(label="🖼️ Descargar Imagen Estática (PNG)", data=buf_png, file_name="grafo_leyes.png", mime="image/png")
    col_pdf.download_button(label="📄 Descargar Documento (PDF)", data=buf_pdf, file_name="grafo_leyes.pdf", mime="application/pdf")

else:
    st.info("👈 Sube tu Excel en el menú lateral.")