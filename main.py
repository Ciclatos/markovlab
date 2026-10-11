
import numpy as np
import pymupdf


# Leer el PDF
def extraer_texto_pdf(ruta_pdf):
    documento = pymupdf.open(stream=ruta_pdf, filetype="pdf")
    texto = ""

    for pagina in documento:
        texto += pagina.get_text()

    documento.close()
    return texto


# Clasificar vocales y consonantes
def clasificar_texto(texto):
    vocales = "aeiouáéíóúü"
    consonantes = "bcdfghjklmnñpqrstvwxyz"
    secuencia = ""

    for letra in texto.lower():
        if letra in vocales:
            secuencia += "V"
        elif letra in consonantes:
            secuencia += "C"

    return secuencia


# Contar las transiciones
def contar_transiciones(secuencia):
    frecuencias = {
        "VV": 0,
        "VC": 0,
        "CV": 0,
        "CC": 0
    }

    for i in range(len(secuencia) - 1):
        transicion = secuencia[i] + secuencia[i + 1]
        frecuencias[transicion] += 1

    return frecuencias


# Calcular la matriz de transición
def calcular_matriz(frecuencias):
    total_v = frecuencias["VV"] + frecuencias["VC"]
    total_c = frecuencias["CV"] + frecuencias["CC"]

    if total_v == 0 or total_c == 0:
        raise ValueError("Se necesitan transiciones desde ambos estados.")

    matriz = [
        [
            frecuencias["VV"] / total_v,
            frecuencias["VC"] / total_v
        ],
        [
            frecuencias["CV"] / total_c,
            frecuencias["CC"] / total_c
        ]
    ]

    return matriz


# Probabilidades a varios pasos
def calcular_pasos(matriz, n):
    matriz_numpy = np.array(matriz)
    resultado = np.linalg.matrix_power(matriz_numpy, n)

    return resultado


# Distribución estacionaria
def calcular_estacionaria(matriz):
    a = matriz[0][1]
    b = matriz[1][0]

    if a + b == 0:
        raise ValueError("No existe una distribución estacionaria única.")

    pi_v = b / (a + b)
    pi_c = a / (a + b)

    return [pi_v, pi_c]


# Ejecutar el análisis
def main():
    print("\n========== MARKOVLAB ==========")

    texto = extraer_texto_pdf("prueba.pdf")
    secuencia = clasificar_texto(texto)
    frecuencias = contar_transiciones(secuencia)

    # Información del documento
    print("\n--- DOCUMENTO ---")
    print("Caracteres extraídos:", len(texto))
    print("Letras analizadas:", len(secuencia))
    print("Transiciones:", sum(frecuencias.values()))

    print("\nTexto extraído:")
    print(texto[:300])

    print("\nSecuencia V/C:")
    print(secuencia[:100])

    # Frecuencias
    print("\n--- FRECUENCIAS ---")

    for transicion, cantidad in frecuencias.items():
        print(transicion, "=", cantidad)

    total = sum(frecuencias.values())

    print("\nTotal:", total)

    print("\nFrecuencias relativas:")
    for transicion, cantidad in frecuencias.items():
        porcentaje = cantidad / total * 100
        print(f"{transicion}: {porcentaje:.2f}%")

    # Matriz de transición
    matriz = calcular_matriz(frecuencias)

    print("\n--- MATRIZ DE TRANSICIÓN ---")
    print("          V         C")
    print("V ", matriz[0])
    print("C ", matriz[1])

    # Comprobar las filas
    print("\n--- VERIFICACIÓN ---")

    for fila in matriz:
        print("Suma de fila:", round(sum(fila), 6))

    # Potencias de la matriz
    print("\n--- PROBABILIDADES A N PASOS ---")

    for n in range(1, 6):
        resultado = calcular_pasos(matriz, n)
        print(f"\nP^{n}:")
        print(resultado)

    # Estado estacionario
    estacionaria = calcular_estacionaria(matriz)

    print("\n--- DISTRIBUCIÓN ESTACIONARIA ---")
    print(f"Vocales: {estacionaria[0] * 100:.2f}%")
    print(f"Consonantes: {estacionaria[1] * 100:.2f}%")

    print("\n========== FIN ==========")


if __name__ == "__main__":
    main()
