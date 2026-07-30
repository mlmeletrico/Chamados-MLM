from flask import Flask, render_template, redirect, request, session, url_for, jsonify
from datetime import datetime
from zoneinfo import ZoneInfo
FUSO = Zeneinfo("America/Sao_paulo")
def agora ():
    return datetime.now(FUSO) 
import sqlite3
import socket

# 🔥 FUSO BRASIL
FUSO = ZoneInfo("America/Sao_Paulo")

def agora():
    return datetime.now(FUSO).strftime("%d/%m/%Y %H:%M:%S")

app = Flask(__name__)
app.secret_key = "chamados123"

USUARIOS = {
    "renan": "123",
    "wallison": "123"
}

BANCO = "chamados.db"

def conectar():
    conn = sqlite3.connect(BANCO)
    conn.row_factory = sqlite3.Row
    return conn

def obter_nome_maquina(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "Não identificado"

def definir_prioridade(titulo, descricao, categoria=""):
    texto = f"{titulo} {descricao} {categoria}".lower()

    palavras_alta = ["servidor", "sem internet", "urgente", "não funciona"]
    palavras_media = ["lento", "erro", "senha", "problema"]

    if any(p in texto for p in palavras_alta):
        return "Alta"
    if any(p in texto for p in palavras_media):
        return "Média"
    return "Baixa"

def criar_banco():
    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            nome TEXT,
            setor TEXT,
            descricao TEXT,
            categoria TEXT,
            prioridade TEXT,
            status TEXT,
            tecnico TEXT,
            inicio TEXT,
            fim TEXT,
            tempo TEXT,
            data TEXT,
            ip TEXT,
            nome_maquina TEXT,
            navegador TEXT
        )
    """)
    conn.commit()
    conn.close()

criar_banco()

@app.route("/")
def index():
    if "tecnico" not in session:
        return redirect("/login")

    conn = conectar()
    chamados = conn.execute("""
        SELECT * FROM chamados
        WHERE status != 'Concluído'
        ORDER BY id DESC
    """).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
    abertos = conn.execute("SELECT COUNT(*) FROM chamados WHERE status='Recebido'").fetchone()[0]
    andamento = conn.execute("SELECT COUNT(*) FROM chamados WHERE status='Em atendimento'").fetchone()[0]
    concluidos = conn.execute("SELECT COUNT(*) FROM chamados WHERE status='Concluído'").fetchone()[0]

    conn.close()

    return render_template("index.html",
        chamados=chamados,
        tecnico=session["tecnico"],
        total=total,
        abertos=abertos,
        andamento=andamento,
        concluidos=concluidos
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = ""

    if request.method == "POST":
        user = request.form["usuario"]
        senha = request.form["senha"]

        if user in USUARIOS and USUARIOS[user] == senha:
            session["tecnico"] = user.capitalize()
            return redirect("/")

        erro = "Login inválido"

    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/cliente", methods=["GET", "POST"])
def cliente():
    if request.method == "POST":
        titulo = request.form["titulo"]
        nome = request.form["nome"]
        setor = request.form["setor"]
        descricao = request.form["descricao"]
        categoria = request.form["categoria"]

        prioridade = definir_prioridade(titulo, descricao, categoria)

        ip = request.remote_addr
        nome_maquina = obter_nome_maquina(ip)
        navegador = request.headers.get("User-Agent")

        conn = conectar()
        conn.execute("""
            INSERT INTO chamados (
                titulo, nome, setor, descricao, categoria,
                prioridade, status, tecnico, inicio, fim, tempo,
                data, ip, nome_maquina, navegador
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            titulo, nome, setor, descricao, categoria,
            prioridade, "Recebido", "", "", "", "",
            agora(), ip, nome_maquina, navegador
        ))
        conn.commit()
        conn.close()

        return render_template("cliente.html", sucesso=True)

    return render_template("cliente.html")

@app.route("/status/<int:id>/<acao>")
def status(id, acao):
    if "tecnico" not in session:
        return redirect("/login")

    conn = conectar()
    chamado = conn.execute("SELECT * FROM chamados WHERE id=?", (id,)).fetchone()

    if acao == "atendimento":
        conn.execute("""
            UPDATE chamados SET status=?, tecnico=?, inicio=?
            WHERE id=?
        """, ("Em atendimento", session["tecnico"], agora(), id))

    elif acao == "concluido":
        fim = agora()

        tempo = ""
        if chamado["inicio"]:
            inicio_dt = datetime.strptime(chamado["inicio"], "%d/%m/%Y %H:%M:%S")
            fim_dt = datetime.strptime(fim, "%d/%m/%Y %H:%M:%S")

            diff = fim_dt - inicio_dt
            s = int(diff.total_seconds())

            tempo = f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

        conn.execute("""
            UPDATE chamados
            SET status=?, tecnico=?, fim=?, tempo=?
            WHERE id=?
        """, ("Concluído", session["tecnico"], fim, tempo, id))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/historico")
def historico():
    if "tecnico" not in session:
        return redirect("/login")

    conn = conectar()

    chamados = conn.execute("""
        SELECT * FROM chamados
        WHERE status='Concluído'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("historico.html", chamados=chamados)

@app.route("/api/chamados_info")
def api():
    conn = conectar()
    total = conn.execute("SELECT COUNT(*) FROM chamados WHERE status!='Concluído'").fetchone()[0]
    alta = conn.execute("SELECT COUNT(*) FROM chamados WHERE prioridade='Alta' AND status!='Concluído'").fetchone()[0]
conn.close()
return jsonify({"total": total, "alta": alta})

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    chamados = []
    buscou = False

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        buscou = True

        if nome:
            conn = conectar()

if __name__ == "__main__":
    app.run(debug=True)
