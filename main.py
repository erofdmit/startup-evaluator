from fastapi import FastAPI
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()

openai.api_key = os.getenv('OPENAI_KEY')

class SurveyResponse(BaseModel):
    target_audience: str
    technical_specifications: str
    budget: str
    competitors: str
    marketing_plan: str
    mvp: str

# Функция для запроса в GPT с учетом истории
def ask_chatgpt(prompt: str, history: list):
    # Добавляем новый запрос в историю
    history.append({"role": "user", "content": prompt})
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,  # Передаем всю историю
    )
    
    # Получаем и сохраняем ответ в историю
    answer = response.choices[0].message.content
    history.append({"role": "assistant", "content": answer})
    
    return answer

# Оценка по каждому аспекту с сохранением контекста
def evaluate_responses(survey: SurveyResponse):
    evaluations = {}
    history = [{"role": "system", "content": "You are an expert startup evaluator. Answer the questions. All answers must be not longer than 200 tokens. Answer in the language of main information"}]
    
    # Вопросы для каждого аспекта
    prompts = {
        "target_audience": f"Оцените готовность целевой аудитории: {survey.target_audience}",
        "technical_specifications": f"Оцените готовность технического задания: {survey.technical_specifications}",
        "budget": f"Оцените готовность бюджета: {survey.budget}",
        "competitors": f"Оцените готовность анализа конкурентов: {survey.competitors}",
        "marketing_plan": f"Оцените готовность маркетинг-плана: {survey.marketing_plan}",
        "mvp": f"Оцените готовность минимально жизнеспособного продукта (MVP): {survey.mvp}",
    }

    # Проходимся по каждому аспекту и добавляем контекст
    for key, prompt in prompts.items():
        evaluations[key] = ask_chatgpt(prompt, history)

    return evaluations, history

# Итоговая оценка с учетом контекста
def ask_overall_readiness(evaluations, history):
    prompt = (
        f"Оцените общую готовность стартапа на основе следующих данных: "
        f"Целевая аудитория: {evaluations['target_audience']}. "
        f"Техническое задание: {evaluations['technical_specifications']}. "
        f"Бюджет: {evaluations['budget']}. "
        f"Анализ конкурентов: {evaluations['competitors']}. "
        f"Маркетинг-план: {evaluations['marketing_plan']}. "
        f"Минимально жизнеспособный продукт (MVP): {evaluations['mvp']}."
        f"Предоставьте общую оценку готовности."
    )
    
    return ask_chatgpt(prompt, history)

# Рекомендации с учетом контекста
def ask_recommendations(evaluations, history):
    prompt = (
        f"На основе следующих данных: "
        f"Целевая аудитория: {evaluations['target_audience']}. "
        f"Техническое задание: {evaluations['technical_specifications']}. "
        f"Бюджет: {evaluations['budget']}. "
        f"Анализ конкурентов: {evaluations['competitors']}. "
        f"Маркетинг-план: {evaluations['marketing_plan']}. "
        f"Минимально жизнеспособный продукт (MVP): {evaluations['mvp']}."
        f"Предоставьте рекомендации для улучшения проекта. Сплошным текстом с пунктами"
    )
    
    return ask_chatgpt(prompt, history)

@app.post("/survey")
async def submit_survey(survey: SurveyResponse):
    # Оценка по каждому аспекту с контекстом
    evaluations, history = evaluate_responses(survey)

    # Общая степень готовности через GPT
    overall_status = ask_overall_readiness(evaluations, history)

    # Рекомендации через GPT
    recommendations = ask_recommendations(evaluations, history)
    
    return {
        "evaluations": evaluations,
        "overall_status": overall_status,
        "recommendations": recommendations
    }


