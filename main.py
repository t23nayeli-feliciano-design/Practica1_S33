import io
import json
import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

# Conexión limpia: Boto3 toma automáticamente las credenciales de ~/.aws/credentials
s3_client = boto3.client('s3', region_name='us-east-1')

# Nombre de tu bucket de AWS S3
BUCKET_NAME = 'practica1-s3-nayeli-2026-631880'


def cargar_y_perfilar_s3(file_key: str, is_json: bool = False) -> pd.DataFrame | None:
    """Descarga archivos desde AWS S3 en memoria (RAM) y genera un perfilamiento de datos."""
    print(f"\n==================================================")
    print(f"=== Procesando objeto S3: {file_key} ===")
    print(f"==================================================")

    try:
        # Lectura directa en memoria
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
        body = response['Body'].read()

        if is_json:
            data_json = json.loads(body.decode('utf-8'))
            df = pd.json_normalize(data_json)
        else:
            df = pd.read_csv(io.BytesIO(body))

        # Perfilamiento de Datos
        print(f"\n[1] Dimensiones del dataset:")
        print(f"    Filas: {df.shape[0]} | Columnas: {df.shape[1]}")

        print("\n[2] Perfil de Tipos de Datos:")
        print(df.dtypes)

        print("\n[3] Conteo de Valores Nulos:")
        nulos = df.isnull().sum()
        print(nulos[nulos > 0] if nulos.sum() > 0 else "Sin valores nulos.")

        # Conversión de fechas si existen
        for col in df.columns:
            if 'fecha' in col.lower() or 'date' in col.lower() or 'time' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                    print(f"\n[Ajuste] Columna '{col}' convertida a datetime.")
                except Exception as e:
                    print(f"[Advertencia] No se pudo convertir '{col}': {e}")

        print("\n[4] Estadísticos Descriptivos:")
        if not df.select_dtypes(include=['number']).empty:
            print(df.describe().T)
        else:
            print("No se encontraron variables numéricas.")

        return df

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"[ERROR] El bucket '{BUCKET_NAME}' no existe.")
        elif error_code == 'NoSuchKey':
            print(f"[ERROR] El archivo '{file_key}' no fue encontrado.")
        elif error_code == 'AccessDenied':
            print("[ERROR] Acceso denegado. Revisa credenciales en ~/.aws/credentials.")
        else:
            print(f"[ERROR AWS]: {e}")
        return None
    except BotoCoreError as e:
        print(f"[ERROR BotoCore]: Error de conexión: {e}")
        return None
    except Exception as e:
        print(f"[ERROR Inesperado]: {e}")
        return None


if __name__ == "__main__":
    df_transacciones = cargar_y_perfilar_s3('raw/transacciones.csv', is_json=False)
    df_logs = cargar_y_perfilar_s3('raw/logs_m2m.json', is_json=True)
