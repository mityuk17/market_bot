import logging
import openpyxl
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ContentType
import db
import config

API_TOKEN = config.telegram_token
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    get_picture = State()
    get_price = State()
    get_title = State()
    get_description = State()
    get_phone_number = State()
    get_new_category_name = State()
    get_message_for_send = State()


@dp.message_handler(commands=['admin'], state= '*')
async def admin(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.admin_ids:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Управление категориями', callback_data='edit_categories'))
    kb.add(types.InlineKeyboardButton(text='Получить статистику по пользователям', callback_data='users_statistic'))
    kb.add(types.InlineKeyboardButton(text='Провести рассылку по пользователям', callback_data='send'))
    await message.answer('Выберите действие', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'admin_menu')
async def admin_call(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if callback_query.message.chat.id not in config.admin_ids:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Управление категориями', callback_data='edit_categories'))
    kb.add(types.InlineKeyboardButton(text='Получить статистику по пользователям', callback_data='users_statistic'))
    kb.add(types.InlineKeyboardButton(text='Провести рассылку по пользователям', callback_data='send'))
    await callback_query.message.edit_text('Выберите действие', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'edit_categories')
async def edit_categories(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Добавить категорию', callback_data='add_category'))
    kb.add(types.InlineKeyboardButton(text='Удалить категорию', callback_data='delete_category'))
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await callback_query.message.edit_text('Выберите действие', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'add_category')
async def add_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await callback_query.message.edit_text('Пришлите название для новой категории', reply_markup=kb)
    await States.get_new_category_name.set()


@dp.message_handler(state=States.get_new_category_name)
async def new_category(message: types.Message, state: FSMContext):
    await state.finish()
    res = db.create_category(message.text)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    if res:
        await message.answer('Категория успешно создана.', reply_markup=kb)
        return
    await message.answer('Не удалось создать категорию, уже существует категория с таким названием.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'delete_category', state='*')
async def delete_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    categories = db.get_categories()
    kb = types.InlineKeyboardMarkup()
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'), callback_data=f'offer_remove_category_{category.get("id")}'))
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await callback_query.message.edit_text('Выберите категорию для удаления', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('offer_remove_category_'), state='*')
async def remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[-1])
    category_name = db.get_category_name(category_id)
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Да', callback_data=f'remove_category_{category_id}'))
    kb.add(types.InlineKeyboardButton(text='Нет', callback_data='cancel_remove_category'))
    await callback_query.message.edit_text(f'Вы уверены, что хотите удалить категорию {category_name}?', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'cancel_remove_category', state='*')
async def cancel_remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await callback_query.message.edit_text('Удаление категории отменено.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('remove_category_'), state='*')
async def confirm_remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    category_id = int(callback_query.data.split('_')[-1])
    db.remove_category(category_id)
    await callback_query.message.edit_text('Категория успешно удалена.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'users_statistic', state='*')
async def users_statistic(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    data = db.get_users()
    wb = openpyxl.Workbook()
    sh = wb.active
    sh.append(['Username', 'id', 'Номер телефона', 'Количество активных объявлений'])
    for i in data:
        sh.append(i)
    wb.save('users_statistic.xlsx')
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await callback_query.message.answer_document(types.InputFile('users_statistic.xlsx'), reply_markup=kb)
    await callback_query.message.edit_text('Статистика по пользователям загружена.')


@dp.callback_query_handler(lambda query: query.data == 'send', state='*')
async def send(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await callback_query.message.edit_text('Пришлите сообщение для рассылки', reply_markup=kb)
    await States.get_message_for_send.set()


@dp.message_handler(state=States.get_message_for_send, content_types=ContentType.ANY)
async def send_message(message: types.Message, state: FSMContext):
    for user in db.get_users():
        user_id = user[1]
        await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='admin_menu'))
    await message.answer('Рассылка успешна отправлена.', reply_markup=kb)
    await state.finish()


@dp.message_handler(commands=['start', 'menu', 'main'], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    if not db.check_user(message.chat.id):
        await message.answer(config.get_phone_number)
        return await States.get_phone_number.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Поиск объявлений', callback_data='search_items'))
    kb.add(types.InlineKeyboardButton(text='Разместить оъявление', callback_data='create_item'))
    kb.add(types.InlineKeyboardButton(text='Посмотреть свои объявления', switch_inline_query_current_chat='myitems'))
    kb.add(types.InlineKeyboardButton(text='Наше сообщество', url=config.group_url))
    await message.answer(config.hello_message, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'cancel', state='*')
async def cancel_remove(callback_query: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='menu'))
    await state.finish()
    await callback_query.message.edit_text('Удаление объявления отменено', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'menu', state='*')
async def main_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if not db.check_user(callback_query.message.chat.id):
        await callback_query.message.edit_text(config.get_phone_number)
        return await States.get_phone_number.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Поиск объявлений', callback_data='search_items'))
    kb.add(types.InlineKeyboardButton(text='Разместить оъявление', callback_data='create_item'))
    kb.add(types.InlineKeyboardButton(text='Посмотреть свои объявления', switch_inline_query_current_chat='myitems'))
    kb.add(types.InlineKeyboardButton(text='Наше сообщество', url=config.group_url))
    await callback_query.message.edit_text(config.hello_message, reply_markup=kb)


@dp.message_handler(commands=['item'], state='*')
async def show_item(message: types.Message, state: FSMContext):
    await state.finish()
    item_id = int(message.text.split(' ')[1])
    item = db.get_item_by_id(item_id)
    if not item:
        await message.answer('Объявление не найдено, скорее всего оно было удалено.')
        return
    await message.answer_photo(photo=item.get('picture1_id'))
    await message.answer_photo(photo=item.get('picture2_id'))
    phone_number = db.get_phone_number(message.from_user.id)
    text= f'''
{item.get('name')}
Цена: {item.get('price')}₽
Описание: {item.get('description')}
Телефон: {phone_number}
'''
    category_name = db.get_category_by_id(item.get('category_id'))
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=category_name, switch_inline_query_current_chat=str(item.get('category_id'))))
    kb.add(types.InlineKeyboardButton(text='Другие категории', callback_data='search_items'))
    if message.from_user.id == item.get('creator_id') or message.from_user.id in config.admin_ids:
        kb.add(types.InlineKeyboardButton(text='Удалить объявление', callback_data=f'offer_delete_item_{item_id}'))
    kb.add(types.InlineKeyboardButton('🔙Главное меню', callback_data='menu'))
    await message.answer(text)
    text = config.after_item.replace('category_name', category_name)
    await message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('offer_delete_item_'), state='*')
async def delete_item(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    item_id = int(callback_query.data.split('_')[-1])
    item = db.get_item_by_id(item_id)
    text = f'''Вы уверены, что хотите удалить объявление {item.get('name')}?'''
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Да', callback_data=f'delete_item_{item_id}'))
    kb.add(types.InlineKeyboardButton(text='Нет', callback_data='cancel'))
    await callback_query.message.edit_text(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('delete_item_'), state='*')
async def delete_item(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    item_id = int(callback_query.data.split('_')[-1])
    db.remove_item_by_id(item_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='menu'))
    await callback_query.message.edit_text('Объявление удалено', reply_markup=kb)


@dp.message_handler(state=States.get_phone_number)
async def get_phone_number(message: types.Message, state: FSMContext):
    await state.finish()
    db.add_user(message.from_user.id, message.from_user.username, message.text)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Поиск объявлений', callback_data='search_items'))
    kb.add(types.InlineKeyboardButton(text='Разместить оъявление', callback_data='create_item'))
    kb.add(types.InlineKeyboardButton(text='Посмотреть свои объявления', switch_inline_query_current_chat='myitems'))
    kb.add(types.InlineKeyboardButton(text='Наше сообщество', url=config.group_url))
    await message.answer(config.hello_message, reply_markup=kb)


'''
Процесс поиска объявлений
'''


@dp.callback_query_handler(lambda query: query.data == 'search_items')
async def search_items(callback_query: types.CallbackQuery):
    await callback_query.answer()
    kb = types.InlineKeyboardMarkup()
    categories = db.get_categories()
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'),
                                          switch_inline_query_current_chat=f'{category.get("id")}'))
    kb.add(types.InlineKeyboardButton(text='🔙Главное меню', callback_data='menu'))
    await callback_query.message.edit_text(config.search_message, reply_markup=kb)


@dp.inline_handler()
async def look_category(inline_query: types.InlineQuery):
    query = inline_query.query
    if query == 'myitems':
        items = db.get_items_by_creator(inline_query.from_user.id)
    else:
        if query.isdigit():
            items = db.get_items_by_category(int(query))
        else:
            items = []
    if len(items) == 0:
        await inline_query.answer([], cache_time=60, is_personal=True,
                                  switch_pm_text=config.no_items, switch_pm_parameter='None')
        return
    answer = list()
    if not inline_query.offset:
        border = 0
    else:
        border = int(inline_query.offset)
    for item in items[border:border+50]:
        answer.append(types.InlineQueryResultArticle(

            id=item.get('id'),
            title=f'{item.get("name")}',
            description=f'{item.get("price")}₽ | {item.get("description")}',
            input_message_content=types.InputTextMessageContent(f'/item {item.get("id")}'),
        ))
    await inline_query.answer(answer, cache_time=60, is_personal=True,
                              switch_pm_text=config.no_items, switch_pm_parameter='None')


''''
Процесс создания объявления
'''


@dp.callback_query_handler(lambda query: query.data == 'create_item', state='*')
async def create_item(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    categories = db.get_categories()
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'),
                                          callback_data=f'create_category_{category.get("id")}'))
    await callback_query.answer()
    await callback_query.message.edit_text(config.search_message, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('create_category_'), state='*')
async def choose_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    async with state.proxy() as data:
        data['category_id'] = int(callback_query.data.split('_')[-1])
    await callback_query.answer()
    await callback_query.message.edit_text(config.send_title, reply_markup=None)
    await States.get_title.set()


@dp.message_handler(state=States.get_title)
async def get_title(message: types.Message, state: FSMContext):
    if len(message.text) > config.max_title_length:
        await message.answer(config.title_too_long)
        return
    async with state.proxy() as data:
        data['title'] = message.text
    await message.answer(config.send_description)
    await States.get_description.set()


@dp.message_handler(state=States.get_description)
async def get_description(message: types.Message, state: FSMContext):
    if len(message.text) > config.max_description_length:
        await message.answer(config.description_too_long)
        return
    async with state.proxy() as data:
        data['description'] = message.text
    await message.answer(config.send_price)
    await States.get_price.set()


@dp.message_handler(state=States.get_price)
async def get_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(config.invalid_price)
        return
    async with state.proxy() as data:
        data['price'] = int(message.text)
    await States.get_picture.set()
    await message.answer(config.send_picture)


@dp.message_handler(content_types=ContentType.PHOTO, state=States.get_picture)
async def get_picture(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data.get('picture1'):
            data['picture2'] = message.photo[-1].file_id
            item_data = {'creator_id': message.from_user.id,
                         'category_id': data.get('category_id'),
                         'title': data.get('title'),
                         'description': data.get('description'),
                         'price': data.get('price'),
                         'picture1': data.get('picture1'),
                         'picture2': data.get('picture2')}
            db.create_item(item_data)
            await message.answer(config.item_created)
            await state.finish()
            await start(message, state)
        else:
            data['picture1'] = message.photo[-1].file_id
            await message.answer(config.send_picture2)


if __name__ == '__main__':
    db.start_db()
    executor.start_polling(dp, skip_updates=True)