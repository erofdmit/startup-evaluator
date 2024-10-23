import logging
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import aiohttp
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_KEY')

logging.basicConfig(level=logging.INFO)

# Создаем бот и диспетчер с FSM (состояния пользователя) с хранилищем в памяти
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Модель для ответа
class SurveyResponse(BaseModel):
    target_audience: str
    technical_specifications: str
    budget: str
    competitors: str
    marketing_plan: str
    mvp: str

# Состояния опроса
class SurveyStates(StatesGroup):
    choosing_language = State()  # Выбор языка
    waiting_for_survey = State()
    asking_target_audience = State()  # Вопрос о целевой аудитории
    asking_technical_specifications = State()  # Техническое задание
    asking_budget = State()  # Вопрос о бюджете
    asking_competitors = State()  # Вопрос о конкурентах
    asking_marketing_plan = State()  # Вопрос о маркетинговом плане
    asking_mvp = State()  # Вопрос о MVP

# Храним временные данные пользователя
questions = {
    'target_audience': {
        'en': "Have you defined your target audience? Who will be your users?",
        'ru': "Определили ли вы вашу целевую аудиторию? Кто будут вашими пользователями?"
    },
    'technical_specifications': {
        'en': "Do you have a technical specification for development?",
        'ru': "Есть ли у вас сформированное техническое задание для разработки?"
    },
    'budget': {
        'en': "Do you have a budget for development and promotion?",
        'ru': "Есть ли у вас бюджет для разработки и последующего продвижения?"
    },
    'competitors': {
        'en': "Have you analyzed competitors? How do you plan to differ?",
        'ru': "Провели ли вы анализ конкурентов? Как вы планируете отличаться?"
    },
    'marketing_plan': {
        'en': "Do you have a marketing plan to attract users?",
        'ru': "У вас есть план по маркетингу и привлечению пользователей?"
    },
    'mvp': {
        'en': "Have you determined the minimal viable product (MVP) for your project?",
        'ru': "Определили ли вы минимальный функционал, который будет включен в ваш продукт?"
    }
}

# Команда для начала бота
@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await message.answer("Please choose your language:\n1. English (/en)\n2. Русский (/ru)")
    await state.set_state(SurveyStates.choosing_language)

# Обработка выбора языка
@router.message(Command("en"), SurveyStates.choosing_language)
@router.message(Command("ru"), SurveyStates.choosing_language)
async def set_language(message: types.Message, state: FSMContext):
    lang = message.text[1:]  # Получаем язык из команды ('/en' или '/ru')
    await state.update_data(lang=lang)
    await message.answer("Language set! Type /survey to start the survey.")
    await state.set_state(SurveyStates.waiting_for_survey)

# Начало опроса
@router.message(Command("survey"), SurveyStates.waiting_for_survey)
async def start_survey(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'lang' not in data:
        await message.answer("Please choose your language first with /en or /ru.")
        return

    # Переходим к следующему вопросу
    lang = data['lang']
    await message.answer(questions['target_audience'][lang])
    await state.set_state(SurveyStates.asking_target_audience)

# Обработка вопросов
@router.message(SurveyStates.asking_target_audience)
async def handle_target_audience(message: types.Message, state: FSMContext):
    await state.update_data(target_audience=message.text)

    # Переходим к следующему вопросу
    data = await state.get_data()
    lang = data['lang']
    await message.answer(questions['technical_specifications'][lang])
    await state.set_state(SurveyStates.asking_technical_specifications)

@router.message(SurveyStates.asking_technical_specifications)
async def handle_technical_specifications(message: types.Message, state: FSMContext):
    await state.update_data(technical_specifications=message.text)

    # Переходим к следующему вопросу
    data = await state.get_data()
    lang = data['lang']
    await message.answer(questions['budget'][lang])
    await state.set_state(SurveyStates.asking_budget)

@router.message(SurveyStates.asking_budget)
async def handle_budget(message: types.Message, state: FSMContext):
    await state.update_data(budget=message.text)

    # Переходим к следующему вопросу
    data = await state.get_data()
    lang = data['lang']
    await message.answer(questions['competitors'][lang])
    await state.set_state(SurveyStates.asking_competitors)

@router.message(SurveyStates.asking_competitors)
async def handle_competitors(message: types.Message, state: FSMContext):
    await state.update_data(competitors=message.text)

    # Переходим к следующему вопросу
    data = await state.get_data()
    lang = data['lang']
    await message.answer(questions['marketing_plan'][lang])
    await state.set_state(SurveyStates.asking_marketing_plan)

@router.message(SurveyStates.asking_marketing_plan)
async def handle_marketing_plan(message: types.Message, state: FSMContext):
    await state.update_data(marketing_plan=message.text)

    # Переходим к следующему вопросу
    data = await state.get_data()
    lang = data['lang']
    await message.answer(questions['mvp'][lang])
    await state.set_state(SurveyStates.asking_mvp)

async def send_long_message(chat_id: int, text: str, bot: Bot, chunk_size: int = 4096):
    """Функция для отправки длинных сообщений по частям."""
    for chunk in [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]:
        await bot.send_message(chat_id, chunk)

async def format_and_send_response(chat_id: int, response_data: dict, bot: Bot):
    """Форматируем и отправляем данные о результатах опроса по частям."""
    
    # Оценки (evaluations)
    evaluations = response_data.get("evaluations", {})
    eval_message = "🔍 **Evaluations**:\n"
    for key, value in evaluations.items():
        eval_message += f"• **{key.capitalize()}**: {value}\n"

    # Отправляем сообщение с оценками
    await send_long_message(chat_id, eval_message, bot)

    # Общий статус (overall_status)
    overall_status = response_data.get("overall_status", "No status available")
    status_message = f"📊 **Overall Status**: {overall_status}\n"
    
    # Отправляем сообщение с общим статусом
    await send_long_message(chat_id, status_message, bot)

    # Рекомендации (recommendations)
    recommendations = response_data.get("recommendations", [])
    rec_message = f"💡 **Recommendations**: \n {recommendations}"

    await send_long_message(chat_id, rec_message, bot)
    

# Используем эту функцию при получении ответа от сервера
@router.message(SurveyStates.asking_mvp)
async def handle_mvp(message: types.Message, state: FSMContext):
    await state.update_data(mvp=message.text)

    # Все вопросы завершены, собираем данные
    data = await state.get_data()
    response_data = SurveyResponse(
        target_audience=data['target_audience'],
        technical_specifications=data['technical_specifications'],
        budget=data['budget'],
        competitors=data['competitors'],
        marketing_plan=data['marketing_plan'],
        mvp=data['mvp']
    )

    # Отправляем данные на сервер
    async with aiohttp.ClientSession() as session:
        async with session.post('http://api:8000/survey', json=response_data.dict()) as resp:
            if resp.status == 200:
                server_response = await resp.json()  # Получаем ответ как JSON
                await format_and_send_response(message.chat.id, server_response, bot)  # Форматируем и отправляем сообщение по частям
            else:
                await message.answer("There was an error submitting your survey. Please try again later.")

    # Очищаем состояние после завершения опроса
    await state.set_state(SurveyStates.waiting_for_survey)
# Основная функция запуска бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
