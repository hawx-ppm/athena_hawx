from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = '6898883366:AAGgyFo4a2r3jVpNLuMe5NG0xg-SUDkVG9E'

def apresentacao(context: CallbackContext) -> None:
    context.bot.send_message(chat_id=context.job.context['chat_id'],
                             text='Olá! Eu sou Jarvis Hawx, seu assistente musical. Como posso ajudar?')

def start(update, context):
    update.message.reply_text('Olá! Eu sou Jarvis Hawx, seu assistente musical. Como posso ajudar?')

def main() -> None:
    updater = Updater(TOKEN)  # Remova o argumento 'use_context=True'

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))

    # Adiciona uma apresentação ao iniciar
    context = CallbackContext(dispatcher)
    context.job_queue.run_once(apresentacao, 0, context={'chat_id': '2137034653'})

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
