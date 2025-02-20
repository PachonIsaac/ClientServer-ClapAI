import socket
import torch
import torchaudio
import torchaudio.transforms as T
from torchvision.transforms import Resize
from model import AudioClassifier

#Configuracion del proexy, MAS ADELANTE SE CAMBIARA
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001

#Cargar el modelo
def load_model(model_path):
    model = AudioClassifier()
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

#Transformar el audio a mel spectrogram
def transform_audio(audio_path, n_mels=128, n_fft=400, hop_length=200):
    waveform, sample_rate = torchaudio.load(audio_path)
    spec = T.MelSpectrogram(
        sample_rate=sample_rate,
        n_fft=n_fft,
        win_length=n_fft,
        hop_length=hop_length,
        n_mels=n_mels,
    )(waveform)
    spec = Resize((256, 256))(spec)
    spec = (spec - spec.mean()) / spec.std()  # normalizar el espectrograma
    return spec.unsqueeze(0)  # agregar una dimension

#Hacer una prediccion con el modelo
def predict(model, audio_path):
    spec = transform_audio(audio_path)
    output = model(spec)
    _, predicted = torch.max(output.data, 1)
    return predicted.item()

#Iniciar el servidor socket
def start_server(): 
    model = load_model("audio_classifier.pth")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen()
    print(f"[SERVER STARTED] Listening on {SERVER_HOST}:{SERVER_PORT}")

    #Conectarse al proxy y registrarse
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.connect((PROXY_HOST, PROXY_PORT))
    proxy_socket.send(b"server")
    proxy_socket.close()

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"[CLIENT CONNECTED] {client_address}")
        
        # Recibir datos de audio
        data = client_socket.recv(4096)
        if not data:
            client_socket.close()
            continue
        
        # Guardar temporalmente el audio recibido
        with open("received_audio.wav", "wb") as f:
            f.write(data)
        
        # Realizar predicción
        prediction = predict(model, "received_audio.wav")
        response = str(prediction).encode()
        
        # Enviar respuesta al cliente (proxy)
        client_socket.send(response)
        client_socket.close()
