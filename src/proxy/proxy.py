from fastapi import FastAPI, UploadFile, File
import httpx
import itertools

app = FastAPI()

# Lista de servidores disponibles
SERVERS = ["http://127.0.0.1:8001/predict/", "http://127.0.0.1:8002/predict/"]
server_iterator = itertools.cycle(SERVERS)  # Round-robin iterator

@app.post("/predict/")
async def proxy_predict(file: UploadFile = File(...)):
    server_url = next(server_iterator)  
    
    # Enviar el archivo al servidor seleccionado
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        response = await client.post(server_url, files=files)
    
    return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
