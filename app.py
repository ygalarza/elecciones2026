import streamlit as st
import requests
import time

st.set_page_config(page_title="ONPE - Datos Reales 2da Vuelta", page_icon="🇵🇪", layout="centered")

# URLs de la API de la ONPE halladas con F12
URL_PARTICIPANTES = "https://resultadosegundavuelta.onpe.gob.pe/presentacion-backend/resumen-general/participantes?idEleccion=10&tipoFiltro=eleccion"
URL_TOTALES = "https://resultadosegundavuelta.onpe.gob.pe/presentacion-backend/resumen-general/totales?idEleccion=10&tipoFiltro=eleccion"

def obtener_datos_reales():
    # Hemos replicado exactamente el comportamiento de tu Microsoft Edge
    headers = {
        "accept": "*/*",
        "accept-language": "es-419,es;q=0.9,es-ES;q=0.8,en;q=0.7,en-GB;q=0.6,en-US;q=0.5",
        "content-type": "application/json",
        "cookie": "_ga=GA1.1.130539352.1781026960; _ga_7X9XC2V582=GS2.1.s1781026959$o1$g1$t1781026973$j46$l0$h791059355; _ga_THMBN2T4BS=GS2.1.s1781035396$o3$g1$t1781036760$j59$l0$h353648308",
        "priority": "u=1, i",
        "referer": "https://resultadosegundavuelta.onpe.gob.pe/main/resumen",
        "sec-ch-ua": '"Microsoft Edge";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
    }
    
    try:
        res_part = requests.get(URL_PARTICIPANTES, headers=headers, timeout=15)
        res_tot = requests.get(URL_TOTALES, headers=headers, timeout=15)
        
        if res_part.status_code == 200 and res_tot.status_code == 200:
            try:
                return {
                    "participantes": res_part.json(),
                    "totales": res_tot.json()
                }
            except Exception:
                st.sidebar.error("❌ ONPE envió HTML (Seguridad activa).")
                with st.sidebar.expander("Ver respuesta"):
                    st.text(res_part.text[:800])
                return None
        else:
            st.sidebar.error(f"❌ Error HTTP: Part={res_part.status_code} | Tot={res_tot.status_code}")
            return None
            
    except Exception as e:
        st.sidebar.error(f"❌ Error general: {e}")
        return None

# --- INTERFAZ GRÁFICA ---
st.title("Conteo Oficial ONPE en Vivo")
st.subheader("Diferencia real de votos en la Segunda Vuelta")

refresh_rate = st.sidebar.slider("Actualizar cada (segundos):", 5, 120, 15)
ver_json_crudo = st.sidebar.checkbox("Ver estructura JSON (Depuración)", value=False)

placeholder = st.empty()

while True:
    datos = obtener_datos_reales()
    
    if datos:
        j_participantes = datos["participantes"]
        j_totales = datos["totales"]
        
        try:
            # ==================================================================
            # 1. ENTRAR DIRECTO A LA LISTA DE CANDIDATOS ("data")
            # ==================================================================
            lista_cand = []
            if isinstance(j_participantes, dict) and "data" in j_participantes:
                lista_cand = j_participantes["data"]
            elif isinstance(j_participantes, list):
                lista_cand = j_participantes
            
            # ==================================================================
            # 2. EXTRACCIÓN DE MÉTRICAS GLOBALES (JSON TOTALES)
            # ==================================================================
            def buscar_llave_exacta(data, llave_objetivo):
                if isinstance(data, dict):
                    if llave_objetivo in data and data[llave_objetivo] is not None:
                        return str(data[llave_objetivo])
                    for k, v in data.items():
                        res = buscar_llave_exacta(v, llave_objetivo)
                        if res: return res
                elif isinstance(data, list):
                    for item in data:
                        res = buscar_llave_exacta(item, llave_objetivo)
                        if res: return res
                return None

            total_actas = buscar_llave_exacta(j_totales, "totalActas") or "0"
            actas_contabilizadas = buscar_llave_exacta(j_totales, "contabilizadas") or "0"
            total_votos_emitidos = buscar_llave_exacta(j_totales, "totalVotosEmitidos") or "0"

            # ==================================================================
            # 3. EXTRACCIÓN CON LAS LLAVES EXACTAS DE TU JSON
            # ==================================================================
            if isinstance(lista_cand, list) and len(lista_cand) >= 2:
                c1_raw = lista_cand[0]
                c2_raw = lista_cand[1]
                
                # Función limpiadora básica para convertir valores del JSON a números puros
                def limpiar_numero(valor):
                    try:
                        if valor is None: return 0.0
                        val_str = str(valor).replace(",", "").replace("%", "").strip()
                        return float(val_str)
                    except ValueError:
                        return 0.0

                # Candidato 1 Mapeado con tus etiquetas exactas
                cand1 = {
                    "nombre": str(c1_raw.get("nombreCandidato", "Desconocido")),
                    "partido": str(c1_raw.get("nombreAgrupacionPolitica", "Desconocido")),
                    "votos": int(limpiar_numero(c1_raw.get("totalVotosValidos", 0))),
                    "porcentaje": limpiar_numero(c1_raw.get("porcentajeVotosValidos", 0.0))
                }
                
                # Candidato 2 Mapeado con tus etiquetas exactas
                cand2 = {
                    "nombre": str(c2_raw.get("nombreCandidato", "Desconocido")),
                    "partido": str(c2_raw.get("nombreAgrupacionPolitica", "Desconocido")),
                    "votos": int(limpiar_numero(c2_raw.get("totalVotosValidos", 0))),
                    "porcentaje": limpiar_numero(c2_raw.get("porcentajeVotosValidos", 0.0))
                }
                
                # Cálculos automáticos calculados en Python
                diferencia = abs(cand1["votos"] - cand2["votos"])
                lider = cand1["nombre"] if cand1["votos"] > cand2["votos"] else cand2["nombre"]
                
                # ==================================================================
                # 4. RENDERIZADO EN PANTALLA PRINCIPAL
                # ==================================================================
                with placeholder.container():
                    # Formateo visual de números grandes arriba
                    try:
                        actas_tot_fmt = f"{int(total_actas.replace(',', '')):,}"
                        actas_cont_fmt = f"{int(actas_contabilizadas.replace(',', '')):,}"
                        votos_emit_fmt = f"{int(total_votos_emitidos.replace(',', '')):,}"
                    except Exception:
                        actas_tot_fmt = total_actas
                        actas_cont_fmt = actas_contabilizadas
                        votos_emit_fmt = total_votos_emitidos

                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Total de Actas", actas_tot_fmt)
                    col_b.metric("Actas Contabilizadas", actas_cont_fmt)
                    col_c.metric("Total Votos Emitidos", votos_emit_fmt)
                    col_d.metric("Última Consulta", time.strftime("%H:%M:%S"))
                    
                    st.markdown("---")
                    
                    # Mostrar la diferencia oficial calculada en tiempo real
                    st.info(f"### 🎯 Diferencia Actual: **{diferencia:,} votos**")
                    st.caption(f"Líder actual del conteo oficial: **{lider}**")
                    st.markdown("---")
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.error(f"### {cand1['nombre']}")
                        st.caption(cand1['partido'])
                        st.metric("Votos Válidos", f"{cand1['votos']:,}")
                        st.subheader(f"{cand1['porcentaje']}%")
                        
                    with col_c2:
                        st.success(f"### {cand2['nombre']}")
                        st.caption(cand2['partido'])
                        st.metric("Votos Válidos", f"{cand2['votos']:,}")
                        st.subheader(f"{cand2['porcentaje']}%")
            else:
                st.warning("⚠️ La estructura 'data' fue hallada pero no contiene la lista de candidatos esperada.")
                
        except Exception as e:
            st.error(f"Error procesando los datos descargados: {e}")
            
        if ver_json_crudo:
            st.markdown("### 🛠️ Estructura del Servidor ONPE (Modo Depuración)")
            st.write("**JSON Totales:**")
            st.json(j_totales)
            st.write("**JSON Participantes:**")
            st.json(j_participantes)
            
    else:
        st.warning("Conectando con la base de datos de la ONPE...")
        
    time.sleep(refresh_rate)
