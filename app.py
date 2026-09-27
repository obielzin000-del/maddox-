from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import re
import html
import os
import sqlite3
from datetime import datetime

# =========================================================
# APP
# =========================================================

app = Flask(__name__)


# =========================================================
# CONFIGURAÇÃO
# =========================================================

CANAL = "SEU_LINK_DO_CANAL"


# =========================================================
# BANCO DE DADOS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

DB = os.path.join(
    DATA_DIR,
    "grupos_plus.db"
)


def conectar():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn


def criar_banco():

    conn = conectar()

    # -------------------------
    # GRUPOS
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS grupos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            descricao TEXT NOT NULL,

            categoria TEXT NOT NULL,

            emoji TEXT NOT NULL,

            membros TEXT DEFAULT '—',

            link TEXT NOT NULL UNIQUE,

            criado_em TEXT NOT NULL

        )
    """)

    # -------------------------
    # PROJETOS / BOTS
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS projetos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            descricao TEXT NOT NULL,

            categoria TEXT NOT NULL,

            icone TEXT NOT NULL,

            link TEXT NOT NULL UNIQUE,

            data TEXT NOT NULL,

            criado_em TEXT NOT NULL

        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# BUSCAR GRUPOS
# =========================================================

def buscar_grupos():

    conn = conectar()

    registros = conn.execute("""
        SELECT
            id,
            nome,
            descricao,
            categoria,
            emoji,
            membros,
            link
        FROM grupos
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [
        dict(registro)
        for registro in registros
    ]


# =========================================================
# BUSCAR PROJETOS
# =========================================================

def buscar_projetos():

    conn = conectar()

    registros = conn.execute("""
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

    conn.close()

    return [
        dict(registro)
        for registro in registros
    ]


# =========================================================
# VERIFICAR GRUPO DUPLICADO
# =========================================================

def grupo_existe(link):

    conn = conectar()

    resultado = conn.execute(
        """
        SELECT id
        FROM grupos
        WHERE link = ?
        LIMIT 1
        """,
        (link,)
    ).fetchone()

    conn.close()

    return resultado is not None


# =========================================================
# VERIFICAR PROJETO DUPLICADO
# =========================================================

def projeto_existe(link):

    conn = conectar()

    resultado = conn.execute(
        """
        SELECT id
        FROM projetos
        WHERE link = ?
        LIMIT 1
        """,
        (link,)
    ).fetchone()

    conn.close()

    return resultado is not None


# =========================================================
# SALVAR GRUPO
# =========================================================

def salvar_grupo(
    nome,
    descricao,
    categoria,
    emoji,
    link
):

    conn = conectar()

    try:

        conn.execute(
            """
            INSERT INTO grupos
            (
                nome,
                descricao,
                categoria,
                emoji,
                membros,
                link,
                criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome,
                descricao,
                categoria,
                emoji,
                "—",
                link,
                datetime.now().isoformat()
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# =========================================================
# CATEGORIAS DE BOTS
# =========================================================

CATEGORIAS_BOT = {

    "Bot": "🤖",

    "Ferramenta": "🛠️",

    "Site": "🌐",

    "Script": "💻",

    "Outros": "📦"

}


# =========================================================
# SALVAR PROJETO
# =========================================================

def salvar_projeto(
    nome,
    descricao,
    categoria,
    link
):

    conn = conectar()

    try:

        conn.execute(
            """
            INSERT INTO projetos
            (
                nome,
                descricao,
                categoria,
                icone,
                link,
                data,
                criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome,
                descricao,
                categoria,
                CATEGORIAS_BOT[categoria],
                link,
                datetime.now().strftime("%d/%m/%Y"),
                datetime.now().isoformat()
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# =========================================================
# BUSCAR DADOS DO CONVITE
# =========================================================

def dados_grupo(link):

    try:

        u = urlparse(link)

        if (
            u.scheme != "https"
            or u.netloc.lower() != "chat.whatsapp.com"
            or not u.path.startswith("/")
        ):

            return None

        codigo = u.path.strip("/")

        if not re.fullmatch(
            r"[A-Za-z0-9_-]{5,}",
            codigo
        ):

            return None

        req = Request(
            link,
            headers={
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )

        pagina = urlopen(
            req,
            timeout=6
        ).read().decode(
            "utf-8",
            errors="ignore"
        )

        def pegar_meta(nome):

            padroes = [

                rf'<meta[^>]+property=["\']{nome}["\'][^>]+content=["\']([^"\']*)',

                rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{nome}["\']',

                rf'<meta[^>]+name=["\']{nome}["\'][^>]+content=["\']([^"\']*)',

                rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']{nome}["\']'

            ]

            for padrao in padroes:

                resultado = re.search(
                    padrao,
                    pagina,
                    re.I
                )

                if resultado:

                    return html.unescape(
                        resultado.group(1)
                    ).strip()

            return ""

        nome = pegar_meta("og:title")

        descricao = pegar_meta(
            "og:description"
        )

        if nome.lower() in (
            "whatsapp group invite",
            "whatsapp group invite link"
        ):

            nome = ""

        if descricao.lower() in (
            "whatsapp group invite",
            "whatsapp group invite link"
        ):

            descricao = ""

        return {

            "nome": nome,

            "descricao": descricao

        }

    except Exception:

        return None


# =========================================================
# VALIDAR LINK DO WHATSAPP
# =========================================================

def link_valido(link):

    try:

        u = urlparse(link)

        return bool(

            u.scheme == "https"

            and
            u.netloc.lower() ==
            "chat.whatsapp.com"

            and
            re.fullmatch(
                r"/[A-Za-z0-9_-]{5,}",
                u.path
            )

        )

    except Exception:

        return False


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route("/")
def inicio():

    grupos = buscar_grupos()

    return render_template_string(
        HTML,
        grupos=grupos,
        canal=CANAL
    )


# =========================================================
# API PARA BUSCAR NOME E DESCRIÇÃO
# =========================================================

@app.route("/api/grupo")
def api_grupo():

    link = request.args.get(
        "link",
        ""
    ).strip()

    if not link_valido(link):

        return jsonify({

            "ok": False,

            "nome": "",

            "descricao": ""

        })

    dados = dados_grupo(link)

    if not dados:

        return jsonify({

            "ok": False,

            "nome": "",

            "descricao": ""

        })

    return jsonify({

        "ok": True,

        "nome": dados.get(
            "nome",
            ""
        ),

        "descricao": dados.get(
            "descricao",
            ""
        )

    })


# =========================================================
# POSTAR GRUPO
# =========================================================

@app.route(
    "/postar",
    methods=["GET", "POST"]
)
def postar():

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

        emoji = request.form.get(
            "emoji",
            "💬"
        ).strip()

        link = request.form.get(
            "link",
            ""
        ).strip()

        if not nome:

            return "Nome do grupo obrigatório.", 400

        if not descricao:

            return "Descrição obrigatória.", 400

        if not link_valido(link):

            return "Link de grupo WhatsApp inválido.", 400

        if len(nome) > 70:

            return "Nome muito grande.", 400

        if len(descricao) > 500:

            return "Descrição muito grande.", 400

        categorias = {

            "Jogos",
            "Amizade",
            "Estudos",
            "Memes",
            "Outros"

        }

        if categoria not in categorias:

            categoria = "Outros"

        if not emoji or len(emoji) > 8:

            emoji = "💬"

        if grupo_existe(link):

            return redirect(
                url_for("inicio")
            )

        salvo = salvar_grupo(

            nome=nome,

            descricao=descricao,

            categoria=categoria,

            emoji=emoji,

            link=link

        )

        if not salvo:

            return (
                "Não foi possível salvar o grupo.",
                500
            )

        return redirect(
            url_for("inicio")
        )

    return render_template_string(
        FORM_HTML
    )


# =========================================================
# ÁREA DE BOTS
# =========================================================

@app.route("/bots")
@app.route("/bots/")
def area_bots():

    projetos = buscar_projetos()

    return render_template_string(
        BOTS_HTML,
        projetos=projetos,
        canal=CANAL
    )


# =========================================================
# PUBLICAR BOT / PROJETO
# =========================================================

@app.route(
    "/bots/publicar",
    methods=["GET", "POST"]
)
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

        if not nome:

            return "Nome obrigatório.", 400

        if not descricao:

            return "Descrição obrigatória.", 400

        if not link:

            return "Link obrigatório.", 400

        if len(nome) > 80:

            return "Nome muito grande.", 400

        if len(descricao) > 500:

            return "Descrição muito grande.", 400

        if categoria not in CATEGORIAS_BOT:

            return "Categoria inválida.", 400

        try:

            url = urlparse(link)

            if (
                url.scheme
                not in ("http", "https")
                or not url.netloc
            ):

                return "Link inválido.", 400

        except Exception:

            return "Link inválido.", 400

        if projeto_existe(link):

            return (
                "Esse projeto já foi publicado.",
                400
            )

        salvo = salvar_projeto(

            nome=nome,

            descricao=descricao,

            categoria=categoria,

            link=link

        )

        if not salvo:

            return (
                "Não foi possível salvar o projeto.",
                500
            )

        return redirect(
            url_for("area_bots")
        )

    return render_template_string(
        BOT_FORM_HTML
    )


# =========================================================
# HTML PRINCIPAL
# =========================================================

HTML = r"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Grupos+ | Itachi</title>

<style>

*{
    box-sizing:border-box;
    margin:0;
    padding:0;
}

html{
    scroll-behavior:smooth;
}

body{
    background:#050505;
    color:#fff;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    overflow-x:hidden;
}

body::before{
    content:"";
    position:fixed;
    inset:0;
    pointer-events:none;
    z-index:-1;

    background:
        radial-gradient(
            circle at 50% 10%,
            rgba(150,0,0,.18),
            transparent 32%
        ),
        radial-gradient(
            circle at 10% 70%,
            rgba(100,0,0,.08),
            transparent 30%
        );
}

/* =========================================================
   HEADER
========================================================= */

header{
    min-height:72px;

    padding:
        12px 7%;

    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:20px;

    position:sticky;

    top:0;

    z-index:50;

    background:
        rgba(5,5,5,.92);

    backdrop-filter:blur(14px);

    border-bottom:
        1px solid
        rgba(150,0,0,.35);

    box-shadow:
        0 8px 30px
        rgba(0,0,0,.5);
}

.logo{
    font-size:25px;
    font-weight:900;
    letter-spacing:1px;

    flex-shrink:0;
}

.logo span{
    color:#d00000;
}

/* MENU DO HEADER */

.menu{

    display:flex;

    align-items:center;

    justify-content:flex-end;

    gap:8px;

    flex-wrap:wrap;

}

.menu-btn{

    display:inline-flex;

    align-items:center;

    justify-content:center;

    padding:
        10px 14px;

    border-radius:10px;

    background:#111;

    border:
        1px solid
        #421010;

    color:white;

    text-decoration:none;

    font-size:13px;

    font-weight:bold;

    white-space:nowrap;

    transition:.25s;

}

.menu-btn:hover{

    background:#760000;

    border-color:#a00000;

    transform:
        translateY(-2px);

}

.channel{
    display:inline-flex;

    align-items:center;

    justify-content:center;

    padding:11px 18px;

    border-radius:10px;

    background:
        linear-gradient(
            135deg,
            #7d0000,
            #d00000
        );

    color:white;

    text-decoration:none;

    font-weight:bold;

    border:
        1px solid
        rgba(255,80,80,.35);

    box-shadow:
        0 0 20px
        rgba(180,0,0,.15);

    transition:.25s;

    white-space:nowrap;
}

.channel:hover{
    transform:translateY(-2px);

    box-shadow:
        0 0 30px
        rgba(220,0,0,.3);
}

/* =========================================================
   HERO
========================================================= */

.hero{
    min-height:570px;

    display:flex;

    align-items:center;

    justify-content:center;

    gap:80px;

    padding:70px 7%;

    position:relative;

    overflow:hidden;

    background:
        linear-gradient(
            90deg,
            #050505 0%,
            #120000 50%,
            #050505 100%
        );
}

.hero::before{
    content:"";

    position:absolute;

    width:600px;
    height:600px;

    border-radius:50%;

    background:
        radial-gradient(
            circle,
            rgba(180,0,0,.18),
            transparent 68%
        );

    left:50%;
    top:50%;

    transform:
        translate(-50%,-50%);

    pointer-events:none;
}

.itachi-box{
    width:390px;
    height:450px;

    display:flex;

    align-items:center;
    justify-content:center;

    position:relative;

    flex-shrink:0;

    animation:
        itachiFloat 5s ease-in-out infinite;
}

.itachi-box::before{
    content:"";

    position:absolute;

    width:320px;
    height:320px;

    border-radius:50%;

    background:
        radial-gradient(
            circle,
            rgba(170,0,0,.28),
            transparent 68%
        );

    filter:blur(10px);

    z-index:0;
}

.itachi-box img{
    width:100%;
    height:100%;

    object-fit:contain;

    position:relative;
    z-index:2;

    filter:
        drop-shadow(
            0 20px 35px
            rgba(0,0,0,.9)
        )
        drop-shadow(
            0 0 18px
            rgba(150,0,0,.22)
        );

    user-select:none;
    pointer-events:none;
}

@keyframes itachiFloat{

    0%,100%{
        transform:
            translateY(0);
    }

    50%{
        transform:
            translateY(-10px);
    }
}

.hero-content{
    max-width:600px;

    position:relative;

    z-index:3;
}

.badge{
    display:inline-block;

    padding:7px 12px;

    border-radius:30px;

    background:
        rgba(130,0,0,.12);

    border:
        1px solid
        rgba(190,0,0,.35);

    color:#d00000;

    font-size:12px;

    font-weight:bold;

    margin-bottom:17px;
}

.hero h1{
    font-size:
        clamp(
            42px,
            6vw,
            72px
        );

    line-height:.95;

    margin-bottom:22px;
}

.hero h1 span{
    color:#c90000;
}

.hero p{
    color:#aaa;

    font-size:17px;

    line-height:1.7;

    max-width:560px;

    margin-bottom:20px;
}

.frase{
    color:#777;

    font-size:14px;

    font-style:italic;

    min-height:42px;

    margin-bottom:28px;

    transition:opacity .3s;
}

.hero-buttons{
    display:flex;

    gap:12px;

    flex-wrap:wrap;
}

.btn{
    display:inline-flex;

    align-items:center;

    justify-content:center;

    padding:13px 20px;

    border-radius:10px;

    text-decoration:none;

    font-weight:bold;

    transition:.25s;
}

.btn-red{
    background:
        linear-gradient(
            135deg,
            #850000,
            #d00000
        );

    color:white;
}

.btn-dark{
    background:#111;

    color:white;

    border:
        1px solid
        #333;
}

.btn:hover{
    transform:
        translateY(-3px);
}

/* =========================================================
   PESQUISA
========================================================= */

.search-area{
    width:86%;
    max-width:1000px;

    margin:
        -28px auto 0;

    position:relative;

    z-index:10;
}

.search{
    width:100%;

    padding:17px 20px;

    border-radius:14px;

    border:
        1px solid
        #321010;

    background:
        rgba(12,12,12,.92);

    color:white;

    outline:none;

    font-size:15px;

    box-shadow:
        0 15px 40px
        rgba(0,0,0,.35);
}

.search:focus{
    border-color:#9c0000;

    box-shadow:
        0 0 25px
        rgba(150,0,0,.12);
}

/* =========================================================
   CATEGORIAS
========================================================= */

.categories{
    width:86%;
    max-width:1200px;

    margin:
        35px auto 0;

    display:flex;

    gap:9px;

    overflow-x:auto;

    padding-bottom:5px;

    scrollbar-width:none;
}

.categories::-webkit-scrollbar{
    display:none;
}

.category{
    white-space:nowrap;

    border:
        1px solid
        #333;

    background:#101010;

    color:#aaa;

    padding:
        10px 17px;

    border-radius:30px;

    cursor:pointer;

    transition:.2s;
}

.category:hover,
.category.active{
    color:white;

    background:#820000;

    border-color:#b00000;
}

/* =========================================================
   GRUPOS
========================================================= */

.container{
    width:86%;
    max-width:1200px;

    margin:
        40px auto 70px;
}

.title{
    font-size:28px;

    margin-bottom:7px;
}

.subtitle{
    color:#666;

    margin-bottom:18px;
}

.carousel-controls{
    display:flex;

    justify-content:flex-end;

    gap:8px;

    margin-bottom:8px;
}

.arrow{
    width:43px;
    height:38px;

    border-radius:9px;

    background:#101010;

    border:
        1px solid
        #461010;

    color:white;

    cursor:pointer;

    font-size:19px;

    transition:.2s;
}

.arrow:hover{
    background:#870000;

    border-color:#b00000;
}

.groups{
    display:flex;

    gap:20px;

    overflow-x:auto;

    overflow-y:hidden;

    padding:
        12px
        5px
        30px;

    scroll-behavior:smooth;

    scroll-snap-type:
        x mandatory;

    scrollbar-width:none;

    cursor:grab;
}

.groups::-webkit-scrollbar{
    display:none;
}

.groups:active{
    cursor:grabbing;
}

.card{
    min-width:315px;

    max-width:315px;

    flex-shrink:0;

    scroll-snap-align:start;

    position:relative;

    overflow:hidden;

    padding:24px;

    border-radius:18px;

    border:
        1px solid
        #351010;

    background:
        linear-gradient(
            145deg,
            #171717,
            #090909
        );

    box-shadow:
        0 12px 35px
        rgba(0,0,0,.4);

    transition:.3s;
}

.card::before{
    content:"";

    position:absolute;

    top:0;
    left:0;

    width:100%;
    height:3px;

    background:
        linear-gradient(
            90deg,
            transparent,
            #b00000,
            transparent
        );
}

.card:hover{
    transform:
        translateY(-8px);

    border-color:#850000;

    box-shadow:
        0 20px 45px
        rgba(0,0,0,.55),
        0 0 25px
        rgba(150,0,0,.12);
}

.card-icon{
    width:55px;
    height:55px;

    display:flex;

    align-items:center;
    justify-content:center;

    border-radius:14px;

    background:#170707;

    border:
        1px solid
        #481010;

    font-size:27px;

    margin-bottom:18px;
}

.card h3{
    font-size:20px;

    margin-bottom:10px;

    white-space:nowrap;

    overflow:hidden;

    text-overflow:ellipsis;
}

.description{
    color:#999;

    line-height:1.55;

    min-height:72px;

    margin-bottom:20px;
}

.card-info{
    display:flex;

    justify-content:space-between;

    gap:10px;

    color:#666;

    font-size:12px;

    margin-bottom:17px;
}

.enter{
    display:block;

    text-align:center;

    padding:12px;

    border-radius:10px;

    background:#810000;

    color:white;

    text-decoration:none;

    font-weight:bold;

    transition:.2s;
}

.enter:hover{
    background:#b90000;
}

.empty{
    padding:60px 20px;

    text-align:center;

    border:
        1px dashed
        #3b1717;

    border-radius:18px;

    color:#666;
}

.empty-icon{
    font-size:45px;

    margin-bottom:15px;
}

/* =========================================================
   FOOTER
========================================================= */

footer{
    text-align:center;

    padding:
        40px 20px;

    border-top:
        1px solid
        #260909;

    color:#555;

    line-height:1.7;
}

footer strong{
    color:#a00000;
}

/* =========================================================
   MOBILE
========================================================= */

@media(max-width:900px){

    header{

        padding:
            12px 5%;

        flex-direction:column;

        align-items:stretch;

    }

    .logo{

        text-align:center;

    }

    .menu{

        justify-content:center;

    }

}

@media(max-width:800px){

    .hero{

        flex-direction:column;

        text-align:center;

        gap:25px;

        padding:
            45px 5%
            65px;
    }

    .itachi-box{

        width:290px;

        height:350px;

        order:-1;
    }

    .hero-content{

        display:flex;

        flex-direction:column;

        align-items:center;
    }

    .hero p{

        font-size:15px;
    }

    .hero-buttons{

        justify-content:center;
    }

    .card{

        min-width:285px;

        max-width:285px;
    }

}

@media(max-width:480px){

    .logo{

        font-size:20px;

    }

    .menu{

        width:100%;

    }

    .menu-btn{

        flex:1;

        padding:
            9px 8px;

        font-size:11px;

    }

    .channel{

        flex:1;

        padding:
            9px 8px;

        font-size:11px;

    }

    .search-area,
    .categories,
    .container{

        width:92%;

    }

}

</style>

</head>

<body>

<header>

    <div class="logo">
        GRUPOS<span>+</span>
    </div>

    <nav class="menu">

        <a
            class="menu-btn"
            href="{{ url_for('inicio') }}"
        >
            👥 Grupos
        </a>

        <a
            class="menu-btn"
            href="{{ url_for('area_bots') }}"
        >
            🤖 Bots & Ferramentas
        </a>

        {% if canal != "SEU_LINK_DO_CANAL" %}

        <a
            class="channel"
            href="{{ canal }}"
            target="_blank"
            rel="noopener noreferrer"
        >
            🔴 Meu canal
        </a>

        {% endif %}

    </nav>

</header>

<section class="hero">

    <div class="itachi-box">

        <img
            src="{{ url_for('static', filename='itachi.png') }}"
            alt="Itachi Uchiha"
        >

    </div>

    <div class="hero-content">

        <div class="badge">
            🔴 SHARINGAN • GRUPOS+
        </div>

        <h1>
            Encontre seu
            <span>grupo.</span>
        </h1>

        <p>
            Descubra comunidades, encontre pessoas
            com os mesmos interesses e compartilhe
            seu próprio grupo.
        </p>

        <div
            class="frase"
            id="frase"
        >
            "As pessoas vivem suas vidas presas
            àquilo que aceitam como correto."
        </div>

        <div class="hero-buttons">

            {% if canal != "SEU_LINK_DO_CANAL" %}

            <a
                class="btn btn-red"
                href="{{ canal }}"
                target="_blank"
                rel="noopener noreferrer"
            >
                🔴 Acessar meu canal
            </a>

            {% endif %}

            <a
                class="btn btn-dark"
                href="{{ url_for('postar') }}"
            >
                ＋ Postar grupo
            </a>

        </div>

    </div>

</section>

<div class="search-area">

    <input
        class="search"
        id="pesquisa"
        type="search"
        maxlength="80"
        placeholder="🔎 Procurar um grupo..."
        autocomplete="off"
    >

</div>

<div class="categories">

    <button
        class="category active"
        onclick="filtrar('Todos', this)"
    >
        Todos
    </button>

    <button
        class="category"
        onclick="filtrar('Jogos', this)"
    >
        🎮 Jogos
    </button>

    <button
        class="category"
        onclick="filtrar('Amizade', this)"
    >
        😎 Amizade
    </button>

    <button
        class="category"
        onclick="filtrar('Estudos', this)"
    >
        📚 Estudos
    </button>

    <button
        class="category"
        onclick="filtrar('Memes', this)"
    >
        😂 Memes
    </button>

    <button
        class="category"
        onclick="filtrar('Outros', this)"
    >
        🔥 Outros
    </button>

</div>

<main class="container">

    <h2 class="title">
        Grupos disponíveis
    </h2>

    <p class="subtitle">
        Passe para o lado para descobrir mais comunidades.
    </p>

    {% if grupos %}

    <div class="carousel-controls">

        <button
            class="arrow"
            onclick="mover(-1)"
        >
            ←
        </button>

        <button
            class="arrow"
            onclick="mover(1)"
        >
            →
        </button>

    </div>

    <div
        class="groups"
        id="grupos"
    >

        {% for grupo in grupos %}

        <article
            class="card"
            data-nome="{{ grupo.nome|lower }}"
            data-categoria="{{ grupo.categoria }}"
        >

            <div class="card-icon">
                {{ grupo.emoji }}
            </div>

            <h3>
                {{ grupo.nome }}
            </h3>

            <p class="description">
                {{ grupo.descricao }}
            </p>

            <div class="card-info">

                <span>
                    👥 {{ grupo.membros }}
                </span>

                <span>
                    {{ grupo.categoria }}
                </span>

            </div>

            <a
                class="enter"
                href="{{ grupo.link }}"
                target="_blank"
                rel="noopener noreferrer"
            >
                Entrar no grupo
            </a>

        </article>

        {% endfor %}

    </div>

    {% else %}

    <div class="empty">

        <div class="empty-icon">
            🩸
        </div>

        <h3>
            Nenhum grupo publicado
        </h3>

        <p>
            Seja o primeiro a compartilhar uma comunidade.
        </p>

    </div>

    {% endif %}

</main>

<footer>

    <strong>GRUPOS+</strong>

    <br>

    Comunidades compartilhadas pela comunidade.

    <br><br>

    <em>
        "Conhecer a si próprio é o começo de toda sabedoria."
    </em>

</footer>

<script>

const frases = [

    "As pessoas vivem suas vidas presas àquilo que aceitam como correto.",

    "As pessoas não conseguem viver sem se agarrar a algo.",

    "O conhecimento e a consciência são vagos, e talvez seja melhor chamá-los de ilusões.",

    "Mesmo o mais forte dos adversários possui uma fraqueza.",

    "Todo mundo vive dentro das próprias ilusões.",

    "Conhecer a si mesmo é o começo de toda sabedoria."

];

let fraseAtual = 0;

setInterval(() => {

    fraseAtual =
        (fraseAtual + 1)
        % frases.length;

    const elemento =
        document.getElementById("frase");

    if(!elemento) return;

    elemento.style.opacity = "0";

    setTimeout(() => {

        elemento.textContent =
            '"' + frases[fraseAtual] + '"';

        elemento.style.opacity = "1";

    }, 300);

}, 5000);


const area =
    document.getElementById("grupos");


function mover(direcao){

    if(!area){
        return;
    }

    area.scrollBy({

        left:
            direcao * 335,

        behavior:
            "smooth"

    });

}


if(area){

    let pressionado = false;

    let inicioX = 0;

    let scrollInicial = 0;

    area.addEventListener(
        "mousedown",
        e => {

            pressionado = true;

            inicioX = e.pageX;

            scrollInicial =
                area.scrollLeft;

        }
    );

    window.addEventListener(
        "mouseup",
        () => {

            pressionado = false;

        }
    );

    area.addEventListener(
        "mousemove",
        e => {

            if(!pressionado){
                return;
            }

            const distancia =
                e.pageX - inicioX;

            area.scrollLeft =
                scrollInicial - distancia;

        }
    );

}


let autoScroll;


function iniciarAuto(){

    if(!area){
        return;
    }

    autoScroll =
        setInterval(() => {

            if(
                area.scrollLeft +
                area.clientWidth >=
                area.scrollWidth - 15
            ){

                area.scrollTo({

                    left:0,

                    behavior:"smooth"

                });

            }else{

                area.scrollBy({

                    left:335,

                    behavior:"smooth"

                });

            }

        }, 4500);

}


function pararAuto(){

    clearInterval(
        autoScroll
    );

}


if(area){

    iniciarAuto();

    area.addEventListener(
        "mouseenter",
        pararAuto
    );

    area.addEventListener(
        "mouseleave",
        iniciarAuto
    );

}


let categoriaAtual = "Todos";


function atualizar(){

    const campo =
        document.getElementById(
            "pesquisa"
        );

    if(!campo){
        return;
    }

    const texto =
        campo.value
        .toLowerCase()
        .trim();

    document
        .querySelectorAll(".card")
        .forEach(card => {

            const nome =
                card.dataset.nome;

            const categoria =
                card.dataset.categoria;

            const textoOk =
                nome.includes(texto);

            const categoriaOk =
                categoriaAtual === "Todos"
                ||
                categoria === categoriaAtual;

            card.style.display =
                textoOk && categoriaOk
                ? ""
                : "none";

        });

}


function filtrar(
    categoria,
    botao
){

    categoriaAtual =
        categoria;

    document
        .querySelectorAll(".category")
        .forEach(btn => {

            btn.classList.remove(
                "active"
            );

        });

    botao.classList.add(
        "active"
    );

    atualizar();

}


const pesquisa =
    document.getElementById(
        "pesquisa"
    );


if(pesquisa){

    pesquisa.addEventListener(
        "input",
        atualizar
    );

}

</script>

</body>

</html>
"""


# =========================================================
# FORMULÁRIO DE GRUPO
# =========================================================

FORM_HTML = r"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Postar grupo | Grupos+</title>

<style>

*{
    box-sizing:border-box;
    margin:0;
    padding:0;
}

body{

    min-height:100vh;

    display:flex;

    justify-content:center;
    align-items:center;

    padding:25px;

    color:white;

    font-family:Arial,sans-serif;

    background:
        radial-gradient(
            circle at top,
            rgba(150,0,0,.18),
            transparent 40%
        ),
        #050505;
}

.box{

    width:100%;
    max-width:560px;

    background:
        linear-gradient(
            145deg,
            #171717,
            #090909
        );

    border:
        1px solid
        #481010;

    border-radius:20px;

    padding:30px;

    box-shadow:
        0 20px 60px
        rgba(0,0,0,.6);
}

.back{

    display:inline-block;

    color:#888;

    text-decoration:none;

    margin-bottom:22px;

}

.back:hover{
    color:white;
}

h1{
    font-size:32px;
    margin-bottom:8px;
}

h1 span{
    color:#c00000;
}

.frase{

    color:#666;

    font-style:italic;

    font-size:13px;

    margin-bottom:25px;
}

label{

    display:block;

    color:#aaa;

    margin:
        17px 0 7px;

    font-size:13px;
}

input,
textarea,
select{

    width:100%;

    background:#080808;

    color:white;

    border:
        1px solid
        #351515;

    border-radius:10px;

    padding:14px;

    outline:none;

    font-size:14px;
}

input:focus,
textarea:focus,
select:focus{

    border-color:#a00000;

    box-shadow:
        0 0 15px
        rgba(150,0,0,.1);
}

textarea{

    min-height:120px;

    resize:vertical;
}

.status{

    min-height:20px;

    margin-top:8px;

    color:#777;

    font-size:12px;
}

button{

    width:100%;

    border:0;

    padding:15px;

    margin-top:24px;

    border-radius:10px;

    color:white;

    background:
        linear-gradient(
            135deg,
            #780000,
            #c00000
        );

    font-weight:bold;

    cursor:pointer;

    transition:.2s;
}

button:hover{
    transform:translateY(-2px);
}

.aviso{

    color:#555;

    font-size:11px;

    line-height:1.5;

    margin-top:15px;
}

</style>

</head>

<body>

<div class="box">

    <a
        class="back"
        href="{{ url_for('inicio') }}"
    >
        ← Voltar
    </a>

    <h1>
        Postar <span>grupo</span>
    </h1>

    <p class="frase">
        "Conhecer a si próprio é o começo de toda sabedoria."
    </p>

    <form method="POST">

        <label>
            Link do grupo
        </label>

        <input
            type="url"
            id="link"
            name="link"
            placeholder="https://chat.whatsapp.com/..."
            autocomplete="off"
            required
        >

        <div
            class="status"
            id="status"
        ></div>

        <label>
            Nome do grupo
        </label>

        <input
            type="text"
            id="nome"
            name="nome"
            maxlength="70"
            placeholder="Nome do grupo"
            required
        >

        <label>
            Descrição
        </label>

        <textarea
            id="descricao"
            name="descricao"
            maxlength="500"
            placeholder="Descrição do grupo"
            required
        ></textarea>

        <label>
            Categoria
        </label>

        <select name="categoria">

            <option value="Jogos">
                🎮 Jogos
            </option>

            <option value="Amizade">
                😎 Amizade
            </option>

            <option value="Estudos">
                📚 Estudos
            </option>

            <option value="Memes">
                😂 Memes
            </option>

            <option value="Outros">
                🔥 Outros
            </option>

        </select>

        <label>
            Emoji
        </label>

        <input
            type="text"
            name="emoji"
            maxlength="8"
            placeholder="🎮"
        >

        <button type="submit">
            🚀 Publicar grupo
        </button>

    </form>

    <p class="aviso">
        Ao colar um convite válido, o sistema tenta
        encontrar automaticamente o nome e a descrição
        disponibilizados pela página pública do convite.
    </p>

</div>

<script>

let timer;

const link =
    document.getElementById("link");

const status =
    document.getElementById("status");

const nome =
    document.getElementById("nome");

const descricao =
    document.getElementById("descricao");


link.addEventListener(
    "input",
    function(){

        clearTimeout(timer);

        const valor =
            this.value.trim();

        nome.value = "";

        descricao.value = "";

        if(
            !valor.startsWith(
                "https://chat.whatsapp.com/"
            )
        ){

            status.textContent =
                "";

            return;

        }

        status.textContent =
            "🔎 Procurando informações...";

        timer = setTimeout(
            async () => {

                try{

                    const resposta =
                        await fetch(
                            "/api/grupo?link="
                            +
                            encodeURIComponent(
                                valor
                            )
                        );

                    const dados =
                        await resposta.json();

                    if(
                        dados.ok &&
                        (
                            dados.nome ||
                            dados.descricao
                        )
                    ){

                        if(dados.nome){

                            nome.value =
                                dados.nome;

                        }

                        if(dados.descricao){

                            descricao.value =
                                dados.descricao;

                        }

                        status.textContent =
                            "✓ Informações encontradas";

                    }else{

                        status.textContent =
                            "⚠️ O WhatsApp não disponibilizou os dados. Preencha manualmente.";

                    }

                }catch{

                    status.textContent =
                        "⚠️ Não foi possível consultar o convite.";

                }

            },
            600
        );

    }
);

</script>

</body>

</html>
"""


# =========================================================
# HTML BOTS
# =========================================================

BOTS_HTML = r"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>Bots & Ferramentas | Grupos+</title>

<style>

*{
    box-sizing:border-box;
    margin:0;
    padding:0;
    font-family:Arial;
}

body{
    background:#070707;
    color:#eee;
    min-height:100vh;

    background-image:
        radial-gradient(
            circle at top,
            rgba(150,0,0,.18),
            transparent 40%
        );
}

header{

    position:sticky;

    top:0;

    z-index:20;

    display:flex;

    justify-content:space-between;

    align-items:center;

    gap:20px;

    padding:
        12px 7%;

    background:
        rgba(5,5,5,.96);

    border-bottom:
        1px solid
        #450000;

}

.logo{
    font-size:25px;
    font-weight:bold;
}

.logo span{
    color:#c40000;
}

nav{
    display:flex;

    gap:8px;

    flex-wrap:wrap;

    justify-content:flex-end;
}

nav a{

    color:white;

    text-decoration:none;

    background:#850000;

    border:
        1px solid
        #c00000;

    padding:10px 15px;

    border-radius:8px;

    font-weight:bold;

    transition:.2s;

}

nav a:hover{
    background:#c00000;

    transform:
        translateY(-2px);
}

/* =========================================================
   HERO
========================================================= */

.hero{

    min-height:360px;

    display:flex;

    align-items:center;

    justify-content:center;

    gap:40px;

    padding:50px 7%;

    border-bottom:
        1px solid
        #420000;

}

.hero img{

    width:220px;

    height:280px;

    object-fit:contain;

    filter:
        drop-shadow(
            0 0 25px
            rgba(180,0,0,.5)
        );

}

.hero h1{

    font-size:45px;

    margin-bottom:15px;

}

.hero h1 span{
    color:#c00000;
}

.hero p{

    max-width:600px;

    color:#aaa;

    line-height:1.7;

}

.frase{

    margin:18px 0;

    color:#ddd;

    font-style:italic;

}

.btn{

    display:inline-block;

    padding:11px 17px;

    background:#8d0000;

    color:white;

    border:
        1px solid
        #d00000;

    border-radius:8px;

    text-decoration:none;

    font-weight:bold;

    transition:.2s;

}

.btn:hover{
    background:#c00000;

    transform:
        translateY(-2px);
}

/* =========================================================
   CONTAINER
========================================================= */

.container{

    max-width:1200px;

    margin:auto;

    padding:45px 20px;

}

.titulo{

    text-align:center;

    font-size:30px;

}

.sub{

    text-align:center;

    color:#777;

    margin:
        8px 0 25px;

}

.busca{

    width:100%;

    padding:15px;

    background:#111;

    color:white;

    border:
        1px solid
        #420000;

    border-radius:9px;

    outline:none;

    margin-bottom:20px;

}

.busca:focus{

    border-color:#a00000;

    box-shadow:
        0 0 15px
        rgba(150,0,0,.15);

}

/* =========================================================
   CATEGORIAS
========================================================= */

.categorias{

    display:flex;

    justify-content:center;

    flex-wrap:wrap;

    gap:8px;

    margin-bottom:25px;

}

.categoria{

    padding:9px 15px;

    background:#111;

    color:#aaa;

    border:
        1px solid
        #390000;

    border-radius:20px;

    cursor:pointer;

    transition:.2s;

}

.categoria:hover,
.categoria.ativa{

    background:#900000;

    color:white;

}

/* =========================================================
   CARDS
========================================================= */

.controles{

    display:flex;

    justify-content:flex-end;

    gap:8px;

    margin-bottom:10px;

}

.controle{

    width:42px;

    height:38px;

    background:#160000;

    color:white;

    border:
        1px solid
        #700000;

    border-radius:8px;

    cursor:pointer;

}

.controle:hover{

    background:#a00000;

}

.lista{

    display:flex;

    gap:18px;

    overflow-x:auto;

    scroll-behavior:smooth;

    padding:
        8px 2px 25px;

    scrollbar-width:none;

}

.lista::-webkit-scrollbar{
    display:none;
}

.card{

    flex:0 0 310px;

    background:
        linear-gradient(
            145deg,
            #161616,
            #0b0b0b
        );

    border:
        1px solid
        #400000;

    border-radius:15px;

    padding:22px;

    box-shadow:
        0 10px 30px
        #000;

    transition:.25s;

}

.card:hover{

    transform:
        translateY(-6px);

    border-color:#a00000;

}

.icone{

    font-size:45px;

    margin-bottom:12px;

}

.card h3{
    margin-bottom:8px;
}

.descricao{

    color:#aaa;

    line-height:1.5;

    min-height:75px;

}

.info{

    display:flex;

    justify-content:space-between;

    color:#777;

    font-size:12px;

    margin:15px 0;

}

.card .btn{

    width:100%;

    text-align:center;

}

.vazio{

    text-align:center;

    padding:60px;

    color:#666;

}

/* =========================================================
   FOOTER
========================================================= */

footer{

    text-align:center;

    padding:35px;

    color:#555;

    border-top:
        1px solid
        #260000;

}

/* =========================================================
   MOBILE
========================================================= */

@media(max-width:700px){

    header{

        flex-direction:column;

        padding:
            12px 5%;

    }

    nav{

        width:100%;

        justify-content:center;

    }

    nav a{

        flex:1;

        text-align:center;

        font-size:12px;

        padding:
            9px 7px;

    }

    .hero{

        flex-direction:column;

        text-align:center;

    }

    .hero img{

        width:180px;

        height:230px;

    }

    .hero h1{

        font-size:35px;

    }

    .card{

        flex-basis:280px;

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

        <a href="{{ url_for('inicio') }}">
            👥 Grupos
        </a>

        <a href="{{ url_for('area_bots') }}">
            🤖 Bots & Ferramentas
        </a>

        {% if canal != "SEU_LINK_DO_CANAL" %}

        <a
            href="{{ canal }}"
            target="_blank"
            rel="noopener noreferrer"
        >
            📢 Meu Canal
        </a>

        {% endif %}

    </nav>

</header>

<section class="hero">

    <img
        src="{{ url_for('static', filename='itachi.png') }}"
        alt="Itachi"
    >

    <div>

        <h1>
            Bots <span>& Ferramentas</span>
        </h1>

        <p>
            Publique seus próprios bots, ferramentas,
            sites, scripts e projetos em um espaço
            separado da área de grupos.
        </p>

        <div class="frase">
            "Conhecer a si próprio é o começo de toda sabedoria."
        </div>

        <a
            class="btn"
            href="{{ url_for('publicar_bot') }}"
        >
            ➕ Publicar projeto
        </a>

    </div>

</section>

<main class="container">

    <h2 class="titulo">
        🚀 Projetos publicados
    </h2>

    <p class="sub">
        Bots e ferramentas disponíveis.
    </p>

    <input
        class="busca"
        id="busca"
        placeholder="🔎 Procurar projeto..."
        oninput="filtrar()"
    >

    <div class="categorias">

        <button
            class="categoria ativa"
            onclick="categoria('Todos',this)"
        >
            Todos
        </button>

        <button
            class="categoria"
            onclick="categoria('Bot',this)"
        >
            🤖 Bots
        </button>

        <button
            class="categoria"
            onclick="categoria('Ferramenta',this)"
        >
            🛠️ Ferramentas
        </button>

        <button
            class="categoria"
            onclick="categoria('Site',this)"
        >
            🌐 Sites
        </button>

        <button
            class="categoria"
            onclick="categoria('Script',this)"
        >
            💻 Scripts
        </button>

        <button
            class="categoria"
            onclick="categoria('Outros',this)"
        >
            📦 Outros
        </button>

    </div>

    {% if projetos %}

    <div class="controles">

        <button
            class="controle"
            onclick="mover(-1)"
        >
            ←
        </button>

        <button
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

        {% for p in projetos %}

        <article
            class="card"
            data-nome="{{ p.nome|lower }}"
            data-categoria="{{ p.categoria }}"
        >

            <div class="icone">
                {{ p.icone }}
            </div>

            <h3>
                {{ p.nome }}
            </h3>

            <p class="descricao">
                {{ p.descricao }}
            </p>

            <div class="info">

                <span>
                    {{ p.categoria }}
                </span>

                <span>
                    {{ p.data }}
                </span>

            </div>

            <a
                class="btn"
                href="{{ p.link }}"
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

        <p style="margin-top:10px">
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


function categoria(
    valor,
    botao
){

    categoriaAtual =
        valor;

    document
        .querySelectorAll(
            ".categoria"
        )
        .forEach(
            x =>
            x.classList.remove(
                "ativa"
            )
        );

    botao.classList.add(
        "ativa"
    );

    filtrar();

}


function filtrar(){

    const busca =
        document.getElementById(
            "busca"
        );

    if(!busca){
        return;
    }

    const texto =
        busca.value
        .toLowerCase()
        .trim();

    document
        .querySelectorAll(".card")
        .forEach(card => {

            const nome =
                card.dataset.nome;

            const cat =
                card.dataset.categoria;

            const nomeOk =
                nome.includes(texto);

            const categoriaOk =
                categoriaAtual === "Todos"
                ||
                cat === categoriaAtual;

            card.style.display =
                nomeOk && categoriaOk
                ? ""
                : "none";

        });

}


function mover(direcao){

    const lista =
        document.getElementById(
            "lista"
        );

    if(!lista){
        return;
    }

    lista.scrollBy({

        left:
            direcao * 330,

        behavior:
            "smooth"

    });

}


setInterval(() => {

    const lista =
        document.getElementById(
            "lista"
        );

    if(!lista){
        return;
    }

    if(!lista.matches(":hover")){

        if(
            lista.scrollLeft +
            lista.clientWidth >=
            lista.scrollWidth - 10
        ){

            lista.scrollTo({

                left:0,

                behavior:"smooth"

            });

        }else{

            lista.scrollBy({

                left:330,

                behavior:"smooth"

            });

        }

    }

},4500);

</script>

</body>

</html>
"""


# =========================================================
# FORMULÁRIO DE BOT
# =========================================================

BOT_FORM_HTML = r"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>Publicar projeto | Grupos+</title>

<style>

*{
    box-sizing:border-box;

    font-family:Arial;
}

body{

    margin:0;

    background:#070707;

    color:white;

}

.box{

    max-width:650px;

    margin:
        50px auto;

    padding:30px;

    background:#111;

    border:
        1px solid
        #450000;

    border-radius:15px;

    box-shadow:
        0 10px 40px
        #000;

}

a{

    color:#c00000;

    text-decoration:none;

}

h1{

    margin-top:25px;

}

h1 span{

    color:#c00000;

}

label{

    display:block;

    margin:
        18px 0 7px;

    font-weight:bold;

}

input,
textarea,
select{

    width:100%;

    padding:13px;

    background:#080808;

    color:white;

    border:
        1px solid
        #420000;

    border-radius:8px;

    outline:none;

}

input:focus,
textarea:focus,
select:focus{

    border-color:#a00000;

}

textarea{

    min-height:120px;

    resize:vertical;

}

button{

    width:100%;

    margin-top:20px;

    padding:14px;

    border:0;

    border-radius:8px;

    background:#900000;

    color:white;

    font-weight:bold;

    cursor:pointer;

}

button:hover{

    background:#c00000;

}

</style>

</head>

<body>

<div class="box">

<a href="{{ url_for('area_bots') }}">
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
    name="nome"
    maxlength="80"
    placeholder="Ex: Takeshi Bot"
    required
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
>

<button type="submit">
    🚀 Publicar projeto
</button>

</form>

</div>

</body>

</html>
"""


# =========================================================
# INICIAR
# =========================================================

criar_banco()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
