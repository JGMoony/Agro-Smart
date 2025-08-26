import pandas as pd

df = pd.read_csv('productos.csv')

# Mostrar filas con categoría vacía
filas_sin_categoria = df[df['category'].isnull() | (df['category'].str.strip() == '')]

print("🔍 Filas sin categoría:")
print(filas_sin_categoria)