from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime
import logging

# Configuração do bot
TOKEN = '6660083240:AAGeSpKaAbrahojwp0cq8agRxMs2hYpwZAg'
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados da conversa
ESCOLHER_OPCAO, CRIAR_NOME, CRIAR_DATA, CRIAR_MENSAGEM, CRIAR_RECORRENCIA, DEFINIR_RECORRENCIA, CONSULTAR_ALERTAS, EXCLUIR_ALERTA = range(8)

# Dicionário para armazenar alertas (em memória)
alertas = {}

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Eu sou Athena Hawx, sua assistente. Use o comando /alerta_calendario para gerenciar seus alertas.")

# Função para exibir o menu principal
async def alerta_calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Criar Alerta", callback_data='criar_alerta')],
        [InlineKeyboardButton("Consultar Alertas", callback_data='consultar_alertas')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Perfeito, vamos verificar nosso calendário para nos organizar. Me diga o que você deseja fazer:",
        reply_markup=reply_markup
    )
    return ESCOLHER_OPCAO

# Processar escolha
async def escolher_opcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'criar_alerta':
        await query.edit_message_text("Vamos criar um novo alerta. Qual será o nome do alerta?")
        return CRIAR_NOME
    elif query.data == 'consultar_alertas':
        return await consultar_alertas(update, context)

# Pergunta nome do alerta
async def criar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nome_alerta'] = update.message.text
    await update.message.reply_text("Qual será a data do alerta? (Formato: DD/MM/AAAA)")
    return CRIAR_DATA

# Pergunta data do alerta
async def criar_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = datetime.strptime(update.message.text, "%d/%m/%Y")
        context.user_data['data_alerta'] = data
        await update.message.reply_text("Qual será a mensagem do alerta?")
        return CRIAR_MENSAGEM
    except ValueError:
        await update.message.reply_text("Data inválida. Por favor, use o formato DD/MM/AAAA.")
        return CRIAR_DATA

# Pergunta mensagem do alerta
async def criar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mensagem_alerta'] = update.message.text
    await update.message.reply_text("O alerta será recorrente? (Sim/Não)")
    return CRIAR_RECORRENCIA

# Processa a recorrência
async def criar_recorrencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resposta = update.message.text.lower()
    
    if resposta in ['sim', 's']:
        await update.message.reply_text("Quantos dias para o próximo alerta recorrente?")
        return DEFINIR_RECORRENCIA
    else:
        await salvar_alerta(update, context, recorrente=False)
        return ConversationHandler.END

# Define recorrência
async def definir_recorrencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dias = int(update.message.text)
        context.user_data['recorrencia_dias'] = dias
        await salvar_alerta(update, context, recorrente=True)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Por favor, insira um número válido de dias.")
        return DEFINIR_RECORRENCIA

# Salva o alerta
async def salvar_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE, recorrente: bool):
    chat_id = str(update.message.chat_id)
    if chat_id not in alertas:
        alertas[chat_id] = []

    alerta = {
        'nome': context.user_data['nome_alerta'],
        'data': context.user_data['data_alerta'].strftime("%d/%m/%Y"),
        'mensagem': context.user_data['mensagem_alerta'],
        'recorrente': recorrente,
        'dias_recorrencia': context.user_data.get('recorrencia_dias', None)
    }

    alertas[chat_id].append(alerta)
    await update.message.reply_text(f"Alerta '{alerta['nome']}' criado com sucesso!")

# Consultar alertas
async def consultar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = str(query.message.chat.id)
    if chat_id in alertas and alertas[chat_id]:
        keyboard = [
            [InlineKeyboardButton(a['nome'], callback_data=f"alerta_{i}")] 
            for i, a in enumerate(alertas[chat_id])
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Seus alertas:", reply_markup=reply_markup)
        return CONSULTAR_ALERTAS
    else:
        await query.edit_message_text("Você não tem alertas cadastrados.")
        return ConversationHandler.END

# Processa alerta selecionado
async def processar_alerta_selecionado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    alerta_index = int(query.data.split('_')[1])
    chat_id = str(query.message.chat.id)
    alerta = alertas[chat_id][alerta_index]

    keyboard = [
        [InlineKeyboardButton("Excluir Alerta", callback_data=f"excluir_{alerta_index}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Alerta: {alerta['nome']}\nData: {alerta['data']}\nRecorrente: {'Sim' if alerta['recorrente'] else 'Não'}",
        reply_markup=reply_markup
    )
    return EXCLUIR_ALERTA

# Excluir alerta
async def excluir_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    alerta_index = int(query.data.split('_')[1])
    chat_id = str(query.message.chat.id)

    del alertas[chat_id][alerta_index]
    await query.edit_message_text("Alerta excluído com sucesso.")
    return ConversationHandler.END

# Cancelar conversa
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

# Configuração do bot
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("alerta_calendario", alerta_calendario)],
        states={
            ESCOLHER_OPCAO: [CallbackQueryHandler(escolher_opcao)],
            CRIAR_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, criar_nome)],
            CRIAR_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, criar_data)],
            CRIAR_MENSAGEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, criar_mensagem)],
            CRIAR_RECORRENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, criar_recorrencia)],
            DEFINIR_RECORRENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, definir_recorrencia)],
            CONSULTAR_ALERTAS: [CallbackQueryHandler(processar_alerta_selecionado)],
            EXCLUIR_ALERTA: [CallbackQueryHandler(excluir_alerta)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
