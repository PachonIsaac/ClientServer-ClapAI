from fastapi import FastAPI, UploadFile, File
import numpy as np
import torch
import librosa
import soundfile as sf
from predict import transform_audio, load_model

app = FastAPI()

# Cargar el modelo entrenado
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = load_model("audio_classifier.pth").to(device)
model.eval()

classes = {0: "Noise", 1: "Clap"}

@app.post("/predict/")
async def predict_audio(file: UploadFile = File(...)):
    # Leer el archivo de audio recibido
    audio_data, sample_rate = sf.read(file.file)
    
    # Guardar temporalmente el archivo para preprocesarlo
    temp_filename = "temp.wav"
    sf.write(temp_filename, audio_data, sample_rate)
    
    # Convertir el audio a espectrograma
    spec = transform_audio(temp_filename).to(device)
    
    with torch.no_grad():
        output = model(spec)
        prediction = torch.argmax(output, dim=1).item()
        probabilities = torch.softmax(output, dim=1)
        predicted_prob = probabilities[0][prediction].item()
    
    return {
        "prediction": classes[prediction],
        "confidence": f"{predicted_prob * 100:.2f}%"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
