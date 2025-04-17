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
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Создаем виджеты для основной вкладки
        self.create_main_tab_widgets()
        
        # Создаем виджеты для вкладки хеджирования
        self.create_hedge_tab_widgets()
        
        # Создаем виджеты для вкладки сеточного хеджирования
        self.create_grid_tab_widgets()
    
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