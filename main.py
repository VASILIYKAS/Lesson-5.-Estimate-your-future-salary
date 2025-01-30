import requests
import statistics
import time
import os
from dotenv import load_dotenv
from terminaltables3 import AsciiTable


AREA = 1
PERIOD = 30
SALARY = 100
PER_PAGE = 50
TOWN = 4
COUNT = 50


def fetch_vacancies_sj(programming_language, page, api_key_sj):
    url = 'https://api.superjob.ru/2.0/vacancies/'

    params = {
        'keywords': f'программист {programming_language}',
        'town': TOWN,
        'not_archive': True,
        'page': page,
        'count': COUNT,
    }
    key = {
        'X-Api-App-Id': api_key_sj
    }

    response = requests.get(url, headers=key, params=params, timeout=60)
    response.raise_for_status()

    vacancies = response.json()
    has_more_pages = vacancies['more']

    return vacancies, has_more_pages


def predict_rub_salary_sj(programming_language, api_key_sj):
    total_avg_salary = []
    vacancies_processed = 0
    page = 0

    while True:
        vacancies, has_more_pages = fetch_vacancies_sj(
            programming_language, page, api_key_sj
        )

        for vacancy in vacancies['objects']:
            salary_from = vacancy.get('payment_from')
            salary_to = vacancy.get('payment_to')
            avg_salary = predict_salary(salary_from, salary_to)
            if salary_from or salary_to:
                total_avg_salary.append(avg_salary)
                vacancies_processed += 1

        vacancies_found_sj = vacancies.get('total')

        if not has_more_pages:
            break

        page += 1

    if total_avg_salary:
        return int(statistics.mean(total_avg_salary)), vacancies_found_sj, vacancies_processed
    else:
        return 0, vacancies_found_sj, vacancies_processed


def fetch_vacancies_hh(programming_language, page):
    params = {
        'text': f'программист {programming_language}',
        'area': AREA,
        'period': PERIOD,
        'salary': SALARY,
        'page': page,
        'per_page': PER_PAGE,
    }

    response = requests.get('https://api.hh.ru/vacancies', params=params)
    response.raise_for_status()

    vacancies = response.json()
    vacancies_found = vacancies['found']

    return vacancies, vacancies_found


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    elif not salary_from or not salary_from:
        return round(salary_to * 0.8)
    elif not salary_to or not salary_from:
        return round(salary_from * 1.2)
    else:
        return round((salary_from + salary_to) / 2)


def predict_rub_salary_hh(programming_language, pages_count):
    total_salaries = []
    vacancies_processed = 0

    for page in range(pages_count):
        vacancies, vacancies_found = fetch_vacancies_hh(programming_language, page)
        time.sleep(1)

        for vacancy in vacancies['items']:
            salary = vacancy.get('salary')
            if salary:
                salary_from = salary.get('from')
                salary_to = salary.get('to')
                avg_salary = predict_salary(salary_from, salary_to)
                total_salaries.append(avg_salary)
                vacancies_processed += 1

    return total_salaries, vacancies_processed, vacancies_found


def create_table(statistics_vacancy, name):
    title = 'HeadHunter' if name == 'hh' else 'SuperJob'

    table_data = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата",
        ]
    ]

    for language, data in statistics_vacancy.items():
        table_data.append([
            language,
            data["vacancies_found"],
            data["vacancies_processed"],
            data["average_salary"],
        ])

    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    load_dotenv()
    api_key_sj = os.environ['SECRET_KEY']
    pages_count_hh = 18

    salary_statistics_sj = {}
    salary_statistics_hh = {}

    programming_languages = ['Python', 'Java',
                             'JavaScript', 'Swift', 'PHP', 'C++', 'C#', 'Go']

    for language in programming_languages:
        avg_salary, vacancies_found_sj, vacancies_processed_sj = predict_rub_salary_sj(
            language, api_key_sj
        )

        salaries_avg, vacancies_processed_hh, vacancies_found = predict_rub_salary_hh(
            language, pages_count_hh
        )

        if salaries_avg:
            average_salary = int(statistics.mean(salaries_avg))
        else:
            average_salary = 0

        salary_statistics_hh[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed_hh,
            "average_salary": average_salary,
        }

        salary_statistics_sj[language] = {
            "vacancies_found": vacancies_found_sj,
            "vacancies_processed": vacancies_processed_sj,
            "average_salary": avg_salary,
        }

    create_table(salary_statistics_sj, name='sj')
    create_table(salary_statistics_hh, name='hh')


if __name__ == "__main__":
    main()
