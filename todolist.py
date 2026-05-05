import pygame
import sys
from datetime import datetime, timedelta
import math

pygame.init()
pygame.font.init()

# ─── Константы ───────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 900, 700
FPS = 60

# Имперская палитра
GOLD          = (212, 175, 55)
DARK_GOLD     = (160, 120, 20)
LIGHT_GOLD    = (240, 210, 100)
CREAM         = (245, 235, 210)
PARCHMENT     = (230, 215, 185)
DARK_PARCHMENT= (200, 180, 140)
IMPERIAL_RED  = (139, 20, 20)
DARK_RED      = (100, 10, 10)
DEEP_MAROON   = (70, 5, 5)
BLACK         = (10, 5, 0)
DARK_BROWN    = (40, 20, 5)
OFF_WHITE     = (250, 245, 235)
SHADOW        = (20, 10, 0, 120)
LIGHT_CREAM   = (252, 248, 238)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Императорский Реестр Дел")
clock = pygame.time.Clock()

# ─── Шрифты ──────────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["Georgia", "Times New Roman", "serif", "DejaVu Serif"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            return f
        except:
            pass
    return pygame.font.Font(None, size)

font_title   = load_font(42, bold=True)
font_heading = load_font(26, bold=True)
font_body    = load_font(19)
font_small   = load_font(15)
font_tiny    = load_font(13)
font_input   = load_font(18)

# ─── Состояние приложения ─────────────────────────────────────────────────────
tasks = []          # [{title, start, end}, ...]
show_modal = False
modal_field = 0     # 0=title, 1=start_date, 2=start_time, 3=end_date, 4=end_time
modal_inputs = ["", "", "", "", ""]
modal_error = ""
scroll_offset = 0
hover_task = -1
hover_add = False
hover_del = -1
anim_tick = 0

# ─── Вспомогательные функции рисования ───────────────────────────────────────

def draw_rect_rounded(surf, color, rect, radius=8, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)

def draw_ornament_line(surf, x1, y, x2, color=GOLD, thickness=2):
    pygame.draw.line(surf, color, (x1, y), (x2, y), thickness)
    pygame.draw.circle(surf, color, (x1, y), 4)
    pygame.draw.circle(surf, color, (x2, y), 4)
    mid = (x1 + x2) // 2
    pygame.draw.circle(surf, color, (mid, y), 5)
    pygame.draw.circle(surf, DARK_GOLD, (mid, y), 3)

def draw_diamond(surf, cx, cy, size, color):
    pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
    pygame.draw.polygon(surf, color, pts)

def draw_fleur(surf, cx, cy, size, color, tick=0):
    """Простой орнаментальный элемент — крест с кругами."""
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        ex = cx + int(math.cos(rad) * size)
        ey = cy + int(math.sin(rad) * size)
        pygame.draw.circle(surf, color, (ex, ey), max(2, size // 4))
    pygame.draw.circle(surf, color, (cx, cy), max(3, size // 3))

def draw_border_frame(surf, rect, color=GOLD, inner_color=DARK_GOLD):
    x, y, w, h = rect
    # Внешняя рамка
    pygame.draw.rect(surf, color, rect, 3, border_radius=4)
    # Внутренняя рамка
    inner = (x + 6, y + 6, w - 12, h - 12)
    pygame.draw.rect(surf, inner_color, inner, 1, border_radius=2)
    # Угловые ромбы
    for cx, cy in [(x, y), (x+w, y), (x, y+h), (x+w, y+h)]:
        draw_diamond(surf, cx, cy, 7, color)

def draw_scrolling_bg(surf):
    surf.fill(DEEP_MAROON)
    # Паттерн из маленьких ромбов
    for row in range(0, HEIGHT + 40, 30):
        for col in range(0, WIDTH + 40, 30):
            off = (row // 30) % 2 * 15
            draw_diamond(surf, col + off, row, 4, (100, 8, 8))
    # Верхняя и нижняя полосы
    pygame.draw.rect(surf, DARK_BROWN, (0, 0, WIDTH, 6))
    pygame.draw.rect(surf, DARK_BROWN, (0, HEIGHT-6, WIDTH, 6))

def parse_datetime(date_str, time_str):
    date_str = date_str.strip()
    time_str = time_str.strip()
    for dfmt in ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            d = datetime.strptime(date_str, dfmt)
            break
        except:
            d = None
    if d is None:
        return None
    for tfmt in ["%H:%M", "%H%M"]:
        try:
            t = datetime.strptime(time_str, tfmt)
            d = d.replace(hour=t.hour, minute=t.minute)
            return d
        except:
            pass
    return None

def fmt_delta(delta):
    total = int(delta.total_seconds())
    if total < 0:
        return "истёк"
    d = total // 86400
    h = (total % 86400) // 3600
    m = (total % 3600) // 60
    if d > 0:
        return f"{d}д {h}ч {m}м"
    elif h > 0:
        return f"{h}ч {m}м"
    else:
        return f"{m}м"

def elapsed_str(start):
    now = datetime.now()
    if now < start:
        return "не начато"
    delta = now - start
    return fmt_delta(delta)

def remaining_str(end):
    now = datetime.now()
    if now > end:
        return "ПРОСРОЧЕНО"
    return fmt_delta(end - now)

def progress_frac(start, end):
    now = datetime.now()
    total = (end - start).total_seconds()
    if total <= 0:
        return 1.0
    elapsed = (now - start).total_seconds()
    return max(0.0, min(1.0, elapsed / total))

# ─── Рисование карточки задачи ───────────────────────────────────────────────

CARD_H = 115
CARD_MARGIN = 12
LIST_TOP = 150
LIST_BOTTOM = HEIGHT - 80

def draw_task_card(surf, task, idx, y, hovered, del_hovered, tick):
    x = 30
    w = WIDTH - 60
    now = datetime.now()
    overdue = now > task["end"]

    # Фон карточки
    card_color = (235, 220, 185) if not overdue else (220, 195, 175)
    shadow_surf = pygame.Surface((w + 6, CARD_H + 6), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(shadow_surf, (10, 5, 0, 80), (3, 4, w + 3, CARD_H + 2), border_radius=8)
    surf.blit(shadow_surf, (x - 3, y - 2))

    border_col = IMPERIAL_RED if overdue else GOLD
    draw_rect_rounded(surf, card_color, (x, y, w, CARD_H), radius=8)
    pygame.draw.rect(surf, border_col, (x, y, w, CARD_H), 2, border_radius=8)

    # Левая декоративная полоса
    strip_color = IMPERIAL_RED if overdue else DARK_GOLD
    pygame.draw.rect(surf, strip_color, (x, y, 8, CARD_H), border_radius=4)
    draw_diamond(surf, x + 4, y + CARD_H // 2, 6, GOLD)

    # Номер
    num_surf = font_small.render(f"§{idx+1}", True, DARK_GOLD)
    surf.blit(num_surf, (x + 16, y + 10))

    # Заголовок
    title_color = DARK_RED if overdue else DARK_BROWN
    title = task["title"]
    if len(title) > 38:
        title = title[:36] + "…"
    t_surf = font_heading.render(title, True, title_color)
    surf.blit(t_surf, (x + 16, y + 30))

    # Даты
    start_str = task["start"].strftime("%d.%m.%Y %H:%M")
    end_str   = task["end"].strftime("%d.%m.%Y %H:%M")
    date_surf = font_tiny.render(f"Начало: {start_str}  →  Конец: {end_str}", True, DARK_BROWN)
    surf.blit(date_surf, (x + 16, y + 62))

    # Прогресс-бар
    bar_x = x + 16
    bar_y = y + 83
    bar_w = w - 180
    bar_h = 10
    pygame.draw.rect(surf, DARK_PARCHMENT, (bar_x, bar_y, bar_w, bar_h), border_radius=5)
    frac = progress_frac(task["start"], task["end"])
    filled_w = max(4, int(bar_w * frac))
    fill_color = IMPERIAL_RED if overdue else (80, 140, 60)
    pygame.draw.rect(surf, fill_color, (bar_x, bar_y, filled_w, bar_h), border_radius=5)
    pygame.draw.rect(surf, DARK_GOLD, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=5)

    # Elapsed / Remaining
    el_text = f"Прошло: {elapsed_str(task['start'])}"
    re_text = f"Осталось: {remaining_str(task['end'])}"
    el_surf = font_tiny.render(el_text, True, (80, 60, 20))
    re_color = IMPERIAL_RED if overdue else (50, 100, 40)
    re_surf = font_tiny.render(re_text, True, re_color)
    surf.blit(el_surf, (bar_x + bar_w + 12, y + 62))
    surf.blit(re_surf, (bar_x + bar_w + 12, y + 80))

    # Кнопка удаления
    del_x = x + w - 38
    del_y = y + 10
    del_col = IMPERIAL_RED if del_hovered else (180, 80, 80)
    pygame.draw.rect(surf, del_col, (del_x, del_y, 24, 24), border_radius=5)
    pygame.draw.rect(surf, DARK_GOLD, (del_x, del_y, 24, 24), 1, border_radius=5)
    x_surf = font_body.render("✕", True, CREAM)
    surf.blit(x_surf, (del_x + 4, del_y + 1))

    return pygame.Rect(del_x, del_y, 24, 24)

# ─── Модальное окно добавления задачи ────────────────────────────────────────

FIELD_LABELS = ["Название дела", "Дата начала (дд.мм.гггг)", "Время начала (чч:мм)",
                "Дата окончания (дд.мм.гггг)", "Время окончания (чч:мм)"]
FIELD_PLACEHOLDERS = ["Составить реляцию...", "01.01.1905", "09:00",
                      "31.12.1905", "23:59"]

def draw_modal(surf, inputs, active_field, error, tick):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 5, 0, 190))
    surf.blit(overlay, (0, 0))

    mw, mh = 560, 480
    mx = (WIDTH - mw) // 2
    my = (HEIGHT - mh) // 2

    # Фон модалки
    draw_rect_rounded(surf, PARCHMENT, (mx, my, mw, mh), radius=10)
    draw_border_frame(surf, (mx, my, mw, mh), GOLD, DARK_GOLD)

    # Угловые флёры
    for cx, cy in [(mx+20, my+20), (mx+mw-20, my+20),
                   (mx+20, my+mh-20), (mx+mw-20, my+mh-20)]:
        draw_fleur(surf, cx, cy, 10, DARK_GOLD)

    # Заголовок
    title = font_heading.render("✦  Новое Дело  ✦", True, IMPERIAL_RED)
    surf.blit(title, (mx + mw//2 - title.get_width()//2, my + 22))
    draw_ornament_line(surf, mx + 30, my + 58, mx + mw - 30, GOLD)

    # Поля ввода (2 колонки: start / end)
    labels_left  = [FIELD_LABELS[1], FIELD_LABELS[2]]
    labels_right = [FIELD_LABELS[3], FIELD_LABELS[4]]

    # Название
    lbl = font_small.render(FIELD_LABELS[0], True, DARK_BROWN)
    surf.blit(lbl, (mx + 30, my + 75))
    fld_rect = pygame.Rect(mx + 30, my + 95, mw - 60, 36)
    is_active = active_field == 0
    draw_rect_rounded(surf, OFF_WHITE, fld_rect, radius=5)
    pygame.draw.rect(surf, GOLD if is_active else DARK_PARCHMENT, fld_rect, 2, border_radius=5)
    val = inputs[0] if inputs[0] else ""
    cursor = "|" if is_active and tick % 60 < 30 else ""
    t = font_input.render(val + cursor, True, BLACK)
    surf.blit(t, (fld_rect.x + 8, fld_rect.y + 8))
    if not inputs[0]:
        ph = font_input.render(FIELD_PLACEHOLDERS[0], True, DARK_PARCHMENT)
        surf.blit(ph, (fld_rect.x + 8, fld_rect.y + 8))

    # Два столбца: начало / конец
    col_labels = [["Дата начала", "Время начала"], ["Дата окончания", "Время окончания"]]
    col_placeholders = [["дд.мм.гггг", "чч:мм"], ["дд.мм.гггг", "чч:мм"]]
    col_field_idxs = [[1, 2], [3, 4]]
    col_x = [mx + 30, mx + mw // 2 + 10]
    col_w = mw // 2 - 45

    for ci in range(2):
        for ri in range(2):
            fidx = col_field_idxs[ci][ri]
            label_txt = col_labels[ci][ri]
            fy = my + 162 + ri * 80
            fx = col_x[ci]

            lbl = font_small.render(label_txt, True, DARK_BROWN)
            surf.blit(lbl, (fx, fy))
            fld_rect = pygame.Rect(fx, fy + 20, col_w, 36)
            is_active = active_field == fidx
            draw_rect_rounded(surf, OFF_WHITE, fld_rect, radius=5)
            pygame.draw.rect(surf, GOLD if is_active else DARK_PARCHMENT, fld_rect, 2, border_radius=5)
            val = inputs[fidx]
            cursor = "|" if is_active and tick % 60 < 30 else ""
            t = font_input.render(val + cursor, True, BLACK)
            surf.blit(t, (fld_rect.x + 8, fld_rect.y + 8))
            if not inputs[fidx]:
                ph = font_input.render(col_placeholders[ci][ri], True, DARK_PARCHMENT)
                surf.blit(ph, (fld_rect.x + 8, fld_rect.y + 8))

    draw_ornament_line(surf, mx + 30, my + 345, mx + mw - 30, DARK_GOLD)

    # Подсказка навигации
    hint = font_tiny.render("Tab — следующее поле  |  Enter — подтвердить  |  Esc — отмена", True, DARK_PARCHMENT)
    surf.blit(hint, (mx + mw//2 - hint.get_width()//2, my + 356))

    # Ошибка
    if error:
        err_surf = font_small.render(error, True, IMPERIAL_RED)
        surf.blit(err_surf, (mx + mw//2 - err_surf.get_width()//2, my + 378))

    # Кнопки
    btn_y = my + mh - 65
    # Подтвердить
    btn_ok = pygame.Rect(mx + mw // 2 - 130, btn_y, 120, 40)
    draw_rect_rounded(surf, IMPERIAL_RED, btn_ok, radius=6)
    pygame.draw.rect(surf, GOLD, btn_ok, 2, border_radius=6)
    ok_t = font_body.render("Занести", True, CREAM)
    surf.blit(ok_t, (btn_ok.centerx - ok_t.get_width()//2, btn_ok.centery - ok_t.get_height()//2))

    # Отмена
    btn_cancel = pygame.Rect(mx + mw // 2 + 10, btn_y, 120, 40)
    draw_rect_rounded(surf, DARK_BROWN, btn_cancel, radius=6)
    pygame.draw.rect(surf, GOLD, btn_cancel, 2, border_radius=6)
    cl_t = font_body.render("Отмена", True, CREAM)
    surf.blit(cl_t, (btn_cancel.centerx - cl_t.get_width()//2, btn_cancel.centery - cl_t.get_height()//2))

    return btn_ok, btn_cancel, [
        pygame.Rect(mx + 30, my + 95, mw - 60, 36),                   # title
        pygame.Rect(col_x[0], my + 182, col_w, 36),                    # start date
        pygame.Rect(col_x[0], my + 262, col_w, 36),                    # start time
        pygame.Rect(col_x[1], my + 182, col_w, 36),                    # end date
        pygame.Rect(col_x[1], my + 262, col_w, 36),                    # end time
    ]

# ─── Попытка добавить задачу ─────────────────────────────────────────────────

def try_add_task():
    global modal_error
    title = modal_inputs[0].strip()
    if not title:
        modal_error = "Необходимо указать название дела"
        return False
    start = parse_datetime(modal_inputs[1], modal_inputs[2])
    if start is None:
        modal_error = "Неверный формат даты/времени начала"
        return False
    end = parse_datetime(modal_inputs[3], modal_inputs[4])
    if end is None:
        modal_error = "Неверный формат даты/времени окончания"
        return False
    if end <= start:
        modal_error = "Срок окончания должен быть позже начала"
        return False
    tasks.append({"title": title, "start": start, "end": end})
    return True

# ─── Главный цикл ────────────────────────────────────────────────────────────

def main():
    global show_modal, modal_field, modal_inputs, modal_error
    global scroll_offset, hover_task, hover_add, hover_del, anim_tick

    running = True
    while running:
        dt = clock.tick(FPS)
        anim_tick += 1
        mx_pos, my_pos = pygame.mouse.get_pos()

        # Вычисляем зоны задач
        visible_tasks = []
        for i, task in enumerate(tasks):
            cy = LIST_TOP + i * (CARD_H + CARD_MARGIN) - scroll_offset
            visible_tasks.append((i, task, cy))

        # Ховер
        hover_task = -1
        hover_del  = -1
        hover_add  = False
        add_btn_rect = pygame.Rect(WIDTH - 180, HEIGHT - 60, 155, 44)
        if add_btn_rect.collidepoint(mx_pos, my_pos):
            hover_add = True
        for i, task, cy in visible_tasks:
            card_rect = pygame.Rect(30, cy, WIDTH - 60, CARD_H)
            del_rect  = pygame.Rect(WIDTH - 68, cy + 10, 24, 24)
            if del_rect.collidepoint(mx_pos, my_pos):
                hover_del = i
            elif card_rect.collidepoint(mx_pos, my_pos):
                hover_task = i

        # ── События ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEWHEEL and not show_modal:
                max_scroll = max(0, len(tasks) * (CARD_H + CARD_MARGIN) - (LIST_BOTTOM - LIST_TOP))
                scroll_offset = max(0, min(max_scroll, scroll_offset - event.y * 30))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if show_modal:
                    btn_ok, btn_cancel, field_rects = draw_modal(
                        pygame.Surface((1, 1)), modal_inputs, modal_field, modal_error, anim_tick)
                    # Перерисуем для получения реальных rect'ов
                    pass  # Обрабатываем через флаги ниже
                    # Попробуем вычислить rect'ы напрямую
                    mw, mh = 560, 480
                    mx_m = (WIDTH - mw) // 2
                    my_m = (HEIGHT - mh) // 2
                    col_x = [mx_m + 30, mx_m + mw // 2 + 10]
                    col_w = mw // 2 - 45
                    real_fields = [
                        pygame.Rect(mx_m + 30, my_m + 95, mw - 60, 36),
                        pygame.Rect(col_x[0], my_m + 182, col_w, 36),
                        pygame.Rect(col_x[0], my_m + 262, col_w, 36),
                        pygame.Rect(col_x[1], my_m + 182, col_w, 36),
                        pygame.Rect(col_x[1], my_m + 262, col_w, 36),
                    ]
                    real_ok     = pygame.Rect(mx_m + mw // 2 - 130, my_m + mh - 65, 120, 40)
                    real_cancel = pygame.Rect(mx_m + mw // 2 + 10,  my_m + mh - 65, 120, 40)

                    if real_ok.collidepoint(mx_pos, my_pos):
                        if try_add_task():
                            show_modal = False
                            modal_inputs = ["", "", "", "", ""]
                            modal_error = ""
                    elif real_cancel.collidepoint(mx_pos, my_pos):
                        show_modal = False
                        modal_inputs = ["", "", "", "", ""]
                        modal_error = ""
                    else:
                        for fi, fr in enumerate(real_fields):
                            if fr.collidepoint(mx_pos, my_pos):
                                modal_field = fi
                                break
                else:
                    if add_btn_rect.collidepoint(mx_pos, my_pos):
                        show_modal = True
                        modal_field = 0
                        modal_inputs = ["", "", "", "", ""]
                        modal_error = ""
                    else:
                        for i, task, cy in visible_tasks:
                            del_rect = pygame.Rect(WIDTH - 68, cy + 10, 24, 24)
                            if del_rect.collidepoint(mx_pos, my_pos):
                                tasks.pop(i)
                                break

            elif event.type == pygame.KEYDOWN and show_modal:
                if event.key == pygame.K_ESCAPE:
                    show_modal = False
                    modal_inputs = ["", "", "", "", ""]
                    modal_error = ""
                elif event.key == pygame.K_TAB:
                    modal_field = (modal_field + 1) % 5
                elif event.key == pygame.K_RETURN:
                    if try_add_task():
                        show_modal = False
                        modal_inputs = ["", "", "", "", ""]
                        modal_error = ""
                elif event.key == pygame.K_BACKSPACE:
                    modal_inputs[modal_field] = modal_inputs[modal_field][:-1]
                    modal_error = ""
                else:
                    if event.unicode and len(modal_inputs[modal_field]) < 60:
                        modal_inputs[modal_field] += event.unicode
                        modal_error = ""
        draw_scrolling_bg(screen)

        # Верхняя панель
        pygame.draw.rect(screen, DARK_BROWN, (0, 0, WIDTH, 130))
        pygame.draw.rect(screen, GOLD, (0, 128, WIDTH, 3))

        # Угловые орнаменты
        for cx, cy in [(40, 65), (WIDTH - 40, 65)]:
            draw_fleur(screen, cx, cy, 18, DARK_GOLD, anim_tick)

        # Заголовок
        title_surf = font_title.render("✦  ИМПЕРАТОРСКИЙ РЕЕСТР ДЕЛ  ✦", True, GOLD)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 20))

        # Подзаголовок с датой
        now_str = datetime.now().strftime("%d %B %Y  |  %H:%M:%S")
        sub_surf = font_small.render(now_str, True, LIGHT_GOLD)
        screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 72))

        draw_ornament_line(screen, 80, 100, WIDTH - 80, DARK_GOLD)

        # Заголовок списка
        count_surf = font_small.render(
            f"Всего дел: {len(tasks)}", True, GOLD)
        screen.blit(count_surf, (35, LIST_TOP - 28))

        # Clip-зона для карточек
        clip_rect = pygame.Rect(0, LIST_TOP, WIDTH, LIST_BOTTOM - LIST_TOP)
        screen.set_clip(clip_rect)

        del_rects = []
        for i, task, cy in visible_tasks:
            if cy + CARD_H < LIST_TOP or cy > LIST_BOTTOM:
                del_rects.append(None)
                continue
            dr = draw_task_card(screen, task, i, cy,
                                hover_task == i, hover_del == i, anim_tick)
            del_rects.append(dr)

        screen.set_clip(None)

        # Пустой список
        if not tasks:
            empty_surf = font_body.render(
                "— Реестр пуст. Добавьте первое дело —", True, LIGHT_GOLD)
            screen.blit(empty_surf, (WIDTH // 2 - empty_surf.get_width() // 2,
                                     LIST_TOP + (LIST_BOTTOM - LIST_TOP) // 2 - 15))

        # Нижняя панель
        pygame.draw.rect(screen, DARK_BROWN, (0, LIST_BOTTOM, WIDTH, HEIGHT - LIST_BOTTOM))
        pygame.draw.rect(screen, GOLD, (0, LIST_BOTTOM, WIDTH, 2))

        # Кнопка добавления
        btn_color = IMPERIAL_RED if hover_add else DARK_RED
        draw_rect_rounded(screen, btn_color, add_btn_rect, radius=8)
        pygame.draw.rect(screen, GOLD, add_btn_rect, 2, border_radius=8)
        draw_diamond(screen, add_btn_rect.x + 20, add_btn_rect.centery, 6, GOLD)
        draw_diamond(screen, add_btn_rect.right - 20, add_btn_rect.centery, 6, GOLD)
        btn_label = font_body.render("✦  Добавить дело", True, CREAM)
        screen.blit(btn_label, (add_btn_rect.centerx - btn_label.get_width() // 2,
                                add_btn_rect.centery - btn_label.get_height() // 2))

        # Скролл-подсказка
        if len(tasks) > 4:
            scroll_hint = font_tiny.render("↕ прокрутка колёсиком", True, DARK_GOLD)
            screen.blit(scroll_hint, (30, HEIGHT - 52))

        # Модальное окно
        if show_modal:
            draw_modal(screen, modal_inputs, modal_field, modal_error, anim_tick)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
