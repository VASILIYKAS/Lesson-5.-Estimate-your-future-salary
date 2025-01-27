import requests
import statistics
import time
import os
from dotenv import load_dotenv
from terminaltables3 import AsciiTable


def fetch_vacancies_sj(vacancies, pages):
    API_KEY = os.environ['SECRET_KEY']

    url = 'https://api.superjob.ru/2.0/vacancies/'

    params = {
        'keywords': f'программист {vacancies}',
        'town': 4,
        'not_archive': True,
        'page': pages,
        'count': 50,
    }
    key = {
        'X-Api-App-Id': API_KEY
    }

    response = requests.get(url, headers=key, params=params, timeout=60)
    response.raise_for_status()

    vacancies_info = response.json()

    return vacancies_info


def predict_rub_salary_sj(vacancies, pages):
    avg_salary = None
    vacancies_processed = 0
    for page in range(pages):
        vacancies_info = fetch_vacancies_sj(vacancies, page)

        for vacancy in vacancies_info['objects']:
            salary_from = vacancy.get('payment_from')
            salary_to = vacancy.get('payment_to')
            avg_salary = predict_salary(salary_from, salary_to)
            vacancies_processed += 1
            time.sleep(2)

    vacancies_found_sj = vacancies_info.get('total')

    return avg_salary, vacancies_found_sj, vacancies_processed


def fetch_vacancies_hh(programming_language, pages):
    params = {
        'text': f'программист {programming_language}',
        'area': 1,
        'period': 30,
        'salary': 100,
        'page': pages,
        'per_page': 50,
        }

    response = requests.get('https://api.hh.ru/vacancies', params=params)
    response.raise_for_status()

    vacancies_info = response.json()

    return vacancies_info


def find_job_vacancies_hh(programming_language, pages):

    vacancies_info = fetch_vacancies_hh(programming_language, pages)
    vacancies_found = vacancies_info['found']

    return vacancies_found


def predict_salary(salary_from, salary_to):
    if salary_from is None and salary_to is None:
        return None
    if salary_from == 0 and salary_to == 0:
        return None
    elif salary_from is None or salary_from == 0:
        return salary_to * 0.8
    elif salary_to is None or salary_from == 0:
        return salary_from * 1.2
    else:
        return (salary_from + salary_to) / 2


def predict_rub_salary_hh(programming_language, pages):
    total_salaries = []

    for page in range(pages):
        vacancies_info = fetch_vacancies_hh(programming_language, page)
        time.sleep(1)

        for vacancy in vacancies_info['items']:
            salary = vacancy.get('salary')
            if salary is not None:
                salary_from = salary.get('from')
                salary_to = salary.get('to')
                avg_salary = predict_salary(salary_from, salary_to)
                total_salaries.append(avg_salary)

    return total_salaries


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
    pages_sj = 2
    pages_hh = 16

    salary_statistics_sj = {}
    salary_statistics_hh = {}

    programming_language = ['Python', 'Java',
                            'JavaScript', 'Swift', 'PHP', 'C++', 'C#', 'Go']

    for language in programming_language:
        avg_salary, vacancies_found_sj, vacancies_processed = predict_rub_salary_sj(
            language, pages_sj
        )
        time.sleep(2)

        vacancies_found = find_job_vacancies_hh(language, pages_hh)
        salaries_avg = predict_rub_salary_hh(language, pages_hh)

        if salaries_avg:
            average_salary = int(statistics.mean(salaries_avg))
        else:
            average_salary = 0

        salary_statistics_hh[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": len(salaries_avg),
            "average_salary": average_salary,
            }

        salary_statistics_sj[language] = {
                "vacancies_found": vacancies_found_sj,
                "vacancies_processed": vacancies_processed,
                "average_salary": avg_salary,
                }

    create_table(salary_statistics_sj, name='sj')
    create_table(salary_statistics_hh, name='hh')


if __name__ == "__main__":
    main()
