import socket
import threading
import itertools

#Configuracion del proxy
PROXY_HOST = "0.0.0.0" # Escuchar en todas las interfaces de red
PROXY_PORT = 5000 # Usar el puerto 5000

#Lista de servidores disponibles
servers = []
lock = threading.Lock()

#Funcion para manejar las conexiones de los clientes (ESP32)
def handle_client(client_socket, client_adress):
    print(f"[CLIENT CONNECTED] {client_adress}")
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break

            #Seleccion de servidor con Round Robin
            with lock:
                if not servers:
                    print("[ERROR] No servers available")
                    client_socket.sedn(b"No servers available")
                    continue
                server_address = next(itertools.cycle(servers))

            #Enviar datos al servidor seleccionado
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect(server_address)
            server_socket.sendall(data)

            #Recibir respuestas del servidor y enviarla al cliente
            response = server_socket.recv(1024)
            client_socket.send(response)
            server_socket.close()
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    client_socket.close()
    print(f"[CLIENT DISCONNECTED] {client_adress}")

#Funcion para manejar las conexiones de servidores
def handle_server(server_socket, server_address):
    print(f"[SERVER REGISTERED] {server_address}")
    with lock:
        servers.append(server_address)
    while True:
        try:
            data = server_socket.recv(1024)
            if not data:
                break
        except Exception as e:
            print(f"[ERROR] {e}")
            break
    with lock:
        servers.remove(server_address)
    server_socket.close()
    print(f"[SERVER DISCONNECTED] {server_address}")

#Iniciar el proxy
def start_proxy():
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((PROXY_HOST, PROXY_PORT))
    proxy_socket.listen()
    print(f"[PROXY STARTED] Listening on {PROXY_HOST}:{PROXY_PORT}")

    while True:
        client_socket, client_address = proxy_socket.accept()
        client_type = client_socket.recv(1024).decode()

        if client_type == "server":
            threading.Thread(target=handle_server, args=(client_socket, client_address)).start()
        else:
            threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

if __name__ == "__main__":
    start_proxy()
        