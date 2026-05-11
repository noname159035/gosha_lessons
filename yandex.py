import random
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


FORM_URL = "https://forms.yandex.ru/u/69fdef9e49363954154f1b39"


MODES = {
    "1": {
        "name": "Тестовый режим",
        "headless": False,
        "delay_between_pages": 10,
    },
    "2": {
        "name": "Обычный режим",
        "headless": True,
        "delay_between_pages": 2,
    }
}


# ---------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------------

def weighted_choice(values):
    answers, weights = zip(*values)
    return random.choices(answers, weights=weights, k=1)[0]


def choice_from_range(values):
    return str(random.choice(values))


def normalize_text(text):
    if not text:
        return ""

    return " ".join(
        text
        .lower()
        .replace("ё", "е")
        .replace("«", "")
        .replace("»", "")
        .replace("“", "")
        .replace("”", "")
        .split()
    )


def text_contains(text, fragment):
    return normalize_text(fragment) in normalize_text(text)


# ---------------------- ПРОФИЛЬ ОТВЕТОВ ПО ТЗ ----------------------

ANSWER_PROFILE = {
    "fashion_interest": lambda: choice_from_range([3, 4, 5]),

    "image_scores": {
        1: {
            "русские мотивы": lambda: choice_from_range([5, 6]),
            "эстетически нравится": lambda: choice_from_range([4, 5]),
            "современно и актуально": lambda: choice_from_range([4, 5]),
            "носил": lambda: choice_from_range([2, 3]),
        },
        2: {
            "русские мотивы": lambda: choice_from_range([5, 6]),
            "эстетически нравится": lambda: "6",
            "современно и актуально": lambda: choice_from_range([5, 6]),
            "носил": lambda: choice_from_range([4, 5]),
        },
        3: {
            "русские мотивы": lambda: "7",
            "эстетически нравится": lambda: "4",
            "современно и актуально": lambda: "4",
            "носил": lambda: choice_from_range([3, 4]),
        },
        4: {
            "русские мотивы": lambda: choice_from_range([4, 5]),
            "эстетически нравится": lambda: choice_from_range([6, 7]),
            "современно и актуально": lambda: choice_from_range([6, 7]),
            "носил": lambda: choice_from_range([6, 7]),
        },
        5: {
            "русские мотивы": lambda: choice_from_range([6, 7]),
            "эстетически нравится": lambda: "6",
            "современно и актуально": lambda: choice_from_range([5, 6]),
            "носил": lambda: choice_from_range([5, 6]),
        },
        6: {
            "русские мотивы": lambda: choice_from_range([1, 2]),
            "эстетически нравится": lambda: choice_from_range([3, 4]),
            "современно и актуально": lambda: choice_from_range([3, 4]),
            "носил": lambda: choice_from_range([2, 3]),
        },
    },

    "designer_message": {
        1: [
            "ассоциируется со свободой",
            "ассоциируется с чем-то летящим",
            "ассоциируется с небом",
            "похоже на русскую зиму",
            "напоминает узоры гжели",
        ],
        2: [
            "переосмысление народных узоров",
            "современный образ с национальными мотивами",
            "национальные мотивы в современной форме",
        ],
        3: [
            "передать образ русской березы",
            "передать образ русских просторов",
            "отсылает к популярному в русской культуре образу берез",
            "показать связь между русской природой и модой",
        ],
        4: [
            "связать природные мотивы с современными образами",
            "осовременить природные мотивы",
        ],
        5: [
            "переплести русские мотивы с современной одеждой и образами",
            "переосмысление русских народных костюмов",
            "показать, что это может выглядеть современно",
            "русские культурные элементы может выглядеть стильно и актуально",
        ],
        6: [
            "не считываю какого-то сообщения",
            "больше похоже на классический образ",
            "не понимаю",
            "не вижу русских мотивов здесь",
            "нет особого посыла",
        ],
    },

    "associations": {
        1: [
            ("Национальная идентичность", 6),
            ("Традиция, наследие", 3),
            ("Современность, мода", 2),
            ("Искусство, творчество", 2),
        ],
        2: [
            ("Современность, мода", 6),
            ("Инновация, эксперимент", 6),
            ("Искусство, творчество", 3),
            ("Национальная идентичность", 2),
        ],
        3: [
            ("Традиция, наследие", 6),
            ("Национальная идентичность", 6),
            ("Стереотип, клише", 2),
            ("Искусство, творчество", 2),
        ],
        4: [
            ("Современность, мода", 6),
            ("Инновация, эксперимент", 6),
            ("Искусство, творчество", 3),
        ],
        5: [
            ("Традиция, наследие", 6),
            ("Современность, мода", 6),
            ("Национальная идентичность", 6),
            ("Искусство, творчество", 2),
        ],
        6: [
            ("Другое", 7),
            ("Современность, мода", 3),
            ("Стереотип, клише", 1),
        ],
    },

    "pleasantness": lambda: choice_from_range([5, 6]),
    "arousal": lambda: choice_from_range([5, 6]),
    "confidence": lambda: choice_from_range([5, 6]),

    "brand_equity": {
        "понимает русскую культуру": lambda: choice_from_range([4, 5]),
        "создает новые смыслы": lambda: choice_from_range([3, 4, 5]),
        "вносит вклад": lambda: choice_from_range([4, 5]),
        "гордился": lambda: choice_from_range([3, 4]),
    },

    "brand_attitude": {
        "высокого качества": lambda: choice_from_range([5, 6]),
        "вызывает у меня доверие": lambda: choice_from_range([5, 6]),
        "кажется мне уникальным": lambda: "4",
        "запомнил": lambda: "4",
        "положительные ассоциации": lambda: choice_from_range([5, 6]),
    },

    "behavior_intention": {
        "купили бы": lambda: choice_from_range([5, 6]),
        "подписались бы": lambda: choice_from_range([5, 6]),
        "поделились бы": lambda: choice_from_range([5, 6]),
        "посетили бы": lambda: choice_from_range([4, 5]),
        "рекомендовали бы": lambda: choice_from_range([4, 5]),
    },

    "cultural_identity": lambda: weighted_choice([
        ("Полностью отождествляю", 5),
        ("В значительной степени", 5),
        ("В некоторой степени", 2),
    ]),

    "national_motifs_attitude": lambda: weighted_choice([
        ("Скорее положительно", 6),
        ("Скорее нейтрально", 2),
    ]),

    "new_russianness_text": lambda: random.choice([
        "Попытка переосмыслить традиции, взять русские народные мотивы в одежде и встроить их в современные модные тренды.",
        "Новая русскость — это когда одежда с фольклорными мотивами вписана в современную моду.",
        "Для меня новая русскость — это возможность сказать «я из России» через интересные и тонкие визуальные намеки.",
    ]),
}


# ---------------------- SELENIUM ----------------------

def create_driver(headless=True):
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.page_load_strategy = "eager"

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def safe_click(driver, element):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        element
    )
    time.sleep(0.2)
    driver.execute_script("arguments[0].click();", element)


def find_clickable_by_text(driver, text):
    candidates = driver.find_elements(
        By.XPATH,
        "//*[self::label or self::button or @role='button' or @role='radio' or @role='checkbox']"
    )

    for el in candidates:
        try:
            if el.is_displayed() and text_contains(el.text, text):
                return el
        except Exception:
            continue

    return None


def click_answer_by_text(driver, text):
    el = find_clickable_by_text(driver, text)

    if el:
        safe_click(driver, el)
        print(f"  выбрано: {text}")
        return True

    print(f"  не найден вариант: {text}")
    return False


def click_checkbox_by_question_text(driver, question_text):
    labels = driver.find_elements(By.XPATH, "//label")

    for label in labels:
        try:
            if not label.is_displayed():
                continue

            if text_contains(label.text, question_text):
                checkbox = label.find_element(By.XPATH, ".//input[@type='checkbox']")
                if not checkbox.is_selected():
                    safe_click(driver, checkbox)

                print(f"  чекбокс выбран: {question_text}")
                return True

        except Exception:
            continue

    print(f"  чекбокс не найден: {question_text}")
    return False


def fill_text_field(driver, text):
    fields = driver.find_elements(
        By.XPATH,
        "//textarea | //input[not(@type) or @type='text' or @type='search']"
    )

    for field in fields:
        try:
            if field.is_displayed() and not field.get_attribute("value"):
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    field
                )
                time.sleep(0.2)
                field.clear()
                field.send_keys(text)
                print(f"  текст: {text[:70]}...")
                return True
        except Exception:
            continue

    print("  текстовое поле не найдено")
    return False


def fill_text_field_near_question(driver, question_fragment, text):
    labels = driver.find_elements(By.XPATH, "//*[@id and contains(@id, '-label')]")

    for label in labels:
        try:
            if not label.is_displayed():
                continue

            if text_contains(label.text, question_fragment):
                label_id = label.get_attribute("id")

                field = driver.find_element(
                    By.XPATH,
                    f"//input[@aria-labelledby='{label_id}'] | //textarea[@aria-labelledby='{label_id}']"
                )

                if field.is_displayed():
                    field.clear()
                    field.send_keys(text)
                    print(f"  текстовый ответ: {text}")
                    return True

        except Exception:
            continue

    blocks = driver.find_elements(
        By.XPATH,
        "//*[self::div or self::fieldset or self::section]"
    )

    matching_blocks = []

    for block in blocks:
        try:
            block_text = block.text
            if block_text and text_contains(block_text, question_fragment):
                matching_blocks.append(block)
        except Exception:
            continue

    matching_blocks = sorted(matching_blocks, key=lambda b: len(b.text or ""))

    for block in matching_blocks:
        try:
            fields = block.find_elements(
                By.XPATH,
                ".//textarea | .//input[not(@type) or @type='text' or @type='search']"
            )

            for field in fields:
                if field.is_displayed():
                    field.clear()
                    field.send_keys(text)
                    print(f"  текстовый ответ: {text}")
                    return True

        except Exception:
            continue

    fields = driver.find_elements(
        By.XPATH,
        "//textarea | //input[not(@type) or @type='text' or @type='search']"
    )

    for field in fields:
        try:
            if field.is_displayed() and not field.get_attribute("value"):
                field.clear()
                field.send_keys(text)
                print(f"  текстовый ответ через fallback: {text}")
                return True
        except Exception:
            continue

    print(f"  текстовое поле рядом с вопросом не найдено: {question_fragment}")
    return False


def click_scale_near_statement(driver, statement_fragment, value):
    rows = driver.find_elements(
        By.XPATH,
        "//*[self::div or self::fieldset or self::section]"
    )

    best_rows = []

    for row in rows:
        try:
            row_text = row.text
            if row_text and text_contains(row_text, statement_fragment):
                best_rows.append(row)
        except Exception:
            continue

    best_rows = sorted(best_rows, key=lambda r: len(r.text or ""))

    for row in best_rows:
        try:
            clickable_options = row.find_elements(
                By.XPATH,
                ".//*[self::label or self::button or @role='radio' or @role='button']"
            )

            for option in clickable_options:
                option_text = normalize_text(option.text)
                if option.is_displayed() and option_text == str(value):
                    safe_click(driver, option)
                    print(f"  {statement_fragment}: {value}")
                    return True

            radio_inputs = row.find_elements(By.XPATH, ".//input[@type='radio']")

            for radio in radio_inputs:
                radio_value = radio.get_attribute("value")
                aria = radio.get_attribute("aria-label") or ""

                if radio_value == str(value) or normalize_text(aria) == str(value):
                    safe_click(driver, radio)
                    print(f"  {statement_fragment}: {value}")
                    return True

        except Exception:
            continue

    print(f"  не найдена шкала: {statement_fragment} -> {value}")
    return False


def click_scale_in_question_block(driver, question_fragment, row_fragment, value):
    blocks = driver.find_elements(
        By.XPATH,
        "//*[self::div or self::fieldset or self::section]"
    )

    matching_blocks = []

    for block in blocks:
        try:
            block_text = block.text
            if block_text and text_contains(block_text, question_fragment):
                matching_blocks.append(block)
        except Exception:
            continue

    matching_blocks = sorted(matching_blocks, key=lambda b: len(b.text or ""))

    for question_block in matching_blocks:
        try:
            rows = question_block.find_elements(
                By.XPATH,
                ".//*[self::div or self::label or self::fieldset]"
            )

            matching_rows = []

            for row in rows:
                try:
                    row_text = row.text
                    if row_text and text_contains(row_text, row_fragment):
                        matching_rows.append(row)
                except Exception:
                    continue

            matching_rows = sorted(matching_rows, key=lambda r: len(r.text or ""))

            for row in matching_rows:
                clickable_options = row.find_elements(
                    By.XPATH,
                    ".//*[self::label or self::button or @role='radio' or @role='button']"
                )

                for option in clickable_options:
                    try:
                        if option.is_displayed() and normalize_text(option.text) == str(value):
                            safe_click(driver, option)
                            print(f"  {question_fragment} / {row_fragment}: {value}")
                            return True
                    except Exception:
                        continue

                radio_inputs = row.find_elements(By.XPATH, ".//input[@type='radio']")

                for radio in radio_inputs:
                    try:
                        radio_value = radio.get_attribute("value")
                        aria = radio.get_attribute("aria-label") or ""

                        if radio_value == str(value) or normalize_text(aria) == str(value):
                            safe_click(driver, radio)
                            print(f"  {question_fragment} / {row_fragment}: {value}")
                            return True
                    except Exception:
                        continue

        except Exception:
            continue

    print(f"  не найдена шкала: {question_fragment} / {row_fragment} -> {value}")
    return False


def find_next_button(driver):
    for text in ["Далее", "Продолжить", "Следующий"]:
        buttons = driver.find_elements(By.XPATH, "//button")

        for btn in buttons:
            try:
                if btn.is_displayed() and btn.is_enabled() and text_contains(btn.text, text):
                    return btn
            except Exception:
                continue

    return None


def find_submit_button(driver):
    for text in ["Отправить", "Завершить"]:
        buttons = driver.find_elements(By.XPATH, "//button")

        for btn in buttons:
            try:
                if btn.is_displayed() and btn.is_enabled() and text_contains(btn.text, text):
                    return btn
            except Exception:
                continue

    return None


# ---------------------- ЗАПОЛНЕНИЕ СТРАНИЦ ----------------------

def detect_image_number(page_text):
    for i in range(1, 7):
        if text_contains(page_text, f"образ {i}"):
            return i

    return None


def fill_q15_new_russianness(driver):
    page_text = driver.find_element(By.TAG_NAME, "body").text

    if not (
        text_contains(page_text, "что для вас означает")
        and text_contains(page_text, "новая русскость")
    ):
        return False

    text = ANSWER_PROFILE["new_russianness_text"]()

    fields = driver.find_elements(
        By.XPATH,
        "//textarea | //input[not(@type) or @type='text' or @type='search']"
    )

    empty_visible_fields = []

    for field in fields:
        try:
            if field.is_displayed() and not field.get_attribute("value"):
                empty_visible_fields.append(field)
        except Exception:
            continue

    if not empty_visible_fields:
        print("  Q15: текстовое поле не найдено")
        return False

    field = empty_visible_fields[-1]

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        field
    )
    time.sleep(0.2)

    field.clear()
    field.send_keys(text)

    print(f"  Q15 заполнен: {text}")
    return True


def fill_simple_detected_questions(driver):
    page_text = driver.find_element(By.TAG_NAME, "body").text

    if text_contains(page_text, "насколько вы интересуетесь модой"):
        click_answer_by_text(driver, ANSWER_PROFILE["fashion_interest"]())

    if text_contains(page_text, "вам больше 18 лет"):
        click_checkbox_by_question_text(driver, "Вам больше 18 лет")

    if text_contains(page_text, "насколько вы отождествляете себя с русской культурой"):
        click_answer_by_text(driver, ANSWER_PROFILE["cultural_identity"]())

    if text_contains(page_text, "как вы в целом относитесь к использованию национальных мотивов"):
        click_answer_by_text(driver, ANSWER_PROFILE["national_motifs_attitude"]())

    fill_q15_new_russianness(driver)


def fill_image_block(driver, image_num):
    print(f"Заполнение блока ОБРАЗ {image_num}")

    scores = ANSWER_PROFILE["image_scores"][image_num]

    click_scale_near_statement(
        driver,
        "легко узнаю русские мотивы",
        scores["русские мотивы"]()
    )

    click_scale_near_statement(
        driver,
        "эстетически нравится",
        scores["эстетически нравится"]()
    )

    click_scale_near_statement(
        driver,
        "современно и актуально",
        scores["современно и актуально"]()
    )

    click_scale_near_statement(
        driver,
        "носил",
        scores["носил"]()
    )

    designer_answer = random.choice(ANSWER_PROFILE["designer_message"][image_num])
    fill_text_field_near_question(
        driver,
        "как вы считаете, что хотел сказать дизайнер этим образом",
        designer_answer
    )

    assoc_pool = ANSWER_PROFILE["associations"][image_num]
    selected_associations = set()

    associations_count = random.randint(1, 3)

    for _ in range(associations_count):
        selected_associations.add(weighted_choice(assoc_pool))

    for association in selected_associations:
        click_answer_by_text(driver, association)

    if image_num == 6 and "Другое" in selected_associations:
        fill_text_field(driver, "Классика, классический образ.")


def fill_emotion_scales(driver):
    page_text = driver.find_element(By.TAG_NAME, "body").text

    if text_contains(page_text, "насколько приятным или неприятным"):
        for i in range(1, 7):
            click_scale_in_question_block(
                driver,
                "насколько приятным или неприятным",
                f"образ {i}",
                ANSWER_PROFILE["pleasantness"]()
            )

    if text_contains(page_text, "насколько спокойным или возбуждающим"):
        for i in range(1, 7):
            click_scale_in_question_block(
                driver,
                "насколько спокойным или возбуждающим",
                f"образ {i}",
                ANSWER_PROFILE["arousal"]()
            )

    if text_contains(page_text, "насколько уверенным или неуверенным"):
        for i in range(1, 7):
            click_scale_in_question_block(
                driver,
                "насколько уверенным или неуверенным",
                f"образ {i}",
                ANSWER_PROFILE["confidence"]()
            )


def fill_brand_blocks(driver):
    page_text = driver.find_element(By.TAG_NAME, "body").text

    if text_contains(page_text, "если бренд использует") and text_contains(page_text, "русский стиль"):
        for statement, answer_func in ANSWER_PROFILE["brand_equity"].items():
            click_scale_near_statement(driver, statement, answer_func())

    if text_contains(page_text, "насколько вы согласны со следующими утверждениями о таком бренде"):
        for statement, answer_func in ANSWER_PROFILE["brand_attitude"].items():
            click_scale_near_statement(driver, statement, answer_func())

    if text_contains(page_text, "насколько вероятно"):
        for statement, answer_func in ANSWER_PROFILE["behavior_intention"].items():
            click_scale_near_statement(driver, statement, answer_func())


def fill_current_page(driver):
    page_text = driver.find_element(By.TAG_NAME, "body").text

    fill_simple_detected_questions(driver)

    image_num = detect_image_number(page_text)
    if image_num:
        fill_image_block(driver, image_num)

    fill_emotion_scales(driver)
    fill_brand_blocks(driver)


# ---------------------- ОСНОВНОЙ ПРОХОД ----------------------

def complete_form_once(driver, delay_between_pages):
    """Заполняет и отправляет одну форму. Возвращает True при успешной отправке."""
    driver.get(FORM_URL)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//body"))
    )

    time.sleep(2)

    page_num = 1

    while True:
        print(f"\nСтраница {page_num}")

        fill_current_page(driver)

        submit_button = find_submit_button(driver)

        if submit_button:
            print(f"Страница заполнена. Ожидание {delay_between_pages} сек. перед отправкой.")
            time.sleep(delay_between_pages)

            print("Нажимаю кнопку отправки...")
            safe_click(driver, submit_button)

            # Ожидаем подтверждения отправки (по ключевым словам на странице)
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: (
                        "спасибо" in d.find_element(By.TAG_NAME, "body").text.lower()
                        or "благодарим" in d.find_element(By.TAG_NAME, "body").text.lower()
                        or "отправлено" in d.find_element(By.TAG_NAME, "body").text.lower()
                    )
                )
                print("Форма успешно отправлена (обнаружено подтверждение).")
                return True
            except Exception as e:
                print(f"Не удалось подтвердить отправку формы: {e}")
                return False

        next_button = find_next_button(driver)

        if next_button:
            print(f"Страница заполнена. Ожидание {delay_between_pages} сек. перед переходом.")
            time.sleep(delay_between_pages)

            safe_click(driver, next_button)

            page_num += 1
            time.sleep(1)
            continue

        print("\nНе найдена кнопка перехода или отправки.")
        return False


def choose_mode():
    print("Выберите режим:")
    print("1 — тестовый: браузер видимый, задержка 10 секунд перед переходом")
    print("2 — обычный: headless, задержка 2 секунды")

    mode = input("Введите 1 или 2: ").strip()

    if mode not in MODES:
        print("Неизвестный режим. Использую тестовый режим.")
        mode = "1"

    return MODES[mode]


# ---------------------- ОСНОВНАЯ ФУНКЦИЯ С ПРОХОДКАМИ ----------------------

def main():
    mode = choose_mode()

    print(f"\nРежим: {mode['name']}")
    print(f"Headless: {mode['headless']}")
    print(f"Задержка между страницами: {mode['delay_between_pages']} сек.")

    try:
        total_runs = int(input("Введите количество проходок: ").strip())
    except Exception:
        total_runs = 1
    print(f"Будет выполнено проходок: {total_runs}\n")

    success_count = 0

    for run_number in range(1, total_runs + 1):
        # Вывод в консоль номера текущей проходки
        print(f"\n=== Проходка {run_number}/{total_runs} ===")

        driver = create_driver(headless=mode["headless"])

        try:
            result = complete_form_once(
                driver=driver,
                delay_between_pages=mode["delay_between_pages"]
            )

            if result:
                print(f"Проходка {run_number} завершена успешно.")
                success_count += 1
            else:
                print(f"Проходка {run_number} завершена с ошибкой (не удалось отправить).")

        except Exception as e:
            print(f"Проходка {run_number} завершена с непредвиденной ошибкой: {e}")

        finally:
            driver.quit()
            # Небольшая пауза между проходками, чтобы не забивать сервер
            time.sleep(2)

    print(f"\nИтого успешных проходок: {success_count}/{total_runs}")


if __name__ == "__main__":
    main()