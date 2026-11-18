# =============================================================================
#  CALCULADORA DE MATERIALES PARA MUROS DE ALBAÑILERÍA
#  Programación Digital CIV-601 · Ingeniería Civil · UCSUR
# =============================================================================

import io
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import pandas as pd
import streamlit as st


# =============================================================================
# PARTE 1 · DATOS DE REFERENCIA
# =============================================================================
BOLSA_KG = 42.5

# nombre: (largo cm, ancho cm, alto cm, tipo, sólido para muro portante)
CATALOGO = {
    "Ladrillo King Kong 18 huecos (24×13×9)":   (24, 13, 9, "ladrillo", False),
    "Ladrillo King Kong sólido tipo IV (24×13×9)": (24, 13, 9, "ladrillo", True),
    "Ladrillo pandereta (23×12×9)":             (23, 12, 9, "pandereta", False),
    "Bloqueta de concreto 39×19×9":             (39, 9, 19, "bloqueta", True),
    "Bloqueta de concreto 39×19×12":            (39, 12, 19, "bloqueta", True),
    "Bloqueta de concreto 39×19×14":            (39, 14, 19, "bloqueta", True),
    "Bloqueta de concreto 39×19×19":            (39, 19, 19, "bloqueta", True),
    "Personalizado":                            None,
}

# dosificación: (kg de cemento por m³ de mortero, m³ de arena por m³ de mortero)
DOSIFICACIONES = {
    "1:4 (cemento : arena)": (364, 1.16),
    "1:5 (cemento : arena)": (302, 1.18),
}

APAREJOS = ["Soga", "Cabeza", "Canto"]

# precio normal, precio por mayor, cantidad mínima para precio por mayor
PRECIOS_TIENDA_A = {
    "Unidad":  [1.20, 1.14, 100],
    "Cemento": [30.90, 30.90, 1],
    "Arena":   [70.00, 70.00, 1],
}
PRECIOS_TIENDA_B = {
    "Unidad":  [1.25, 0.98, 1000],
    "Cemento": [32.00, 29.50, 100],
    "Arena":   [75.00, 55.00, 5],
}
PRECIO_UNIDAD_REF = {"ladrillo": 1.20, "pandereta": 0.85, "bloqueta": 2.50}


# =============================================================================
# PARTE 2 · CÁLCULOS DE INGENIERÍA
# =============================================================================
def redondear_arriba(x, paso=1.0):
    return math.ceil(round(x / paso, 6)) * paso


def geometria(largo, ancho, alto, aparejo):
    if aparejo == "Soga":
        return largo, alto, ancho
    elif aparejo == "Cabeza":
        return ancho, alto, largo
    else:
        return largo, ancho, alto


def validar_muro(largo, alto, aberturas):
    errores = []
    area_ab = 0
    for i in range(len(aberturas)):
        a = aberturas[i]
        if a["ancho"] <= 0 or a["alto"] <= 0 or a["cantidad"] < 1:
            errores.append(f"Abertura {i + 1}: medidas o cantidad no válidas.")
        elif a["ancho"] > largo or a["alto"] > alto:
            errores.append(f"Abertura {i + 1} ({a['tipo']}) es más grande que el muro.")
        area_ab = area_ab + a["ancho"] * a["alto"] * a["cantidad"]
    if area_ab >= largo * alto:
        errores.append("Las aberturas ocupan todo el muro o más.")
    return errores


def area_muro(largo, alto, aberturas):
    area_ab = 0
    for a in aberturas:
        area_ab = area_ab + a["ancho"] * a["alto"] * a["cantidad"]
    return largo * alto, area_ab, largo * alto - area_ab


def consumo_por_m2(unidad, junta, aparejo, dosificacion):
    l, a, h = unidad[0] / 100, unidad[1] / 100, unidad[2] / 100
    horiz, vert, espesor = geometria(l, a, h, aparejo)
    area_modular = (horiz + junta) * (vert + junta)
    unidades_m2 = 1 / area_modular
    mortero_m2 = espesor - unidades_m2 * (l * a * h)
    kg_cem, arena_m3 = DOSIFICACIONES[dosificacion]
    return {
        "espesor": espesor,
        "area_modular": area_modular,
        "unidades_m2": unidades_m2,
        "mortero_m2": mortero_m2,
        "cemento_m2": mortero_m2 * kg_cem / BOLSA_KG,
        "arena_m2": mortero_m2 * arena_m3,
    }


def materiales_totales(area_neta, consumo, desperdicio):
    f = 1 + desperdicio / 100
    return {
        "Unidad":  area_neta * consumo["unidades_m2"] * f,
        "Cemento": area_neta * consumo["cemento_m2"] * f,
        "Arena":   area_neta * consumo["arena_m2"] * f,
        "Mortero": area_neta * consumo["mortero_m2"] * f,
    }


def materiales_a_comprar(necesario, stock):
    return {
        "Unidad":  max(0, redondear_arriba(necesario["Unidad"] - stock["Unidad"])),
        "Cemento": max(0, redondear_arriba(necesario["Cemento"] - stock["Cemento"])),
        "Arena":   max(0.0, redondear_arriba(necesario["Arena"] - stock["Arena"], 0.5)),
    }


def cobertura_stock(stock, consumo, desperdicio):
    f = 1 + desperdicio / 100
    cobertura = {}
    pares = [("Unidad", consumo["unidades_m2"]), ("Cemento", consumo["cemento_m2"]),
             ("Arena", consumo["arena_m2"])]
    for nombre, por_m2 in pares:
        if por_m2 > 0:
            cobertura[nombre] = stock[nombre] / (por_m2 * f)
        else:
            cobertura[nombre] = 0
    return cobertura


# =============================================================================
# PARTE 3 · COMPARACIÓN DE TIENDAS
# =============================================================================
def costo_en_tienda(compra, precios):
    detalle = {}
    total = 0
    for material in ["Unidad", "Cemento", "Arena"]:
        normal, mayor, minimo = precios[material]
        cantidad = compra[material]
        if cantidad >= minimo:
            precio, modo = mayor, "por mayor"
        else:
            precio, modo = normal, "por menor"
        subtotal = cantidad * precio
        detalle[material] = (cantidad, precio, modo, subtotal)
        total = total + subtotal
    return total, detalle


def compra_mixta(det_a, det_b):
    total = 0
    eleccion = {}
    for material in ["Unidad", "Cemento", "Arena"]:
        if det_a[material][3] <= det_b[material][3]:
            eleccion[material] = "A"
            total = total + det_a[material][3]
        else:
            eleccion[material] = "B"
            total = total + det_b[material][3]
    return total, eleccion


# =============================================================================
# PARTE 4 · ASISTENTE INTELIGENTE (SISTEMA EXPERTO DE REGLAS)
# =============================================================================
def asistente_tecnico(unidad, tipo_muro, zona, muros, desperdicio, junta_cm):
    avisos = []
    tipo, solido = unidad[3], unidad[4]
    if tipo_muro == "Portante":
        if tipo == "pandereta" and zona > 1:
            avisos.append(("error", "La Norma E.070 prohíbe el ladrillo pandereta en muros "
                                    "portantes (solo se permite en zona sísmica 1). Use un ladrillo sólido."))
        elif not solido:
            avisos.append(("warning", "Para muros portantes la Norma E.070 exige unidades sólidas "
                                      "(perforaciones < 30 %). El King Kong 18 huecos no cumple: "
                                      "use King Kong sólido tipo IV o V."))
        elif tipo == "bloqueta":
            avisos.append(("info", "Verifique que la bloqueta sea de uso estructural (NTP 399.602)."))
    else:
        if tipo == "pandereta":
            avisos.append(("success", "Pandereta adecuada para tabiquería (muro no portante)."))
    for i in range(len(muros)):
        m = muros[i]
        if m["alto"] > 3:
            avisos.append(("warning", f"Muro {i + 1}: altura mayor de 3 m; verifique arriostramiento."))
        if m["area_bruta"] > 0 and m["area_ab"] / m["area_bruta"] > 0.5:
            avisos.append(("info", f"Muro {i + 1}: las aberturas superan el 50 % del área."))
    if desperdicio < 3:
        avisos.append(("warning", "Desperdicio menor de 3 %: puede faltar material por roturas y cortes."))
    if junta_cm > 1.5:
        avisos.append(("info", "Junta mayor de 1.5 cm: aumenta el consumo de mortero."))
    return avisos


def asistente_compra(area_total, umbral, total_a, total_b, total_mix, eleccion):
    if total_a <= total_b:
        mejor, total_mejor, otro = "Tienda A", total_a, total_b
    else:
        mejor, total_mejor, otro = "Tienda B", total_b, total_a
    mensajes = []
    if area_total > umbral:
        mensajes.append(f"Obra grande ({area_total:.1f} m² > {umbral:.0f} m²): conviene comprar por mayor.")
    else:
        mensajes.append(f"Obra pequeña ({area_total:.1f} m² ≤ {umbral:.0f} m²): se compara precio por menor.")
    mensajes.append(f"Recomendación: comprar todo en **{mejor}** por S/ {total_mejor:,.2f} "
                    f"(ahorro de S/ {otro - total_mejor:,.2f}).")
    if total_mejor > 0 and (total_mejor - total_mix) / total_mejor > 0.03:
        texto = ", ".join(f"{m} en Tienda {t}" for m, t in eleccion.items())
        mensajes.append(f"Opción más económica: compra mixta ({texto}) por S/ {total_mix:,.2f}.")
    return mejor, mensajes


# =============================================================================
# PARTE 5 · GRÁFICOS
# =============================================================================
def dibujar_muro(m, unidad, aparejo, junta):
    l, a, h = unidad[0] / 100, unidad[1] / 100, unidad[2] / 100
    horiz, vert, _ = geometria(l, a, h, aparejo)
    mh, mv = horiz + junta, vert + junta
    fig, ax = plt.subplots(figsize=(9, max(2.8, min(7, 9 * m["alto"] / m["largo"] + 0.8))))
    ax.add_patch(Rectangle((0, 0), m["largo"], m["alto"], color="#d6cfc4"))
    piezas, fila, y = [], 0, 0.0
    color = "#9aa0a6" if unidad[3] == "bloqueta" else "#b5552b"
    while y < m["alto"]:
        x = -mh / 2 if fila % 2 else 0.0
        while x < m["largo"]:
            x0, x1 = max(x, 0), min(x + horiz, m["largo"])
            if x1 > x0:
                piezas.append(Rectangle((x0, y), x1 - x0, min(vert, m["alto"] - y)))
            x += mh
        y += mv
        fila += 1
    ax.add_collection(PatchCollection(piezas, facecolor=color, edgecolor="#5c3a21", linewidth=0.3))
    lista = []
    for ab in m["aberturas"]:
        for _ in range(ab["cantidad"]):
            lista.append(ab)
    if lista:
        ocupado = sum(ab["ancho"] for ab in lista)
        espacio = max((m["largo"] - ocupado) / (len(lista) + 1), 0)
        x = espacio
        for ab in lista:
            y0 = 0 if ab["tipo"] == "Puerta" else min(0.9, m["alto"] - ab["alto"])
            fc = "#6b4423" if ab["tipo"] == "Puerta" else "#a8d8f0"
            ax.add_patch(Rectangle((x, y0), ab["ancho"], ab["alto"], facecolor=fc, edgecolor="black", lw=1.2))
            x += ab["ancho"] + espacio
    ax.set_xlim(-0.1, m["largo"] + 0.1)
    ax.set_ylim(-0.1, m["alto"] + 0.1)
    ax.set_aspect("equal")
    ax.set_xlabel("Largo (m)")
    ax.set_ylabel("Altura (m)")
    ax.set_title(f"{m['nombre']} · {m['largo']:.2f} × {m['alto']:.2f} m · neta {m['area_neta']:.2f} m²")
    fig.tight_layout()
    return fig


def grafico_tiendas(det_a, det_b):
    materiales = ["Unidad", "Cemento", "Arena"]
    va = [det_a[m][3] for m in materiales]
    vb = [det_b[m][3] for m in materiales]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    x = range(len(materiales))
    ax.bar([i - 0.2 for i in x], va, 0.4, label="Tienda A", color="#2e5e8c")
    ax.bar([i + 0.2 for i in x], vb, 0.4, label="Tienda B", color="#b5552b")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["Ladrillo/Bloqueta", "Cemento", "Arena"])
    ax.set_ylabel("Soles (S/)")
    ax.set_title("Costo por material en cada tienda")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


# =============================================================================
# PARTE 6 · HOJA DE RESULTADOS (PDF)
# =============================================================================
def generar_pdf(lineas, figuras):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        por_pagina = 55
        for inicio in range(0, len(lineas), por_pagina):
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.06, 0.96, "\n".join(lineas[inicio:inicio + por_pagina]),
                     va="top", family="monospace", fontsize=8.5)
            pdf.savefig(fig)
            plt.close(fig)
        for f in figuras:
            pdf.savefig(f)
    buffer.seek(0)
    return buffer


# =============================================================================
# PARTE 7 · INTERFAZ WEB
# =============================================================================
st.set_page_config(page_title="Calculadora de Muros · UCSUR", page_icon="🧱", layout="wide")

st.markdown("""
<style>
.cabecera {background: linear-gradient(90deg,#1f3b5c,#b5552b); color:white;
           padding:18px 26px; border-radius:14px; margin-bottom:12px}
.cabecera h1 {margin:0; font-size:28px}
.cabecera p {margin:4px 0 0 0; opacity:.85}
</style>
<div class="cabecera">
  <h1>🧱 Calculadora de Materiales para Muros</h1>
  <p>Programación Digital CIV-601 · Ingeniería Civil · Universidad Científica del Sur</p>
</div>
""", unsafe_allow_html=True)

# ---- 7.1 Barra lateral: parámetros ----
with st.sidebar:
    st.header("⚙️ Parámetros")
    tipo_muro = st.radio("Tipo de muro", ["Portante", "Tabique (no portante)"])
    tipo_muro = "Portante" if tipo_muro == "Portante" else "Tabique"
    zona = st.selectbox("Zona sísmica (E.030)", [1, 2, 3, 4], index=3)
    junta_cm = st.slider("Espesor de junta (cm)", 0.8, 2.5, 1.5, 0.1)
    desperdicio = st.slider("Desperdicio (%)", 0, 20, 5)
    dosificacion = st.selectbox("Dosificación del mortero", list(DOSIFICACIONES))
    umbral = st.number_input("Umbral obra grande (m²)", 50.0, 5000.0, 500.0, 50.0)
    st.caption("Mortero: método geométrico. Factores de cemento y arena referenciales; "
               "contrastar con tabla CAPECO o ficha del fabricante.")

junta = junta_cm / 100

paso1, paso2, paso3, paso4, paso5 = st.tabs(
    ["1️⃣ Muros", "2️⃣ Ladrillo / bloqueta", "3️⃣ Materiales que tengo", "4️⃣ Tiendas", "📊 Resultados"])

# ---- 7.2 Muros y aberturas ----
with paso1:
    n_muros = st.number_input("¿Cuántos muros tiene la obra?", 1, 20, 1, 1)
    muros = []
    errores_muros = []
    pestañas = st.tabs([f"Muro {i + 1}" for i in range(int(n_muros))])
    for i in range(int(n_muros)):
        with pestañas[i]:
            c1, c2 = st.columns(2)
            largo = c1.number_input("Largo (m)", 0.1, 100.0, 5.0, 0.05, key=f"l{i}")
            alto = c2.number_input("Alto (m)", 0.1, 10.0, 2.6, 0.05, key=f"h{i}")
            st.markdown("**Puertas y ventanas** (agregue filas con ➕)")
            inicial = pd.DataFrame([{"tipo": "Puerta", "ancho": 0.90, "alto": 2.10, "cantidad": 1}]) \
                if i == 0 else pd.DataFrame(columns=["tipo", "ancho", "alto", "cantidad"])
            tabla = st.data_editor(
                inicial, num_rows="dynamic", key=f"ab{i}", width="stretch",
                column_config={
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["Puerta", "Ventana"], required=True),
                    "ancho": st.column_config.NumberColumn("Ancho (m)", min_value=0.0, step=0.05),
                    "alto": st.column_config.NumberColumn("Alto (m)", min_value=0.0, step=0.05),
                    "cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
                })
            aberturas = []
            for _, fila in tabla.dropna(subset=["tipo"]).iterrows():
                aberturas.append({
                    "tipo": fila["tipo"],
                    "ancho": float(fila["ancho"] or 0),
                    "alto": float(fila["alto"] or 0),
                    "cantidad": int(fila["cantidad"] or 1),
                })
            errores = validar_muro(largo, alto, aberturas)
            for e in errores:
                st.error(e)
                errores_muros.append(f"Muro {i + 1}: {e}")
            bruta, ab, neta = area_muro(largo, alto, aberturas)
            k1, k2, k3 = st.columns(3)
            k1.metric("Área bruta", f"{bruta:.2f} m²")
            k2.metric("Aberturas", f"{ab:.2f} m²")
            k3.metric("Área neta", f"{neta:.2f} m²")
            muros.append({"nombre": f"Muro {i + 1}", "largo": largo, "alto": alto, "aberturas": aberturas,
                          "area_bruta": bruta, "area_ab": ab, "area_neta": neta})

# ---- 7.3 Unidad de albañilería ----
with paso2:
    c1, c2 = st.columns(2)
    nombre_unidad = c1.selectbox("Tipo de unidad", list(CATALOGO))
    aparejo = c2.selectbox("Aparejo", APAREJOS)
    if CATALOGO[nombre_unidad] is None:
        p1, p2, p3, p4 = st.columns(4)
        ul = p1.number_input("Largo (cm)", 5.0, 60.0, 24.0, 0.5)
        ua = p2.number_input("Ancho (cm)", 5.0, 40.0, 13.0, 0.5)
        uh = p3.number_input("Alto (cm)", 3.0, 30.0, 9.0, 0.5)
        tp = p4.selectbox("Material", ["ladrillo", "pandereta", "bloqueta"])
        unidad = (ul, ua, uh, tp, tp != "pandereta")
    else:
        unidad = CATALOGO[nombre_unidad]
    consumo = consumo_por_m2(unidad, junta, aparejo, dosificacion)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Unidades por m²", f"{consumo['unidades_m2']:.2f}")
    k2.metric("Espesor del muro", f"{consumo['espesor'] * 100:.0f} cm")
    k3.metric("Cemento por m²", f"{consumo['cemento_m2']:.3f} bolsas")
    k4.metric("Arena por m²", f"{consumo['arena_m2']:.4f} m³")

# ---- 7.4 Stock del usuario ----
with paso3:
    st.markdown("Ingrese lo que ya tiene en obra; se descontará de la compra.")
    c1, c2, c3 = st.columns(3)
    stock = {
        "Unidad": c1.number_input("Ladrillos / bloquetas (und)", 0, 100000, 0, 10),
        "Cemento": c2.number_input("Cemento (bolsas de 42.5 kg)", 0, 10000, 0, 1),
        "Arena": c3.number_input("Arena gruesa (m³)", 0.0, 1000.0, 0.0, 0.5),
    }
    cobertura = cobertura_stock(stock, consumo, desperdicio)
    k1, k2, k3 = st.columns(3)
    k1.metric("Con sus ladrillos alcanza", f"{cobertura['Unidad']:.2f} m²")
    k2.metric("Con su cemento alcanza", f"{cobertura['Cemento']:.2f} m²")
    k3.metric("Con su arena alcanza", f"{cobertura['Arena']:.2f} m²")

# ---- 7.5 Precios de las tiendas ----
with paso4:
    st.markdown("Precios referenciales de Lima (nov. 2026). **Reemplácelos por sus cotizaciones.**")

    def editor_tienda(titulo, base, clave):
        datos = dict(base)
        datos["Unidad"] = list(base["Unidad"])
        if unidad[3] != "ladrillo":
            ref = PRECIO_UNIDAD_REF[unidad[3]]
            datos["Unidad"] = [ref, round(ref * base["Unidad"][1] / base["Unidad"][0], 2), base["Unidad"][2]]
        df = pd.DataFrame(
            [[m, datos[m][0], datos[m][1], datos[m][2]] for m in ["Unidad", "Cemento", "Arena"]],
            columns=["Material", "Precio normal (S/)", "Precio por mayor (S/)", "Mínimo para mayor"])
        st.subheader(titulo)
        df = st.data_editor(df, key=clave, disabled=["Material"], hide_index=True, width="stretch")
        precios = {}
        for _, f in df.iterrows():
            precios[f["Material"]] = [float(f["Precio normal (S/)"]), float(f["Precio por mayor (S/)"]),
                                      float(f["Mínimo para mayor"])]
        return precios

    c1, c2 = st.columns(2)
    with c1:
        precios_a = editor_tienda("🏪 Tienda A · Ferretería (por menor)", PRECIOS_TIENDA_A, f"ta_{unidad[3]}")
    with c2:
        precios_b = editor_tienda("🏭 Tienda B · Distribuidora (por mayor)", PRECIOS_TIENDA_B, f"tb_{unidad[3]}")
    st.caption("Unidades: ladrillo/bloqueta por unidad, cemento por bolsa, arena por m³. "
               "Tienda A: precios Sodimac. Tienda B y bloqueta: valores de ejemplo, cotizar.")

# ---- 7.6 Resultados ----
with paso5:
    if errores_muros:
        st.error("Corrija los errores de los muros antes de ver los resultados.")
        st.stop()

    area_bruta_total = sum(m["area_bruta"] for m in muros)
    area_ab_total = sum(m["area_ab"] for m in muros)
    area_total = sum(m["area_neta"] for m in muros)
    necesario = materiales_totales(area_total, consumo, desperdicio)
    compra = materiales_a_comprar(necesario, stock)
    total_a, det_a = costo_en_tienda(compra, precios_a)
    total_b, det_b = costo_en_tienda(compra, precios_b)
    total_mix, eleccion = compra_mixta(det_a, det_b)
    mejor, mensajes = asistente_compra(area_total, umbral, total_a, total_b, total_mix, eleccion)
    avisos = asistente_tecnico(unidad, tipo_muro, zona, muros, desperdicio, junta_cm)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Área neta total", f"{area_total:.2f} m²")
    k2.metric("Unidades a comprar", f"{compra['Unidad']:,.0f}")
    k3.metric("Cemento a comprar", f"{compra['Cemento']:.0f} bolsas")
    k4.metric("Arena a comprar", f"{compra['Arena']:.1f} m³")
    k5.metric("Mejor costo", f"S/ {min(total_a, total_b):,.2f}", mejor)

    st.subheader("🤖 Asistente inteligente")
    for m in mensajes:
        st.success(m)
    for nivel, texto in avisos:
        getattr(st, nivel)(texto)

    st.subheader("📐 Muros")
    st.dataframe(pd.DataFrame([{
        "Muro": m["nombre"], "Largo (m)": m["largo"], "Alto (m)": m["alto"],
        "Área bruta (m²)": round(m["area_bruta"], 3), "Aberturas (m²)": round(m["area_ab"], 3),
        "Área neta (m²)": round(m["area_neta"], 3),
        "Unidades": redondear_arriba(m["area_neta"] * consumo["unidades_m2"] * (1 + desperdicio / 100)),
    } for m in muros]), hide_index=True, width="stretch")

    st.subheader("🧱 Materiales")
    st.dataframe(pd.DataFrame([
        {"Material": "Ladrillo / bloqueta (und)", "Necesario": round(necesario["Unidad"], 1),
         "Tengo": stock["Unidad"], "Comprar": compra["Unidad"]},
        {"Material": "Cemento (bolsas 42.5 kg)", "Necesario": round(necesario["Cemento"], 2),
         "Tengo": stock["Cemento"], "Comprar": compra["Cemento"]},
        {"Material": "Arena gruesa (m³)", "Necesario": round(necesario["Arena"], 3),
         "Tengo": stock["Arena"], "Comprar": compra["Arena"]},
        {"Material": "Mortero (m³)", "Necesario": round(necesario["Mortero"], 3), "Tengo": None, "Comprar": None},
    ]), hide_index=True, width="stretch")

    st.subheader("🏪 Comparación de tiendas")
    filas = []
    for mat in ["Unidad", "Cemento", "Arena"]:
        filas.append({"Material": mat, "Cantidad": det_a[mat][0],
                      "Tienda A": f"S/ {det_a[mat][3]:,.2f} ({det_a[mat][2]})",
                      "Tienda B": f"S/ {det_b[mat][3]:,.2f} ({det_b[mat][2]})",
                      "Más barato": f"Tienda {eleccion[mat]}"})
    filas.append({"Material": "TOTAL", "Cantidad": None, "Tienda A": f"S/ {total_a:,.2f}",
                  "Tienda B": f"S/ {total_b:,.2f}", "Más barato": f"Mixta S/ {total_mix:,.2f}"})
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    fig_t = grafico_tiendas(det_a, det_b)
    st.pyplot(fig_t)

    st.subheader("🖼️ Dibujo de los muros")
    figuras_muros = []
    pest = st.tabs([m["nombre"] for m in muros])
    for i in range(len(muros)):
        with pest[i]:
            fig = dibujar_muro(muros[i], unidad, aparejo, junta)
            st.pyplot(fig)
            figuras_muros.append(fig)

    # ---- 7.7 Descarga de la hoja de resultados ----
    lineas = [
        "CALCULADORA DE MATERIALES PARA MUROS - INFORME",
        "Programación Digital CIV-601 · Ingeniería Civil · UCSUR",
        "=" * 78,
        f"Unidad: {nombre_unidad}  ·  Aparejo: {aparejo}",
        f"Tipo de muro: {tipo_muro}  ·  Zona sísmica: {zona}",
        f"Junta: {junta_cm:.1f} cm  ·  Desperdicio: {desperdicio} %  ·  Mortero {dosificacion}",
        "",
        "MUROS",
    ]
    for m in muros:
        lineas.append(f"  {m['nombre']}: {m['largo']:.2f} x {m['alto']:.2f} m | bruta {m['area_bruta']:.2f} | "
                      f"aberturas {m['area_ab']:.2f} | neta {m['area_neta']:.2f} m²")
        for ab in m["aberturas"]:
            lineas.append(f"      - {ab['cantidad']} {ab['tipo']}(s) de {ab['ancho']:.2f} x {ab['alto']:.2f} m")
    lineas += [
        f"  Área bruta total: {area_bruta_total:.2f} m²   Aberturas: {area_ab_total:.2f} m²   "
        f"ÁREA NETA: {area_total:.2f} m²",
        "",
        "CONSUMO POR m²",
        f"  Unidades: {consumo['unidades_m2']:.2f}   Mortero: {consumo['mortero_m2']:.4f} m³   "
        f"Cemento: {consumo['cemento_m2']:.3f} bolsas   Arena: {consumo['arena_m2']:.4f} m³",
        "",
        "MATERIALES              NECESARIO        TENGO      COMPRAR",
        f"  Unidades (und)      {necesario['Unidad']:>11.1f} {stock['Unidad']:>12} {compra['Unidad']:>12,.0f}",
        f"  Cemento (bolsas)    {necesario['Cemento']:>11.2f} {stock['Cemento']:>12} {compra['Cemento']:>12.0f}",
        f"  Arena (m³)          {necesario['Arena']:>11.3f} {stock['Arena']:>12.1f} {compra['Arena']:>12.1f}",
        f"  Mortero (m³)        {necesario['Mortero']:>11.3f}",
        "",
        "COMPARACIÓN DE TIENDAS",
    ]
    for mat in ["Unidad", "Cemento", "Arena"]:
        lineas.append(f"  {mat:<8} A: S/ {det_a[mat][3]:>10,.2f} ({det_a[mat][2]})   "
                      f"B: S/ {det_b[mat][3]:>10,.2f} ({det_b[mat][2]})")
    lineas += [
        f"  TOTAL    A: S/ {total_a:>10,.2f}   B: S/ {total_b:>10,.2f}   Mixta: S/ {total_mix:,.2f}",
        "",
        "ASISTENTE INTELIGENTE",
    ]
    for m in mensajes:
        lineas.append("  * " + m.replace("**", ""))
    for _, texto in avisos:
        lineas.append("  ! " + texto)
    lineas += ["", "Nota: estimación preliminar; no reemplaza planos ni especificaciones técnicas."]

    pdf = generar_pdf(lineas, [fig_t] + figuras_muros)
    c1, c2 = st.columns(2)
    c1.download_button("📄 Descargar hoja de resultados (PDF)", pdf, "hoja_resultados_muros.pdf",
                       "application/pdf", width="stretch")
    c2.download_button("📊 Descargar materiales (CSV)",
                       pd.DataFrame(filas).to_csv(index=False).encode("utf-8"),
                       "comparacion_tiendas.csv", "text/csv", width="stretch")
