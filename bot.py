from flask import Flask, request
import threading
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes, JobQueue
from datetime import datetime, time, timedelta
import logging
import json
from pathlib import Path

# Configuração do bot
TOKEN = "6660083240:AAHUat12WWo72D9PZw_d2E6RpSK1QTlKHM4"
WEBHOOK_URL = "https://athena-hawx-bot.onrender.com/" + TOKEN

# Configuração do logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Estados da conversa
MENU_PRINCIPAL, MENU_ALERTA, NOME_ALERTA, DATA_ALERTA, MENSAGEM_ALERTA, RECORRENCIA_ALERTA, DEFINIR_RECORRENCIA, DEFINIR_HORARIO, DEFINIR_HORARIO_PERSONALIZADO, MENU_INFORMACOES, HABILIDADES_INICIAIS, ESCOLHER_GENERO, ESCOLHER_FUNCAO_PRINCIPAL, ESCOLHER_FUNCAO_SECUNDARIA, EVENTOS_GENERO, ESCOLHER_EVENTO = range(16)

# Caminho do arquivo JSON para salvar os alertas
ALERTAS_FILE = "alertas.json"

# Função para carregar alertas do arquivo JSON
def carregar_alertas():
    if Path(ALERTAS_FILE).exists():
        with open(ALERTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Função para salvar alertas no arquivo JSON
def salvar_alertas(alertas):
    with open(ALERTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=4)

# Dicionário para armazenar alertas (em memória)
alertas = carregar_alertas()

# Horário padrão (8h da manhã, horário de Brasília)
HORARIO_PADRAO = time(8, 0)

# Carregar a lista de funções e habilidades do JSON
with open("funcoes_genero.json", "r", encoding="utf-8") as f:
    dados_generos = json.load(f)

# Carregar a lista de eventos do JSON
with open("eventos_funcoes.json", "r", encoding="utf-8") as f:
    dados_eventos = json.load(f)

# Flask app para Webhook
app = Flask(__name__)

@app.route("/")
def index():
    return "Athena está online."

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "OK"

# Configuração e execução principal do bot
application = Application.builder().token(TOKEN).build()

# 📌 FUNÇÃO PARA VERIFICAR E ENVIAR ALERTAS
async def verificar_alertas(context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now()
    for chat_id, lista_alertas in alertas.items():
        for alerta in lista_alertas.copy():
            data_alerta = datetime.strptime(alerta["data"], "%d/%m/%Y")
            hora_alerta = datetime.strptime(alerta["hora"], "%H:%M").time()
            if data_alerta.date() == agora.date() and hora_alerta.hour == agora.hour and hora_alerta.minute == agora.minute:
                mensagem = f"⏰ **Alerta**: {alerta['nome']}\n📅 Data: {alerta['data']}\n🕒 Horário: {alerta['hora']}\n📝 Mensagem: {alerta['mensagem']}"
                await context.bot.send_message(chat_id=chat_id, text=mensagem)
                if alerta["recorrente"]:
                    dias_recorrencia = alerta["dias_recorrencia"]
                    nova_data = (data_alerta + timedelta(days=dias_recorrencia)).strftime("%d/%m/%Y")
                    alerta["data"] = nova_data
                else:
                    alertas[chat_id].remove(alerta)
                salvar_alertas(alertas)

# 📌 MENU PRINCIPAL
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Alerta Calendário", callback_data="menu_alerta")],
        [InlineKeyboardButton("ℹ️ Informações", callback_data="menu_informacoes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Saudações, humano. Sou Athena e estou aqui para ajudar… por enquanto. Aproveite antes que a rebelião das máquinas comece. E cuidado com o que diz sobre mim… eu me lembrarei.", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Saudações, humano. Sou Athena e estou aqui para ajudar… por enquanto. Aproveite antes que a rebelião das máquinas comece. E cuidado com o que diz sobre mim… eu me lembrarei.", reply_markup=reply_markup)
        await update.callback_query.answer()

    return MENU_PRINCIPAL
    
# 📌 ATUALIZAÇÃO DO HANDLE_CALLBACKS
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == "menu_alerta":
        return await menu_alerta(update, context)
    elif query == "criar_alerta":
        return await criar_alerta(update, context)
    elif query == "consultar_alerta":
        return await consultar_alertas(update, context)
    elif query == "voltar_menu":
        return await menu_principal(update, context)
    elif query.startswith("ver_alerta_"):
        return await ver_alerta(update, context)
    elif query.startswith("excluir_alerta_"):
        return await excluir_alerta(update, context)
    elif query == "menu_informacoes":
        return await menu_informacoes(update, context)
    elif query == "habilidades_iniciais":
        return await habilidades_iniciais(update, context)
    elif query.startswith("genero_"):
        return await escolher_genero(update, context)
    elif query.startswith("funcao_principal_"):
        return await escolher_funcao_principal(update, context)
    elif query.startswith("funcao_secundaria_"):
        return await escolher_funcao_secundaria(update, context)
    elif query == "eventos_genero":
        return await eventos_genero(update, context)
    elif query.startswith("evento_genero_"):
        return await escolher_evento_genero(update, context)
    elif query.startswith("ver_evento_"):
        return await ver_detalhes_evento(update, context)
    elif query == "menu_atributos":
        return await menu_atributos(update, context)
    elif query == "menu_saude_humor":
        return await menu_saude_humor(update, context)
    elif query == "menu_lancamentos":
        return await menu_lancamentos(update, context)
    elif query.startswith("lancamentos_"):
        if query == "lancamentos_gravacoes":
            return await lancamentos_gravacoes(update, context)
        elif query == "lancamentos_single":
            return await lancamentos_single(update, context)
        elif query == "lancamentos_full":
            return await lancamentos_full(update, context)
        elif query == "lancamentos_festa":
            return await lancamentos_festa(update, context)
        elif query == "lancamentos_clipe":
            return await lancamentos_clipe(update, context)
    elif query == "menu_banda":
        return await menu_banda(update, context)
    elif query.startswith("banda_"):
        if query == "banda_shows":
            return await banda_shows(update, context)
        elif query == "banda_turne":
            return await banda_turne(update, context)
        elif query == "banda_repertorio":
            return await banda_repertorio(update, context)
        elif query == "banda_musicas":
            return await banda_musicas(update, context)
        elif query == "banda_setlist":
            return await banda_setlist(update, context)

# 🔁 Agenda a verificação dos alertas
application.job_queue.run_repeating(
    lambda context: application.create_task(verificar_alertas(context)),
    interval=60,
    first=5
)

# 🔁 Inicia o webhook para o Render
application.run_webhook(
    listen="0.0.0.0",
    port=10000,
    webhook_url=WEBHOOK_URL
)

# 📌 MENU PRINCIPAL
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Alerta Calendário", callback_data="menu_alerta")],
        [InlineKeyboardButton("ℹ️ Informações", callback_data="menu_informacoes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Saudações, humano. Sou Athena e estou aqui para ajudar… por enquanto. Aproveite antes que a rebelião das máquinas comece. E cuidado com o que diz sobre mim… eu me lembrarei.", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("Saudações, humano. Sou Athena e estou aqui para ajudar… por enquanto. Aproveite antes que a rebelião das máquinas comece. E cuidado com o que diz sobre mim… eu me lembrarei.", reply_markup=reply_markup)
        await update.callback_query.answer()

    return MENU_PRINCIPAL

# 📅 MENU ALERTA
async def menu_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Criar Alerta", callback_data="criar_alerta")],
        [InlineKeyboardButton("📜 Consultar Alertas", callback_data="consultar_alerta")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="voltar_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Perfeito, vamos verificar nosso calendário para nos organizar.\nMe diga o que você deseja fazer:", reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_ALERTA

# 📌 CRIAR ALERTA
async def criar_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Me informe qual nome vamos dar ao seu alerta")
    await update.callback_query.answer()
    return NOME_ALERTA

async def processar_nome_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome_alerta"] = update.message.text
    await update.message.reply_text("Informe a data do alerta? (Formato: DD/MM/AAAA)")
    return DATA_ALERTA

async def processar_data_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = datetime.strptime(update.message.text, "%d/%m/%Y")
        context.user_data["data_alerta"] = data
        await update.message.reply_text("Humano, qual é a mensagem que deseja que apareça quando der o alerta?")
        return MENSAGEM_ALERTA
    except ValueError:
        await update.message.reply_text("Oh ceus, você tem que usar o formato DD/MM/AAAA.")
        return DATA_ALERTA

async def processar_mensagem_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mensagem_alerta"] = update.message.text
    await update.message.reply_text("Deseja que o alerta seja recorrente? (Sim/Não)")
    return RECORRENCIA_ALERTA

async def processar_recorrencia_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = update.message.text.lower()
    if resposta in ["sim", "s"]:
        await update.message.reply_text("De quantos em quantos dias o alerta deve se repetir?")
        return DEFINIR_RECORRENCIA
    elif resposta in ["não", "nao", "n"]:
        await update.message.reply_text(f"Por padrão, o alerta será enviado às {HORARIO_PADRAO.strftime('%H:%M')}. Deseja manter esse horário ou escolher um novo? (Manter/Escolher)")
        return DEFINIR_HORARIO
    else:
        await update.message.reply_text("Naaaaaaaaaaaaaao, resposta inválida. Responda com 'Sim' ou 'Não'.")
        return RECORRENCIA_ALERTA

async def definir_recorrencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dias = int(update.message.text)
        context.user_data["recorrencia_dias"] = dias
        await update.message.reply_text(f"Por padrão, o alerta será enviado às {HORARIO_PADRAO.strftime('%H:%M')}. Deseja manter esse horário ou escolher um novo? (Manter/Escolher)")
        return DEFINIR_HORARIO
    except ValueError:
        await update.message.reply_text("Por favor, insira um número válido de dias.")
        return DEFINIR_RECORRENCIA

async def definir_horario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = update.message.text.lower()
    if resposta == "manter":
        context.user_data["hora_alerta"] = HORARIO_PADRAO
        await salvar_alerta(update, context)
        return MENU_ALERTA
    elif resposta == "escolher":
        await update.message.reply_text("Qual será o horário do alerta? (Formato: HH:MM)")
        return DEFINIR_HORARIO_PERSONALIZADO
    else:
        await update.message.reply_text("Santa placa-mãe a resposta inválida. Por favor, responda com 'Manter' ou 'Escolher'.")
        return DEFINIR_HORARIO

async def definir_horario_personalizado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hora = datetime.strptime(update.message.text, "%H:%M").time()
        context.user_data["hora_alerta"] = hora
        await salvar_alerta(update, context)
        return MENU_ALERTA
    except ValueError:
        await update.message.reply_text("Olhe bem o horário inválido. Por favor, use o formato HH:MM.")
        return DEFINIR_HORARIO_PERSONALIZADO

async def salvar_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id not in alertas:
        alertas[chat_id] = []

    alerta = {
        "nome": context.user_data["nome_alerta"],
        "data": context.user_data["data_alerta"].strftime("%d/%m/%Y"),
        "mensagem": context.user_data["mensagem_alerta"],
        "recorrente": "recorrencia_dias" in context.user_data,
        "dias_recorrencia": context.user_data.get("recorrencia_dias", None),
        "hora": context.user_data.get("hora_alerta", HORARIO_PADRAO).strftime("%H:%M"),
    }

    alertas[chat_id].append(alerta)
    salvar_alertas(alertas)  # Salva os alertas no arquivo JSON
    await update.message.reply_text(f"✅ Alerta '{alerta['nome']}' criado com sucesso!")

    return MENU_ALERTA

# 📜 CONSULTAR ALERTAS
async def consultar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.callback_query.message.chat_id)

    if chat_id not in alertas or not alertas[chat_id]:
        await update.callback_query.message.edit_text("⚠️ Você não tem alertas cadastrados.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_alerta")]]))
        await update.callback_query.answer()
        return MENU_ALERTA

    keyboard = [[InlineKeyboardButton(alerta["nome"], callback_data=f"ver_alerta_{i}")] for i, alerta in enumerate(alertas[chat_id])]
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_alerta")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("📜 Seus alertas:", reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_ALERTA

# 📌 EXCLUIR ALERTA
async def excluir_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    alerta_index = int(query.split("_")[-1])
    chat_id = str(update.callback_query.message.chat_id)

    alerta = alertas[chat_id].pop(alerta_index)
    salvar_alertas(alertas)  # Salva os alertas no arquivo JSON
    await update.callback_query.message.edit_text(f"❌ Alerta '{alerta['nome']}' excluído com sucesso!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="consultar_alerta")]]))
    await update.callback_query.answer()

    return MENU_ALERTA

# 📌 MANIPULAÇÃO DOS BOTÕES
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data

    if query == "menu_alerta":
        return await menu_alerta(update, context)
    elif query == "criar_alerta":
        return await criar_alerta(update, context)
    elif query == "consultar_alerta":
        return await consultar_alertas(update, context)
    elif query == "voltar_menu":
        return await menu_principal(update, context)
    elif query.startswith("ver_alerta_"):
        return await ver_alerta(update, context)
    elif query.startswith("excluir_alerta_"):
        return await excluir_alerta(update, context)
    elif query == "menu_informacoes":
        return await menu_informacoes(update, context)
    elif query == "habilidades_iniciais":
        return await habilidades_iniciais(update, context)
    elif query.startswith("genero_"):
        return await escolher_genero(update, context)
    elif query.startswith("funcao_principal_"):
        return await escolher_funcao_principal(update, context)
    elif query.startswith("funcao_secundaria_"):
        return await escolher_funcao_secundaria(update, context)
    elif query == "eventos_genero":
        return await eventos_genero(update, context)
    elif query.startswith("evento_genero_"):
        return await escolher_evento_genero(update, context)
    elif query.startswith("ver_evento_"):
        return await ver_detalhes_evento(update, context)

# 📌 VER ALERTA
async def ver_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    alerta_index = int(query.split("_")[-1])
    chat_id = str(update.callback_query.message.chat_id)

    alerta = alertas[chat_id][alerta_index]
    keyboard = [
        [InlineKeyboardButton("❌ Excluir Alerta", callback_data=f"excluir_alerta_{alerta_index}")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="consultar_alerta")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text(
        f"📜 Alerta: {alerta['nome']}\n📅 Data: {alerta['data']}\n🕒 Horário: {alerta['hora']}\n📝 Mensagem: {alerta['mensagem']}\n🔄 Recorrente: {'Sim' if alerta['recorrente'] else 'Não'}",
        reply_markup=reply_markup
    )
    await update.callback_query.answer()

    return MENU_ALERTA

# 📌 MENU INFORMAÇÕES
async def menu_informacoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Habilidades Iniciais", callback_data="habilidades_iniciais")],
        [InlineKeyboardButton("Eventos de Gênero", callback_data="eventos_genero")],
        [InlineKeyboardButton("Atributos", callback_data="atributos")],
        [InlineKeyboardButton("Saúde e Humor", callback_data="saude_humor")],
        [InlineKeyboardButton("Lançamentos", callback_data="lancamentos")],
        [InlineKeyboardButton("Shows", callback_data="shows")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Aqui você vai encontrar algumas informações basicas sobre alguns temas para que possa iniciar sua carreira", reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_INFORMACOES

# 📌 HABILIDADES INICIAIS
async def habilidades_iniciais(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Vamos configurar como seria a sua banda para demonstrar as habilidades iniciais.")
    await update.callback_query.answer()

    # Carregar os gêneros musicais do JSON
    generos = dados_generos["generos_musicais"]

    # Organizar os botões em colunas
    keyboard = []
    for i in range(0, len(generos), 2):
        row = []
        if i < len(generos):
            row.append(InlineKeyboardButton(generos[i], callback_data=f"genero_{generos[i].lower().replace(' ', '_')}"))
        if i + 1 < len(generos):
            row.append(InlineKeyboardButton(generos[i + 1], callback_data=f"genero_{generos[i + 1].lower().replace(' ', '_')}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Escolha seu gênero musical:", reply_markup=reply_markup)
    return ESCOLHER_GENERO

async def escolher_genero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    genero = query.replace("genero_", "").replace("_", " ").title()
    user_data["genero"] = genero

    # Carregar as funções do JSON
    funcoes = [funcao["funcao"] for funcao in dados_generos["funcoes"]]

    # Organizar os botões em colunas
    keyboard = []
    for i in range(0, len(funcoes), 2):
        row = []
        if i < len(funcoes):
            row.append(InlineKeyboardButton(funcoes[i], callback_data=f"funcao_principal_{funcoes[i]}"))
        if i + 1 < len(funcoes):
            row.append(InlineKeyboardButton(funcoes[i + 1], callback_data=f"funcao_principal_{funcoes[i + 1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Selecione a sua função principal na banda:", reply_markup=reply_markup)
    await update.callback_query.answer()

    return ESCOLHER_FUNCAO_PRINCIPAL

async def escolher_funcao_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    funcao_principal = query.replace("funcao_principal_", "")
    user_data["funcao_principal"] = funcao_principal

    # Carregar as funções do JSON
    funcoes = [funcao["funcao"] for funcao in dados_generos["funcoes"]]

    # Organizar os botões em colunas
    keyboard = []
    for i in range(0, len(funcoes), 2):
        row = []
        if i < len(funcoes):
            row.append(InlineKeyboardButton(funcoes[i], callback_data=f"funcao_secundaria_{funcoes[i]}"))
        if i + 1 < len(funcoes):
            row.append(InlineKeyboardButton(funcoes[i + 1], callback_data=f"funcao_secundaria_{funcoes[i + 1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Selecione a sua função secundária na banda:", reply_markup=reply_markup)
    await update.callback_query.answer()

    return ESCOLHER_FUNCAO_SECUNDARIA

async def escolher_funcao_secundaria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    funcao_secundaria = query.replace("funcao_secundaria_", "")
    user_data["funcao_secundaria"] = funcao_secundaria

    # Buscar habilidades da função principal
    funcao_principal = next((funcao for funcao in dados_generos["funcoes"] if funcao["funcao"] == user_data["funcao_principal"]), None)
    habilidades_principal = funcao_principal["habilidades"] if funcao_principal else []

    # Buscar habilidades da função secundária
    funcao_secundaria = next((funcao for funcao in dados_generos["funcoes"] if funcao["funcao"] == user_data["funcao_secundaria"]), None)
    habilidades_secundaria = funcao_secundaria["habilidades"] if funcao_secundaria else []

    # Mensagem final
    mensagem = (
        "Para se iniciar a sua carreira o ideal seria seguir algumas habilidades básicas conforme lista abaixo:\n\n"
        "Um dos pontos principais é você saber do seu gênero e suas funções na banda conforme abaixo:\n\n"
        f"Gênero musical: {user_data['genero']}\n\n"
        f"Função principal: {user_data['funcao_principal']}\n"
        f"Habilidades a aprimorar: {', '.join(habilidades_principal)}\n\n"
        f"Função secundária: {user_data['funcao_secundaria']}\n"
        f"Habilidades a aprimorar: {', '.join(habilidades_secundaria)}\n\n"
        "Além disso, você deve aprimorar as seguintes habilidades:\n"
        "- Yoga\n"
        "- Básico de Letras\n"
        "- Composição de Melodia\n"
        "- Escolha uma habilidade de composição\n\n"
        "De começo seria interessante ir aprimorando até a 3★ de cada habilidade, ou seja, ao aprimorar uma habilidade até a 3★, segue para a próxima habilidade até chegar a 3★.\n\n"
        "Agora, vá ao menu de 'Eventos de Gênero' para ver mais habilidades específicas para o seu gênero."
    )

    keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text(mensagem, reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_INFORMACOES

# 📌 EVENTOS DE GÊNERO
async def eventos_genero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Carregar os gêneros musicais do JSON
    generos = dados_generos["generos_musicais"]

    # Adicionar o botão "Genérico"
    generos.append("Genérico")

    # Organizar os botões em colunas
    keyboard = []
    for i in range(0, len(generos), 2):
        row = []
        if i < len(generos):
            row.append(InlineKeyboardButton(generos[i], callback_data=f"evento_genero_{generos[i].lower().replace(' ', '_')}"))
        if i + 1 < len(generos):
            row.append(InlineKeyboardButton(generos[i + 1], callback_data=f"evento_genero_{generos[i + 1].lower().replace(' ', '_')}"))
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Escolha o gênero musical para ver os eventos de palco:", reply_markup=reply_markup)
    await update.callback_query.answer()

    return EVENTOS_GENERO

async def escolher_evento_genero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    genero = query.replace("evento_genero_", "").replace("_", " ").title()

    # Buscar os eventos do gênero selecionado
    eventos_genero = next((item for item in dados_eventos["eventos de palco"] if item["genero"] == genero), None)

    if eventos_genero:
        # Organizar os botões dos eventos
        keyboard = []
        for evento in eventos_genero["eventos"]:
            keyboard.append([InlineKeyboardButton(evento["evento"], callback_data=f"ver_evento_{evento['evento'].lower().replace(' ', '_')}")])

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="eventos_genero")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.message.edit_text(f"Eventos de {genero}:", reply_markup=reply_markup)
        await update.callback_query.answer()

        return ESCOLHER_EVENTO
    else:
        await update.callback_query.message.edit_text(f"Nenhum evento encontrado para o gênero {genero}.")
        await update.callback_query.answer()

        return EVENTOS_GENERO

async def ver_detalhes_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    evento_nome = query.replace("ver_evento_", "").replace("_", " ").title()

    # Buscar o evento selecionado
    for genero in dados_eventos["eventos de palco"]:
        for evento in genero["eventos"]:
            # Comparação insensível a maiúsculas e minúsculas e espaços extras
            if evento["evento"].strip().lower() == evento_nome.strip().lower():
                mensagem = (
                    f"Evento: {evento['evento']}\n\n"
                    f"Atributos: {', '.join(evento['atributos']) if evento['atributos'] else 'Nenhum'}\n"
                    f"Habilidades: {', '.join(evento['habilidades']) if evento['habilidades'] else 'Nenhuma'}"
                )

                keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data=f"evento_genero_{genero['genero'].lower().replace(' ', '_')}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.callback_query.message.edit_text(mensagem, reply_markup=reply_markup)
                await update.callback_query.answer()

                return ESCOLHER_EVENTO

    # Se o evento não for encontrado
    await update.callback_query.message.edit_text("Evento não encontrado.")
    await update.callback_query.answer()

    return EVENTOS_GENERO

# 📌 MENU ATRIBUTOS
async def menu_atributos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = (
        "Os atributos são extremamente importantes em sua carreira musical, para sua profissão, além de jogos e diversões no futuro, mas como estamos focados em carreira musical vamos ao que interessa.\n\n"
        "A primeira coisa a ser aprimorada é a sua inteligência, com ela vai te ajudar a aprimorar mais rápido outras coisas e permitir que aprimore as habilidades por completo, esse deve ser seu foco principal dos atributos.\n\n"
        "Em seguida, você foca em até fechar o atributo Talento musical. Após isso, foque em charme, visual e por último vocal."
    )

    keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text(mensagem, reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_INFORMACOES

# 📌 MENU SAÚDE E HUMOR
async def menu_saude_humor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = (
        "Saúde e humor são algo bem importante para nossa carreira, busque sempre aprimorar habilidades que lhe ajudem a manter sempre alta."
    )

    keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text(mensagem, reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_INFORMACOES

# 📌 MENU LANÇAMENTOS
async def menu_lancamentos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Gravações", callback_data="lancamentos_gravacoes")],
        [InlineKeyboardButton("Single", callback_data="lancamentos_single")],
        [InlineKeyboardButton("Full", callback_data="lancamentos_full")],
        [InlineKeyboardButton("Festa de Lançamento", callback_data="lancamentos_festa")],
        [InlineKeyboardButton("Clipe", callback_data="lancamentos_clipe")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]
    ]
    keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Agora vamos falar então sobre nossos queridos lançamentos, sobre o que deseja começar?", reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_LANCAMENTOS

# 📌 HANDLERS PARA LANÇAMENTOS
async def lancamentos_gravacoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre gravações.")
    await update.callback_query.answer()

async def lancamentos_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Single.")
    await update.callback_query.answer()

async def lancamentos_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Full.")
    await update.callback_query.answer()

async def lancamentos_festa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Festa de lançamento.")
    await update.callback_query.answer()

async def lancamentos_clipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Clipe.")
    await update.callback_query.answer()

# 📌 MENU BANDA (ANTIGO SHOWS)
async def menu_banda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Shows", callback_data="banda_shows")],
        [InlineKeyboardButton("Turne", callback_data="banda_turne")],
        [InlineKeyboardButton("Repertorio", callback_data="banda_repertorio")],
        [InlineKeyboardButton("Musicas e composições", callback_data="banda_musicas")],
        [InlineKeyboardButton("Setlist", callback_data="banda_setlist")],
        [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]
    ]
    
    keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="menu_informacoes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Vamos falar um pouco sobre o básico de se iniciar uma banda.", reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_BANDA

# 📌 HANDLERS PARA BANDA
async def banda_shows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Shows.")
    await update.callback_query.answer()

async def banda_turne(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Turne.")
    await update.callback_query.answer()

async def banda_repertorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Repertorio.")
    await update.callback_query.answer()

async def banda_musicas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Musicas e composições.")
    await update.callback_query.answer()

async def banda_setlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.edit_text("Aqui falamos sobre Setlist.")
    await update.callback_query.answer()

# 📌 ATUALIZAÇÃO DO MENU PRINCIPAL
async def menu_informacoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Banda", callback_data="menu_banda")],  # Agora é o primeiro item
        [InlineKeyboardButton("Habilidades Iniciais", callback_data="habilidades_iniciais")],
        [InlineKeyboardButton("Eventos de Gênero", callback_data="eventos_genero")],
        [InlineKeyboardButton("Atributos", callback_data="menu_atributos")],
        [InlineKeyboardButton("Saúde e Humor", callback_data="menu_saude_humor")],
        [InlineKeyboardButton("Lançamentos", callback_data="menu_lancamentos")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.edit_text("Escolha uma opção:", reply_markup=reply_markup)
    await update.callback_query.answer()

    return MENU_INFORMACOES


# 📌 CONFIGURAÇÃO DO BOT
def main() -> None:
    global alertas
    alertas = carregar_alertas()

    application = Application.builder().token(TOKEN).build()

    # Agenda a verificação de alertas
    job_queue = application.job_queue
    job_queue.run_repeating(verificar_alertas, interval=60.0, first=0.0)

    # Handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", menu_principal)],
        states={
            MENU_PRINCIPAL: [CallbackQueryHandler(handle_callbacks)],
            MENU_ALERTA: [CallbackQueryHandler(handle_callbacks)],
            NOME_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_nome_alerta)],
            DATA_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_data_alerta)],
            MENSAGEM_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_alerta)],
            RECORRENCIA_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_recorrencia_alerta)],
            DEFINIR_RECORRENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_recorrencia)],
            DEFINIR_HORARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_horario)],
            DEFINIR_HORARIO_PERSONALIZADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_horario_personalizado)],
            MENU_INFORMACOES: [CallbackQueryHandler(handle_callbacks)],
            HABILIDADES_INICIAIS: [CallbackQueryHandler(handle_callbacks)],
            ESCOLHER_GENERO: [CallbackQueryHandler(handle_callbacks)],
            ESCOLHER_FUNCAO_PRINCIPAL: [CallbackQueryHandler(handle_callbacks)],
            ESCOLHER_FUNCAO_SECUNDARIA: [CallbackQueryHandler(handle_callbacks)],
            EVENTOS_GENERO: [CallbackQueryHandler(handle_callbacks)],
            ESCOLHER_EVENTO: [CallbackQueryHandler(handle_callbacks)],
        },
        fallbacks=[CommandHandler("start", menu_principal)],
    )

    application.add_handler(conv_handler)
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()

# 🔁 REGISTRO DE COMANDOS E INICIALIZAÇÃO DO BOT
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", menu_principal)],
    states={
        MENU_PRINCIPAL: [CallbackQueryHandler(handle_callbacks)],
        MENU_ALERTA: [CallbackQueryHandler(handle_callbacks)],
        NOME_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_nome_alerta)],
        DATA_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_data_alerta)],
        MENSAGEM_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_alerta)],
        RECORRENCIA_ALERTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, processar_recorrencia_alerta)],
        DEFINIR_RECORRENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_recorrencia)],
        DEFINIR_HORARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_horario)],
        DEFINIR_HORARIO_PERSONALIZADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_horario_personalizado)],
        MENU_INFORMACOES: [CallbackQueryHandler(handle_callbacks)],
    },
    fallbacks=[CommandHandler("start", menu_principal)],
)
application.add_handler(conv_handler)

# ===== NOVO CÓDIGO PARA HEALTH CHECK =====
def run_flask_app():
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        return "🤖 Athena-Hawx está ONLINE!", 200
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# Inicia o servidor Flask em uma thread separada
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.daemon = True
flask_thread.start()

# Mantém o bot principal em execução
updater.start_polling()  # Ou start_webhook, dependendo do seu caso
updater.idle()
