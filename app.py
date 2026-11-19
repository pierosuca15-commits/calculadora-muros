# Calculadora de ladrillos, cemento y arena para muros (version web)
# Proyecto EC2 - Programacion Digital

import streamlit as st


# ---------- Parte 1: datos fijos ----------
ladrillo_largo = 0.24      # ladrillo king kong puesto horizontal (en metros)
ladrillo_ancho = 0.12
ladrillo_alto = 0.09
cemento_kg_por_m3 = 364    # mortero 1:4
arena_m3_por_m3 = 1.16
bolsa_kg = 42.5
desperdicio = 5            # en porcentaje


# ---------- Parte 2: funciones de ayuda ----------

# redondea hacia arriba (388.2 -> 389)
def redondear_arriba(x):
    x = round(x, 6)    # quita errores pequenos de decimales
    if x > int(x):
        return int(x) + 1
    return int(x)


# ---------- Parte 3: ingreso de datos ----------
st.title("Calculadora de ladrillos para muros")
st.caption("Proyecto EC2 - Programacion Digital - UCSUR")

n_muros = st.number_input("Cuantos muros tiene la obra?", min_value=1, max_value=50, value=1, step=1)
junta = st.number_input("Junta en cm (normalmente 1.5)", min_value=1.0, max_value=2.0, value=1.5, step=0.1) / 100

total_area = 0
total_ladrillos = 0
total_mortero = 0
hay_error = False

for i in range(int(n_muros)):
    st.subheader(f"Muro {i + 1}")
    c1, c2 = st.columns(2)
    largo = c1.number_input("Largo (m)", min_value=0.1, max_value=100.0, value=5.0, step=0.1, key=f"largo{i}")
    alto = c2.number_input("Alto (m)", min_value=0.1, max_value=10.0, value=2.6, step=0.1, key=f"alto{i}")

    # puertas y ventanas
    n_aberturas = st.number_input("Cuantas puertas o ventanas tiene?", min_value=0, max_value=20,
                                  value=0, step=1, key=f"nab{i}")
    area_aberturas = 0
    for j in range(int(n_aberturas)):
        a1, a2 = st.columns(2)
        ancho = a1.number_input(f"Abertura {j + 1}: ancho (m)", min_value=0.1, max_value=20.0,
                                value=0.9, step=0.1, key=f"ancho{i}_{j}")
        alto_ab = a2.number_input(f"Abertura {j + 1}: alto (m)", min_value=0.1, max_value=10.0,
                                  value=2.1, step=0.1, key=f"altoab{i}_{j}")
        area_aberturas = area_aberturas + ancho * alto_ab

    if area_aberturas >= largo * alto:
        st.error(f"Muro {i + 1}: las puertas y ventanas tapan todo el muro")
        hay_error = True

    area_neta = largo * alto - area_aberturas
    st.write(f"Area neta del muro {i + 1}: {area_neta:.2f} m2")

    # ladrillo puesto horizontal: se ve el largo y el muro tiene el ancho de espesor
    ladrillos_m2 = 1 / ((ladrillo_largo + junta) * (ladrillo_alto + junta))
    mortero_m2 = ladrillo_ancho - ladrillos_m2 * ladrillo_largo * ladrillo_ancho * ladrillo_alto

    total_area = total_area + area_neta
    total_ladrillos = total_ladrillos + area_neta * ladrillos_m2
    total_mortero = total_mortero + area_neta * mortero_m2


# ---------- Parte 4: resultados ----------
st.divider()
if st.button("Calcular", type="primary"):
    if hay_error:
        st.error("Corrija las medidas de las puertas y ventanas antes de calcular")
    else:
        factor = 1 + desperdicio / 100
        ladrillos = redondear_arriba(total_ladrillos * factor)
        mortero = total_mortero * factor
        bolsas = redondear_arriba(mortero * cemento_kg_por_m3 / bolsa_kg)
        arena = mortero * arena_m3_por_m3

        st.header("Resultados")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Area neta total", f"{total_area:.2f} m2")
        r2.metric("Ladrillos", ladrillos)
        r3.metric("Bolsas de cemento", bolsas)
        r4.metric("Arena gruesa", f"{arena:.2f} m3")
        st.caption("Es una estimacion: el mortero real puede ser un poco mas.")
