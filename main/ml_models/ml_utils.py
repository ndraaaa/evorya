import joblib

# Load model yang sudah dilatih
model = joblib.load('main/ml_models/model_ai_kecurangan.pkl')

def prediksi_ai(fitur):
    hasil = model.predict([fitur])
    return int(hasil[0])
