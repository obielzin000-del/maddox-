from flask import Blueprint, render_template_string, request, redirect, url_for
from urllib.parse import urlparse
from datetime import datetime
import sqlite3
import os


bots_bp = Blueprint("bots", __name__, url_prefix="/bots")


# =========================================================
# BANCO DE DADOS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANCO = os.path.join(BASE_DIR, "grupos.db")


def conectar():

    conexao = sqlite3.connect(BANCO)

    conexao.row_factory = sqlite3.Row

    return conexao


def criar_tabela():

    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS projetos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            descricao TEXT NOT NULL,

            categoria TEXT NOT NULL,

            icone TEXT NOT NULL,

            link TEXT NOT NULL UNIQUE,

            data TEXT NOT NULL

        )
    """)

    conexao.commit()

    conexao.close()


# Cria a tabela automaticamente
criar_tabela()


# =========================================================
# CATEGORIAS
# =========================================================

CATEGORIAS = {
    "Bot": "🤖",
    "Ferramenta": "🛠️",
    "Site": "🌐",
    "Script": "💻",
    "Outros": "📦"
}


# =========================================================
# VALIDAÇÃO
# =========================================================

def link_valido(link):

    try:

        url = urlparse(link)

        return (
            url.scheme in ("http", "https")
            and bool(url.netloc)
        )

    except Exception:

        return False


# =========================================================
# PEGAR PROJETOS DO BANCO
# =========================================================

def buscar_projetos():

    conexao = conectar()

    registros = conexao.execute("""
        SELECT
            id,
            nome,
            descricao,
            categoria,
            icone,
            link,
            data
        FROM projetos
        ORDER BY id DESC
    """).fetchall()

    conexao.close()

    return [dict(registro) for registro in registros]


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@bots_bp.route("/")
def area_bots():

    projetos = buscar_projetos()

    return render_template_string(
        PAGINA_BOTS,
        projetos=projetos
    )


# =========================================================
# PUBLICAR PROJETO
# =========================================================

@bots_bp.route("/publicar", methods=["GET", "POST"])
def publicar_bot():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        categoria = request.form.get(
            "categoria",
            "Outros"
        ).strip()

        link = request.form.get(
            "link",
            ""
        ).strip()


        # -----------------------------------------
        # VALIDAÇÕES
        # -----------------------------------------

        if not nome or not descricao or not link:

            return "Preencha todos os campos.", 400


        if len(nome) > 80:

            return (
                "O nome pode ter no máximo "
                "80 caracteres.",
                400
            )


        if len(descricao) > 500:

            return (
                "A descrição pode ter no máximo "
                "500 caracteres.",
                400
            )


        if categoria not in CATEGORIAS:

            return "Categoria inválida.", 400


        if not link_valido(link):

            return "Link inválido.", 400


        # -----------------------------------------
        # SALVAR NO SQLITE
        # -----------------------------------------

        try:

            conexao = conectar()

            conexao.execute("""
                INSERT INTO projetos (
                    nome,
                    descricao,
                    categoria,
                    icone,
                    link,
                    data
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                nome,
                descricao,
                categoria,
                CATEGORIAS[categoria],
                link,
                datetime.now().strftime("%d/%m/%Y")
            ))

            conexao.commit()

            conexao.close()

        except sqlite3.IntegrityError:

            return (
                "Esse projeto já foi publicado.",
                400
            )

        except Exception as erro:

            print(
                "ERRO AO SALVAR PROJETO:",
                erro
            )

            return (
                "Erro ao salvar o projeto.",
                500
            )


        return redirect(
            url_for("bots.area_bots")
        )


    return render_template_string(
        PAGINA_PUBLICAR
    )


# =========================================================
# HTML — BOTS & FERRAMENTAS
# =========================================================

PAGINA_BOTS = """

<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Bots & Ferramentas | Grupos+</title>


<style>

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: Arial, Helvetica, sans-serif;
}


body {

    background:
        radial-gradient(
            circle at top,
            rgba(150, 0, 0, .18),
            transparent 40%
        ),
        #070707;

    color: #eee;

    min-height: 100vh;
}


/* ================= HEADER ================= */

header {

    position: sticky;
    top: 0;
    z-index: 20;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 16px 7%;

    background: rgba(5, 5, 5, .97);

    border-bottom: 1px solid #450000;

    box-shadow:
        0 5px 25px rgba(0,0,0,.5);
}


.logo {

    color: white;

    font-size: 25px;

    font-weight: bold;
}


.logo span {

    color: #c40000;
}


nav {

    display: flex;

    gap: 8px;

    flex-wrap: wrap;
}


nav a {

    color: white;

    text-decoration: none;

    background: #850000;

    border: 1px solid #c00000;

    padding: 10px 15px;

    border-radius: 8px;

    font-weight: bold;

    transition: .2s;
}


nav a:hover {

    background: #c00000;

    transform: translateY(-2px);
}


/* ================= HERO ================= */

.hero {

    min-height: 390px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 45px;

    padding: 55px 7%;

    border-bottom: 1px solid #420000;

    overflow: hidden;
}


.hero img {

    width: 230px;

    height: 300px;

    object-fit: contain;

    filter:
        drop-shadow(
            0 0 25px
            rgba(190,0,0,.5)
        );
}


.hero h1 {

    font-size: 46px;

    margin-bottom: 15px;
}


.hero h1 span {

    color: #c00000;
}


.hero p {

    max-width: 620px;

    color: #aaa;

    line-height: 1.7;

    font-size: 16px;
}


.frase {

    margin: 20px 0;

    color: #ddd;

    font-style: italic;

    max-width: 600px;
}


.btn {

    display: inline-block;

    padding: 11px 18px;

    background: #8d0000;

    color: white;

    border: 1px solid #d00000;

    border-radius: 8px;

    text-decoration: none;

    font-weight: bold;

    cursor: pointer;

    transition: .2s;
}


.btn:hover {

    background: #c00000;

    transform: translateY(-2px);

    box-shadow:
        0 0 18px
        rgba(190,0,0,.3);
}


/* ================= CONTAINER ================= */

.container {

    max-width: 1200px;

    margin: auto;

    padding: 45px 20px;
}


.titulo {

    text-align: center;

    font-size: 30px;
}


.subtitulo {

    text-align: center;

    color: #777;

    margin: 8px 0 25px;
}


/* ================= BUSCA ================= */

.busca {

    width: 100%;

    padding: 15px;

    background: #111;

    color: white;

    border: 1px solid #420000;

    border-radius: 9px;

    outline: none;

    margin-bottom: 20px;

    font-size: 15px;
}


.busca:focus {

    border-color: #a00000;

    box-shadow:
        0 0 12px
        rgba(160,0,0,.2);
}


/* ================= CATEGORIAS ================= */

.categorias {

    display: flex;

    justify-content: center;

    flex-wrap: wrap;

    gap: 8px;

    margin-bottom: 25px;
}


.categoria {

    padding: 9px 15px;

    background: #111;

    color: #aaa;

    border: 1px solid #390000;

    border-radius: 20px;

    cursor: pointer;

    transition: .2s;
}


.categoria:hover,
.categoria.ativa {

    background: #900000;

    color: white;

    border-color: #d00000;
}


/* ================= CONTROLES ================= */

.controles {

    display: flex;

    justify-content: flex-end;

    gap: 8px;

    margin-bottom: 10px;
}


.controle {

    width: 42px;

    height: 38px;

    background: #160000;

    color: white;

    border: 1px solid #700000;

    border-radius: 8px;

    cursor: pointer;

    font-size: 18px;

    transition: .2s;
}


.controle:hover {

    background: #900000;
}


/* ================= CARDS ================= */

.lista {

    display: flex;

    gap: 18px;

    overflow-x: auto;

    scroll-behavior: smooth;

    padding: 8px 2px 25px;

    scrollbar-width: none;

    cursor: grab;
}


.lista:active {

    cursor: grabbing;
}


.lista::-webkit-scrollbar {

    display: none;
}


.card {

    flex: 0 0 310px;

    background:
        linear-gradient(
            145deg,
            #161616,
            #0b0b0b
        );

    border: 1px solid #400000;

    border-radius: 15px;

    padding: 22px;

    box-shadow:
        0 10px 30px #000;

    transition: .25s;
}


.card:hover {

    transform: translateY(-6px);

    border-color: #a00000;

    box-shadow:
        0 12px 35px
        rgba(150,0,0,.2);
}


.icone {

    font-size: 45px;

    margin-bottom: 12px;
}


.card h3 {

    margin-bottom: 8px;

    word-break: break-word;
}


.descricao {

    color: #aaa;

    line-height: 1.5;

    min-height: 75px;

    word-break: break-word;
}


.info {

    display: flex;

    justify-content: space-between;

    gap: 10px;

    color: #777;

    font-size: 12px;

    margin: 15px 0;
}


.card .btn {

    width: 100%;

    text-align: center;
}


/* ================= VAZIO ================= */

.vazio {

    text-align: center;

    padding: 60px;

    color: #666;
}


.vazio h3 {

    color: #aaa;

    margin-bottom: 8px;
}


/* ================= FOOTER ================= */

footer {

    text-align: center;

    padding: 35px;

    color: #555;

    border-top: 1px solid #260000;
}


/* ================= MOBILE ================= */

@media (max-width: 700px) {

    header {

        flex-direction: column;

        gap: 12px;

    }


    .hero {

        flex-direction: column;

        text-align: center;

        padding-top: 40px;

    }


    .hero img {

        width: 180px;

        height: 230px;

    }


    .hero h1 {

        font-size: 35px;

    }


    .card {

        flex-basis: 280px;

    }

}

</style>

</head>


<body>


<header>

    <div class="logo">

        Grupos<span>+</span>

    </div>


    <nav>

        <a href="/">

            👥 Grupos

        </a>


        <a href="/bots">

            🤖 Bots & Ferramentas

        </a>

    </nav>

</header>


<section class="hero">


    <img
        src="/static/itachi.png"
        alt="Itachi Uchiha"
    >


    <div>

        <h1>

            Bots <span>& Ferramentas</span>

        </h1>


        <p>

            Um espaço separado dentro do Grupos+
            para publicar seus bots, ferramentas,
            sites, scripts e outros projetos.

        </p>


        <div class="frase">

            "Conhecer a si próprio é o começo
            de toda sabedoria."

        </div>


        <a
            class="btn"
            href="/bots/publicar"
            style="
                display:inline-block !important;
                visibility:visible !important;
                opacity:1 !important;
            "
        >

            ➕ Publicar projeto

        </a>

    </div>

</section>


<main class="container">


    <h2 class="titulo">

        🚀 Projetos publicados

    </h2>


    <p class="subtitulo">

        Bots e ferramentas disponíveis.

    </p>


    <input
        class="busca"
        id="busca"
        type="search"
        autocomplete="off"
        placeholder="🔎 Procurar projeto..."
        oninput="filtrar()"
    >


    <div class="categorias">


        <button
            type="button"
            class="categoria ativa"
            onclick="selecionar('Todos', this)"
        >

            Todos

        </button>


        <button
            type="button"
            class="categoria"
            onclick="selecionar('Bot', this)"
        >

            🤖 Bots

        </button>


        <button
            type="button"
            class="categoria"
            onclick="selecionar('Ferramenta', this)"
        >

            🛠️ Ferramentas

        </button>


        <button
            type="button"
            class="categoria"
            onclick="selecionar('Site', this)"
        >

            🌐 Sites

        </button>


        <button
            type="button"
            class="categoria"
            onclick="selecionar('Script', this)"
        >

            💻 Scripts

        </button>


        <button
            type="button"
            class="categoria"
            onclick="selecionar('Outros', this)"
        >

            📦 Outros

        </button>


    </div>


    {% if projetos %}


    <div class="controles">

        <button
            type="button"
            class="controle"
            onclick="mover(-1)"
        >
            ←
        </button>


        <button
            type="button"
            class="controle"
            onclick="mover(1)"
        >
            →
        </button>

    </div>


    <div
        class="lista"
        id="lista"
    >


        {% for projeto in projetos %}


        <article
            class="card"
            data-nome="{{ projeto.nome|lower }}"
            data-descricao="{{ projeto.descricao|lower }}"
            data-categoria="{{ projeto.categoria }}"
        >


            <div class="icone">

                {{ projeto.icone }}

            </div>


            <h3>

                {{ projeto.nome }}

            </h3>


            <p class="descricao">

                {{ projeto.descricao }}

            </p>


            <div class="info">

                <span>

                    {{ projeto.categoria }}

                </span>


                <span>

                    {{ projeto.data }}

                </span>

            </div>


            <a
                class="btn"
                href="{{ projeto.link }}"
                target="_blank"
                rel="noopener noreferrer"
            >

                Abrir projeto

            </a>


        </article>


        {% endfor %}


    </div>


    {% else %}


    <div class="vazio">

        <h3>

            Nenhum projeto publicado

        </h3>


        <p>

            Publique seu primeiro bot ou ferramenta.

        </p>

    </div>


    {% endif %}


</main>


<footer>

    Grupos+ • Bots & Ferramentas

</footer>


<script>

let categoriaAtual = "Todos";


function selecionar(valor, botao) {

    categoriaAtual = valor;


    document
        .querySelectorAll(".categoria")
        .forEach(elemento => {

            elemento.classList.remove("ativa");

        });


    botao.classList.add("ativa");


    filtrar();

}


function filtrar() {

    const campo =
        document.getElementById("busca");


    const texto =
        campo.value
        .trim()
        .toLowerCase();


    document
        .querySelectorAll(".card")
        .forEach(card => {


            const nome =
                card.dataset.nome;


            const descricao =
                card.dataset.descricao;


            const categoria =
                card.dataset.categoria;


            const textoOk =
                !texto ||
                nome.includes(texto) ||
                descricao.includes(texto);


            const categoriaOk =
                categoriaAtual === "Todos" ||
                categoria === categoriaAtual;


            card.style.display =
                textoOk && categoriaOk
                ? ""
                : "none";

        });

}


function mover(direcao) {

    const lista =
        document.getElementById("lista");


    if (!lista) return;


    lista.scrollBy({

        left: direcao * 330,

        behavior: "smooth"

    });

}


/* AUTO-SCROLL */

setInterval(() => {

    const lista =
        document.getElementById("lista");


    if (!lista) return;


    if (
        !lista.matches(":hover") &&
        document.activeElement?.id !== "busca"
    ) {

        const chegouFim =
            lista.scrollLeft +
            lista.clientWidth >=
            lista.scrollWidth - 10;


        if (chegouFim) {

            lista.scrollTo({
                left: 0,
                behavior: "smooth"
            });

        } else {

            lista.scrollBy({
                left: 330,
                behavior: "smooth"
            });

        }

    }

}, 4500);


/* ARRASTAR */

const lista =
    document.getElementById("lista");


if (lista) {

    let arrastando = false;

    let inicioX = 0;

    let scrollInicial = 0;


    lista.addEventListener(
        "mousedown",
        evento => {

            arrastando = true;

            inicioX = evento.pageX;

            scrollInicial =
                lista.scrollLeft;

        }
    );


    window.addEventListener(
        "mouseup",
        () => {

            arrastando = false;

        }
    );


    lista.addEventListener(
        "mousemove",
        evento => {

            if (!arrastando) return;

            evento.preventDefault();


            const distancia =
                evento.pageX - inicioX;


            lista.scrollLeft =
                scrollInicial - distancia;

        }
    );

}

</script>


</body>

</html>

"""


# =========================================================
# HTML — PUBLICAÇÃO
# =========================================================

PAGINA_PUBLICAR = """

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Publicar projeto | Grupos+</title>


<style>

* {
    box-sizing: border-box;
    font-family: Arial, Helvetica, sans-serif;
}


body {

    margin: 0;

    background:
        radial-gradient(
            circle at top,
            rgba(150,0,0,.18),
            transparent 40%
        ),
        #070707;

    color: white;

    min-height: 100vh;
}


.box {

    max-width: 650px;

    margin: 50px auto;

    padding: 30px;

    background: #111;

    border: 1px solid #450000;

    border-radius: 15px;

    box-shadow:
        0 10px 40px #000;
}


.voltar {

    color: #c00000;

    text-decoration: none;
}


h1 {

    margin-top: 25px;
}


h1 span {

    color: #c00000;
}


label {

    display: block;

    margin: 18px 0 7px;

    font-weight: bold;
}


input,
textarea,
select {

    width: 100%;

    padding: 13px;

    background: #080808;

    color: white;

    border: 1px solid #420000;

    border-radius: 8px;

    outline: none;

    font-size: 15px;
}


input:focus,
textarea:focus,
select:focus {

    border-color: #a00000;

    box-shadow:
        0 0 12px
        rgba(160,0,0,.2);
}


textarea {

    min-height: 130px;

    resize: vertical;
}


button {

    width: 100%;

    margin-top: 20px;

    padding: 14px;

    border: 0;

    border-radius: 8px;

    background: #900000;

    color: white;

    font-weight: bold;

    cursor: pointer;

    font-size: 15px;
}


button:hover {

    background: #c00000;
}


.aviso {

    color: #777;

    font-size: 13px;

    line-height: 1.5;

    margin-top: 15px;
}


@media(max-width:700px) {

    .box {

        margin: 20px;

        padding: 22px;

    }

}

</style>

</head>


<body>


<div class="box">


<a
    class="voltar"
    href="/bots"
>

    ← Voltar para Bots & Ferramentas

</a>


<h1>

    Publicar <span>projeto</span>

</h1>


<form method="POST">


<label>

    Nome do projeto

</label>


<input
    type="text"
    name="nome"
    maxlength="80"
    placeholder="Ex: Takeshi Bot"
    required
    autocomplete="off"
>


<label>

    Descrição

</label>


<textarea
    name="descricao"
    maxlength="500"
    placeholder="Explique o que seu projeto faz..."
    required
></textarea>


<label>

    Categoria

</label>


<select name="categoria">

    <option value="Bot">
        🤖 Bot
    </option>

    <option value="Ferramenta">
        🛠️ Ferramenta
    </option>

    <option value="Site">
        🌐 Site
    </option>

    <option value="Script">
        💻 Script
    </option>

    <option value="Outros">
        📦 Outros
    </option>

</select>


<label>

    Link do projeto

</label>


<input
    type="url"
    name="link"
    placeholder="https://..."
    required
    autocomplete="url"
>


<button type="submit">

    🚀 Publicar projeto

</button>


</form>


<p class="aviso">

    Publique somente projetos e links que você
    tem autorização para compartilhar.

</p>


</div>


</body>

</html>

"""
