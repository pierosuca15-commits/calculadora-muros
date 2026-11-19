# =============================================================================
#  PROYECTO EC2 · CALCULADORA DE LADRILLOS Y MORTERO PARA MUROS
#  Programación Digital CIV-601 · Ingeniería Civil · UCSUR
#  Docente: Choy Samalvides, Julio Carlos Alonso
#  Integrantes: Jheison Pari Condori · Suca Antachoque Piero Aldair ·
#               Anjhelo David Chavez Cantaro · Yorleni Esmith Cordova Tocto ·
#               Giancarlo Chavez Huamani
#
#  Fórmulas (sección 5 del EC2):
#   Área neta        = largo × altura − área total de aberturas
#   Área modular     = (largo ladrillo + junta) × (altura ladrillo + junta)
#   Cantidad base    = área neta ÷ área modular
#   Cantidad final   = redondear hacia arriba [cantidad base × (1 + desperdicio/100)]
#   Mortero          = área neta × espesor del muro × (1 − ladrillos por m² × largo × altura)
#                      × (1 + desperdicio/100)
#   Supuesto del mortero: ladrillo macizo colocado de soga (su profundidad es
#   igual al espesor del muro). Contrastar con la ficha técnica del fabricante.
#   Costo total      = ladrillos × precio unitario + mortero × precio por m³
# =============================================================================


# =============================================================================
# PARTE 1 · VALIDACIÓN DE DATOS
# =============================================================================
def es_numero(texto):
    if len(texto) == 0 or texto == ".":
        return False
    puntos = 0
    for c in texto:
        if c == ".":
            puntos = puntos + 1
        elif c < "0" or c > "9":
            return False
    return puntos <= 1


def leer_numero(mensaje, minimo, maximo):
    texto = input(mensaje).strip().replace(",", ".")
    while not es_numero(texto) or float(texto) < minimo or float(texto) > maximo:
        if len(texto) == 0:
            print("   ⚠ El campo está vacío.")
        elif not es_numero(texto):
            print("   ⚠ Ingrese solo números positivos (use punto decimal).")
        else:
            print(f"   ⚠ El valor debe estar entre {minimo} y {maximo}.")
        texto = input(mensaje).strip().replace(",", ".")
    return float(texto)


def leer_entero(mensaje, minimo, maximo):
    valor = leer_numero(mensaje, minimo, maximo)
    while valor != int(valor):
        print("   ⚠ Ingrese un número entero.")
        valor = leer_numero(mensaje, minimo, maximo)
    return int(valor)


def leer_opcion(mensaje, opciones):
    for i in range(len(opciones)):
        print(f"   {i + 1}. {opciones[i]}")
    op = leer_entero(mensaje, 1, len(opciones))
    return opciones[op - 1]


def redondear_arriba(x):
    x = round(x, 6)
    if x > int(x):
        return int(x) + 1
    return int(x)


# =============================================================================
# PARTE 2 · INGRESO DE DATOS
# =============================================================================
def ingresar_muro():
    print("\n--- 1. DATOS DEL MURO ---")
    largo = leer_numero("Largo del muro (m): ", 0.1, 100)
    altura = leer_numero("Altura del muro (m): ", 0.1, 10)
    espesor = leer_numero("Espesor del muro (m, ej. 0.13): ", 0.05, 0.50)
    tipo_muro = leer_opcion("Tipo de muro: ", ("Tabique (no portante)", "Muro portante"))
    return largo, altura, espesor, tipo_muro


def ingresar_aberturas(largo, altura):
    print("\n--- 2. PUERTAS Y VENTANAS ---")
    area_muro = largo * altura
    aberturas = []
    area_total = 0
    n = leer_entero("¿Cuántos tipos de puertas o ventanas tiene? (0 = ninguna): ", 0, 10)
    i = 0
    while i < n:
        print(f"Abertura {i + 1}")
        tipo = leer_opcion("  Tipo: ", ("Puerta", "Ventana"))
        ancho = leer_numero("  Ancho (m): ", 0.1, largo)
        alto = leer_numero("  Alto (m): ", 0.1, altura)
        cantidad = leer_entero("  Cantidad: ", 1, 20)
        area = ancho * alto * cantidad
        if area_total + area >= area_muro:
            print("   ⚠ Las aberturas no pueden igualar ni superar el área del muro. Ingrésela de nuevo.")
        else:
            aberturas.append([tipo, ancho, alto, cantidad, area])
            area_total = area_total + area
            i = i + 1
    return aberturas


def ingresar_ladrillo():
    print("\n--- 3. LADRILLO Y JUNTAS ---")
    tipo_ladrillo = leer_opcion("Tipo de ladrillo: ",
                                ("King Kong 18 huecos", "Pandereta", "Macizo", "Otro"))
    disposicion = leer_opcion("Disposición del ladrillo: ", ("Soga", "Cabeza", "Canto"))
    largo_lad = leer_numero("Largo del ladrillo (m, ej. 0.24): ", 0.05, 0.60)
    alto_lad = leer_numero("Altura del ladrillo (m, ej. 0.09): ", 0.03, 0.40)
    junta = leer_numero("Espesor de junta (m, ej. 0.015): ", 0.005, 0.03)
    return tipo_ladrillo, disposicion, largo_lad, alto_lad, junta


def ingresar_desperdicio_y_precios():
    print("\n--- 4. DESPERDICIO, MORTERO Y PRECIOS ---")
    desperdicio = leer_numero("Desperdicio (%, ej. 5): ", 0, 50)
    tipo_mortero = leer_opcion("Tipo de mortero: ",
                               ("Cemento-arena 1:4", "Cemento-arena 1:5", "Otro"))
    precio_ladrillo = leer_numero("Precio por ladrillo (S/ por unidad): ", 0, 100)
    precio_mortero = leer_numero("Precio del mortero (S/ por m³): ", 0, 5000)
    return desperdicio, tipo_mortero, precio_ladrillo, precio_mortero


# =============================================================================
# PARTE 3 · CÁLCULOS
# =============================================================================
def calcular_area_neta(largo, altura, aberturas):
    area_bruta = largo * altura
    area_aberturas = 0
    for a in aberturas:
        area_aberturas = area_aberturas + a[4]
    return area_bruta, area_aberturas, area_bruta - area_aberturas


def calcular_ladrillos(area_neta, largo_lad, alto_lad, junta, desperdicio):
    area_modular = (largo_lad + junta) * (alto_lad + junta)
    cantidad_base = area_neta / area_modular
    cantidad_final = redondear_arriba(cantidad_base * (1 + desperdicio / 100))
    return area_modular, cantidad_base, cantidad_final


def calcular_mortero(area_neta, espesor, largo_lad, alto_lad, area_modular, desperdicio):
    ladrillos_m2 = 1 / area_modular
    mortero_m2 = espesor * (1 - ladrillos_m2 * largo_lad * alto_lad)
    mortero_total = mortero_m2 * area_neta * (1 + desperdicio / 100)
    return mortero_m2, mortero_total


def calcular_costos(cantidad, precio_ladrillo, mortero, precio_mortero):
    costo_ladrillos = cantidad * precio_ladrillo
    costo_mortero = mortero * precio_mortero
    return costo_ladrillos, costo_mortero, costo_ladrillos + costo_mortero


# =============================================================================
# PARTE 4 · RESUMEN DE RESULTADOS
# =============================================================================
def mostrar_resumen(muro, aberturas, ladrillo, datos, areas, lad, mortero, costos):
    largo, altura, espesor, tipo_muro = muro
    tipo_ladrillo, disposicion, largo_lad, alto_lad, junta = ladrillo
    desperdicio, tipo_mortero, precio_ladrillo, precio_mortero = datos

    print("\n" + "=" * 60)
    print("                 RESUMEN DE LA ESTIMACIÓN")
    print("=" * 60)
    print("DATOS INGRESADOS")
    print(f"  Muro: {largo:.2f} m × {altura:.2f} m · espesor {espesor:.2f} m · {tipo_muro}")
    print(f"  Ladrillo: {tipo_ladrillo} ({largo_lad:.3f} × {alto_lad:.3f} m) · disposición {disposicion}")
    print(f"  Junta: {junta:.3f} m · Desperdicio: {desperdicio:.0f} % · Mortero {tipo_mortero}")
    if len(aberturas) == 0:
        print("  Aberturas: ninguna")
    else:
        for a in aberturas:
            print(f"  - {a[3]} {a[0]}(s) de {a[1]:.2f} × {a[2]:.2f} m = {a[4]:.2f} m²")
    print("-" * 60)
    print("ÁREAS")
    print(f"  Área bruta del muro ......... {areas[0]:10.3f} m²")
    print(f"  Área de aberturas ........... {areas[1]:10.3f} m²")
    print(f"  ÁREA NETA ................... {areas[2]:10.3f} m²")
    print("-" * 60)
    print("LADRILLOS")
    print(f"  Área modular ................ {lad[0]:10.5f} m²")
    print(f"  Ladrillos por m² ............ {1 / lad[0]:10.2f}")
    print(f"  Cantidad base ............... {lad[1]:10.1f}")
    print(f"  CANTIDAD FINAL .............. {lad[2]:10} und")
    print("-" * 60)
    print("MORTERO")
    print(f"  Mortero por m² .............. {mortero[0]:10.4f} m³/m²")
    print(f"  VOLUMEN DE MORTERO .......... {mortero[1]:10.3f} m³")
    print("-" * 60)
    print("COSTOS")
    print(f"  Ladrillos ({lad[2]} × S/ {precio_ladrillo:.2f}) ....... S/ {costos[0]:10.2f}")
    print(f"  Mortero ({mortero[1]:.3f} m³ × S/ {precio_mortero:.2f}) .. S/ {costos[1]:10.2f}")
    print(f"  COSTO TOTAL ................. S/ {costos[2]:10.2f}")
    print("=" * 60)
    print("Supuestos: ladrillo macizo colocado de soga; el mortero se estima por")
    print("geometría y debe contrastarse con la ficha técnica del fabricante.")
    print("Estimación preliminar: no reemplaza planos ni la revisión profesional.")


# =============================================================================
# PARTE 5 · PROGRAMA PRINCIPAL
# =============================================================================
def main():
    print("=" * 60)
    print("     🧱 CALCULADORA DE LADRILLOS Y MORTERO PARA MUROS")
    print("        Proyecto EC2 · Programación Digital · UCSUR")
    print("=" * 60)

    while True:
        muro = ingresar_muro()
        aberturas = ingresar_aberturas(muro[0], muro[1])
        ladrillo = ingresar_ladrillo()
        datos = ingresar_desperdicio_y_precios()

        areas = calcular_area_neta(muro[0], muro[1], aberturas)
        lad = calcular_ladrillos(areas[2], ladrillo[2], ladrillo[3], ladrillo[4], datos[0])
        mortero = calcular_mortero(areas[2], muro[2], ladrillo[2], ladrillo[3], lad[0], datos[0])
        costos = calcular_costos(lad[2], datos[2], mortero[1], datos[3])

        mostrar_resumen(muro, aberturas, ladrillo, datos, areas, lad, mortero, costos)

        otra = input("\n¿Desea calcular otro muro? (s/n): ").strip().lower()
        while otra != "s" and otra != "n":
            otra = input("   Responda s o n: ").strip().lower()
        if otra == "n":
            print("\n¡Gracias por usar la calculadora!")
            break


main()
