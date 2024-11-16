import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox

# Configuração do servidor
HOST = "192.168.1.12"  # Endereço IP do servidor
PORT = 9999  # Porta utilizada para a conexão do cliente ao servidor
socket_cliente = None  # Socket do cliente inicializado como None
nome_usuario = ""  # Nome do usuário inicializado vazio


def enviar_mensagem():
    """Função para enviar mensagem quando o botão é clicado ou o Enter é pressionado."""
    global socket_cliente, nome_usuario
    mensagem = (
        entrada_mensagem.get().strip()
    )  # Obtém a mensagem digitada pelo usuário e remove espaços desnecessários
    if mensagem:  # Verifica se a mensagem não está vazia
        try:
            if mensagem.startswith("@"):  # Detecta mensagem privada
                destinatario = mensagem.split(" ")[0][1:]  # Extrai o destinatário
                if (
                    destinatario == nome_usuario
                ):  # Verifica se o destinatário é o próprio usuário
                    lista_chat.config(state=tk.NORMAL)
                    lista_chat.insert(
                        tk.END,
                        "Você não pode enviar mensagens privadas para si mesmo.\n",
                        "erro",
                    )  # Exibe erro na interface
                    lista_chat.config(state=tk.DISABLED)
                    entrada_mensagem.delete(0, tk.END)  # Limpa o campo de entrada
                    return  # Sai da função

            else:
                lista_chat.config(state=tk.NORMAL)
                lista_chat.insert(
                    tk.END, f"Você: {mensagem}\n", "enviado"
                )  # Mostra a mensagem enviada na interface
                lista_chat.config(state=tk.DISABLED)

            socket_cliente.sendall(mensagem.encode())  # Envia a mensagem ao servidor
            entrada_mensagem.delete(0, tk.END)  # Limpa o campo de entrada
            lista_chat.yview(tk.END)  # Rola a interface para mostrar a mensagem enviada
        except Exception as e:
            lista_chat.config(state=tk.NORMAL)
            lista_chat.insert(
                tk.END, f"Erro ao enviar mensagem: {e}\n", "erro"
            )  # Mostra erro caso ocorra
            lista_chat.config(state=tk.DISABLED)


def enviar_mensagem_evento(event):
    """Função para enviar mensagem ao pressionar Enter."""
    enviar_mensagem()  # Chama a função de envio de mensagens


def recebe_mensagens():
    """Recebe mensagens do servidor."""
    global socket_cliente
    while True:
        try:
            mensagem = socket_cliente.recv(
                1024
            ).decode()  # Recebe mensagens do servidor
            if mensagem.startswith("Erro:"):  # Detecta mensagens de erro do servidor
                lista_chat.config(state=tk.NORMAL)
                lista_chat.insert(
                    tk.END, f"{mensagem}\n", "erro"
                )  # Exibe mensagem de erro em vermelho
                lista_chat.config(state=tk.DISABLED)
                messagebox.showerror(
                    "Erro", mensagem.strip()
                )  # Exibe uma caixa de erro
                socket_cliente.close()  # Fecha o socket do cliente

                # Permite ao usuário alterar o nome de usuário
                input_nome.config(state=tk.NORMAL)
                botao_conectar.config(state=tk.NORMAL)
                return  # Encerra a thread para permitir nova tentativa de conexão

            elif (
                mensagem == "Conectado ao servidor.\n"
            ):  # Detecta mensagem de conexão bem-sucedida
                lista_chat.config(state=tk.NORMAL)
                lista_chat.insert(
                    tk.END, mensagem, "conexao"
                )  # Exibe mensagem de conexão em azul
                lista_chat.config(state=tk.DISABLED)
            elif mensagem.startswith(
                "Usuários ativos:"
            ):  # Lista de usuários conectados
                lista_chat.config(state=tk.NORMAL)
                lista_chat.insert(tk.END, f"{mensagem}\n", "info")
                lista_chat.config(state=tk.DISABLED)
            elif "(privado)" in mensagem:  # Detecta mensagens privadas
                lista_chat.config(state=tk.NORMAL)
                lista_chat.insert(
                    tk.END, f"{mensagem}\n", "privado"
                )  # Exibe mensagem privada
                lista_chat.config(state=tk.DISABLED)
            else:  # Mensagens gerais
                lista_chat.config(state=tk.NORMAL)
                lista_chat.insert(
                    tk.END, f"{mensagem}\n", "recebido"
                )  # Exibe mensagens públicas
                lista_chat.config(state=tk.DISABLED)
            lista_chat.yview(tk.END)  # Rola para o final da interface
        except Exception:
            lista_chat.config(state=tk.NORMAL)
            lista_chat.insert(
                tk.END, "Erro: conexão perdida.\n", "erro"
            )  # Mostra erro de conexão perdida
            lista_chat.config(state=tk.DISABLED)
            break  # Encerra o loop caso ocorra um erro


def conectar():
    """Conecta o cliente ao servidor."""
    global socket_cliente, nome_usuario
    nome_usuario = input_nome.get().strip()  # Obtém o nome digitado pelo usuário

    # Validações de nome de usuário
    if " " in nome_usuario or "@" in nome_usuario:  # Restringe espaços ou "@" no nome
        label_erro_nome.config(text="O nome não pode conter espaços ou '@'.")
        return
    if not nome_usuario:  # Verifica se o nome não está vazio
        label_erro_nome.config(text="O nome de usuário não pode estar vazio.")
        return

    # Limpa mensagem de erro caso o nome seja válido
    label_erro_nome.config(text="")

    try:
        socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_cliente.connect((HOST, PORT))  # Conecta ao servidor
        socket_cliente.sendall(
            nome_usuario.encode()
        )  # Envia o nome de usuário para o servidor

        # Inicia uma thread para receber mensagens
        thread_recebe = threading.Thread(target=recebe_mensagens)
        thread_recebe.daemon = True
        thread_recebe.start()

        # Ajusta os estados da interface após conexão bem-sucedida
        input_nome.config(state=tk.DISABLED)
        botao_conectar.config(state=tk.DISABLED)
        entrada_mensagem.config(state=tk.NORMAL)
        botao_enviar.config(state=tk.NORMAL)
    except ConnectionRefusedError:
        messagebox.showerror(
            "Erro de Conexão", "O servidor está offline. Tente novamente mais tarde."
        )
        lista_chat.config(state=tk.NORMAL)
        lista_chat.insert(tk.END, "Erro: O servidor não está iniciado.\n", "erro")
        lista_chat.config(state=tk.DISABLED)
    except Exception as e:
        lista_chat.config(state=tk.NORMAL)
        lista_chat.insert(
            tk.END, f"Erro ao conectar: {e}\n", "erro"
        )  # Exibe outros erros
        lista_chat.config(state=tk.DISABLED)


def conectar_evento(event):
    """Função para conectar ao pressionar Enter."""
    conectar()


def desconectar():
    """Desconecta o cliente do servidor e fecha a janela."""
    global socket_cliente
    if socket_cliente:  # Verifica se há uma conexão ativa
        try:
            socket_cliente.sendall(
                f"{nome_usuario} saiu do chat.".encode()
            )  # Notifica saída
        except Exception:
            pass  # Ignora erros ao enviar mensagem de saída
        finally:
            try:
                socket_cliente.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass  # Ignora erros ao fechar o socket
            socket_cliente.close()  # Fecha o socket do cliente
            socket_cliente = None  # Reinicia o socket como None
        lista_chat.config(state=tk.NORMAL)
        lista_chat.insert(
            tk.END, "Desconectado do servidor.\n", "conexao"
        )  # Informa desconexão
        lista_chat.config(state=tk.DISABLED)

    root.destroy()  # Fecha a interface Tkinter


# Configuração da interface gráfica com Tkinter
root = tk.Tk()
root.title("Chat Cliente")  # Título da janela
root.configure(bg="#d9e6f2")  # Cor de fundo azul claro

# Configurações e elementos da interface (rótulos, botões e campos)

# Label e entrada para o nome do usuário
tk.Label(root, text="Informe seu nome:", bg="#d9e6f2", font=("Arial", 12)).pack(
    padx=10, pady=5
)
input_nome = tk.Entry(
    root, width=30, font=("Arial", 12)
)  # Campo para digitar o nome do usuário
input_nome.pack(padx=10, pady=5)

# Label para exibir erros relacionados ao nome do usuário
label_erro_nome = tk.Label(
    root, text="", fg="red", bg="#d9e6f2", font=("Arial", 10)
)  # Mensagens de erro do nome
label_erro_nome.pack(padx=10, pady=5)

# Botão para conectar
botao_conectar = tk.Button(
    root,
    text="Conectar",
    command=conectar,  # Chama a função para conectar
    bg="#4a90e2",
    fg="white",
    font=("Arial", 10, "bold"),
)
botao_conectar.pack(padx=10, pady=5)

# Vinculação do evento Enter ao campo de entrada de nome de usuário
input_nome.bind("<Return>", conectar_evento)  # Permite pressionar Enter para conectar

# Caixa de texto rolável para exibição de mensagens do chat
lista_chat = scrolledtext.ScrolledText(
    root, width=50, height=20, state=tk.DISABLED, bg="#f0f4f8", font=("Arial", 10)
)
lista_chat.pack(padx=10, pady=10)

# Configuração de cores para mensagens
lista_chat.tag_config(
    "enviado", foreground="#4a90e2"
)  # Mensagens enviadas pelo usuário (azul)
lista_chat.tag_config(
    "recebido", foreground="black"
)  # Mensagens recebidas de outros usuários
lista_chat.tag_config(
    "privado", foreground="black"
)  # Mensagens privadas (preto padrão)
lista_chat.tag_config("conexao", foreground="blue")  # Mensagens de conexão (azul claro)
lista_chat.tag_config("erro", foreground="red")  # Mensagens de erro (vermelho)

# Campo para digitar mensagens
entrada_mensagem = tk.Entry(
    root, width=40, state=tk.DISABLED, font=("Arial", 12)
)  # Campo desabilitado inicialmente
entrada_mensagem.pack(padx=10, pady=5)
entrada_mensagem.bind(
    "<Return>", enviar_mensagem_evento
)  # Liga Enter ao envio de mensagens

# Botão para enviar mensagens
botao_enviar = tk.Button(
    root,
    text="Enviar",
    command=enviar_mensagem,  # Chama a função para enviar a mensagem
    state=tk.DISABLED,  # Desabilitado inicialmente
    bg="#4a90e2",
    fg="white",
    font=("Arial", 10, "bold"),
)
botao_enviar.pack(padx=10, pady=5)

# Botão para desconectar
botao_sair = tk.Button(
    root,
    text="Sair",
    command=desconectar,  # Chama a função para desconectar e fechar a interface
    bg="#4a90e2",
    fg="white",
    font=("Arial", 10, "bold"),
)
botao_sair.pack(padx=10, pady=5)

# Inicia o loop principal da interface gráfica
root.mainloop()
