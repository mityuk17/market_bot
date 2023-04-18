import logging
import re

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
    get_subcategory_name = State()
    get_new_price = State()
    get_pictures_amount = State()
    get_new_title = State()
    get_new_description = State()
    get_new_pictures = State()


def check_links(text):
    url_extract_pattern = r"[a-zA-Z1-9]+\.[a-zA-z]{2,}"
    data1 = re.findall(url_extract_pattern, text)
    return bool(data1)


@dp.callback_query_handler(lambda query: query.data == 'change_phone_number')
async def change_phone_number(callback_query: types.CallbackQuery):
    await States.get_phone_number.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='menu'))
    await callback_query.message.edit_text(config.get_new_phone_number, reply_markup=kb)


@dp.message_handler(commands=['admin'], state= '*')
async def admin(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.admin_ids:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Управление категориями', callback_data='edit_categories'))
    kb.add(types.InlineKeyboardButton(text='Управление подкатегориями', callback_data='edit_subcategories'))
    kb.add(types.InlineKeyboardButton(text='Получить статистику по пользователям', callback_data='users_statistic'))
    kb.add(types.InlineKeyboardButton(text='Провести рассылку по пользователям', callback_data='send'))
    kb.add(types.InlineKeyboardButton(text='Изменить количество фотографий в объявлении', callback_data='change_pictures_amount'))
    await message.answer('Выберите действие', reply_markup=kb)


@dp.message_handler(commands=['unban'])
async def unban(message: types.Message):
    if message.from_user.id in config.admin_ids:
        user_id = int(message.text.split()[1])
    else:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.back, callback_data='admin_menu'))
    if not await db.check_banned(user_id):
        await message.answer('Пользователь не заблокирован.',reply_markup=kb)
    else:
        await db.unban_user(user_id)
        await bot.send_message(chat_id=user_id, text=config.unban_message)
        await message.answer('Пользователь был разблокирован.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'admin_menu', state='*')
async def admin_call(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if callback_query.message.chat.id not in config.admin_ids:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Управление категориями', callback_data='edit_categories'))
    kb.add(types.InlineKeyboardButton(text='Управление подкатегориями', callback_data='edit_subcategories'))
    kb.add(types.InlineKeyboardButton(text='Получить статистику по пользователям', callback_data='users_statistic'))
    kb.add(types.InlineKeyboardButton(text='Провести рассылку по пользователям', callback_data='send'))
    kb.add(types.InlineKeyboardButton(text='Изменить количество фотографий в объявлении', callback_data='change_pictures_amount'))
    await callback_query.message.edit_text('Выберите действие', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'edit_categories')
async def edit_categories(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Добавить категорию', callback_data='add_category'))
    kb.add(types.InlineKeyboardButton(text='Удалить категорию', callback_data='delete_category'))
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.edit_text('Выберите действие', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'add_category')
async def add_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.edit_text('Пришлите название для новой категории', reply_markup=kb)
    await States.get_new_category_name.set()


@dp.message_handler(state=States.get_new_category_name)
async def new_category(message: types.Message, state: FSMContext):
    await state.finish()
    res = db.create_category(message.text, 0)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    if res:
        await message.answer('Категория успешно создана.', reply_markup=kb)
        return
    await message.answer('Не удалось создать категорию, уже существует категория с таким названием.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'delete_category', state='*')
async def delete_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    categories = await db.get_main_categories()
    kb = types.InlineKeyboardMarkup()
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'), callback_data=f'offer_remove_category_{category.get("id")}'))
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.edit_text('Выберите категорию для удаления', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('offer_remove_category_'), state='*')
async def remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split('_')[-1])
    category_name = await db.get_category_name(category_id)
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.yes, callback_data=f'remove_category_{category_id}'))
    kb.add(types.InlineKeyboardButton(text=config.no, callback_data='cancel_remove_category'))
    await callback_query.message.edit_text(f'Вы уверены, что хотите удалить категорию {category_name}?', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'cancel_remove_category', state='*')
async def cancel_remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.edit_text('Удаление категории отменено.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('remove_category_'), state='*')
async def confirm_remove_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    category_id = int(callback_query.data.split('_')[-1])
    await db.remove_category(category_id)
    await callback_query.message.edit_text('Категория успешно удалена.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'edit_subcategories')
async def edit_subcategories(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    categories = await db.get_main_categories()
    kb = types.InlineKeyboardMarkup()
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'), callback_data=f'edit_sub_{category.get("id")}'))
    kb.add(types.InlineKeyboardButton(text=config.back, callback_data='admin_menu'))
    await callback_query.message.edit_text('Выберите для какой категории изменить подкатегории:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('edit_sub_'), state='*')
async def edit_subs(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    subcategories = await db.get_subcategories(int(callback_query.data.split('_')[-1]))
    kb = types.InlineKeyboardMarkup()
    for subcategory in subcategories:
        kb.add(types.InlineKeyboardButton(text=subcategory.get('name'), callback_data=f'offer_remove_subcategory_{subcategory.get("id")}'))
    kb.add(types.InlineKeyboardButton(text='Создать новую подкатегорию', callback_data=f'add_subcategory_{int(callback_query.data.split("_")[-1])}'))
    kb.add(types.InlineKeyboardButton(text=config.back, callback_data=f'edit_subcategories'))
    await callback_query.message.edit_text('Выберите подкатегорию для изменения:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('offer_remove_subcategory_'))
async def go_to_remove(callback_query: types.CallbackQuery):
    category_id = int(callback_query.data.split("_")[-1])
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.yes, callback_data = f'remove_subcategory_{category_id}'))
    kb.add(types.InlineKeyboardButton(text=config.no, callback_data=f'edit_sub_{(await db.get_category_by_id(category_id)).get("previous_category")}'))
    await callback_query.message.edit_text(f'Вы уверены, что хотите удалить подкатегорию {(await db.get_category_by_id(category_id)).get("name")}?', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('remove_subcategory_'), state='*')
async def delete_subcategory(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    category_id = int(callback_query.data.split('_')[-1])
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.back, callback_data=f'edit_sub_{(await db.get_category_by_id(category_id)).get("previous_category")}'))
    await db.remove_category(category_id)
    await callback_query.message.edit_text('Подкатегория успешно удалена.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('add_subcategory_'), state='*')
async def start_adding_subcategory(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    category_id = int(callback_query.data.split('_')[-1])
    await States.get_subcategory_name.set()
    async with state.proxy() as data:
        data['category_id'] = category_id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.back, callback_data=f'edit_sub_{category_id}'))
    await callback_query.message.edit_text('Введите название для новой подкатегории:')


@dp.message_handler(state=States.get_subcategory_name)
async def add_new_subcategory(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        category_id = data['category_id']
    category_name = message.text
    await db.create_category(category_name, category_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.back, callback_data=f'edit_sub_{category_id}'))
    await message.answer('Подкатегория успешно создана', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'users_statistic', state='*')
async def users_statistic(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    data = await db.get_users()
    wb = openpyxl.Workbook()
    sh = wb.active
    sh.append(['Username', 'id', 'Номер телефона', 'Количество активных объявлений'])
    for i in data:
        sh.append(i)
    wb.save('users_statistic.xlsx')
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.answer_document(document=types.InputFile('users_statistic.xlsx'))
    await callback_query.message.answer('Статистика по пользователям загружена.', reply_markup=kb)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda query: query.data == 'send', state='*')
async def send(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.edit_text('Пришлите сообщение для рассылки', reply_markup=kb)
    await States.get_message_for_send.set()


@dp.message_handler(state=States.get_message_for_send, content_types=ContentType.ANY)
async def send_message(message: types.Message, state: FSMContext):
    for user in await db.get_users():
        user_id = user[1]
        await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await message.answer('Рассылка успешна отправлена.', reply_markup=kb)
    await state.finish()


@dp.callback_query_handler(lambda query: query.data =='change_pictures_amount')
async def change_pictures_amount(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await callback_query.message.edit_text('Введите новое значение для количества фотографий в изображений:', reply_markup=kb)
    await States.get_pictures_amount.set()


@dp.message_handler(state=States.get_pictures_amount)
async def get_pictures_amount(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    if not message.text.isdigit():
        await message.answer('Неверный формат', reply_markup=kb)
        return
    pictures_amount = message.text
    await db.change_param('amount_pictures', pictures_amount)
    await message.answer('Количество фотографий в объявлении изменено')
    await state.finish()


@dp.message_handler(commands=['start', 'menu', 'main'], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    if not await db.check_user(message.chat.id):
        await message.answer(config.get_phone_number)
        return await States.get_phone_number.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.search_item, callback_data='search_items'))
    kb.add(types.InlineKeyboardButton(text=config.create_item, callback_data='create_item'))
    kb.add(types.InlineKeyboardButton(text=config.look_my_items, switch_inline_query_current_chat='myitems'))
    kb.add(types.InlineKeyboardButton(text=config.change_phone_number, callback_data='change_phone_number'))
    kb.add(types.InlineKeyboardButton(text=config.our_group, url=config.group_url))
    kb.add(types.InlineKeyboardButton(text=config.support, url=config.support_url))
    await message.answer(config.hello_message, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'cancel', state='*')
async def cancel_remove(callback_query: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='menu'))
    await state.finish()
    await callback_query.message.edit_text(config.remove_item_cancelled, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'menu', state='*')
async def main_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if not await db.check_user(callback_query.message.chat.id):
        await callback_query.message.edit_text(config.get_phone_number)
        return await States.get_phone_number.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.search_item, callback_data='search_items'))
    kb.add(types.InlineKeyboardButton(text=config.create_item, callback_data='create_item'))
    kb.add(types.InlineKeyboardButton(text=config.look_my_items, switch_inline_query_current_chat='myitems'))
    kb.add(types.InlineKeyboardButton(text=config.change_phone_number, callback_data='change_phone_number'))
    kb.add(types.InlineKeyboardButton(text=config.our_group, url=config.group_url))
    kb.add(types.InlineKeyboardButton(text=config.support, url=config.support_url))
    await callback_query.message.edit_text(config.hello_message, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('item_'))
async def show_item_callback(callback_query: types.CallbackQuery):
    item_id = int(callback_query.data.split('_')[-1])
    item = await db.get_item_by_id(item_id)
    if not item:
        await callback_query.message.edit_text(config.item_not_found)
        return
    for picture in item.get('pictures_id').strip(':::').split(':::'):
        await bot.send_photo(chat_id=callback_query.message.chat.id, photo=picture)
    phone_number = await db.get_phone_number(item.get('creator_id'))
    text = f'''
    {item.get('name')}
    Цена: {item.get('price')}₽
    Описание: {item.get('description')}
    Телефон: {phone_number}
    '''
    category = await db.get_category_by_id(item.get('category_id'))
    category_name = category.get('name')
    kb = types.InlineKeyboardMarkup()
    if item.get('target') == 'sell':
        emodzi = category_name.split()[-1]
        kb.add(types.InlineKeyboardButton(text=f'Предложение {emodzi}',
                                          switch_inline_query_current_chat=f'sell_{item.get("category_id")}'))
    elif item.get('target') == 'buy':
        kb.add(types.InlineKeyboardButton(text=f'{category_name} {config.demand}',
                                          switch_inline_query_current_chat=f'buy_{item.get("category_id")}', ))
    kb.add(types.InlineKeyboardButton(text=config.other_categories, callback_data='search_items'))
    if callback_query.from_user.id == item.get('creator_id') or callback_query.from_user.id in config.admin_ids:
        kb.add(types.InlineKeyboardButton(text=config.remove_item, callback_data=f'offer_delete_item_{item_id}'))
    if callback_query.from_user.id == item.get('creator_id'):
        kb.add(types.InlineKeyboardButton(text=config.change_item, callback_data=f'change_item_{item_id}'))
    kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
    await callback_query.message.answer(text)
    text = config.after_item.replace('category_name', category_name)
    await callback_query.message.answer(text, reply_markup=kb)
    await callback_query.message.delete()


@dp.message_handler(commands=['item'], state='*')
async def show_item(message: types.Message, state: FSMContext):
    item_id = int(message.text.split(' ')[1])
    item = await db.get_item_by_id(item_id)
    if not item:
        await message.answer(config.item_not_found)
        return
    for picture in item.get('pictures_id').strip(':::').split(':::'):
        await bot.send_photo(chat_id=message.chat.id, photo=picture)
    phone_number = await db.get_phone_number(item.get('creator_id'))
    text = f'''
{item.get('name')}
Цена: {item.get('price')}
Описание: {item.get('description')}
Телефон: {phone_number}
'''
    category = await db.get_category_by_id(item.get('category_id'))
    category_name = category.get('name')
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Поиск по ключевому слову', switch_inline_query_current_chat=''))
    if item.get('target') == 'sell':
        emodzi = category_name.split()[-1]
        kb.add(types.InlineKeyboardButton(text=f'Предложение {emodzi}', switch_inline_query_current_chat=f'sell_{item.get("category_id")}'))
    elif item.get('target') == 'buy':
        kb.add(types.InlineKeyboardButton(text=f'{category_name} {config.demand}', switch_inline_query_current_chat=f'buy_{item.get("category_id")}', ))
    kb.add(types.InlineKeyboardButton(text=config.other_categories, callback_data='search_items'))
    if message.from_user.id == item.get('creator_id') or message.from_user.id in config.admin_ids:
        kb.add(types.InlineKeyboardButton(text=config.remove_item, callback_data=f'offer_delete_item_{item_id}'))
    if message.from_user.id == item.get('creator_id'):
        kb.add(types.InlineKeyboardButton(text=config.change_item, callback_data=f'change_item_{item_id}'))
    if message.from_user.id in config.admin_ids:
        kb.add(types.InlineKeyboardButton(text=config.ban_user, callback_data=f'ban_user_{item.get("creator_id")}'))
    kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
    await message.answer(text)
    text = config.after_item.replace('category_name', category_name)
    await message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('ban_user_'))
async def ban(callback_query: types.CallbackQuery):
    user_id = callback_query.data.split('_')[-1]
    user = await db.get_user_by_id(user_id)
    username = user[1]
    await db.ban_user(user_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
    await callback_query.message.edit_text(f'Пользователь {username} ({user_id}) заблокирован.', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('change_'))
async def change_price(callback_query: types.CallbackQuery, state: FSMContext):
    target = callback_query.data.split('_')[1]
    item_id = callback_query.data.split('_')[-1]
    if target == 'item':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Цена', callback_data=f'change_price_{item_id}'))
        kb.add(types.InlineKeyboardButton(text='Название', callback_data=f'change_title_{item_id}'))
        kb.add(types.InlineKeyboardButton(text='Описание', callback_data=f'change_description_{item_id}'))
        kb.add(types.InlineKeyboardButton(text='Фотографии', callback_data=f'change_pictures_{item_id}'))
        kb.add(types.InlineKeyboardButton(text=config.back, callback_data=f'item_{item_id}'))
        await callback_query.message.edit_text('Выберите пункт для редактирования', reply_markup=kb)
    elif target == 'price':
        await States.get_new_price.set()
        async with state.proxy() as data:
            data['item_id'] = int(callback_query.data.split('_')[-1])
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
        await callback_query.message.edit_text(config.get_new_price, reply_markup=kb)
    elif target == 'title':
        await States.get_new_title.set()
        async with state.proxy() as data:
            data['item_id'] = int(callback_query.data.split('_')[-1])
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
        await callback_query.message.edit_text(config.get_new_title, reply_markup=kb)
    elif target == 'description':
        await States.get_new_description.set()
        async with state.proxy() as data:
            data['item_id'] = int(callback_query.data.split('_')[-1])
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
        await callback_query.message.edit_text(config.get_new_description, reply_markup=kb)
    elif target == 'pictures':
        await States.get_new_pictures.set()
        async with state.proxy() as data:
            data['item_id'] = int(callback_query.data.split('_')[-1])
            data['pictures'] = ''
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(config.main_menu, callback_data='menu'))
        await callback_query.message.edit_text(text=config.get_new_picture, reply_markup=kb)


@dp.message_handler(state=States.get_new_price)
async def get_price(message: types.Message, state: FSMContext):
    price = message.text
    async with state.proxy() as data:
        item_id = data['item_id']
    await db.change_price(item_id, price)
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await message.answer('Цена изменена.', reply_markup=kb)


@dp.message_handler(state=States.get_new_title)
async def get_price(message: types.Message, state: FSMContext):
    title = message.text
    if len(title) > config.max_title_length:
        await message.answer('Слишком длинное название.')
        return
    if check_links(title):
        await message.answer('Название не должно содержать в себе ссылок!')
        return
    async with state.proxy() as data:
        item_id = data['item_id']
    await db.change_title(item_id, title)
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await message.answer('Название объявления изменено.', reply_markup=kb)


@dp.message_handler(state=States.get_new_description)
async def get_price(message: types.Message, state: FSMContext):
    description = message.text
    if len(description) > config.max_description_length:
        await message.answer('Слишком длинное описание.')
        return
    if check_links(description):
        await message.answer('Описание не должно содержать в себе ссылок!')
        return
    async with state.proxy() as data:
        item_id = data['item_id']
    await db.change_description(item_id, description)
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
    await message.answer('Описание объявления изменено.', reply_markup=kb)


@dp.message_handler(state=States.get_new_pictures, content_types=ContentType.PHOTO)
async def get_pictures(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    async with state.proxy() as data:
        data['pictures'] = data['pictures'].strip() + f':::{photo_id}'
        pictures_amount = len(data['pictures'].strip(':::').split(':::'))
    if pictures_amount == int(await db.get_param_value('amount_pictures')):
        async with state.proxy() as data:
            pictures = data['pictures']
            item_id = data['item_id']
            await db.change_pictures(item_id, pictures)
        await state.finish()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='admin_menu'))
        await message.answer('Фотографии в объявлении изменены.', reply_markup=kb)
    else:
        await message.answer(config.send_picture2)


@dp.callback_query_handler(lambda query: query.data.startswith('offer_delete_item_'), state='*')
async def delete_item(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    item_id = int(callback_query.data.split('_')[-1])
    item = await db.get_item_by_id(item_id)
    text = f'''Вы уверены, что хотите удалить объявление {item.get('name')}?'''
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.yes, callback_data=f'delete_item_{item_id}'))
    kb.add(types.InlineKeyboardButton(text='НЕТ ❌', callback_data='cancel'))
    await callback_query.message.edit_text(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('delete_item_'), state='*')
async def delete_item(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    item_id = int(callback_query.data.split('_')[-1])
    await db.remove_item_by_id(item_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='menu'))
    await callback_query.message.edit_text(config.item_removed_success, reply_markup=kb)


@dp.message_handler(state=States.get_phone_number)
async def get_phone_number(message: types.Message, state: FSMContext):
    await state.finish()
    if not await db.check_user(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.username, message.text)
    else:
        await db.change_phone_number(message.from_user.id, message.text)
        await message.answer('Номер телефона успешно изменен.')
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=config.search_item, callback_data='search_items'))
    kb.add(types.InlineKeyboardButton(text=config.create_item, callback_data='create_item'))
    kb.add(types.InlineKeyboardButton(text=config.look_my_items, switch_inline_query_current_chat='myitems'))
    kb.add(types.InlineKeyboardButton(text=config.change_phone_number, callback_data='change_phone_number'))
    kb.add(types.InlineKeyboardButton(text=config.our_group, url=config.group_url))
    kb.add(types.InlineKeyboardButton(text=config.support, url=config.support_url))
    await message.answer(config.hello_message, reply_markup=kb)


'''
Процесс поиска объявлений
'''


@dp.callback_query_handler(lambda query: query.data == 'search_items')
async def search_items(callback_query: types.CallbackQuery):
    await callback_query.answer()
    kb = types.InlineKeyboardMarkup()
    categories = await db.get_main_categories()
    kb.add(types.InlineKeyboardButton(text='Поиск по ключевому слову', switch_inline_query_current_chat=''))
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'),
                                          callback_data=f'category_{category.get("id")}'))
    kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='menu'))
    await callback_query.message.edit_text(config.search_message, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('category_'), state='*')
async def choose_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    category_id = int(callback_query.data.split('_')[-1])
    kb = types.InlineKeyboardMarkup()
    if await db.is_subcategories(category_id):
        subcategories = await db.get_subcategories(category_id)
        for subcategory in subcategories:
            kb.add(types.InlineKeyboardButton(text=subcategory.get('name'),
                                              callback_data=f'category_{subcategory.get("id")}'))
        kb.add(types.InlineKeyboardButton(text=config.back, callback_data='search_items'))
        await callback_query.message.edit_text(config.choose_subcategory, reply_markup=kb)
    else:
        kb.add(types.InlineKeyboardButton(text=config.demand, switch_inline_query_current_chat=f'buy_{category_id}'))
        category_name = (await db.get_category_by_id(category_id)).get('name')
        emodzi = category_name.split()[-1]
        kb.add(types.InlineKeyboardButton(text=f'Предложение {emodzi}', switch_inline_query_current_chat=f'sell_{category_id}'))
        kb.add(types.InlineKeyboardButton(text=config.back, callback_data='search_items'))
        await callback_query.message.edit_text('Выберите действие:', reply_markup=kb)


@dp.inline_handler()
async def look_category(inline_query: types.InlineQuery):
    query = inline_query.query
    if query == 'myitems':
        items = await db.get_items_by_creator(inline_query.from_user.id)
    elif query.startswith('buy') or query.startswith('sell'):
        if query.startswith('buy'):
            category_id = int(query.split('_')[-1])
            items = await db.get_items_by_category(category_id, 'buy')
        elif query.startswith('sell'):
            category_id = int(query.split('_')[-1])
            items = await db.get_items_by_category(category_id, 'sell')
        else:
            items = []
    else:
        keyword = query
        items = await db.get_items_by_keyword(keyword)

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
    if await db.check_banned(callback_query.from_user.id):
        kb.add(types.InlineKeyboardButton(text='Связаться с администрацией', url = config.unban_group_url))
        kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='menu'))
        await callback_query.message.edit_text(config.banned, reply_markup=kb)
        return
    categories = await db.get_main_categories()
    for category in categories:
        kb.add(types.InlineKeyboardButton(text=category.get('name'),
                                          callback_data=f'create_category_{category.get("id")}'))
    await callback_query.answer()
    await callback_query.message.edit_text(config.select_category, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('create_category_'), state='*')
async def choose_category(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    async with state.proxy() as data:
        data['category_id'] = int(callback_query.data.split('_')[-1])
    kb = types.InlineKeyboardMarkup()
    if await db.is_subcategories(int(callback_query.data.split('_')[-1])):
        subcategories = await db.get_subcategories(int(callback_query.data.split('_')[-1]))
        for subcategory in subcategories:
            kb.add(types.InlineKeyboardButton(text=subcategory.get('name'),
                                              callback_data=f'create_category_{subcategory.get("id")}'))
        await callback_query.message.edit_text(text=config.choose_subcategory, reply_markup=kb)
    else:
        kb.add(types.InlineKeyboardButton(text=config.demand, callback_data=f'create_target_buy'))
        category_id = int(callback_query.data.split('_')[-1])
        category_name = (await db.get_category_by_id(category_id)).get('name')
        emodzi = category_name.split()[-1]
        kb.add(types.InlineKeyboardButton(text=f'Предложение {emodzi}', callback_data=f'create_target_sell'))
        kb.add(types.InlineKeyboardButton(text=config.back, callback_data='menu'))
        await callback_query.message.edit_text(text='Выберите тип объявления:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('create_target_'), state='*')
async def choose_target(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['target'] = callback_query.data.split('_')[-1]
    await callback_query.answer()
    await callback_query.message.edit_text(config.send_title, reply_markup=None)
    await States.get_title.set()


@dp.message_handler(state=States.get_title)
async def get_title(message: types.Message, state: FSMContext):
    if len(message.text) > config.max_title_length:
        await message.answer(config.title_too_long)
        return
    if check_links(message.text):
        await message.answer('Название не должно содержать ссылок!')
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
    if check_links(message.text):
        await message.answer('Описание не должно содержать ссылок!')
        return
    async with state.proxy() as data:
        data['description'] = message.text
    await message.answer(config.send_price)
    await States.get_price.set()


@dp.message_handler(state=States.get_price)
async def get_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
        data['pictures'] = ''
    await States.get_picture.set()
    await message.answer(config.send_picture)


@dp.message_handler(content_types=ContentType.PHOTO, state=States.get_picture)
async def get_picture(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['pictures'] = data['pictures'] + f':::{message.photo[-1].file_id}'
        if len(data.get('pictures').strip(':::').split(':::')) == int(await db.get_param_value('amount_pictures')):
            item_data = {'creator_id': message.from_user.id,
                         'category_id': data.get('category_id'),
                         'title': data.get('title'),
                         'description': data.get('description'),
                         'price': data.get('price'),
                         'pictures' : data.get('pictures'),
                         'target': data.get('target')}
            await db.create_item(item_data)
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text=config.main_menu, callback_data='menu'))
            await message.answer(config.item_created, reply_markup=kb)
            await state.finish()
        else:
            await message.answer(config.send_picture2)


if __name__ == '__main__':
    db.start_db()

    executor.start_polling(dp, skip_updates=True)