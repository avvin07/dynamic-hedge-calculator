import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import locale
from tkinter import messagebox

# Настройка локализации для поддержки разделителей как "," так и "."
try:
    locale.setlocale(locale.LC_NUMERIC, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_NUMERIC, 'Russian_Russia.1251')
    except:
        pass  # Если не удалось установить локаль, оставляем стандартную

class HedgeTransaction:
    def __init__(self, price, amount, direction, fee, order_number):
        self.price = price
        self.amount = amount
        self.direction = direction
        self.fee = fee
        self.order_number = order_number

class UniswapV3HedgeCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Калькулятор хеджирования Uniswap V3")
        # Изменяем размер окна на более книжный формат и увеличиваем на 20%
        self.geometry("960x1200")  # Было 800x1000, увеличено на 20%
        self.configure(bg="#f0f0f0")
        
        # Добавляем обработчик изменения размера окна
        self.bind("<Configure>", self.on_window_resize)
        
        # Initialize variables
        self.current_price = tk.DoubleVar(value=1616)
        self.lower_bound = tk.DoubleVar(value=1550)
        self.upper_bound = tk.DoubleVar(value=2200)
        self.total_pool_value = tk.DoubleVar(value=10000)
        
        # Отключаем автоматическое обновление графиков при изменении значений
        # self.current_price.trace_add("write", self.on_variable_change)
        # self.lower_bound.trace_add("write", self.on_variable_change)
        # self.upper_bound.trace_add("write", self.on_variable_change)
        # self.total_pool_value.trace_add("write", self.on_variable_change)
        
        # Хеджирующий инструмент
        self.hedge_enabled = tk.BooleanVar(value=True)  # По умолчанию включено
        self.hedge_instrument = tk.StringVar(value="Фьючерс ETH")
        self.hedge_amount = tk.DoubleVar(value=5.408)  # Инициализируем примерным значением ETH
        self.hedge_price = tk.DoubleVar(value=1616)
        # Добавляем комиссию для хеджирования - устанавливаем 0.2% по умолчанию
        self.hedge_fee_percent = tk.DoubleVar(value=0.2)  # 0.2% комиссия по умолчанию
        self.hedge_fee_value = tk.StringVar(value="0.00")  # Переменная для отображения суммы комиссии
        
        # Переменные для сеточного хеджирования
        self.grid_step = tk.DoubleVar(value=50.0)  # Шаг сетки в USDC
        self.grid_fee = tk.DoubleVar(value=0.2)  # Комиссия для сеточного хеджирования
        self.simulation_prices = []  # Список цен для симуляции
        self.grid_transactions = []  # Список транзакций сеточного хеджирования
        
        # Переменные для анализа результатов
        self.exit_price = tk.DoubleVar(value=2200)
        self.base_pnl = tk.StringVar(value="0.00")
        self.hedge_pnl = tk.StringVar(value="0.00")
        self.total_pnl = tk.StringVar(value="0.00")
        
        # Переменные для динамического хеджирования
        self.dynamic_step = tk.DoubleVar(value=50.0)  # Шаг изменения цены для ребалансировки
        self.dynamic_prices = []  # Список пользовательских цен
        self.dynamic_price_vars = []  # Список переменных для полей ввода цен
        self.dynamic_results = []  # Результаты расчетов
        
        # Добавляем отслеживание изменений для цены выхода - обновляем только результаты, не графики
        self.exit_price.trace_add("write", self.on_exit_price_change)
        
        # Флаг для предотвращения множественных обновлений
        self.updating = False
        
        # Инициализация переменных для сеточного хеджирования
        self.simulation_results = []
        
        # Create the GUI
        self.create_widgets()
        
        # Initial calculation
        self.calculate()
    
    def create_widgets(self):
        # Создаем вкладки
        self.tab_control = ttk.Notebook(self)
        
        # Основная вкладка
        self.main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.main_tab, text="Основная позиция")
        
        # Вкладка хеджирования
        self.hedge_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.hedge_tab, text="Хеджирование")
        
        # Вкладка сеточного хеджирования
        self.grid_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.grid_tab, text="Сеточное хеджирование")
        
        # Добавляем вкладку динамического хеджирования
        self.dynamic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dynamic_tab, text="Динамический хедж")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Создаем виджеты для основной вкладки
        self.create_main_tab_widgets()
        
        # Создаем виджеты для вкладки хеджирования
        self.create_hedge_tab_widgets()
        
        # Создаем виджеты для вкладки сеточного хеджирования
        self.create_grid_tab_widgets()
        
        # Создаем виджеты для вкладки динамического хеджирования
        self.create_dynamic_tab_widgets()
    
    def create_main_tab_widgets(self):
        # Create input frame on main tab
        input_frame = ttk.LabelFrame(self.main_tab, text="Входные параметры", padding=10)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        # Current price
        ttk.Label(input_frame, text="Текущая цена (ETH):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.current_price, width=15).grid(row=0, column=1, pady=5)
        
        # Lower bound
        ttk.Label(input_frame, text="Нижняя граница (USDC):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.lower_bound, width=15).grid(row=1, column=1, pady=5)
        
        # Upper bound
        ttk.Label(input_frame, text="Верхняя граница (USDC):").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.upper_bound, width=15).grid(row=2, column=1, pady=5)
        
        # Total pool value
        ttk.Label(input_frame, text="Общая стоимость пула (USDC):").grid(row=0, column=2, sticky="w", padx=20, pady=5)
        ttk.Entry(input_frame, textvariable=self.total_pool_value, width=15).grid(row=0, column=3, pady=5)
        
        # Create results frame
        self.results_frame = ttk.LabelFrame(self.main_tab, text="Результаты расчетов", padding=10)
        self.results_frame.pack(fill="x", padx=20, pady=10)
        
        # Results variables
        self.liquidity_var = tk.StringVar()
        self.eth_amount_var = tk.StringVar()
        self.usdc_amount_var = tk.StringVar()
        
        self.upper_eth_var = tk.StringVar()
        self.upper_usdc_var = tk.StringVar()
        
        self.lower_eth_var = tk.StringVar()
        self.lower_usdc_var = tk.StringVar()
        
        # Current position
        ttk.Label(self.results_frame, text="Текущая позиция:").grid(row=0, column=0, sticky="w", pady=5, columnspan=2)
        ttk.Label(self.results_frame, text="Ликвидность (L):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(self.results_frame, textvariable=self.liquidity_var).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(self.results_frame, text="Количество ETH:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Label(self.results_frame, textvariable=self.eth_amount_var).grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(self.results_frame, text="Количество USDC:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Label(self.results_frame, textvariable=self.usdc_amount_var).grid(row=3, column=1, sticky="w", pady=5)
        
        # Upper bound reached
        ttk.Label(self.results_frame, text="При достижении верхней границы:").grid(row=0, column=2, sticky="w", pady=5, padx=20, columnspan=2)
        ttk.Label(self.results_frame, text="Количество ETH:").grid(row=1, column=2, sticky="w", pady=5, padx=20)
        ttk.Label(self.results_frame, textvariable=self.upper_eth_var).grid(row=1, column=3, sticky="w", pady=5)
        
        ttk.Label(self.results_frame, text="Количество USDC:").grid(row=2, column=2, sticky="w", pady=5, padx=20)
        ttk.Label(self.results_frame, textvariable=self.upper_usdc_var).grid(row=2, column=3, sticky="w", pady=5)
        
        # Lower bound reached
        ttk.Label(self.results_frame, text="При достижении нижней границы:").grid(row=4, column=0, sticky="w", pady=5, columnspan=2)
        ttk.Label(self.results_frame, text="Количество ETH:").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Label(self.results_frame, textvariable=self.lower_eth_var).grid(row=5, column=1, sticky="w", pady=5)
        
        ttk.Label(self.results_frame, text="Количество USDC:").grid(row=6, column=0, sticky="w", pady=5)
        ttk.Label(self.results_frame, textvariable=self.lower_usdc_var).grid(row=6, column=1, sticky="w", pady=5)
        
        # Добавляем кнопку "Обновить графики" в правую часть панели результатов (где была стрелка)
        update_button = ttk.Button(self.results_frame, text="Обновить графики", command=self.refresh_plots, width=20)
        update_button.grid(row=5, column=2, rowspan=2, columnspan=2, pady=10, padx=20, sticky="nsew")
        
        # Настройка главного контейнера для растяжения
        self.main_tab.rowconfigure(2, weight=1)
        self.main_tab.columnconfigure(0, weight=1)
        
        # Create plot frame for main position
        self.plot_frame = ttk.LabelFrame(self.main_tab, text="Визуализация диапазона ликвидности", padding=10)
        self.plot_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create matplotlib figure with subplots for main position в книжном формате
        self.figure = plt.Figure(figsize=(7, 8), dpi=100)
        self.ax1 = self.figure.add_subplot(211)  # Верхний график для ETH и USDC
        self.ax2 = self.figure.add_subplot(212)  # Нижний график для общей ценности
        self.figure.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_hedge_tab_widgets(self):
        # Создаем фрейм-контейнер для размещения трех фреймов в одной строке
        hedge_container = ttk.Frame(self.hedge_tab)
        hedge_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Настраиваем веса для столбцов, чтобы они равномерно распределялись
        hedge_container.columnconfigure(0, weight=1)
        hedge_container.columnconfigure(1, weight=1)
        hedge_container.columnconfigure(2, weight=1)
        
        # Настроим веса строк: верхняя для настроек, нижняя для графика
        hedge_container.rowconfigure(0, weight=0)  # Верхняя строка не растягивается
        hedge_container.rowconfigure(1, weight=1)  # Нижняя строка растягивается
        
        # 1. Создаем фрейм настроек хеджирования (слева)
        hedge_frame = ttk.LabelFrame(hedge_container, text="Настройки хеджирования", padding=10)
        hedge_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        
        # Enable hedge checkbox
        hedge_check = ttk.Checkbutton(hedge_frame, text="Включить хеджирование", variable=self.hedge_enabled, 
                       command=self.update_hedge)
        hedge_check.grid(row=0, column=0, sticky="w", pady=5, columnspan=2)
        
        # По умолчанию устанавливаем хеджирование включенным
        self.hedge_enabled.set(True)
        
        # Hedge instrument selection
        ttk.Label(hedge_frame, text="Инструмент:").grid(row=1, column=0, sticky="w", pady=5)
        hedge_combo = ttk.Combobox(hedge_frame, textvariable=self.hedge_instrument, state="readonly", width=15)
        hedge_combo['values'] = ("Фьючерс ETH", "Опцион ETH PUT", "Опцион ETH CALL")
        hedge_combo.grid(row=1, column=1, pady=5)
        hedge_combo.bind("<<ComboboxSelected>>", self.update_hedge_amount)
        
        # Hedge amount
        ttk.Label(hedge_frame, text="Количество:").grid(row=2, column=0, sticky="w", pady=5)
        self.hedge_amount_entry = ttk.Entry(hedge_frame, textvariable=self.hedge_amount, width=15)
        self.hedge_amount_entry.grid(row=2, column=1, pady=5)
        
        # Hedge price
        ttk.Label(hedge_frame, text="Цена хеджирования:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(hedge_frame, textvariable=self.hedge_price, width=15).grid(row=3, column=1, pady=5)
        
        # Hedge fee - добавляем поле для комиссии
        ttk.Label(hedge_frame, text="Комиссия (%):").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(hedge_frame, textvariable=self.hedge_fee_percent, width=15).grid(row=4, column=1, pady=5)
        
        # Auto-hedge button
        ttk.Button(hedge_frame, text="Авто-хедж", command=self.auto_hedge).grid(row=5, column=0, pady=10, padx=5, sticky="e")
        
        # Apply hedge button
        ttk.Button(hedge_frame, text="Применить хедж", command=self.calculate).grid(row=5, column=1, pady=10, padx=5)
        
        # 2. Создаем фрейм результатов хеджирования (посередине)
        hedge_results_frame = ttk.LabelFrame(hedge_container, text="Результаты хеджирования", padding=10)
        hedge_results_frame.grid(row=0, column=1, sticky="n", padx=5, pady=5)
        
        # Hedge results variables
        self.hedge_eth_var = tk.StringVar()
        self.hedge_usdc_var = tk.StringVar()
        
        # Display hedge position info
        ttk.Label(hedge_results_frame, text="Хеджирующая позиция:").grid(row=0, column=0, sticky="w", pady=5, columnspan=2)
        ttk.Label(hedge_results_frame, text="Количество ETH:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(hedge_results_frame, textvariable=self.hedge_eth_var).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(hedge_results_frame, text="Стоимость (USDC):").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Label(hedge_results_frame, textvariable=self.hedge_usdc_var).grid(row=2, column=1, sticky="w", pady=5)
        
        # Добавляем отображение комиссии
        ttk.Label(hedge_results_frame, text="В т.ч. комиссия (USDC):").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Label(hedge_results_frame, textvariable=self.hedge_fee_value).grid(row=3, column=1, sticky="w", pady=5)
        
        # 3. Создаем фрейм анализа результатов (справа)
        exit_frame = ttk.LabelFrame(hedge_container, text="Анализ результатов при выходе", padding=10)
        exit_frame.grid(row=0, column=2, sticky="ne", padx=5, pady=5)
        
        # Exit price input
        ttk.Label(exit_frame, text="Цена выхода (USDC):").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(exit_frame, textvariable=self.exit_price, width=15).grid(row=0, column=1, pady=5)
        
        # Calculate exit button
        ttk.Button(exit_frame, text="Рассчитать результат", command=self.calculate_exit_results).grid(row=0, column=2, pady=5, padx=10)
        
        # Display results
        ttk.Label(exit_frame, text="Прибыль/убыток базовой позиции (USDC):").grid(row=1, column=0, sticky="w", pady=5, columnspan=2)
        self.result_label = ttk.Label(exit_frame, textvariable=self.base_pnl, width=15)
        self.result_label.grid(row=1, column=2, sticky="w", pady=5)
        
        ttk.Label(exit_frame, text="Прибыль/убыток от хеджа (USDC):").grid(row=2, column=0, sticky="w", pady=5, columnspan=2)
        self.hedge_result_label = ttk.Label(exit_frame, textvariable=self.hedge_pnl, width=15)
        self.hedge_result_label.grid(row=2, column=2, sticky="w", pady=5)
        
        # Добавляем отображение комиссии хеджа в результатах
        self.exit_fee_value = tk.StringVar(value="0.00")
        ttk.Label(exit_frame, text="В т.ч. комиссия (USDC):").grid(row=3, column=0, sticky="w", pady=5, columnspan=2)
        self.exit_fee_label = ttk.Label(exit_frame, textvariable=self.exit_fee_value, width=15)
        self.exit_fee_label.grid(row=3, column=2, sticky="w", pady=5)
        
        ttk.Label(exit_frame, text="Общий результат (USDC):").grid(row=4, column=0, sticky="w", pady=5, columnspan=2)
        self.total_result_label = ttk.Label(exit_frame, textvariable=self.total_pnl, width=15, font=('Helvetica', 10, 'bold'))
        self.total_result_label.grid(row=4, column=2, sticky="w", pady=5)
        
        # 4. Создаем фрейм для графика (внизу на всю ширину)
        self.hedge_plot_frame = ttk.LabelFrame(hedge_container, text="Визуализация хеджированной позиции", padding=10)
        self.hedge_plot_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        # Create matplotlib figure with subplots for hedged position в книжном формате
        self.hedge_figure = plt.Figure(figsize=(9, 9), dpi=100)
        # Один график для сравнения стоимости
        self.hedge_ax2 = self.hedge_figure.add_subplot(111)
        # Отключаем автоматический layout для ручного контроля отступов
        self.hedge_figure.subplots_adjust(left=0.12, right=0.9, top=0.9, bottom=0.1)
        self.hedge_canvas = FigureCanvasTkAgg(self.hedge_figure, self.hedge_plot_frame)
        self.hedge_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_grid_tab_widgets(self):
        # Фрейм для настроек сетки
        settings_frame = ttk.LabelFrame(self.grid_tab, text="Настройки сетки")
        settings_frame.pack(fill="x", padx=5, pady=5)
        
        # Шаг сетки
        ttk.Label(settings_frame, text="Шаг сетки (USDC):").grid(row=0, column=0, padx=5, pady=5)
        self.grid_step = ttk.Entry(settings_frame)
        self.grid_step.grid(row=0, column=1, padx=5, pady=5)
        self.grid_step.insert(0, "100")
        
        # Комиссия
        ttk.Label(settings_frame, text="Комиссия (%):").grid(row=1, column=0, padx=5, pady=5)
        self.grid_fee = ttk.Entry(settings_frame)
        self.grid_fee.grid(row=1, column=1, padx=5, pady=5)
        self.grid_fee.insert(0, "0.2")
        
        # Кнопка расчета
        ttk.Button(settings_frame, text="Рассчитать сетку", command=self.calculate_grid).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Фрейм для результатов
        results_frame = ttk.LabelFrame(self.grid_tab, text="Результаты")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Таблица результатов
        self.grid_results_text = tk.Text(results_frame, height=10)
        self.grid_results_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Фрейм для симуляции
        sim_frame = ttk.LabelFrame(self.grid_tab, text="Симуляция")
        sim_frame.pack(fill="x", padx=5, pady=5)
        
        # Поле для ввода цен
        ttk.Label(sim_frame, text="Цены для симуляции (через запятую):").grid(row=0, column=0, padx=5, pady=5)
        self.sim_prices = ttk.Entry(sim_frame, width=50)
        self.sim_prices.grid(row=0, column=1, padx=5, pady=5)
        
        # Кнопка запуска симуляции
        ttk.Button(sim_frame, text="Запустить симуляцию", command=self.run_simulation).grid(row=1, column=0, columnspan=2, pady=5)
        
        # График результатов
        self.grid_fig, (self.grid_ax1, self.grid_ax2) = plt.subplots(2, 1, figsize=(8, 6))
        self.grid_canvas = FigureCanvasTkAgg(self.grid_fig, master=self.grid_tab)
        self.grid_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_dynamic_tab_widgets(self):
        """Создает виджеты для вкладки динамического хеджирования"""
        # Создаем верхний фрейм для настроек
        settings_frame = ttk.LabelFrame(self.dynamic_tab, text="Параметры динамического хеджирования")
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Шаг изменения цены
        ttk.Label(settings_frame, text="Шаг изменения цены (USDC):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.dynamic_step, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Комиссия
        ttk.Label(settings_frame, text="Комиссия (%):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        fee_entry = ttk.Entry(settings_frame, width=10)
        fee_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        fee_entry.insert(0, str(self.hedge_fee_percent.get()))
        
        # Фрейм для ввода цен
        price_frame = ttk.LabelFrame(self.dynamic_tab, text="Последовательность цен")
        price_frame.pack(fill="x", padx=10, pady=5)
        
        # Создаем контейнер для полей ввода цен
        self.dynamic_price_container = ttk.Frame(price_frame)
        self.dynamic_price_container.pack(fill="x", padx=5, pady=5)
        
        # Кнопка добавления цены
        add_price_button = ttk.Button(price_frame, text="Добавить цену", command=self.add_price_field)
        add_price_button.pack(pady=5)
        
        # Добавляем начальные поля для цен
        self.add_initial_price_fields()
        
        # Кнопка расчета
        calc_button = ttk.Button(self.dynamic_tab, text="Рассчитать динамический хедж", 
                               command=self.calculate_dynamic_hedge, width=30)
        calc_button.pack(pady=10)
        
        # Фрейм для результатов
        self.dynamic_results_frame = ttk.LabelFrame(self.dynamic_tab, text="Результаты")
        self.dynamic_results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Текстовое поле для вывода результатов
        self.dynamic_results_text = tk.Text(self.dynamic_results_frame, height=10)
        self.dynamic_results_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Фрейм для графиков
        self.dynamic_plot_frame = ttk.LabelFrame(self.dynamic_tab, text="Графики результатов")
        self.dynamic_plot_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Создаем фигуру для графиков
        self.dynamic_fig = plt.Figure(figsize=(8, 8), dpi=100)
        
        # Создаем только один график для P&L
        self.dynamic_ax = self.dynamic_fig.add_subplot(111)  # График P&L
        
        # Настраиваем отступы
        self.dynamic_fig.tight_layout(pad=3.0)
        
        # Создаем холст для отображения графиков
        self.dynamic_canvas = FigureCanvasTkAgg(self.dynamic_fig, master=self.dynamic_plot_frame)
        self.dynamic_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    def add_initial_price_fields(self):
        """Инициализирует начальные поля для ввода цен"""
        # Начальная цена - это текущая цена из основной вкладки
        current_price = self.current_price.get()
        step = self.dynamic_step.get()
        
        # Цена 1 - движение вниз от текущей цены
        price1 = tk.DoubleVar(value=current_price - step)
        self.dynamic_price_vars.append(price1)
        
        # Цена 2 - возврат к текущей цене
        price2 = tk.DoubleVar(value=current_price)
        self.dynamic_price_vars.append(price2)
        
        # Цена 3 - движение вверх от текущей цены
        price3 = tk.DoubleVar(value=current_price + step)
        self.dynamic_price_vars.append(price3)
        
        # Создаем поля ввода для каждой цены
        for i, price_var in enumerate(self.dynamic_price_vars):
            self.create_price_field(i, price_var)
    
    def create_price_field(self, index, price_var):
        """Создает поле для ввода цены"""
        frame = ttk.Frame(self.dynamic_price_container)
        frame.pack(fill="x", pady=2)
        
        ttk.Label(frame, text=f"Цена {index+1}:").pack(side="left", padx=5)
        
        entry = ttk.Entry(frame, textvariable=price_var, width=10)
        entry.pack(side="left", padx=5)
        
        # Кнопка удаления (кроме первого поля)
        if index > 0:
            ttk.Button(frame, text="Удалить", 
                     command=lambda idx=index: self.delete_price_field(idx)).pack(side="left", padx=5)
    
    def add_price_field(self):
        """Добавляет новое поле для ввода цены"""
        try:
            # Создаем новую переменную
            new_price = tk.DoubleVar(value=100.0)
            self.dynamic_price_vars.append(new_price)
            
            # Создаем поле ввода
            self.create_price_field(len(self.dynamic_price_vars)-1, new_price)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении поля цены: {str(e)}")
    
    def delete_price_field(self, index):
        """Удаляет поле для ввода цены"""
        try:
            # Проверяем валидность индекса
            if 0 <= index < len(self.dynamic_price_vars):
                # Удаляем переменную
                del self.dynamic_price_vars[index]
                
                # Уничтожаем все существующие поля
                for widget in self.dynamic_price_container.winfo_children():
                    widget.destroy()
                
                # Пересоздаем поля с новыми индексами
                for i, price_var in enumerate(self.dynamic_price_vars):
                    self.create_price_field(i, price_var)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении поля цены: {str(e)}")
    
    def calculate_dynamic_hedge(self):
        """Расчет динамического хеджирования по заданной последовательности цен"""
        try:
            # Получаем параметры
            step = float(str(self.dynamic_step.get()).replace(',', '.'))
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            fee_percent = float(str(self.hedge_fee_percent.get()).replace(',', '.')) / 100.0
            
            # Получаем начальные параметры основной позиции
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            # Рассчитываем ликвидность
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                           (math.sqrt(current_price) - math.sqrt(lower_bound)))
            
            # Получаем начальную позицию хеджирования
            initial_hedge_amount = float(str(self.hedge_amount.get()).replace(',', '.')) if self.hedge_enabled.get() else 0
            initial_hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
            
            # Получаем список цен от пользователя
            user_prices = [float(str(var.get()).replace(',', '.')) for var in self.dynamic_price_vars]
            
            # Проверяем наличие хотя бы одной цены
            if not user_prices:
                messagebox.showerror("Ошибка", "Введите хотя бы одну цену")
                return
            
            # Создаем список для результатов
            self.dynamic_results = []
            
            # Добавляем начальную позицию (шаг 0)
            initial_eth = self.calculate_delta_for_price(current_price)
            initial_hedge = -initial_hedge_amount
            initial_total_delta = initial_eth + initial_hedge
            initial_fee = abs(initial_hedge) * initial_hedge_price * fee_percent
            
            self.dynamic_results.append({
                "step": 0,
                "price": current_price,
                "pool_eth": initial_eth,
                "hedge_eth": initial_hedge,
                "delta": initial_total_delta,
                "hedge_change": 0,
                "fee": initial_fee,
                "total_fee": initial_fee,
                "hedge_pnl": 0,
                "cumulative_pnl": 0,
                "price_direction": "start"  # Начальное состояние
            })
            
            # Формируем хронологическую последовательность цен
            # Начинаем с текущей цены (шаг 0), затем идет цена1, цена2, ...
            prices_sequence = self.form_price_sequence(current_price, user_prices)
            
            # Рассчитываем для каждой последующей цены
            cumulative_pnl = 0
            total_fee = initial_fee
            prev_hedge = initial_hedge
            prev_price = current_price
            prev_pool_eth = initial_eth  # Запоминаем предыдущий объем ETH в пуле
            
            for step_idx, price in enumerate(prices_sequence[1:], start=1):
                # Определяем направление движения цены
                price_direction = "up" if price > prev_price else "down"
                
                # Рассчитываем дельту пула при новой цене
                pool_eth = self.calculate_delta_for_price(price)
                
                # Рассчитываем необходимую дельту хеджа для нейтральной позиции
                required_hedge = -pool_eth
                
                # ИСПРАВЛЕНИЕ: Проверяем, изменился ли объем ETH в основной позиции
                eth_change = pool_eth - prev_pool_eth
                pool_eth_changed = abs(eth_change) > 0.0001  # С учетом погрешности вычислений
                
                # Изменение хеджа - всегда ребалансируем, но по-разному в зависимости от направления
                hedge_change = required_hedge - prev_hedge
                hedge_eth = required_hedge  # Всегда устанавливаем нейтральную позицию
                
                # Тип операции (увеличение или сокращение шорта)
                operation_type = ""
                if abs(hedge_change) < 0.0001:  # С учетом погрешности вычислений
                    operation_type = "no_change"  # Нет изменения хеджа
                elif hedge_change > 0:
                    operation_type = "reduce_short"  # Сокращение шорта (закрытие части позиции)
                elif hedge_change < 0:
                    operation_type = "increase_short"  # Увеличение шорта
                
                # Общая дельта
                total_delta = pool_eth + hedge_eth
                
                # Комиссия за изменение хеджа (только если реально меняем позицию)
                fee = 0
                if abs(hedge_change) >= 0.0001:
                    fee = abs(hedge_change) * price * fee_percent
                total_fee += fee
                
                # ИСПРАВЛЕННЫЙ РАСЧЕТ P&L ХЕДЖА:
                # 1. P&L считаем только при фактическом изменении позиции
                # 2. Если позиция не меняется, P&L для этого шага = 0
                
                step_pnl = 0
                
                if abs(hedge_change) >= 0.0001:
                    # Для оставшейся части позиции (нереализованный P&L)
                    # Для шорта (prev_hedge < 0)
                    unrealized_pnl = 0
                    
                    # Мы учитываем P&L от изменения цены только если меняем объем позиции
                    if prev_hedge < 0:  # У нас шорт (отрицательные значения ETH)
                        # При падении цены: положительный P&L, при росте: отрицательный
                        unrealized_pnl = abs(prev_hedge) * (prev_price - price)
                    
                    # Для измененной части позиции (если закрываем часть позиции)
                    realized_pnl = 0
                    if hedge_change > 0 and prev_hedge < 0:  # Если уменьшаем шорт
                        # Прибыль/убыток от закрытия части позиции
                        realized_pnl = hedge_change * (prev_price - price)
                    
                    # Общий P&L для данного шага
                    step_pnl = unrealized_pnl + realized_pnl
                
                # Накопленный P&L
                cumulative_pnl += step_pnl
                
                # Сохраняем результаты
                self.dynamic_results.append({
                    "step": step_idx,
                    "price": price,
                    "pool_eth": pool_eth,
                    "hedge_eth": hedge_eth,
                    "delta": total_delta,
                    "hedge_change": hedge_change,
                    "fee": fee,
                    "total_fee": total_fee,
                    "hedge_pnl": step_pnl,
                    "cumulative_pnl": cumulative_pnl,
                    "price_direction": price_direction,
                    "operation_type": operation_type,
                    "eth_changed": pool_eth_changed
                })
                
                # Обновляем значения для следующей итерации
                prev_hedge = hedge_eth
                prev_price = price
                prev_pool_eth = pool_eth
            
            # Отображаем результаты
            self.display_dynamic_results()
            
            # Отображаем графики
            self.plot_dynamic_results()
            
            # Выводим сообщение о завершении расчета
            messagebox.showinfo("Расчет завершен", 
                        f"Расчет динамического хеджирования завершен.\n\n"
                        f"Итоговая дельта: {self.dynamic_results[-1]['delta']:.4f}\n"
                        f"Накопленный P&L хеджа: {self.dynamic_results[-1]['cumulative_pnl']:.2f} USDC\n"
                        f"Общая комиссия: {self.dynamic_results[-1]['total_fee']:.2f} USDC")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при расчете динамического хеджирования: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def form_price_sequence(self, entry_price, user_prices):
        """
        Формирует хронологическую последовательность цен для расчета.
        
        Последовательность цен:
        1. Начинается с entry_price (начальная цена)
        2. Затем идет по порядку: цена1, цена2, цена3 и т.д.
        3. Между соседними ценами добавляются промежуточные шаги с заданным шагом
        """
        try:
            step = float(str(self.dynamic_step.get()).replace(',', '.'))
            
            # Последовательность начинается с текущей цены входа
            price_sequence = [entry_price]
            
            # Получаем цены из полей ввода в порядке их отображения
            ordered_prices = []
            for price_var in self.dynamic_price_vars:
                price = float(str(price_var.get()).replace(',', '.'))
                ordered_prices.append(price)
            
            # Добавляем каждую цену в последовательность с промежуточными шагами
            for target_price in ordered_prices:
                if target_price == entry_price:
                    continue  # Пропускаем, если цена совпадает с начальной
                
                # Получаем последнюю цену в последовательности
                last_price = price_sequence[-1]
                
                # Определяем направление движения
                direction = 1 if target_price > last_price else -1
                
                # Добавляем промежуточные шаги
                current = last_price + direction * step
                while (direction == 1 and current < target_price) or (direction == -1 and current > target_price):
                    price_sequence.append(current)
                    current += direction * step
                
                # Добавляем целевую цену
                price_sequence.append(target_price)
            
            return price_sequence
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при формировании последовательности цен: {str(e)}")
            import traceback
            traceback.print_exc()
            return [entry_price]  # В случае ошибки возвращаем только начальную цену
    
    def display_dynamic_results(self):
        """Отображает результаты динамического хеджирования в текстовом поле"""
        self.dynamic_results_text.delete(1.0, tk.END)
        
        # Заголовок
        header = "Шаг\tЦена\t\tETH в пуле\tФьючерс\tДельта\tИзменение\tКомиссия\tP&L\tНакопл. P&L\tСтратегия\n"
        self.dynamic_results_text.insert(tk.END, header)
        self.dynamic_results_text.insert(tk.END, "-" * 140 + "\n")
        
        # Данные
        prev_price = None
        for result in self.dynamic_results:
            # Добавляем индикаторы изменения цены и позиции
            price_indicator = ""
            hedge_indicator = ""
            strategy_note = ""
            
            if prev_price is not None:
                if result['price'] > prev_price:
                    price_indicator = "↑"
                    if result.get('operation_type') == "reduce_short":
                        strategy_note = "Сокращение шорта"
                    elif result.get('operation_type') == "no_change":
                        strategy_note = "Без изменений"
                elif result['price'] < prev_price:
                    price_indicator = "↓"
                    if result.get('operation_type') == "increase_short":
                        strategy_note = "Увеличение шорта"
                    elif result.get('operation_type') == "no_change":
                        strategy_note = "Без изменений"
                
                if result['hedge_change'] > 0.0001:
                    hedge_indicator = "↑" # Уменьшаем размер шорта (закрываем часть)
                elif result['hedge_change'] < -0.0001:
                    hedge_indicator = "↓" # Увеличиваем размер шорта
            
            prev_price = result['price']
            
            # Форматируем строку таблицы
            row = (f"{result['step']}\t{result['price']:.2f} {price_indicator}\t" +
                  f"{result['pool_eth']:.4f}\t{result['hedge_eth']:.4f}\t" +
                  f"{result['delta']:.4f}\t{result['hedge_change']:.4f} {hedge_indicator}\t" +
                  f"{result['fee']:.2f}\t{result['hedge_pnl']:.2f}\t{result['cumulative_pnl']:.2f}\t{strategy_note}\n")
            
            self.dynamic_results_text.insert(tk.END, row)
        
        # Итоговые результаты
        if self.dynamic_results:
            last_result = self.dynamic_results[-1]
            
            self.dynamic_results_text.insert(tk.END, "\nИтоговые результаты:\n")
            self.dynamic_results_text.insert(tk.END, f"Итоговая дельта: {last_result['delta']:.4f}\n")
            self.dynamic_results_text.insert(tk.END, f"Накопленный P&L: {last_result['cumulative_pnl']:.2f} USDC\n")
            self.dynamic_results_text.insert(tk.END, f"Общая комиссия: {last_result['total_fee']:.2f} USDC\n")
            self.dynamic_results_text.insert(tk.END, f"Чистый результат: {last_result['cumulative_pnl'] - last_result['total_fee']:.2f} USDC\n")
            
            # Добавляем пояснения
            self.dynamic_results_text.insert(tk.END, "\nПояснения:\n")
            self.dynamic_results_text.insert(tk.END, "↑ в столбце Цена - цена выросла\n")
            self.dynamic_results_text.insert(tk.END, "↓ в столбце Цена - цена упала\n")
            self.dynamic_results_text.insert(tk.END, "↑ в столбце Изменение - уменьшение размера шорта (закрытие части позиции)\n")
            self.dynamic_results_text.insert(tk.END, "↓ в столбце Изменение - увеличение размера шорта\n")
            self.dynamic_results_text.insert(tk.END, "При падении цены: прибыль по хеджу (шорту), убыток по основной позиции\n")
            self.dynamic_results_text.insert(tk.END, "При росте цены: убыток по хеджу (шорту), прибыль по основной позиции\n")
            self.dynamic_results_text.insert(tk.END, "Без изменений: когда объем ETH в пуле и хедж не меняется, P&L на этом шаге = 0\n")
    
    def plot_dynamic_results(self):
        """Отображает результаты динамического хеджирования на графике"""
        # Если нет результатов, ничего не делаем
        if not self.dynamic_results:
            return
            
        # Очищаем график
        self.dynamic_ax.clear()
        
        # Подготавливаем данные для графиков
        steps = [r['step'] for r in self.dynamic_results]
        prices = [r['price'] for r in self.dynamic_results]
        
        # Данные для P&L
        base_pnl = []         # P&L основной позиции
        hedge_pnl = []        # P&L хеджа
        combined_pnl = []     # Совместный P&L
        
        # Первая цена - это всегда цена входа
        initial_price = prices[0]
        initial_eth = self.dynamic_results[0]['pool_eth']
        initial_hedge = self.dynamic_results[0]['hedge_eth']
        
        # ИСПРАВЛЕННАЯ ЛОГИКА РАСЧЕТА НАЧАЛЬНОЙ СТОИМОСТИ И P&L ОСНОВНОЙ ПОЗИЦИИ
        # Общая стоимость пула состоит из ETH и USDC, но хранится в одном активе (USDC)
        
        # Для позиции LP в Uniswap V3:
        # - При падении цены: ETH растет, USDC падает, общая стоимость в USDC падает (убыток)
        # - При росте цены: ETH падает, USDC растет, общая стоимость в USDC растет (прибыль)
        
        # Начальные параметры основной позиции
        lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
        upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
        total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
        
        # Рассчитываем ликвидность (L)
        liquidity = total_pool_value / (((1/math.sqrt(initial_price) - 1/math.sqrt(upper_bound)) * initial_price) + 
                                        (math.sqrt(initial_price) - math.sqrt(lower_bound)))
        
        # Начальные значения
        initial_eth_value = initial_eth * initial_price  # Стоимость ETH в USDC
        initial_usdc = total_pool_value - initial_eth_value  # Примерная стоимость USDC части
        
        cumulative_hedge_pnl = 0
        
        # Массивы для хранения индексов точек разных операций
        increase_short_points = []  # Точки увеличения шорта (при падении цены)
        reduce_short_points = []    # Точки сокращения шорта (при росте цены)
        no_change_points = []       # Точки без изменений
        
        # Массивы для стрелок направления P&L
        down_price_points = []      # Участки падения цены
        up_price_points = []        # Участки роста цены
        
        for i, result in enumerate(self.dynamic_results):
            price = result['price']
            pool_eth = result['pool_eth']
            
            # Определение типа операции
            if i > 0:
                prev_price = self.dynamic_results[i-1]['price']
                
                # Определяем направление движения цены для аннотаций
                if price < prev_price:
                    down_price_points.append((i-1, i))
                elif price > prev_price:
                    up_price_points.append((i-1, i))
                
                if result.get('operation_type') == "reduce_short":
                    reduce_short_points.append(i)
                elif result.get('operation_type') == "increase_short":
                    increase_short_points.append(i)
                elif result.get('operation_type') == "no_change":
                    no_change_points.append(i)
            
            # ИСПРАВЛЕННЫЙ РАСЧЕТ P&L ПОЗИЦИИ:
            
            # 1. Считаем текущие активы в пуле
            current_eth_value = pool_eth * price  # Стоимость ETH в USDC
            
            # Рассчитываем текущую USDC часть через ликвидность
            sqrt_price = math.sqrt(price)
            usdc_amount = liquidity * (sqrt_price - math.sqrt(lower_bound))
            
            # 2. Считаем общую стоимость позиции в USDC
            current_total_value = current_eth_value + usdc_amount
            
            # 3. Рассчитываем P&L основной позиции как разницу между текущей и начальной стоимостью
            base_pnl_value = current_total_value - total_pool_value
            
            # Накопленный P&L хеджа
            if i > 0:
                cumulative_hedge_pnl = self.dynamic_results[i]['cumulative_pnl']
                
            # Совместный P&L
            combined_pnl_value = base_pnl_value + cumulative_hedge_pnl
            
            # Добавляем в списки
            base_pnl.append(base_pnl_value)
            hedge_pnl.append(cumulative_hedge_pnl)
            combined_pnl.append(combined_pnl_value)
            
        # График P&L
        self.dynamic_ax.plot(steps, base_pnl, 'g-', linewidth=2, label='P&L основной позиции')
        self.dynamic_ax.plot(steps, hedge_pnl, 'r-', linewidth=2, label='P&L хеджа')
        self.dynamic_ax.plot(steps, combined_pnl, 'b-', linewidth=2, label='Совместный P&L')
        
        # Добавляем маркеры на линии для обычных точек
        self.dynamic_ax.plot(steps, base_pnl, 'go', markersize=5)
        self.dynamic_ax.plot(steps, hedge_pnl, 'ro', markersize=5)
        self.dynamic_ax.plot(steps, combined_pnl, 'bo', markersize=5)
        
        # Выделяем точки разных стратегий
        for idx in reduce_short_points:
            # Точки сокращения шорта (при росте цены)
            self.dynamic_ax.plot(steps[idx], hedge_pnl[idx], 'r^', markersize=10, alpha=0.7, 
                            label='Сокращение шорта' if idx == reduce_short_points[0] else "")
            self.dynamic_ax.plot(steps[idx], combined_pnl[idx], 'b^', markersize=10, alpha=0.7)
            
        for idx in increase_short_points:
            # Точки увеличения шорта (при падении цены)
            self.dynamic_ax.plot(steps[idx], hedge_pnl[idx], 'rv', markersize=9, alpha=0.7,
                            label='Увеличение шорта' if idx == increase_short_points[0] else "")
            self.dynamic_ax.plot(steps[idx], combined_pnl[idx], 'bv', markersize=9, alpha=0.7)
            
        for idx in no_change_points:
            # Точки без изменений позиции
            self.dynamic_ax.plot(steps[idx], hedge_pnl[idx], 'rs', markersize=8, alpha=0.7,
                            label='Без изменений' if idx == no_change_points[0] else "")
            self.dynamic_ax.plot(steps[idx], combined_pnl[idx], 'bs', markersize=8, alpha=0.7)
        
        # Аннотации с ценами и значениями P&L
        for i, step in enumerate(steps):
            # Аннотация с ценой (только для ключевых точек)
            if i == 0 or i == len(steps)-1 or (i % 3 == 0):
                self.dynamic_ax.annotate(f"{prices[i]:.0f}", 
                                      xy=(step, combined_pnl[i]),
                                      xytext=(0, 10),
                                      textcoords='offset points',
                                      ha='center',
                                      fontsize=8)
            
            # Аннотация с изменением хеджа (если есть)
            if i > 0 and abs(self.dynamic_results[i]['hedge_change']) > 0.01:
                change = self.dynamic_results[i]['hedge_change']
                operation = self.dynamic_results[i].get('operation_type', '')
                
                # Разные маркеры для разных операций
                if operation == "reduce_short":
                    marker = "△"  # Треугольник вверх для сокращения шорта
                    color = 'green'
                elif operation == "increase_short":
                    marker = "▽"  # Треугольник вниз для увеличения шорта
                    color = 'red'
                else:
                    marker = "○"  # Круг для других операций
                    color = 'gray'
                
                self.dynamic_ax.annotate(marker, 
                                      xy=(step, hedge_pnl[i]),
                                      xytext=(0, -15 if change > 0 else 15),
                                      textcoords='offset points',
                                      ha='center',
                                      color=color,
                                      fontsize=10)
        
        # Добавляем горизонтальную линию на уровне 0
        self.dynamic_ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
        
        # Настраиваем оси
        self.dynamic_ax.set_xlabel('Шаг', fontsize=10)
        self.dynamic_ax.set_ylabel('P&L (USDC)', fontsize=10)
        self.dynamic_ax.set_title('Профиль P&L с ребалансировкой хеджа', fontsize=12, fontweight='bold')
        
        # Настраиваем x-ось для отображения целых шагов
        self.dynamic_ax.set_xticks(steps)
        self.dynamic_ax.set_xticklabels([str(step) for step in steps])
        
        # Добавляем легенду
        self.dynamic_ax.legend(loc='best', fontsize=9)
        
        # Добавляем пояснение к маркерам и движению цены
        self.dynamic_ax.annotate("△ - сокращение шорта, ▽ - увеличение шорта, □ - без изменений", 
                              xy=(0.5, 0.01),
                              xycoords='figure fraction',
                              ha='center',
                              fontsize=8)
        
        # Добавляем текстовое пояснение взаимосвязи движения цены и P&L
        self.dynamic_ax.text(0.02, 0.02, 
                          "При падении цены: ↑ прибыль по хеджу, ↓ убыток по основной позиции\n"
                          "При росте цены: ↓ убыток по хеджу, ↑ прибыль по основной позиции\n"
                          "Без изменений объема ETH: P&L для этого шага = 0",
                          transform=self.dynamic_ax.transAxes,
                          fontsize=8,
                          bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5'))
        
        # Включаем сетку
        self.dynamic_ax.grid(True, alpha=0.3)
        
        # Настраиваем макет
        self.dynamic_fig.tight_layout(pad=3.0)
        
        # Обновляем холст
        self.dynamic_canvas.draw()
    
    def auto_hedge(self):
        """Автоматически настраивает хеджирующую позицию"""
        self.hedge_enabled.set(True)
        self.update_hedge()
            
        # Получаем ETH из текущей позиции
        try:
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                           (math.sqrt(current_price) - math.sqrt(lower_bound)))
            eth_amount = liquidity * (1/math.sqrt(current_price) - 1/math.sqrt(upper_bound))
            
            # Устанавливаем противоположную позицию для фьючерса
            self.hedge_amount.set(round(eth_amount, 6))
            self.hedge_price.set(current_price)
            
            self.calculate()
        except Exception as e:
            print(f"Error in auto_hedge: {e}")
    
    def update_hedge(self):
        """Обновляет состояние элементов интерфейса при изменении статуса хеджирования"""
        if self.hedge_enabled.get():
            self.hedge_amount_entry.config(state="normal")
        else:
            self.hedge_amount_entry.config(state="disabled")
            # Сбрасываем сумму хеджирования при отключении
            self.hedge_amount.set(0)
        
        # Обновляем только данные без графиков
        self.calculate_only_text()
    
    def update_hedge_amount(self, event=None):
        """Обновляет сумму хеджирования в зависимости от выбранного инструмента"""
        instrument = self.hedge_instrument.get()
        # Здесь можно добавить специфичную логику для разных инструментов
        # Обновляем только данные без графиков
        self.calculate_only_text()
    
    def calculate_only_text(self):
        """Выполняет все расчеты, но не обновляет графики"""
        try:
            # Устанавливаем флаг обновления, чтобы предотвратить рекурсивные вызовы
            self.updating = True
            
            # Обработка входных значений с учетом возможности запятой вместо точки
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            # Calculate liquidity (L)
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                           (math.sqrt(current_price) - math.sqrt(lower_bound)))
            
            # Calculate current position
            eth_amount = liquidity * (1/math.sqrt(current_price) - 1/math.sqrt(upper_bound))
            usdc_amount = liquidity * (math.sqrt(current_price) - math.sqrt(lower_bound))
            
            # Calculate at upper bound
            upper_eth_amount = 0
            upper_usdc_amount = (math.sqrt(upper_bound) - math.sqrt(current_price)) * liquidity + usdc_amount
            
            # Calculate at lower bound
            lower_eth_amount = (math.sqrt(current_price) - math.sqrt(lower_bound)) * liquidity / lower_bound + eth_amount
            lower_usdc_amount = 0
            
            # Update result variables
            self.liquidity_var.set(f"{liquidity:.6f}")
            self.eth_amount_var.set(f"{eth_amount:.6f}")
            self.usdc_amount_var.set(f"{usdc_amount:.6f}")
            
            self.upper_eth_var.set(f"{upper_eth_amount:.6f}")
            self.upper_usdc_var.set(f"{upper_usdc_amount:.6f}")
            
            self.lower_eth_var.set(f"{lower_eth_amount:.6f}")
            self.lower_usdc_var.set(f"{lower_usdc_amount:.6f}")
            
            # Обновляем информацию о хеджирующей позиции
            hedge_eth = 0
            hedge_usdc = 0
            hedge_fee = 0  # Инициализируем комиссию
            
            if self.hedge_enabled.get():
                hedge_amount = float(str(self.hedge_amount.get()).replace(',', '.'))
                hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
                
                # Получаем комиссию
                try:
                    hedge_fee_percent = float(str(self.hedge_fee_percent.get()).replace(',', '.')) / 100.0
                except:
                    hedge_fee_percent = 0.002  # 0.2% по умолчанию
                
                # Расчет комиссии
                hedge_fee = hedge_amount * hedge_price * hedge_fee_percent
                self.hedge_fee_value.set(f"{hedge_fee:.2f}")  # Обновляем переменную комиссии
                
                # Устанавливаем противоположную позицию для фьючерса
                hedge_eth = -hedge_amount
                
                # Сумма в USDC от продажи ETH по цене хеджирования
                # Для шорта: получаем USDC в момент продажи ETH, поэтому положительное значение
                hedge_usdc = abs(hedge_eth) * hedge_price
            else:
                self.hedge_fee_value.set("0.00")  # Сбрасываем комиссию если хеджирование выключено
                
            self.hedge_eth_var.set(f"{hedge_eth:.6f}")
            self.hedge_usdc_var.set(f"{hedge_usdc:.6f}")
            
            # Обновляем результаты при выходе
            self.calculate_exit_results_no_graph()
            
        except Exception as e:
            print(f"Error in calculation: {e}")
        finally:
            # Сбрасываем флаг обновления
            self.updating = False
    
    def calculate(self):
        """Выполняет все расчеты и обновляет графики - теперь вызывается только из refresh_plots"""
        self.calculate_only_text()  # Сначала обновим текстовые данные
        
        try:
            # Полностью пересоздаем фигуры и графики для основной вкладки
            plt.close(self.figure)
            self.figure = plt.Figure(figsize=(7, 8), dpi=100)
            self.ax1 = self.figure.add_subplot(211)  # Верхний график для ETH и USDC
            self.ax2 = self.figure.add_subplot(212)  # Нижний график для общей ценности
            
            # Уничтожить старый холст и создать новый
            self.canvas.get_tk_widget().destroy()
            self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Полностью пересоздаем фигуры и графики для хеджирования
            plt.close(self.hedge_figure)
            self.hedge_figure = plt.Figure(figsize=(7, 8), dpi=100)
            self.hedge_ax2 = self.hedge_figure.add_subplot(111)  # Один график для сравнения стоимости
            
            # Уничтожить старый холст и создать новый
            self.hedge_canvas.get_tk_widget().destroy()
            self.hedge_canvas = FigureCanvasTkAgg(self.hedge_figure, self.hedge_plot_frame)
            self.hedge_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Параметры для графиков
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                           (math.sqrt(current_price) - math.sqrt(lower_bound)))
            
            # Обновляем информацию о хеджирующей позиции
            hedge_eth = 0
            hedge_usdc = 0
            
            if self.hedge_enabled.get():
                hedge_amount = float(str(self.hedge_amount.get()).replace(',', '.'))
                hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
                hedge_eth = -hedge_amount
                hedge_usdc = abs(hedge_eth) * hedge_price
            
            # Update plot for main position
            self.plot_liquidity_range(current_price, lower_bound, upper_bound, liquidity)
            
            # Update plot with exit price if available
            try:
                exit_price = float(str(self.exit_price.get()).replace(',', '.'))
                if exit_price > 0:
                    # Расчет и отображение с маркером цены выхода
                    self.plot_hedged_position_with_exit(current_price, lower_bound, upper_bound, 
                                                    hedge_amount, exit_price)
                else:
                    # Стандартное отображение
                    self.plot_hedged_position(current_price, lower_bound, upper_bound, liquidity, hedge_eth, hedge_usdc)
            except Exception as e:
                print(f"Error handling exit price: {e}")
                # Стандартное отображение при ошибке
                self.plot_hedged_position(current_price, lower_bound, upper_bound, liquidity, hedge_eth, hedge_usdc)
        
        except Exception as e:
            print(f"Error updating plots: {e}")
            
    def calculate_exit_results_no_graph(self):
        """Рассчитывает результаты при выходе по указанной цене без обновления графика"""
        try:
            # Получение значений
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            exit_price = float(str(self.exit_price.get()).replace(',', '.'))
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            # Расчет ликвидности и позиции на текущем уровне
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                           (math.sqrt(current_price) - math.sqrt(lower_bound)))
            
            # Расчет текущей позиции
            eth_amount_current = liquidity * (1/math.sqrt(current_price) - 1/math.sqrt(upper_bound))
            usdc_amount_current = liquidity * (math.sqrt(current_price) - math.sqrt(lower_bound))
            current_total_value = eth_amount_current * current_price + usdc_amount_current
            
            # Расчет выхода по указанной цене
            if exit_price < lower_bound:
                # Все в ETH
                eth_amount_exit = liquidity * (1/math.sqrt(lower_bound) - 1/math.sqrt(upper_bound))
                usdc_amount_exit = 0
            elif exit_price > upper_bound:
                # Все в USDC
                eth_amount_exit = 0
                usdc_amount_exit = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))
            else:
                # В диапазоне
                eth_amount_exit = liquidity * (1/math.sqrt(exit_price) - 1/math.sqrt(upper_bound))
                usdc_amount_exit = liquidity * (math.sqrt(exit_price) - math.sqrt(lower_bound))
            
            # Общая стоимость позиции на выходе
            exit_total_value = eth_amount_exit * exit_price + usdc_amount_exit
            
            # Прибыль/убыток базовой позиции
            base_pnl = exit_total_value - total_pool_value
            self.base_pnl.set(f"{base_pnl:.2f}")
            
            # Расчет результатов хеджа
            hedge_pnl = 0
            hedge_fee = 0
            if self.hedge_enabled.get():
                hedge_amount = float(str(self.hedge_amount.get()).replace(',', '.'))
                hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
                
                # Получаем комиссию
                try:
                    hedge_fee_percent = float(str(self.hedge_fee_percent.get()).replace(',', '.')) / 100.0
                except:
                    hedge_fee_percent = 0.002  # 0.2% по умолчанию
                
                # Расчет комиссии
                hedge_fee = hedge_amount * hedge_price * hedge_fee_percent
                self.exit_fee_value.set(f"{hedge_fee:.2f}")  # Обновляем значение комиссии в результатах
                
                # Для шорта: прибыль = количество * (цена продажи - цена выкупа) - комиссия
                hedge_pnl = -hedge_amount * (exit_price - hedge_price) - hedge_fee
            else:
                self.exit_fee_value.set("0.00")  # Сбрасываем комиссию
                
            self.hedge_pnl.set(f"{hedge_pnl:.2f}")
            
            # Общий результат - прибыль/убыток относительно начальной суммы
            total_pnl = base_pnl + hedge_pnl
            self.total_pnl.set(f"{total_pnl:.2f}")
            
            # Раскраска результатов в зависимости от прибыли/убытка
            for var, label in [
                (self.base_pnl, self.result_label), 
                (self.hedge_pnl, self.hedge_result_label),
                (self.exit_fee_value, self.exit_fee_label),
                (self.total_pnl, self.total_result_label)
            ]:
                try:
                    value = float(var.get())
                    if value > 0:
                        label.config(foreground="green")
                    elif value < 0:
                        label.config(foreground="red")
                    else:
                        label.config(foreground="black")
                except:
                    pass
            
        except Exception as e:
            print(f"Error in calculate_exit_results_no_graph: {e}")
            
    def calculate_exit_results(self):
        """Рассчитывает результаты при выходе по указанной цене и обновляет график"""
        self.calculate_exit_results_no_graph()  # Сначала расчет без графика
        
        # Запускаем обновление графиков
        self.refresh_plots()
    
    def on_exit_price_change(self, *args):
        """Обработчик изменения цены выхода для автоматического пересчета"""
        if not self.updating:
            self.after(100, self.calculate_exit_results_no_graph)  # Только текстовые поля, не графики
            
    def on_variable_change(self, *args):
        """Обработчик изменений переменных для автоматического пересчета"""
        if not self.updating:
            self.after(100, self.calculate_only_text)  # Только текстовые поля, не графики
    
    def plot_liquidity_range(self, current_price, lower_bound, upper_bound, liquidity):
        # Уже не нужно очищать, так как графики пересозданы
        # Расширяем диапазон отображения на 25%
        price_min = lower_bound * 0.75  # расширяем на 25% вниз
        price_max = upper_bound * 1.25  # расширяем на 25% вверх
        
        # Create price range for x-axis с расширенным диапазоном
        price_range = np.linspace(price_min, price_max, 1000)
        
        # Calculate ETH and USDC amounts at each price
        eth_amounts = []
        usdc_amounts = []
        total_values = []
        
        for price in price_range:
            if price < lower_bound:
                # All liquidity is in ETH when below lower bound
                eth = liquidity * (1/math.sqrt(lower_bound) - 1/math.sqrt(upper_bound))
                usdc = 0
            elif price > upper_bound:
                # All liquidity is in USDC when above upper bound
                eth = 0
                usdc = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))
            else:
                # Within range - liquidity is split between tokens
                eth = liquidity * (1/math.sqrt(price) - 1/math.sqrt(upper_bound))
                usdc = liquidity * (math.sqrt(price) - math.sqrt(lower_bound))
            
            eth_amounts.append(eth)
            usdc_amounts.append(usdc)
            total_values.append(eth * price + usdc)
        
        # График 1: ETH и USDC с двойной осью Y
        color_eth = '#1f77b4'
        color_usdc = '#2ca02c'
        
        # ETH на левой оси Y
        l1 = self.ax1.plot(price_range, eth_amounts, linewidth=2.5, label='ETH', color=color_eth)
        self.ax1.set_ylabel('ETH', fontsize=10, color=color_eth)
        self.ax1.tick_params(axis='y', labelcolor=color_eth)
        
        # USDC на правой оси Y
        ax1_right = self.ax1.twinx()
        l2 = ax1_right.plot(price_range, usdc_amounts, linewidth=2, label='USDC', color=color_usdc)
        ax1_right.set_ylabel('USDC', fontsize=10, color=color_usdc)
        ax1_right.tick_params(axis='y', labelcolor=color_usdc)
        
        # Устанавливаем диапазон X для лучшего отображения
        self.ax1.set_xlim(price_min, price_max)
        
        # Отмечаем границы и текущую цену на обоих графиках
        v1 = self.ax1.axvline(x=lower_bound, color='gray', linestyle='--')
        v2 = self.ax1.axvline(x=upper_bound, color='gray', linestyle='--')
        v3 = self.ax1.axvline(x=current_price, color='black', linestyle='-')
        
        # То же для правой оси
        ax1_right.axvline(x=lower_bound, color='gray', linestyle='--')
        ax1_right.axvline(x=upper_bound, color='gray', linestyle='--')
        ax1_right.axvline(x=current_price, color='black', linestyle='-')
        
        # График 2: Общая ценность
        self.ax2.plot(price_range, total_values, linewidth=2, label='Общая стоимость (USDC)', color='#d62728')
        
        # Получаем общую стоимость пула
        try:
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
        except:
            total_pool_value = 10000  # значение по умолчанию
            
        # Добавляем горизонтальную линию для общей стоимости пула
        h1 = self.ax2.axhline(y=total_pool_value, color='blue', linestyle='--', linewidth=1.5)
        
        # Устанавливаем тот же диапазон X для второго графика
        self.ax2.set_xlim(price_min, price_max)
        
        # Отмечаем на втором графике
        self.ax2.axvline(x=lower_bound, color='gray', linestyle='--')
        self.ax2.axvline(x=upper_bound, color='gray', linestyle='--')
        self.ax2.axvline(x=current_price, color='black', linestyle='-')
        
        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)
        
        # Настраиваем оси - добавляем отступы, чтобы избежать наложения текста
        self.ax1.tick_params(axis='x', labelsize=9, pad=2)
        self.ax1.tick_params(axis='y', labelsize=9, pad=2)
        ax1_right.tick_params(axis='y', labelsize=9, pad=2)
        
        self.ax2.tick_params(axis='x', labelsize=9, pad=2)
        self.ax2.tick_params(axis='y', labelsize=9, pad=2)
        
        # Объединяем линии для общей легенды на верхнем графике
        lines = l1 + l2 + [v1, v3]
        labels = ['ETH', 'USDC', 'Границы диапазона', 'Текущая цена']
        self.ax1.legend(lines, labels, loc='best', fontsize=8, framealpha=0.7)
        
        # Устанавливаем подписи для верхнего графика
        self.ax1.set_title('Количество ETH и USDC', fontsize=12, fontweight='bold')
        
        # Устанавливаем подписи для нижнего графика
        self.ax2.set_title('Общая стоимость позиции', fontsize=12, fontweight='bold')
        self.ax2.set_xlabel('Цена (USDC за ETH)', fontsize=10)
        self.ax2.set_ylabel('Стоимость (USDC)', fontsize=10)
        
        # Добавляем линию исходной суммы в легенду
        self.ax2.legend(['Общая стоимость (USDC)', f'Исходная сумма ({total_pool_value} USDC)', 
                       'Границы диапазона', 'Текущая цена'], 
                      loc='best', fontsize=8, framealpha=0.7)
        
        # Настраиваем оси и форматирование чисел
        self.ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.1f}".format(x)))
        self.ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.0f}".format(x)))
        
        # Выравниваем макет
        self.figure.tight_layout(pad=4.0)
        
        # Draw the plot and flush_events для принудительного обновления
        self.canvas.draw()
        self.canvas.flush_events()
    
    def plot_hedged_position(self, current_price, lower_bound, upper_bound, liquidity, hedge_eth, hedge_usdc):
        # Уже не нужно очищать, так как график пересоздан
        
        # Расширяем диапазон отображения на 25%
        price_min = lower_bound * 0.75  # расширяем на 25% вниз
        price_max = upper_bound * 1.25  # расширяем на 25% вверх
        
        # Create price range for x-axis с расширенным диапазоном
        price_range = np.linspace(price_min, price_max, 1000)
        
        # Calculate base position values
        eth_amounts = []
        usdc_amounts = []
        base_total_values = []
        
        # Calculate hedge position values
        hedge_pnl_values = []
        
        # Calculate combined position values
        total_values = []
        
        # Получаем цену хеджа безопасным способом
        try:
            hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
        except:
            hedge_price = current_price
        
        # Получаем первоначальную сумму пула
        try:
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
        except:
            total_pool_value = 10000  # значение по умолчанию
        
        # Получаем комиссию безопасным способом
        try:
            hedge_fee_percent = float(str(self.hedge_fee_percent.get()).replace(',', '.')) / 100.0
        except:
            hedge_fee_percent = 0.002  # 0.2% по умолчанию
        
        for price in price_range:
            # Базовая позиция
            if price < lower_bound:
                # All liquidity is in ETH when below lower bound
                eth = liquidity * (1/math.sqrt(lower_bound) - 1/math.sqrt(upper_bound))
                usdc = 0
            elif price > upper_bound:
                # All liquidity is in USDC when above upper bound
                eth = 0
                usdc = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))
            else:
                # Within range - liquidity is split between tokens
                eth = liquidity * (1/math.sqrt(price) - 1/math.sqrt(upper_bound))
                usdc = liquidity * (math.sqrt(price) - math.sqrt(lower_bound))
            
            eth_amounts.append(eth)
            usdc_amounts.append(usdc)
            base_value = eth * price + usdc
            base_total_values.append(base_value)
            
            # Хеджирующая позиция (шорт фьючерс) с учетом комиссии
            hedge_eth_val = hedge_eth  # Фиксированное количество (отрицательное для шорта)
            
            # Расчет комиссии (0.2% от объема сделки)
            hedge_fee = abs(hedge_eth_val) * hedge_price * hedge_fee_percent
            
            # Для шорта: прибыль = (цена продажи - текущая цена) * количество - комиссия
            hedge_price_diff = hedge_price - price  # Это положительно, если цена упала
            hedge_pnl = -hedge_eth_val * hedge_price_diff - hedge_fee  # Вычитаем комиссию
            
            hedge_pnl_values.append(hedge_pnl)
            
            # Правильная сумма должна быть близка к исходному total_pool_value, 
            # с изменениями только за счет P&L хеджа
            total_value = base_value + hedge_pnl
            
            total_values.append(total_value)
        
        # График: Сравнение общей ценности
        l1 = self.hedge_ax2.plot(price_range, base_total_values, linewidth=2, 
                              label='Без хеджа (USDC)', color='#d62728')
        l2 = self.hedge_ax2.plot(price_range, total_values, linewidth=2, 
                              label='С хеджем (USDC)', color='#2ca02c')
        
        # Устанавливаем значения оси Y для графика
        min_value = min(min(base_total_values), min(total_values))
        max_value = max(max(base_total_values), max(total_values))
        value_margin = (max_value - min_value) * 0.1
        self.hedge_ax2.set_ylim(min_value - value_margin, max_value + value_margin)
        
        # Добавляем горизонтальную линию для исходной суммы
        l3 = self.hedge_ax2.axhline(y=total_pool_value, color='blue', linestyle='--', 
                           label=f'Исходная сумма ({total_pool_value} USDC)')
        
        # Устанавливаем диапазон X для графика
        self.hedge_ax2.set_xlim(price_min, price_max)
        
        # Отметки на графике
        l4 = self.hedge_ax2.axvline(x=lower_bound, color='gray', linestyle='--', label='Границы диапазона')
        self.hedge_ax2.axvline(x=upper_bound, color='gray', linestyle='--')
        l5 = self.hedge_ax2.axvline(x=current_price, color='black', linestyle='-', label='Текущая цена')
        l6 = self.hedge_ax2.axvline(x=hedge_price, color='blue', linestyle=':', linewidth=1, label='Цена хеджа')
        
        self.hedge_ax2.grid(True, alpha=0.3)
        
        # Настраиваем оси
        self.hedge_ax2.tick_params(axis='x', labelsize=9, pad=2)
        self.hedge_ax2.tick_params(axis='y', labelsize=9, pad=2)
        
        # Настраиваем график
        self.hedge_ax2.set_title('Сравнение общей стоимости позиции', fontsize=14, fontweight='bold', pad=15)
        self.hedge_ax2.set_xlabel('Цена (USDC за ETH)', fontsize=12)
        self.hedge_ax2.set_ylabel('Стоимость (USDC)', fontsize=12)
        
        # Возвращаем легенду внутрь графика
        self.hedge_ax2.legend(loc='best', fontsize=10, framealpha=0.7)
        
        # Настраиваем подписи на осях для лучшей читаемости
        self.hedge_ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.0f}".format(x)))
        
        # Не используем tight_layout для предотвращения проблем с размерами
        # Вместо этого используем manual adjustment
        
        # Draw the plot and flush_events для принудительного обновления
        self.hedge_canvas.draw()
        self.hedge_canvas.flush_events()
    
    def plot_hedged_position_with_exit(self, current_price, lower_bound, upper_bound, 
                                      hedge_amount, exit_price):
        """Рисует графики с маркером цены выхода"""
        # Сначала выполним обычный расчет и построение
        liquidity = float(str(self.total_pool_value.get()).replace(',', '.')) / (
            ((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
            (math.sqrt(current_price) - math.sqrt(lower_bound))
        )
        
        hedge_eth = 0
        hedge_usdc = 0
        
        if self.hedge_enabled.get():
            hedge_eth = -hedge_amount
            hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
            hedge_usdc = abs(hedge_eth) * hedge_price
            
        # Стандартное построение графиков
        self.plot_hedged_position(current_price, lower_bound, upper_bound, liquidity, hedge_eth, hedge_usdc)
        
        # Добавляем маркер цены выхода на график
        if exit_price > 0:
            # Добавляем линию цены выхода
            exit_line = self.hedge_ax2.axvline(x=exit_price, color='red', linestyle='-.', 
                                             linewidth=2, label='Цена выхода')
            
            # Обновляем легенду графика с увеличенным размером шрифта
            self.hedge_ax2.legend(loc='best', fontsize=10, framealpha=0.7)
            
            # Draw the plot and flush_events для принудительного обновления
            self.hedge_canvas.draw()
            self.hedge_canvas.flush_events()
    
    def refresh_plots(self):
        """Полное обновление графиков без выполнения расчётов"""
        # Полностью пересоздаем фигуры и графики для основной вкладки
        plt.close(self.figure)
        
        # Используем фиксированные, но разумные размеры для фигур
        # Это безопаснее, чем динамические размеры, которые могут быть слишком большими
        self.figure = plt.Figure(figsize=(7, 8), dpi=100)
        self.ax1 = self.figure.add_subplot(211)  # Верхний график для ETH и USDC
        self.ax2 = self.figure.add_subplot(212)  # Нижний график для общей ценности
        
        # Уничтожить старый холст и создать новый
        self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Полностью пересоздаем фигуры и графики для хеджирования
        plt.close(self.hedge_figure)
        
        # Используем фиксированные размеры для хеджевого графика
        self.hedge_figure = plt.Figure(figsize=(7, 8), dpi=100)
        self.hedge_ax2 = self.hedge_figure.add_subplot(111)  # Один график для сравнения стоимости
        
        # Уничтожить старый холст и создать новый
        self.hedge_canvas.get_tk_widget().destroy()
        self.hedge_canvas = FigureCanvasTkAgg(self.hedge_figure, self.hedge_plot_frame)
        self.hedge_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Пересчитываем и перерисовываем графики
        self.calculate()
    
    def calculate_delta_for_price(self, price):
        """Рассчитывает дельту (количество ETH) для заданной цены"""
        try:
            # Получаем текущие параметры
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            # Рассчитываем ликвидность
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                           (math.sqrt(current_price) - math.sqrt(lower_bound)))
            
            # Если цена ниже нижней границы
            if price <= lower_bound:
                return liquidity * (1/math.sqrt(lower_bound) - 1/math.sqrt(upper_bound))
            
            # Если цена выше верхней границы
            elif price >= upper_bound:
                return 0
            
            # Если цена в диапазоне
            else:
                return liquidity * (1/math.sqrt(price) - 1/math.sqrt(upper_bound))
        
        except Exception as e:
            print(f"Ошибка при расчете дельты: {str(e)}")
            return 0
    
    def calculate_grid(self):
        try:
            # Получаем параметры
            grid_step = float(self.grid_step.get())
            fee_percent = float(self.grid_fee.get()) / 100
            
            # Получаем текущие параметры позиции
            current_price = float(self.current_price.get())
            lower_bound = float(self.lower_bound.get())
            upper_bound = float(self.upper_bound.get())
            total_value = float(self.total_pool_value.get())
            
            # Рассчитываем сетку цен
            prices = []
            price = lower_bound
            while price <= upper_bound:
                prices.append(price)
                price += grid_step
            
            # Рассчитываем дельту для каждой цены
            deltas = []
            for price in prices:
                delta = self.calculate_delta_for_price(price)
                deltas.append(delta)
            
            # Отображаем результаты
            self.grid_results_text.delete(1.0, tk.END)
            self.grid_results_text.insert(tk.END, "Цена\tДельта\n")
            self.grid_results_text.insert(tk.END, "-" * 30 + "\n")
            
            for price, delta in zip(prices, deltas):
                self.grid_results_text.insert(tk.END, f"{price:.2f}\t{delta:.2f}\n")
            
            # Строим график
            self.grid_ax1.clear()
            self.grid_ax2.clear()
            
            # График дельты
            self.grid_ax1.plot(prices, deltas, 'b-')
            self.grid_ax1.set_title('Дельта по цене')
            self.grid_ax1.set_xlabel('Цена')
            self.grid_ax1.set_ylabel('Дельта')
            self.grid_ax1.grid(True)
            
            # График PnL
            pnl = [delta * (price - current_price) for price, delta in zip(prices, deltas)]
            self.grid_ax2.plot(prices, pnl, 'r-')
            self.grid_ax2.set_title('PnL по цене')
            self.grid_ax2.set_xlabel('Цена')
            self.grid_ax2.set_ylabel('PnL')
            self.grid_ax2.grid(True)
            
            self.grid_canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при расчете сетки: {str(e)}")
    
    def run_simulation(self):
        try:
            # Получаем цены для симуляции
            prices_str = self.sim_prices.get()
            if not prices_str:
                raise ValueError("Введите цены для симуляции")
            
            prices = [float(p.strip()) for p in prices_str.split(',')]
            
            # Получаем текущие параметры
            current_price = float(self.current_price.get())
            grid_step = float(self.grid_step.get())
            fee_percent = float(self.grid_fee.get()) / 100
            
            # Рассчитываем транзакции
            transactions = []
            total_fee = 0
            
            for i, price in enumerate(prices):
                # Рассчитываем дельту для текущей цены
                delta = self.calculate_delta_for_price(price)
                
                # Если это не первая цена, рассчитываем изменение дельты
                if i > 0:
                    prev_delta = self.calculate_delta_for_price(prices[i-1])
                    delta_change = delta - prev_delta
                    
                    if abs(delta_change) > 0:
                        # Рассчитываем комиссию
                        fee = abs(delta_change) * price * fee_percent
                        total_fee += fee
                        
                        # Создаем транзакцию
                        direction = "Покупка" if delta_change > 0 else "Продажа"
                        transaction = HedgeTransaction(
                            price=price,
                            amount=abs(delta_change),
                            direction=direction,
                            fee=fee,
                            order_number=i
                        )
                        transactions.append(transaction)
            
            # Отображаем результаты
            self.grid_results_text.delete(1.0, tk.END)
            self.grid_results_text.insert(tk.END, "Транзакции:\n")
            self.grid_results_text.insert(tk.END, "-" * 50 + "\n")
            
            for t in transactions:
                self.grid_results_text.insert(tk.END, 
                    f"#{t.order_number} {t.direction} {t.amount:.4f} ETH по {t.price:.2f} USDC (комиссия: {t.fee:.2f} USDC)\n")
            
            self.grid_results_text.insert(tk.END, f"\nОбщая комиссия: {total_fee:.2f} USDC\n")
            
            # Строим график
            self.grid_ax1.clear()
            self.grid_ax2.clear()
            
            # График цен
            self.grid_ax1.plot(range(len(prices)), prices, 'b-')
            self.grid_ax1.set_title('Цены')
            self.grid_ax1.set_xlabel('Шаг')
            self.grid_ax1.set_ylabel('Цена')
            self.grid_ax1.grid(True)
            
            # График PnL
            pnl = []
            cumulative_pnl = 0
            for i, price in enumerate(prices):
                if i > 0:
                    delta = self.calculate_delta_for_price(price)
                    pnl_change = delta * (price - prices[i-1])
                    cumulative_pnl += pnl_change
                pnl.append(cumulative_pnl)
            
            self.grid_ax2.plot(range(len(prices)), pnl, 'r-')
            self.grid_ax2.set_title('Кумулятивный PnL')
            self.grid_ax2.set_xlabel('Шаг')
            self.grid_ax2.set_ylabel('PnL')
            self.grid_ax2.grid(True)
            
            self.grid_canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при симуляции: {str(e)}")

    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        # Проверяем, что ресайз произошел для главного окна, а не для дочерних виджетов
        if event.widget == self:
            # Обновляем графики при изменении размера с небольшой задержкой
            # чтобы не вызывать обновление на каждый пиксель ресайза
            self.after_cancel(self.resize_timer) if hasattr(self, 'resize_timer') else None
            self.resize_timer = self.after(200, self.refresh_plots)

if __name__ == "__main__":
    app = UniswapV3HedgeCalculator()
    app.mainloop() 