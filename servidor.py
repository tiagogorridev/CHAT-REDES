import socket
import threading

clientes = {}  # Dicionário que armazena os clientes conectados (socket -> nome_usuario)
lock = (
    threading.Lock()
)  # Lock para proteger o acesso ao dicionário de clientes em operações simultâneas


def handle_cliente(cliente_socket, endereco_cliente):
    """Gerencia as mensagens recebidas de um cliente."""
    try:
        # Recebe o nome do usuário enviado pelo cliente
        nome_usuario = cliente_socket.recv(1024).decode()

        with lock:
            # Verifica se o nome do usuário já está em uso
            if nome_usuario in clientes.values():
                # Envia uma mensagem de erro para o cliente caso o nome esteja em uso
                cliente_socket.sendall(
                    "Erro: Já existe um usuário ativo com esse nome.\n".encode()
                )
                cliente_socket.close()  # Fecha a conexão com o cliente
                return  # Sai da função

            # Adiciona o cliente ao dicionário de clientes conectados
            clientes[cliente_socket] = nome_usuario
            # Log dos clientes conectados para o console do servidor
            print(
                f"[Servidor] Clientes conectados: {[clientes[s] for s in clientes.keys()]}"
            )

        # Captura o IP e a porta do cliente
        ip, porta = endereco_cliente
        # Formata a mensagem de entrada do cliente com IP e porta
        mensagem_entrada = f"{nome_usuario} entrou no chat. (IP: {ip}, Porta: {porta})"

        # Envia uma mensagem de boas-vindas com IP e porta para o próprio cliente
        cliente_socket.sendall(
            f"Bem-vindo, {nome_usuario}! Seu IP: {ip}, Porta: {porta}\n".encode()
        )

        # Envia uma mensagem de confirmação de conexão ao servidor
        cliente_socket.sendall("Conectado ao servidor.\n".encode())
        # Envia a lista de usuários ativos para o cliente
        enviar_usuarios_ativos(cliente_socket)

        # Envia a mensagem de entrada para todos os outros clientes
        broadcast(mensagem_entrada, cliente_socket)
        # Exibe a mensagem de entrada no console do servidor
        print(mensagem_entrada)

        # Loop para receber mensagens do cliente
        while True:
            # Aguarda e recebe mensagens enviadas pelo cliente
            mensagem = cliente_socket.recv(1024).decode()
            if mensagem:
                # Exibe a mensagem recebida no console do servidor
                print(f"Recebido de {nome_usuario}: {mensagem}")

                # Verifica se o cliente enviou uma mensagem indicando que saiu do chat
                if mensagem.lower() == f"{nome_usuario} saiu do chat.":
                    # Formata a mensagem de saída do cliente
                    mensagem_saida = (
                        f"{nome_usuario} saiu do chat. (IP: {ip}, Porta: {porta})"
                    )
                    # Envia a mensagem de saída para todos os outros clientes
                    broadcast(mensagem_saida, cliente_socket)
                    with lock:
                        # Remove o cliente do dicionário de clientes conectados
                        if cliente_socket in clientes:
                            del clientes[cliente_socket]
                            print(f"[Servidor] Cliente {nome_usuario} removido.")
                    break  # Sai do loop

                # Verifica se a mensagem é privada (começa com "@")
                if mensagem.startswith("@"):
                    # Divide a mensagem para obter o destinatário e o conteúdo
                    destinatario, mensagem_unicast = mensagem[1:].split(" ", 1)
                    # Envia a mensagem privada para o destinatário
                    enviar_unicast(
                        destinatario,
                        f"{nome_usuario} (privado): {mensagem_unicast}",
                        cliente_socket,
                    )
                else:
                    # Envia a mensagem como broadcast para todos os outros clientes
                    broadcast(f"{nome_usuario}: {mensagem}", cliente_socket)
    except (ConnectionResetError, BrokenPipeError):
        # Trata a desconexão inesperada do cliente
        print(f"Conexão perdida com {clientes.get(cliente_socket, 'desconhecido')}")
    finally:
        # Remove o cliente da lista ao desconectar
        with lock:
            if cliente_socket in clientes:
                # Envia uma mensagem de saída para os outros clientes
                broadcast(f"{clientes[cliente_socket]} saiu do chat.", cliente_socket)
                print(f"[Servidor] Removendo cliente {clientes[cliente_socket]}")
                # Remove o cliente do dicionário
                del clientes[cliente_socket]
        try:
            cliente_socket.shutdown(socket.SHUT_RDWR)  # Fecha a conexão completamente
        except Exception:
            pass  # Ignora erros ao fechar o socket
        cliente_socket.close()  # Fecha o socket do cliente


def broadcast(mensagem, cliente_socket):
    """Envia uma mensagem para todos os clientes conectados."""
    with lock:
        # Itera sobre todos os clientes conectados
        for cliente in clientes:
            # Verifica se o cliente atual não é o remetente da mensagem
            if cliente != cliente_socket:
                try:
                    # Envia a mensagem para o cliente
                    cliente.sendall(mensagem.encode())
                except:
                    # Fecha o socket do cliente em caso de erro
                    cliente.close()
                    with lock:
                        # Remove o cliente com erro do dicionário
                        if cliente in clientes:
                            del clientes[cliente]


def enviar_unicast(destinatario, mensagem, remetente_socket):
    """Envia uma mensagem privada ao destinatário e exibe no remetente também."""
    with lock:
        # Obtém o nome do remetente
        remetente_nome = clientes[remetente_socket]
        # Procura pelo destinatário no dicionário de clientes
        for cliente_socket, nome in clientes.items():
            if nome == destinatario:  # Verifica se encontrou o destinatário
                try:
                    # Envia a mensagem para o destinatário
                    cliente_socket.sendall(mensagem.encode())
                    # Envia uma cópia da mensagem para o remetente
                    mensagem_remetente = f"{remetente_nome} (privado para @{destinatario}): {mensagem.split(': ', 1)[1]}"
                    remetente_socket.sendall(mensagem_remetente.encode())
                except Exception:
                    pass
                return  # Sai da função após enviar a mensagem
        # Caso o destinatário não seja encontrado, envia um erro para o remetente
        remetente_socket.sendall(f"Usuário {destinatario} não encontrado.\n".encode())


def enviar_usuarios_ativos(cliente_socket):
    """Envia a lista de usuários ativos para o cliente."""
    with lock:
        # Cria uma lista com os nomes dos usuários conectados
        usuarios = [nome for socket_cliente, nome in clientes.items()]
        # Formata a lista de usuários como uma string separada por quebras de linha
        lista_usuarios = "\n".join(usuarios)
        # Envia a lista de usuários para o cliente
        cliente_socket.sendall(f"Usuários ativos:\n{lista_usuarios}\n".encode())


# Configuração do servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP
servidor.bind(("192.168.1.12", 9999))  # Vincula o socket ao IP e porta do servidor
servidor.listen(5)  # Define o número máximo de conexões pendentes
print(
    f"Servidor iniciado em {servidor.getsockname()}"
)  # Exibe a mensagem de inicialização do servidor

while True:
    # Aceita uma nova conexão de cliente
    cliente_socket, endereco_cliente = servidor.accept()
    print(
        f"Nova conexão de {endereco_cliente}"
    )  # Exibe o endereço do cliente no console

    # Cria uma thread para gerenciar o cliente
    thread = threading.Thread(
        target=handle_cliente, args=(cliente_socket, endereco_cliente)
    )  # Passa o socket e o endereço do cliente como argumentos
    thread.daemon = True  # Define a thread como daemon
    thread.start()  # Inicia a thread
