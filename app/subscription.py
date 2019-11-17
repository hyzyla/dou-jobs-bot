from telegram import Update, CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    MessageHandler,
    Filters,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    Dispatcher,
)

from app import db
from app.enum import AddSubscriptionStates, SubscriptionPageState
from app.models import City, Position, Subscription
from app.utils import get_cities_keyboard, update_list_page, get_positions_keyboard


def add_subscription(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Для підпсання на нові вакансії потрібно пройти невелике опитування. "
        "Якщо бажаєте відхили опитування введіть команду /cancel"
    )
    update.message.reply_text(
        text=(
            "Вкажіть місто де потрібно шукати вакансії, для цього оберіть один "
            "і з варіантів зі списку нижче. Використовуйте кнопки ⬅️️ та ➡️ для навігації між "
            "сторінками списку"
        ),
        reply_markup=get_cities_keyboard(),
    )
    return AddSubscriptionStates.city


def add_city_navigate(update: Update, context: CallbackContext):
    return update_list_page(update, prefix='city', func=get_cities_keyboard)


def add_city(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    _, suffix = callback_query.data.strip().split('.')
    city = City.query.filter_by(id=suffix).first()

    callback_query.answer(
        callback_query=callback_query.id,
        text=f"Дякую, я запам'ятав твій вибір",
        cache_time=60,
    )
    message: Message = callback_query.message
    message.reply_text(
        text=(
            f"Ви обрали місто {city.name}. Залишилося додати категорію "
            f"в якій потрібно шукати вакансії. Оберіть один і з варіантів "
            f"перелічених нижче 👇🏼"
        ),
        reply_markup=get_positions_keyboard(),
    )
    context.user_data['city_id'] = city.id
    context.user_data['city_name'] = city.name

    return AddSubscriptionStates.position


def add_position_navigate(update: Update, context: CallbackContext):
    return update_list_page(update, prefix='position', func=get_positions_keyboard)


def add_subscription_fallback(update: Update, context: CallbackContext):
    update.message.reply_text("Оберіть варіант зі списку вище")


def add_position(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    _, suffix = callback_query.data.strip().split('.')
    position = Position.query.filter_by(id=suffix).first()
    city_name: str = context.user_data['city_name']
    city_id: str = context.user_data['city_id']
    message: Message = callback_query.message

    subscription = Subscription(
        chat_id=message.chat_id,
        city_id=city_id,
        position_id=position.id,
    )
    subscription.soft_add()
    db.session.commit()

    callback_query.answer(
        callback_query=callback_query.id,
        text=f"Дякую, я запам'ятав твій вибір",
        cache_time=60,
    )

    message.reply_text(
        text=(
            f"Опитування завершено 🎉. \n"
            f"Тепер я буду тебе повіщувати про "
            f"нові вакансії з категорії *{position.name}* у місті *{city_name}*."
        ),
        parse_mode='Markdown',
    )
    return ConversationHandler.END


def cancel_add_subscription(update: Update, context: CallbackContext):
    update.message.reply_text('Гаразд додамо підписку іного разу')
    return ConversationHandler.END


def list_subscription(update: Update, context: CallbackContext):
    send_function = (
        update.message.reply_text
        if update.message else
        update.callback_query.edit_message_text
    )
    if update.callback_query:
        update.callback_query.answer()

    items = db.session.query(Subscription, Position, City).join(Position).join(City).all()
    if not items:
        send_function(text=(
            "У вас немає підписок, щоб піписатися на нові вакансії "
            "виконайте команду /add"
        ))
        return

    keyboards = []
    for subscription, position, city in items:
        button_text = f'{position.name} в місті {city.name}    ➡️'
        callback_data = f'subscription.choose.{subscription.id}'
        button = InlineKeyboardButton(button_text, callback_data=callback_data)
        keyboards.append([button])

    markup = InlineKeyboardMarkup(keyboards)
    send_function(
        text="Ось список твої підписок",
        reply_markup=markup,
    )

    return SubscriptionPageState.list


def choose_subscription(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    _, _, suffix = callback_query.data.strip().split('.')
    subscription, position, city = (
        db.session.query(Subscription, Position, City).join(Position).join(City)
        .filter(Subscription.id == suffix).first()
    )
    keyboards = [
        [
            InlineKeyboardButton(
                text='Повернутися назад ↩️',
                callback_data='subscription.list',
            ),
            InlineKeyboardButton(
                text='Скасувати підписку ❌',
                callback_data=f'subscription.delete.{subscription.id}',
            ),
        ]
    ]

    markup = InlineKeyboardMarkup(keyboards, resize_keyboard=True)

    callback_query.answer()
    callback_query.edit_message_text(
        text=(
            "Ваша підписка: \n"
            f"*Місто:* {city.name}\n"
            f"*Категорія:* {position.name}"
        ),
        parse_mode="Markdown",
        reply_markup=markup,
    )


def delete_subscription(update: Update, context: CallbackContext):
    callback_query: CallbackQuery = update.callback_query
    _, _, suffix = callback_query.data.strip().split('.')

    subscription = Subscription.query.get(suffix)
    if not subscription:
        return

    db.session.delete(subscription)
    db.session.commit()

    list_subscription(update, context)


def add_subscription_handlers(dp: Dispatcher):
    dp.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('add', add_subscription)],
            states={
                AddSubscriptionStates.city: [
                    CallbackQueryHandler(add_city_navigate, pattern=r'city\.(prev|next)\.\d+'),
                    CallbackQueryHandler(add_city, pattern=r'city\.\d+')
                ],
                AddSubscriptionStates.position: [
                    CallbackQueryHandler(add_position_navigate, pattern=r'position\.(prev|next)\.\d+'),
                    CallbackQueryHandler(add_position, pattern=r'position\.\d+')
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel_add_subscription),
                MessageHandler(Filters.text, add_subscription_fallback),
            ],
            allow_reentry=True,
        )
    )

    # Manage subscription
    dp.add_handler(CommandHandler('list', list_subscription))
    dp.add_handler(CallbackQueryHandler(choose_subscription, pattern=r'subscription\.choose\.\d+'))
    dp.add_handler(CallbackQueryHandler(delete_subscription, pattern=r'subscription\.delete\.\d+'))
    dp.add_handler(CallbackQueryHandler(list_subscription, pattern=r'subscription\.list'))
