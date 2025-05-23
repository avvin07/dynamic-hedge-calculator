import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import locale
from tkinter import messagebox
from tkinter import filedialog
import pandas as pd
import os
import re
import traceback
import csv

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
        self.dynamic_fee = tk.DoubleVar(value=0.1)  # Комиссия для динамического хеджирования
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
        
        # Вкладка сеточного хеджирования (создаем, но не добавляем в интерфейс)
        self.grid_tab = ttk.Frame(self)  # Создаем, но не добавляем в tab_control
        
        # Добавляем вкладку динамического хеджирования
        self.dynamic_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dynamic_tab, text="Динамический хедж")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Создаем виджеты для основной вкладки
        self.create_main_tab_widgets()
        
        # Создаем виджеты для вкладки хеджирования
        self.create_hedge_tab_widgets()
        
        # Создаем виджеты для вкладки сеточного хеджирования (скрытой)
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
        
        # Buttons for export and import
        ttk.Button(input_frame, text="Экспорт в CSV", command=self.export_to_csv).grid(row=1, column=2, padx=20, pady=5, sticky="w")
        ttk.Button(input_frame, text="Загрузить из файла", command=lambda: self.load_prices_and_display(self.current_price)).grid(row=2, column=2, padx=20, pady=5, sticky="w")
        
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
        ttk.Button(settings_frame, text="Рассчитать сетку", command=self.calculate_grid).grid(row=2, column=0, padx=5, pady=5)
        
        # Кнопки для экспорта и импорта
        ttk.Button(settings_frame, text="Экспорт в CSV", command=self.export_to_csv).grid(row=2, column=1, padx=5, pady=5)
        
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
        
        # Кнопка для загрузки цен из файла
        ttk.Button(sim_frame, text="Загрузить из файла", 
                 command=self.load_prices_for_simulation).grid(row=0, column=2, padx=5, pady=5)
        
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
        # Расширяем диапазон отображения: 20% слева и 15% справа
        price_min = lower_bound * 0.8  # расширяем на 20% вниз
        price_max = upper_bound * 1.15  # расширяем на 15% вверх
        
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
        
        # Расширяем диапазон отображения: 20% слева и 15% справа
        price_min = lower_bound * 0.8  # расширяем на 20% вниз
        price_max = upper_bound * 1.15  # расширяем на 15% вверх
        
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
        
        # Расчет комиссии хеджа
        hedge_fee = abs(hedge_eth) * hedge_price * hedge_fee_percent
        
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
            
            # Для шорта: прибыль = (цена продажи - текущая цена) * количество - комиссия
            hedge_price_diff = hedge_price - price  # Это положительно, если цена упала
            hedge_pnl = -hedge_eth_val * hedge_price_diff - hedge_fee  # Вычитаем комиссию
            
            # Смещаем кривую P&L хеджа, чтобы она проходила через точку входа (total_pool_value)
            # Простое визуальное смещение (не влияет на расчеты P&L)
            if abs(hedge_eth) > 0.0001:  # Проверяем, что хедж активен
                hedge_pnl_adjusted = total_pool_value + hedge_pnl
            else:
                hedge_pnl_adjusted = total_pool_value  # Если хедж не активен, просто рисуем горизонтальную линию
            
            hedge_pnl_values.append(hedge_pnl_adjusted)
            
            # Оригинальное значение P&L используем для расчета общей стоимости
            total_value = base_value + hedge_pnl
            
            total_values.append(total_value)
        
        # График: Сравнение общей ценности
        l1 = self.hedge_ax2.plot(price_range, base_total_values, linewidth=2, 
                              label='Без хеджа (USDC)', color='#d62728')
        l2 = self.hedge_ax2.plot(price_range, total_values, linewidth=2, 
                              label='С хеджем (USDC)', color='#2ca02c')
        
        # Добавляем кривую P&L хеджа (полупрозрачную)
        lh = self.hedge_ax2.plot(price_range, hedge_pnl_values, linewidth=1.5, 
                            label='P&L хеджа (USDC)', color='#ff7f0e', alpha=0.4)
        
        # Устанавливаем значения оси Y для графика
        min_value = min(min(base_total_values), min(total_values), min(hedge_pnl_values))
        max_value = max(max(base_total_values), max(total_values), max(hedge_pnl_values))
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
        hedge_price = current_price  # По умолчанию используем текущую цену
        
        if self.hedge_enabled.get():
            hedge_eth = -hedge_amount
            hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
            hedge_usdc = abs(hedge_eth) * hedge_price
            
        # Стандартное построение графиков
        self.plot_hedged_position(current_price, lower_bound, upper_bound, liquidity, hedge_eth, hedge_usdc)
        
        # Добавляем маркер цены выхода на график
        if exit_price > 0:
            # Расширяем диапазон отображения: 20% слева и 15% справа
            price_min = lower_bound * 0.8
            price_max = upper_bound * 1.15
            
            # Получаем данные графика
            price_range = np.linspace(price_min, price_max, 1000)
            
            # Получаем первоначальную сумму пула
            try:
                total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            except:
                total_pool_value = 10000  # значение по умолчанию
            
            # Получаем комиссию
            try:
                hedge_fee_percent = float(str(self.hedge_fee_percent.get()).replace(',', '.')) / 100.0
            except:
                hedge_fee_percent = 0.002  # 0.2% по умолчанию
            
            # Расчет значений для пометки пересечений
            # Вычисляем значения в точке выхода
            if exit_price < lower_bound:
                # Все в ETH
                exit_eth = liquidity * (1/math.sqrt(lower_bound) - 1/math.sqrt(upper_bound))
                exit_usdc = 0
            elif exit_price > upper_bound:
                # Все в USDC
                exit_eth = 0
                exit_usdc = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))
            else:
                # В диапазоне
                exit_eth = liquidity * (1/math.sqrt(exit_price) - 1/math.sqrt(upper_bound))
                exit_usdc = liquidity * (math.sqrt(exit_price) - math.sqrt(lower_bound))
            
            # Базовая стоимость позиции
            exit_base_value = exit_eth * exit_price + exit_usdc
            
            # Расчет комиссии хеджа
            hedge_fee = abs(hedge_eth) * hedge_price * hedge_fee_percent
            
            # Расчет P&L хеджа при цене выхода
            hedge_price_diff = hedge_price - exit_price
            exit_hedge_pnl = -hedge_eth * hedge_price_diff - hedge_fee
            
            # Общая стоимость с хеджем
            exit_total_value = exit_base_value + exit_hedge_pnl
            
            # Смещаем значение P&L хеджа для отображения на графике
            if abs(hedge_eth) > 0.0001:  # Проверяем, что хедж активен
                exit_hedge_pnl_adjusted = total_pool_value + exit_hedge_pnl
            else:
                exit_hedge_pnl_adjusted = total_pool_value  # Если хедж не активен, используем исходное значение
            
            # Добавляем линию цены выхода
            exit_line = self.hedge_ax2.axvline(x=exit_price, color='red', linestyle='-.', 
                                             linewidth=2, label='Цена выхода')
            
            # Добавляем аннотацию точек пересечений с ценой выхода
            # Точки пересечения с кривой без хеджа (над линией)
            self.hedge_ax2.plot([exit_price], [exit_base_value], 'ro', markersize=7)
            self.hedge_ax2.annotate(f"Базовая позиция: {exit_base_value:.0f} USDC", 
                                xy=(exit_price, exit_base_value),
                                xytext=(10, 30),  # Увеличиваем отступ вверх
                                textcoords="offset points",
                                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"),
                                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                                fontsize=10)  # Увеличиваем размер шрифта
            
            # Точки пересечения с кривой с хеджем (под линией)
            self.hedge_ax2.plot([exit_price], [exit_total_value], 'go', markersize=7)
            self.hedge_ax2.annotate(f"С хеджем: {exit_total_value:.0f} USDC", 
                                xy=(exit_price, exit_total_value),
                                xytext=(10, -30),  # Отступ вниз
                                textcoords="offset points",
                                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"),
                                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                                fontsize=10)  # Увеличиваем размер шрифта
            
            # Точки пересечения с кривой P&L хеджа (в сторону)
            self.hedge_ax2.plot([exit_price], [exit_hedge_pnl_adjusted], 'yo', markersize=6, alpha=0.8)
            self.hedge_ax2.annotate(f"P&L хеджа: {exit_hedge_pnl:.0f} USDC", 
                                xy=(exit_price, exit_hedge_pnl_adjusted),
                                xytext=(40, 0),  # Смещаем подпись вправо
                                textcoords="offset points",
                                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"),
                                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                                fontsize=10)  # Увеличиваем размер шрифта
            
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
        fee_entry = ttk.Entry(settings_frame, textvariable=self.dynamic_fee, width=10)
        fee_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Создаем верхний контейнер для размещения фреймов ввода цен и итоговых результатов
        top_container = ttk.Frame(self.dynamic_tab)
        top_container.pack(fill="x", padx=10, pady=5)
        
        # Настраиваем веса для размещения элементов
        top_container.columnconfigure(0, weight=2)  # Для фрейма ввода цен
        top_container.columnconfigure(1, weight=1)  # Для фрейма итоговых результатов

        # Фрейм для ввода цен (слева)
        price_frame = ttk.LabelFrame(top_container, text="Последовательность цен")
        price_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        
        # Создаем контейнер с прокруткой для полей ввода цен
        price_scroll_container = ttk.Frame(price_frame)
        price_scroll_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Создаем вертикальный скроллбар
        price_scrollbar = ttk.Scrollbar(price_scroll_container, orient="vertical")
        price_scrollbar.pack(side="right", fill="y")
        
        # Создаем холст с привязкой к скроллбару
        price_canvas = tk.Canvas(price_scroll_container, yscrollcommand=price_scrollbar.set)
        price_canvas.pack(side="left", fill="both", expand=True)
        
        # Привязываем скроллбар к холсту
        price_scrollbar.config(command=price_canvas.yview)
        
        # Создаем фрейм внутри холста для размещения полей ввода
        self.dynamic_price_container = ttk.Frame(price_canvas)
        
        # Размещаем фрейм на холсте
        price_canvas_window = price_canvas.create_window((0, 0), window=self.dynamic_price_container, anchor="nw")
        
        # Настраиваем обработчики событий для корректной прокрутки
        def on_price_frame_configure(event):
            # Обновляем размер области прокрутки при изменении размера внутреннего фрейма
            price_canvas.configure(scrollregion=price_canvas.bbox("all"))
            # Также обновляем ширину окна холста при изменении ширины внутреннего фрейма
            price_canvas.itemconfig(price_canvas_window, width=event.width)
        
        def on_canvas_configure(event):
            # Обновляем ширину внутреннего окна при изменении размера холста
            price_canvas.itemconfig(price_canvas_window, width=event.width)
        
        # Привязываем обработчики
        self.dynamic_price_container.bind("<Configure>", on_price_frame_configure)
        price_canvas.bind("<Configure>", on_canvas_configure)
        
        # Активируем прокрутку мышью
        def on_mousewheel(event):
            price_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        price_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Кнопки для управления ценами
        buttons_container = ttk.Frame(price_frame)
        buttons_container.pack(fill="x", padx=5, pady=5)
        
        # Добавляем переменную для отслеживания режима ввода
        self.price_input_mode = tk.StringVar(value="single")  # "single" или "bulk"
        
        # Добавляем контейнер для массового ввода цен
        self.bulk_price_container = ttk.Frame(price_frame)
        
        # Текстовое поле для массового ввода цен
        bulk_label = ttk.Label(self.bulk_price_container, text="Введите цены (через запятую или каждая с новой строки):")
        bulk_label.pack(side="top", fill="x", padx=5, pady=2)
        
        # Создаем текстовое поле с прокруткой
        bulk_text_frame = ttk.Frame(self.bulk_price_container)
        bulk_text_frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        self.bulk_price_text = tk.Text(bulk_text_frame, height=10, width=30)
        self.bulk_price_text.pack(side="left", fill="both", expand=True)
        
        bulk_scrollbar = ttk.Scrollbar(bulk_text_frame, command=self.bulk_price_text.yview)
        bulk_scrollbar.pack(side="right", fill="y")
        self.bulk_price_text.config(yscrollcommand=bulk_scrollbar.set)
        
        # Кнопка для применения массового ввода
        apply_bulk_button = ttk.Button(self.bulk_price_container, text="Применить цены", 
                                     command=self.apply_bulk_prices)
        apply_bulk_button.pack(side="bottom", pady=5)
        
        # Кнопки для переключения режимов ввода
        mode_container = ttk.Frame(buttons_container)
        mode_container.pack(side="right", padx=5)
        
        ttk.Label(mode_container, text="Режим ввода:").pack(side="left", padx=5)
        ttk.Radiobutton(mode_container, text="Построчно", variable=self.price_input_mode, 
                       value="single", command=self.toggle_price_input_mode).pack(side="left")
        ttk.Radiobutton(mode_container, text="Все сразу", variable=self.price_input_mode, 
                       value="bulk", command=self.toggle_price_input_mode).pack(side="left")
        
        # Стандартные кнопки управления ценами
        add_price_button = ttk.Button(buttons_container, text="Добавить цену", command=self.add_price_field)
        add_price_button.pack(side="left", padx=5)
        
        # Кнопка загрузки цен из файла
        load_prices_button = ttk.Button(buttons_container, text="Загрузить из файла", command=self.load_prices_from_file_and_update)
        load_prices_button.pack(side="left", padx=5)
        
        # Кнопка для просмотра цен в табличном виде
        view_prices_button = ttk.Button(buttons_container, text="Просмотр цен", command=self.show_prices_as_table)
        view_prices_button.pack(side="left", padx=5)
        
        # Кнопка для очистки всех значений
        clear_all_button = ttk.Button(buttons_container, text="Очистить все значения", command=self.clear_all_price_fields)
        clear_all_button.pack(side="left", padx=5)
        
        # Добавляем начальные поля для цен
        self.add_initial_price_fields()
        
        # По умолчанию скрываем контейнер массового ввода
        self.bulk_price_container.pack_forget()
        
        # Фрейм для итоговых результатов (справа)
        self.summary_frame = ttk.LabelFrame(top_container, text="Итоговые результаты")
        self.summary_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        
        # Переменные для хранения итоговых результатов
        self.summary_vars = {
            "delta": tk.StringVar(value="0.0000"),
            "base_pnl": tk.StringVar(value="0.00"),
            "hedge_pnl": tk.StringVar(value="0.00"),
            "total_pnl": tk.StringVar(value="0.00"),
            "fee": tk.StringVar(value="0.00"),
            "net_pnl": tk.StringVar(value="0.00")
        }
        
        # Добавляем элементы отображения итоговых результатов
        ttk.Label(self.summary_frame, text="Итоговая дельта:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(self.summary_frame, textvariable=self.summary_vars["delta"]).grid(row=0, column=1, padx=5, pady=2, sticky="e")
        
        ttk.Label(self.summary_frame, text="P&L основной позиции:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.base_pnl_label = ttk.Label(self.summary_frame, textvariable=self.summary_vars["base_pnl"])
        self.base_pnl_label.grid(row=1, column=1, padx=5, pady=2, sticky="e")
        
        ttk.Label(self.summary_frame, text="P&L хеджа:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.hedge_pnl_label = ttk.Label(self.summary_frame, textvariable=self.summary_vars["hedge_pnl"])
        self.hedge_pnl_label.grid(row=2, column=1, padx=5, pady=2, sticky="e")
        
        ttk.Label(self.summary_frame, text="Общий P&L:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.total_pnl_label = ttk.Label(self.summary_frame, textvariable=self.summary_vars["total_pnl"], font=('Helvetica', 9, 'bold'))
        self.total_pnl_label.grid(row=3, column=1, padx=5, pady=2, sticky="e")
        
        ttk.Label(self.summary_frame, text="Общая комиссия:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(self.summary_frame, textvariable=self.summary_vars["fee"]).grid(row=4, column=1, padx=5, pady=2, sticky="e")
        
        ttk.Label(self.summary_frame, text="Чистый результат:").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.net_pnl_label = ttk.Label(self.summary_frame, textvariable=self.summary_vars["net_pnl"], font=('Helvetica', 9, 'bold'))
        self.net_pnl_label.grid(row=5, column=1, padx=5, pady=2, sticky="e")
        
        # Кнопки для расчета и экспорта результатов
        buttons_frame = ttk.Frame(self.dynamic_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        # Кнопка расчета
        calc_button = ttk.Button(buttons_frame, text="Рассчитать динамический хедж", 
                               command=self.calculate_dynamic_hedge, width=30)
        calc_button.pack(side="left", padx=5, pady=5)
        
        # Кнопка экспорта в CSV
        export_csv_button = ttk.Button(buttons_frame, text="Экспорт в CSV", 
                                    command=self.export_dynamic_to_csv, width=15)
        export_csv_button.pack(side="left", padx=5, pady=5)
        
        # Фрейм для результатов
        self.dynamic_results_frame = ttk.LabelFrame(self.dynamic_tab, text="Результаты")
        self.dynamic_results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Улучшенное текстовое поле с прокруткой для вывода результатов
        text_container = ttk.Frame(self.dynamic_results_frame)
        text_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Добавляем вертикальную полосу прокрутки
        scrollbar_y = ttk.Scrollbar(text_container)
        scrollbar_y.pack(side="right", fill="y")
        
        # Добавляем горизонтальную полосу прокрутки
        scrollbar_x = ttk.Scrollbar(text_container, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Текстовое поле с поддержкой прокрутки и монопропорциональным шрифтом
        self.dynamic_results_text = tk.Text(text_container, height=10, wrap="none",
                                     xscrollcommand=scrollbar_x.set,
                                     yscrollcommand=scrollbar_y.set,
                                     font=("Courier New", 10))
        self.dynamic_results_text.pack(fill="both", expand=True)
        
        # Привязываем полосы прокрутки к текстовому полю
        scrollbar_y.config(command=self.dynamic_results_text.yview)
        scrollbar_x.config(command=self.dynamic_results_text.xview)
        
        # Фрейм для графиков
        self.dynamic_plot_frame = ttk.LabelFrame(self.dynamic_tab, text="Графики результатов")
        self.dynamic_plot_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Создаем фигуру для графиков - увеличиваем размеры
        self.dynamic_fig = plt.Figure(figsize=(10, 6), dpi=100)
        
        # Создаем только один график для P&L
        self.dynamic_ax = self.dynamic_fig.add_subplot(111)  # График P&L
        
        # Настраиваем отступы вручную
        self.dynamic_fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15, hspace=0.4, wspace=0.4)
        
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
            fee_percent = float(str(self.dynamic_fee.get()).replace(',', '.')) / 100.0
            
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
            
            # Рассчитываем начальное количество ETH и USDC в пуле
            initial_eth = self.calculate_delta_for_price(current_price)
            initial_usdc_amount = liquidity * (math.sqrt(current_price) - math.sqrt(lower_bound))
            initial_total_value = initial_eth * current_price + initial_usdc_amount
            
            # Добавляем начальную позицию (шаг 0)
            initial_hedge = -initial_hedge_amount
            initial_total_delta = initial_eth + initial_hedge
            initial_fee = abs(initial_hedge) * initial_hedge_price * fee_percent
            
            self.dynamic_results.append({
                "step": 0,
                "price": current_price,
                "pool_eth": initial_eth,
                "pool_usdc": initial_usdc_amount,
                "pool_value": initial_total_value,
                "hedge_eth": initial_hedge,
                "delta": initial_total_delta,
                "hedge_change": 0,
                "fee": initial_fee,
                "total_fee": initial_fee,
                "hedge_pnl": 0,
                "base_pnl": 0,
                "total_pnl": 0,
                "price_direction": "start"  # Начальное состояние
            })
            
            # Формируем хронологическую последовательность цен
            # Начинаем с текущей цены (шаг 0), затем идет цена1, цена2, ...
            prices_sequence = self.form_price_sequence(current_price, user_prices)
            
            # Рассчитываем для каждой последующей цены
            cumulative_hedge_pnl = 0
            total_fee = initial_fee
            prev_hedge = initial_hedge
            prev_price = current_price
            prev_pool_eth = initial_eth  # Запоминаем предыдущий объем ETH в пуле
            
            for step_idx, price in enumerate(prices_sequence[1:], start=1):
                # Определяем направление движения цены
                price_direction = "up" if price > prev_price else "down"
                
                # Рассчитываем дельту пула при новой цене
                pool_eth = self.calculate_delta_for_price(price)
                
                # ИСПРАВЛЕНИЕ: Правильно рассчитываем USDC в пуле через ликвидность и новую цену
                # 1. При цене ниже нижней границы
                if price <= lower_bound:
                    pool_usdc = 0  # Все в ETH
                # 2. При цене выше верхней границы
                elif price >= upper_bound:
                    pool_usdc = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))  # Все в USDC
                # 3. При цене в диапазоне
                else:
                    pool_usdc = liquidity * (math.sqrt(price) - math.sqrt(lower_bound))
                
                # Общая стоимость пула в USDC
                pool_value = pool_eth * price + pool_usdc
                
                # ИСПРАВЛЕНИЕ: P&L основной позиции - пропорционально изменению цены для активов в диапазоне
                # Для ETH/USDC LP в Uniswap V3:
                # - При росте цены: часть ETH конвертируется в USDC, общая стоимость растет
                # - При падении цены: добавляется ETH за счет USDC, общая стоимость падает
                
                # Базовый P&L - разница между текущей и начальной стоимостью
                base_pnl = pool_value - initial_total_value
                
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
                
                # ИСПРАВЛЕНИЕ: Точно рассчитываем P&L хеджа для данного шага
                # 1. P&L считаем при изменении цены, независимо от фактического изменения позиции
                # 2. Учитываем и реализованный, и нереализованный P&L
                
                # Расчет P&L хеджа от изменения цены
                # Для шорта (prev_hedge < 0):
                # - При падении цены - положительный P&L (prev_price > price)
                # - При росте цены - отрицательный P&L (prev_price < price)
                unrealized_pnl = 0
                if prev_hedge < 0:  # У нас шорт (отрицательные значения ETH)
                    unrealized_pnl = abs(prev_hedge) * (prev_price - price)
                
                # Для измененной части позиции (если закрываем часть позиции)
                realized_pnl = 0
                if hedge_change > 0 and prev_hedge < 0:  # Если уменьшаем шорт
                    # Прибыль/убыток от закрытия части позиции
                    realized_pnl = hedge_change * (prev_price - price)
                
                # Общий P&L хеджа для данного шага
                step_pnl = unrealized_pnl + realized_pnl
                
                # Накопленный P&L хеджа
                cumulative_hedge_pnl += step_pnl
                
                # Общий P&L (базовый + хедж)
                total_pnl = base_pnl + cumulative_hedge_pnl
                
                # Сохраняем результаты
                self.dynamic_results.append({
                    "step": step_idx,
                    "price": price,
                    "pool_eth": pool_eth,
                    "pool_usdc": pool_usdc,
                    "pool_value": pool_value,
                    "hedge_eth": hedge_eth,
                    "delta": total_delta,
                    "hedge_change": hedge_change,
                    "fee": fee,
                    "total_fee": total_fee,
                    "hedge_pnl": step_pnl,
                    "cumulative_hedge_pnl": cumulative_hedge_pnl,
                    "base_pnl": base_pnl,
                    "total_pnl": total_pnl,
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
                        f"P&L основной позиции: {self.dynamic_results[-1]['base_pnl']:.2f} USDC\n"
                        f"P&L хеджа: {self.dynamic_results[-1]['cumulative_hedge_pnl']:.2f} USDC\n"
                        f"Общий P&L: {self.dynamic_results[-1]['total_pnl']:.2f} USDC\n"
                        f"Общая комиссия: {self.dynamic_results[-1]['total_fee']:.2f} USDC")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при расчете динамического хеджирования: {str(e)}")
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
        
        # Форматируем заголовок таблицы с использованием моноширинного шрифта
        header = "{:<5} {:<10} {:<10} {:<10} {:<12} {:<10} {:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<15}\n".format(
            "Шаг", "Цена", "ETH пул", "USDC пул", "Стоим. пула", "Фьючерс", "Дельта", "Изменение", 
            "Комиссия", "P&L хеджа", "P&L базы", "Общий P&L", "Стратегия"
        )
        self.dynamic_results_text.insert(tk.END, header)
        self.dynamic_results_text.insert(tk.END, "-" * 150 + "\n")
        
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
            
            # Определяем цвет (красный/зеленый) для значений P&L
            # Используем накопленный P&L хеджа вместо шагового
            cumulative_hedge_pnl = result.get('cumulative_hedge_pnl', 0)
            hedge_pnl_sign = "+" if cumulative_hedge_pnl > 0 else ""
            
            base_pnl = result.get('base_pnl', 0)
            base_pnl_sign = "+" if base_pnl > 0 else ""
            
            total_pnl = result.get('total_pnl', 0)
            total_pnl_sign = "+" if total_pnl > 0 else ""
            
            # Форматируем строку таблицы с монопропорциональным шрифтом для лучшего выравнивания
            row_format = "{:<5} {:<10} {:<10} {:<10} {:<12} {:<10} {:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<15}\n"
            row = row_format.format(
                result['step'],
                f"{result['price']:.2f} {price_indicator}",
                f"{result['pool_eth']:.4f}",
                f"{result['pool_usdc']:.2f}",
                f"{result['pool_value']:.2f}",
                f"{result['hedge_eth']:.4f}",
                f"{result['delta']:.4f}",
                f"{result['hedge_change']:.4f} {hedge_indicator}",
                f"{result['fee']:.2f}",
                f"{hedge_pnl_sign}{cumulative_hedge_pnl:.2f}",
                f"{base_pnl_sign}{base_pnl:.2f}",
                f"{total_pnl_sign}{total_pnl:.2f}",
                strategy_note
            )
            
            # Применяем теги для цветового выделения
            self.dynamic_results_text.insert(tk.END, row)
        
        # Итоговые результаты
        if self.dynamic_results:
            last_result = self.dynamic_results[-1]
            
            self.dynamic_results_text.insert(tk.END, "\nИтоговые результаты:\n")
            self.dynamic_results_text.insert(tk.END, "-" * 50 + "\n")
            
            # Получаем начальные и конечные значения для расчета результатов
            initial_eth = self.dynamic_results[0]['pool_eth']
            initial_usdc = self.dynamic_results[0]['pool_usdc']
            initial_value = self.dynamic_results[0]['pool_value']
            
            final_eth = last_result['pool_eth']
            final_usdc = last_result['pool_usdc']
            final_value = last_result['pool_value']
            
            # P&L базовой позиции
            base_pnl = last_result['base_pnl']
            base_pnl_sign = "+" if base_pnl > 0 else ""
            self.dynamic_results_text.insert(tk.END, f"P&L основной позиции: {base_pnl_sign}{base_pnl:.2f} USDC\n")
            
            # Изменение состава пула
            self.dynamic_results_text.insert(tk.END, f"   Начальное состояние пула: {initial_eth:.4f} ETH + {initial_usdc:.2f} USDC = {initial_value:.2f} USDC\n")
            self.dynamic_results_text.insert(tk.END, f"   Конечное состояние пула:  {final_eth:.4f} ETH + {final_usdc:.2f} USDC = {final_value:.2f} USDC\n")
            
            # P&L хеджа
            cumulative_hedge_pnl = last_result['cumulative_hedge_pnl']
            hedge_sign = "+" if cumulative_hedge_pnl > 0 else ""
            self.dynamic_results_text.insert(tk.END, f"P&L хеджа: {hedge_sign}{cumulative_hedge_pnl:.2f} USDC\n")
            
            # Комиссия
            self.dynamic_results_text.insert(tk.END, f"Общая комиссия: {last_result['total_fee']:.2f} USDC\n")
            
            # Чистый результат (общий P&L минус комиссия)
            total_pnl = last_result['total_pnl']
            total_pnl_sign = "+" if total_pnl > 0 else ""
            net_result = total_pnl - last_result['total_fee']
            net_sign = "+" if net_result > 0 else ""
            self.dynamic_results_text.insert(tk.END, f"Общий P&L: {total_pnl_sign}{total_pnl:.2f} USDC\n")
            self.dynamic_results_text.insert(tk.END, f"Чистый результат: {net_sign}{net_result:.2f} USDC\n")
            
            # Обновляем данные в блоке итоговых результатов
            self.update_summary_values(last_result, net_result)
            
            # Добавляем пояснения
            self.dynamic_results_text.insert(tk.END, "\nПояснения:\n")
            self.dynamic_results_text.insert(tk.END, "-" * 50 + "\n")
            self.dynamic_results_text.insert(tk.END, "↑ в столбце Цена - цена выросла\n")
            self.dynamic_results_text.insert(tk.END, "↓ в столбце Цена - цена упала\n")
            self.dynamic_results_text.insert(tk.END, "↑ в столбце Изменение - уменьшение размера шорта (закрытие части позиции)\n")
            self.dynamic_results_text.insert(tk.END, "↓ в столбце Изменение - увеличение размера шорта\n")
            self.dynamic_results_text.insert(tk.END, "При падении цены: прибыль по хеджу (шорту), убыток по основной позиции\n")
            self.dynamic_results_text.insert(tk.END, "При росте цены: убыток по хеджу (шорту), прибыль по основной позиции\n")
            self.dynamic_results_text.insert(tk.END, "Без изменений: когда объем ETH в пуле и хедж не меняется, P&L хеджа на этом шаге = 0\n")
    
    def update_summary_values(self, last_result, net_result):
        """Обновляет значения в блоке итоговых результатов"""
        # Обновляем переменные для отображения
        delta_value = last_result['delta']
        self.summary_vars["delta"].set(f"{delta_value:.4f}")
        
        base_pnl = last_result['base_pnl']
        base_pnl_sign = "+" if base_pnl > 0 else ""
        self.summary_vars["base_pnl"].set(f"{base_pnl_sign}{base_pnl:.2f}")
        
        cumulative_hedge_pnl = last_result['cumulative_hedge_pnl']
        hedge_sign = "+" if cumulative_hedge_pnl > 0 else ""
        self.summary_vars["hedge_pnl"].set(f"{hedge_sign}{cumulative_hedge_pnl:.2f}")
        
        total_pnl = last_result['total_pnl']
        total_pnl_sign = "+" if total_pnl > 0 else ""
        self.summary_vars["total_pnl"].set(f"{total_pnl_sign}{total_pnl:.2f}")
        
        fee = last_result['total_fee']
        self.summary_vars["fee"].set(f"{fee:.2f}")
        
        net_sign = "+" if net_result > 0 else ""
        self.summary_vars["net_pnl"].set(f"{net_sign}{net_result:.2f}")
        
        # Устанавливаем цвета для значений (зеленый для положительных, красный для отрицательных)
        self.base_pnl_label.config(foreground="green" if base_pnl > 0 else "red" if base_pnl < 0 else "black")
        self.hedge_pnl_label.config(foreground="green" if cumulative_hedge_pnl > 0 else "red" if cumulative_hedge_pnl < 0 else "black")
        self.total_pnl_label.config(foreground="green" if total_pnl > 0 else "red" if total_pnl < 0 else "black")
        self.net_pnl_label.config(foreground="green" if net_result > 0 else "red" if net_result < 0 else "black")
    
    def plot_dynamic_results(self):
        """Отображает результаты динамического хеджирования на графике"""
        # Если нет результатов, ничего не делаем
        if not self.dynamic_results:
            return
            
        try:
            # Полностью удаляем и пересоздаем график вместо простой очистки
            # Удаляем старый холст
            for widget in self.dynamic_plot_frame.winfo_children():
                widget.destroy()
                
            # Пересоздаем фигуру и оси
            self.dynamic_fig = plt.Figure(figsize=(10, 6), dpi=100)
            self.dynamic_ax = self.dynamic_fig.add_subplot(111)
            
            # Настраиваем отступы
            self.dynamic_fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
            
            # Создаем новый холст
            self.dynamic_canvas = FigureCanvasTkAgg(self.dynamic_fig, master=self.dynamic_plot_frame)
            self.dynamic_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            # Подготавливаем данные для графиков
            steps = [r['step'] for r in self.dynamic_results]
            prices = [r['price'] for r in self.dynamic_results]
            
            # Данные для P&L
            base_pnl = []         # P&L основной позиции
            hedge_pnl = []        # P&L хеджа
            combined_pnl = []     # Совместный P&L
            
            # Массивы для хранения индексов точек разных операций
            increase_short_points = []  # Точки увеличения шорта (при падении цены)
            reduce_short_points = []    # Точки сокращения шорта (при росте цены)
            no_change_points = []       # Точки без изменений
            
            for i, result in enumerate(self.dynamic_results):
                # Получаем значения базового P&L
                base_pnl.append(result['base_pnl'])
                
                # Получаем значения хеджа
                # Проверяем, какой ключ используется для хеджа
                if 'cumulative_hedge_pnl' in result:
                    hedge_pnl.append(result['cumulative_hedge_pnl'])
                else:
                    hedge_pnl.append(result.get('cumulative_pnl', 0))
                
                # Общий P&L
                if 'total_pnl' in result:
                    combined_pnl.append(result['total_pnl'])
                else:
                    # Вычисляем как сумму
                    combined_pnl.append(base_pnl[-1] + hedge_pnl[-1])
                
                # Определение типа операции
                if i > 0:
                    if result.get('operation_type') == "reduce_short":
                        reduce_short_points.append(i)
                    elif result.get('operation_type') == "increase_short":
                        increase_short_points.append(i)
                    elif result.get('operation_type') == "no_change":
                        no_change_points.append(i)
            
            # Находим минимальные и максимальные значения для масштабирования осей
            all_values = base_pnl + hedge_pnl + combined_pnl
            min_val = min(all_values) if all_values else 0
            max_val = max(all_values) if all_values else 0
            
            # Добавляем отступы для лучшей визуализации (минимум 10% от диапазона или 100 USDC)
            y_margin = max((max_val - min_val) * 0.15, 100)
            y_min = min_val - y_margin
            y_max = max_val + y_margin
            
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
            
            # Аннотации с ценами
            for i, step in enumerate(steps):
                # Аннотация с ценой (только для ключевых точек)
                if i == 0 or i == len(steps)-1 or i % (max(1, len(steps) // 10)) == 0:
                    self.dynamic_ax.annotate(f"{prices[i]:.0f}", 
                                         xy=(step, combined_pnl[i]),
                                         xytext=(0, 10),
                                         textcoords='offset points',
                                         ha='center',
                                         fontsize=8)
            
            # Добавляем горизонтальную линию на уровне 0
            self.dynamic_ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
            
            # Настраиваем оси
            self.dynamic_ax.set_xlabel('Шаг', fontsize=10)
            self.dynamic_ax.set_ylabel('P&L (USDC)', fontsize=10)
            self.dynamic_ax.set_title('Профиль P&L с ребалансировкой хеджа', fontsize=12, fontweight='bold')
            
            # Устанавливаем диапазон оси Y
            self.dynamic_ax.set_ylim(y_min, y_max)
            
            # Настраиваем x-ось для отображения целых шагов
            self.dynamic_ax.set_xticks(steps)
            
            # Поворачиваем метки оси X если их много
            if len(steps) > 10:
                self.dynamic_ax.set_xticklabels([str(step) for step in steps], rotation=45, ha='right')
            else:
                self.dynamic_ax.set_xticklabels([str(step) for step in steps])
            
            # Добавляем легенду в оптимальном месте
            self.dynamic_ax.legend(loc='best', fontsize=9)
            
            # Добавляем пояснение к маркерам и движению цены
            self.dynamic_fig.text(0.5, 0.01, 
                             "△ - сокращение шорта, ▽ - увеличение шорта, □ - без изменений", 
                             ha='center', fontsize=8)
            
            # Добавляем текстовое пояснение взаимосвязи движения цены и P&L
            text_box = self.dynamic_ax.text(0.02, 0.02, 
                            "При падении цены: ↑ прибыль по хеджу, ↓ убыток по основной позиции\n"
                            "При росте цены: ↓ убыток по хеджу, ↑ прибыль по основной позиции\n"
                            "LP-позиция в Uniswap V3 имеет асимметричное изменение P&L",
                            transform=self.dynamic_ax.transAxes,
                            fontsize=8,
                            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.5'))
            
            # Включаем сетку
            self.dynamic_ax.grid(True, alpha=0.3)
            
            # Обновляем макет
            self.dynamic_fig.tight_layout()
            
            # Обновляем холст
            self.dynamic_canvas.draw()
            
            # Сохраняем график в временный файл для будущего экспорта в CSV
            try:
                # Создаем временную директорию, если её нет
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Путь к файлу с графиком
                self.chart_temp_path = os.path.join(temp_dir, "cumulative_hedge_pnl.png")
                
                # Сохраняем график
                self.dynamic_fig.savefig(self.chart_temp_path, dpi=150, bbox_inches='tight')
            except Exception as chart_error:
                print(f"Предупреждение: Не удалось сохранить график для экспорта: {str(chart_error)}")
                self.chart_temp_path = None
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при построении графика: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_prices_from_file(self, target_widget=None):
        """Загружает цены из файла"""
        try:
            # Открываем диалог выбора файла
            file_path = filedialog.askopenfilename(
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
                title="Выберите файл с ценами"
            )
            
            if not file_path:
                return None  # Пользователь отменил выбор
            
            prices = []
            
            # Открываем файл и читаем содержимое
            with open(file_path, 'r') as file:
                content = file.read().strip()
                
                # Если файл содержит запятые, рассматриваем его как список цен, разделенных запятыми
                if ',' in content:
                    # Разделяем по запятым и обрабатываем каждый элемент
                    values = [item.strip() for item in content.split(',')]
                    for value in values:
                        if value and not value.startswith('#'):
                            try:
                                # Преобразуем значение в число с плавающей точкой
                                price = float(value.replace(',', '.'))
                                prices.append(price)
                            except ValueError:
                                # Пропускаем нечисловые значения
                                continue
                else:
                    # Если запятых нет, обрабатываем каждую строку отдельно
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue  # Пропускаем пустые строки и комментарии
                        
                        try:
                            # Преобразуем значение в число с плавающей точкой
                            price = float(line.replace(',', '.'))
                            prices.append(price)
                        except ValueError:
                            # Пропускаем нечисловые значения
                            continue
            
            if not prices:
                messagebox.showwarning("Предупреждение", "В выбранном файле не найдено числовых значений цен")
                return None
            
            print(f"Загружено {len(prices)} цен: {prices}")  # Отладочный вывод
            return prices
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке цен из файла: {str(e)}")
            traceback.print_exc()
            return None

    def load_prices_from_file_and_update(self):
        """Загружает цены из файла и обновляет поля ввода цен на вкладке динамического хеджирования"""
        prices = self.load_prices_from_file()
        
        if prices and len(prices) > 0:
            # Если загружено больше 10 цен, предлагаем использовать массовый режим
            if len(prices) > 10:
                use_bulk = messagebox.askyesno(
                    "Много цен", 
                    f"Загружено {len(prices)} цен. Хотите использовать режим массового ввода для более удобного просмотра?"
                )
                
                if use_bulk:
                    # Переключаемся на режим массового ввода
                    self.price_input_mode.set("bulk")
                    self.toggle_price_input_mode()
                    
                    # Форматируем цены для отображения в текстовом поле
                    # Если цен меньше 50, выводим каждую на новой строке
                    # Иначе выводим через запятую для экономии места
                    if len(prices) < 50:
                        price_text = "\n".join([str(price) for price in prices])
                    else:
                        price_text = ", ".join([str(price) for price in prices])
                    
                    # Очищаем текстовое поле и вставляем цены
                    self.bulk_price_text.delete("1.0", "end")
                    self.bulk_price_text.insert("1.0", price_text)
                    
                    messagebox.showinfo("Успешно", f"Загружено {len(prices)} цен в режиме массового ввода")
                    return True
            
            # Стандартная обработка для режима одиночного ввода
            # Очищаем существующие поля ввода цен
            self.dynamic_price_vars = []
            
            # Удаляем все виджеты из контейнера
            for widget in self.dynamic_price_container.winfo_children():
                widget.destroy()
            
            # Создаем новые поля для каждой цены из файла
            for price in prices:
                price_var = tk.DoubleVar(value=price)
                self.dynamic_price_vars.append(price_var)
            
            # Отображаем поля ввода для загруженных цен
            for i, price_var in enumerate(self.dynamic_price_vars):
                self.create_price_field(i, price_var)
            
            messagebox.showinfo("Успешно", f"Загружено {len(prices)} цен")
            return True
            
        return False

    def calculate_eth_amount(self, current_eth, current_usdc, current_price, new_price, price_range):
        """
        Рассчитывает новое количество ETH в пуле при изменении цены
        с учетом особенностей Uniswap V3
        
        Args:
            current_eth (float): Текущее количество ETH в пуле
            current_usdc (float): Текущее количество USDC в пуле
            current_price (float): Текущая цена ETH в USDC
            new_price (float): Новая цена ETH в USDC
            price_range (dict): Словарь с ключами 'lower' и 'upper' для границ диапазона
            
        Returns:
            float: Новое количество ETH в пуле
        """
        # Используем существующий метод calculate_delta_for_price, который уже правильно
        # рассчитывает ETH с учетом особенностей Uniswap V3
        new_eth = self.calculate_delta_for_price(new_price)
        return new_eth

    def calculate_uniswap_v3_delta(self, price_sqrt, lower_bound_sqrt, upper_bound_sqrt):
        """
        Рассчитывает дельту (чувствительность к изменению цены) для позиции в Uniswap V3
        
        Args:
            price_sqrt (float): Квадратный корень из текущей цены
            lower_bound_sqrt (float): Квадратный корень из нижней границы ценового диапазона
            upper_bound_sqrt (float): Квадратный корень из верхней границы ценового диапазона
            
        Returns:
            float: Значение дельты от 0 до 1
        """
        # За пределами диапазона
        if price_sqrt <= lower_bound_sqrt:
            return 1.0  # 100% ETH
        elif price_sqrt >= upper_bound_sqrt:
            return 0.0  # 0% ETH (все в USDC)
        
        # В пределах диапазона - рассчитываем дельту по формуле
        # Формула для дельты в Uniswap V3: (sqrt(P_upper) - sqrt(P)) / (sqrt(P_upper) - sqrt(P_lower))
        delta = (upper_bound_sqrt - price_sqrt) / (upper_bound_sqrt - lower_bound_sqrt)
        
        return delta

    def export_to_csv(self):
        """
        Экспортирует результаты расчетов в CSV файл
        """
        try:
            # Открываем диалог сохранения файла
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Сохранить результаты в CSV"
            )
            
            if not file_path:
                return  # Пользователь отменил сохранение
            
            # Собираем данные для экспорта в зависимости от текущей активной вкладки
            active_tab = self.tab_control.index(self.tab_control.select())
            
            # Получаем основные параметры из интерфейса
            current_price = float(str(self.current_price.get()).replace(',', '.'))
            lower_bound = float(str(self.lower_bound.get()).replace(',', '.'))
            upper_bound = float(str(self.upper_bound.get()).replace(',', '.'))
            total_pool_value = float(str(self.total_pool_value.get()).replace(',', '.'))
            
            # Рассчитываем ликвидность
            liquidity = total_pool_value / (((1/math.sqrt(current_price) - 1/math.sqrt(upper_bound)) * current_price) + 
                                         (math.sqrt(current_price) - math.sqrt(lower_bound)))
            
            # Получаем комиссию хеджирования
            try:
                hedge_fee_percent = float(str(self.hedge_fee_percent.get()).replace(',', '.')) / 100.0
            except:
                hedge_fee_percent = 0.002  # 0.2% по умолчанию
            
            # Создаем ценовой диапазон для экспорта
            step = (upper_bound - lower_bound) / 50
            price_range = []
            price = max(0.1, lower_bound * 0.75)  # Начинаем с 75% нижней границы, но не меньше 0.1
            while price <= upper_bound * 1.25:  # Заканчиваем на 125% верхней границы
                price_range.append(price)
                price += step
            
            # Собираем данные для каждой цены
            data = []
            
            for price in price_range:
                # Расчет значений базовой позиции в зависимости от цены
                if price < lower_bound:
                    eth = liquidity * (1/math.sqrt(lower_bound) - 1/math.sqrt(upper_bound))
                    usdc = 0
                elif price > upper_bound:
                    eth = 0
                    usdc = liquidity * (math.sqrt(upper_bound) - math.sqrt(lower_bound))
                else:
                    eth = liquidity * (1/math.sqrt(price) - 1/math.sqrt(upper_bound))
                    usdc = liquidity * (math.sqrt(price) - math.sqrt(lower_bound))
                
                base_value = eth * price + usdc
                
                # Расчет значений хеджирующей позиции
                hedge_value = 0
                if self.hedge_enabled.get():
                    hedge_amount = float(str(self.hedge_amount.get()).replace(',', '.'))
                    hedge_price = float(str(self.hedge_price.get()).replace(',', '.'))
                    
                    # P&L хеджа (для шорта ETH)
                    hedge_value = hedge_amount * (hedge_price - price) - (hedge_amount * hedge_price * hedge_fee_percent)
                
                # Общая стоимость позиции
                total_value = base_value + hedge_value
                
                # Добавляем строку с данными
                row = {
                    'Цена': price,
                    'ETH в пуле': eth,
                    'USDC в пуле': usdc,
                    'Стоимость пула': base_value,
                }
                
                if self.hedge_enabled.get():
                    row.update({
                        'P&L хеджа': hedge_value,
                        'Общая стоимость': total_value
                    })
                
                data.append(row)
            
            # Сохраняем данные в CSV
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            
            messagebox.showinfo("Экспорт завершен", f"Данные успешно экспортированы в {file_path}")
        
        except Exception as e:
            messagebox.showerror("Ошибка при экспорте", f"Не удалось экспортировать данные: {str(e)}")
            traceback.print_exc()

    def load_prices_for_simulation(self):
        """Загружает цены из файла для симуляции сеточного хеджирования"""
        prices = self.load_prices_from_file()
        
        if prices and len(prices) > 0:
            # Преобразуем список цен в строку с запятыми
            price_string = ", ".join([str(price) for price in prices])
            
            # Обновляем поле ввода цен для симуляции
            self.sim_prices.delete(0, tk.END)
            self.sim_prices.insert(0, price_string)
            
            messagebox.showinfo("Успешно", f"Загружено {len(prices)} цен для симуляции")
            return True
            
        return False
        
    # Обновляем метод load_prices_and_display для работы с текстовыми полями (Entry)
    def load_prices_and_display(self, text_widget):
        """Загружает цены из файла и устанавливает их в указанное текстовое поле или переменную"""
        prices = self.load_prices_from_file()
        
        if prices and len(prices) > 0:
            # Проверяем тип виджета/переменной
            if isinstance(text_widget, tk.Entry):
                # Для Entry widget - вставляем текст напрямую
                text_widget.delete(0, tk.END)
                text_widget.insert(0, str(prices[0]))
            else:
                # Для StringVar или DoubleVar - устанавливаем через set
                text_widget.set(prices[0])
                
            # Если загружено больше одной цены, спрашиваем пользователя
            if len(prices) > 1:
                use_for_sim = messagebox.askyesno(
                    "Найдено несколько цен", 
                    f"Загружено {len(prices)} цен. Хотите использовать их для симуляции?"
                )
                
                if use_for_sim:
                    # Если текущая вкладка - сеточное хеджирование
                    if self.tab_control.index(self.tab_control.select()) == 2:
                        # Преобразуем список цен в строку с запятыми для симуляции
                        price_string = ", ".join([str(price) for price in prices])
                        self.sim_prices.delete(0, tk.END)
                        self.sim_prices.insert(0, price_string)
                    # Если не сеточное хеджирование, переходим на вкладку динамического хеджирования
                    else:
                        # Переключаемся на вкладку динамического хеджирования
                        self.tab_control.select(3)  # Индекс вкладки динамического хеджирования
                        
                        # Очищаем существующие поля ввода цен
                        self.dynamic_price_vars = []
                        
                        # Удаляем все виджеты из контейнера
                        for widget in self.dynamic_price_container.winfo_children():
                            widget.destroy()
                        
                        # Создаем новые поля для каждой цены из файла
                        for price in prices:
                            price_var = tk.DoubleVar(value=price)
                            self.dynamic_price_vars.append(price_var)
                        
                        # Отображаем поля ввода для загруженных цен
                        for i, price_var in enumerate(self.dynamic_price_vars):
                            self.create_price_field(i, price_var)
            
            messagebox.showinfo("Загрузка завершена", f"Загружено {len(prices)} цен из файла")
            
            # Обновляем расчеты
            self.calculate_only_text()
            
            return True
        
        return False

    def export_dynamic_to_csv(self):
        """Экспортирует результаты динамического хеджирования в CSV файл"""
        try:
            # Проверяем, есть ли результаты для экспорта
            if not hasattr(self, 'dynamic_results') or not self.dynamic_results:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта. Сначала выполните расчет.")
                return
                
            # Открываем диалог сохранения файла
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Сохранить данные как CSV"
            )
            
            if not file_path:
                return  # Пользователь отменил сохранение
                
            # Формируем данные для экспорта
            data = []
            for step_data in self.dynamic_results:
                data.append({
                    'Шаг': step_data.get('step', 0),
                    'Цена': step_data.get('price', 0),
                    'ETH в пуле': step_data.get('pool_eth', 0),
                    'USDC в пуле': step_data.get('pool_usdc', 0),
                    'Стоимость пула': step_data.get('pool_value', 0),
                    'Хедж ETH': step_data.get('hedge_eth', 0),
                    'Дельта': step_data.get('delta', 0),
                    'Изменение хеджа': step_data.get('hedge_change', 0),
                    'Комиссия': step_data.get('fee', 0),
                    'Общая комиссия': step_data.get('total_fee', 0),
                    'P&L хеджа за шаг': step_data.get('hedge_pnl', 0),
                    'Накопленный P&L хеджа': step_data.get('cumulative_hedge_pnl', 0),
                    'P&L базовой позиции': step_data.get('base_pnl', 0),
                    'Общий P&L': step_data.get('total_pnl', 0),
                    'Направление цены': step_data.get('price_direction', ''),
                    'Тип операции': step_data.get('operation_type', '')
                })
                
            # Сохраняем данные в CSV
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            
            messagebox.showinfo("Экспорт завершен", f"Данные успешно экспортированы в {file_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте данных: {str(e)}")
            traceback.print_exc()

    def apply_bulk_prices(self):
        """Применяет цены из текстового поля для массового ввода"""
        try:
            # Получаем текст из текстового поля
            bulk_prices_text = self.bulk_price_text.get("1.0", "end-1c")
            
            # Если текст содержит запятые, разделяем по запятым, иначе по новым строкам
            if ',' in bulk_prices_text:
                # Разделяем по запятым
                parts = bulk_prices_text.split(',')
                price_strings = [part.strip() for part in parts if part.strip()]
            else:
                # Разделяем по строкам
                price_strings = [line.strip() for line in bulk_prices_text.split('\n') if line.strip()]
            
            # Проверяем, что есть хотя бы одна цена
            if not price_strings:
                messagebox.showwarning("Предупреждение", "Не найдено ни одной цены. Введите цены через запятую или каждую с новой строки.")
                return
            
            # Пытаемся преобразовать строки в числа
            prices = []
            for price_str in price_strings:
                try:
                    # Заменяем запятую на точку для корректного преобразования
                    price = float(price_str.replace(',', '.'))
                    prices.append(price)
                except ValueError:
                    # Пропускаем значения, которые не могут быть преобразованы в числа
                    continue
            
            # Проверяем, что есть хотя бы одна действительная цена
            if not prices:
                messagebox.showwarning("Предупреждение", "Не удалось преобразовать ни одну из введенных строк в числа.")
                return
            
            # Очищаем существующие поля
            # Удаляем все переменные
            self.dynamic_price_vars.clear()
            
            # Удаляем все виджеты из контейнера
            for widget in self.dynamic_price_container.winfo_children():
                widget.destroy()
            
            # Создаем новые переменные для каждой цены
            for price in prices:
                price_var = tk.DoubleVar(value=price)
                self.dynamic_price_vars.append(price_var)
            
            # Создаем поля ввода для каждой цены
            for i, price_var in enumerate(self.dynamic_price_vars):
                self.create_price_field(i, price_var)
            
            messagebox.showinfo("Успешно", f"Добавлено {len(prices)} цен")
            
            # Переключаем режим на отображение отдельных полей
            self.price_input_mode.set("single")
            self.bulk_price_container.pack_forget()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при применении цен: {str(e)}")
            traceback.print_exc()

    def toggle_price_input_mode(self):
        """Переключает режим ввода цен"""
        if self.price_input_mode.get() == "single":
            self.price_input_mode.set("bulk")
            self.bulk_price_container.pack(fill="both", expand=True)
        else:
            self.price_input_mode.set("single")
            self.bulk_price_container.pack_forget()
    
    def show_prices_as_table(self):
        """Отображает все цены в виде компактной таблицы с прокруткой"""
        # Создаем новое окно
        table_window = tk.Toplevel(self)
        table_window.title("Список цен")
        table_window.geometry("400x600")
        
        # Создаем фрейм с прокруткой
        frame = ttk.Frame(table_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вертикальная прокрутка
        scrollbar_y = ttk.Scrollbar(frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        
        # Горизонтальная прокрутка
        scrollbar_x = ttk.Scrollbar(frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Создаем виджет Text для таблицы
        price_text = tk.Text(frame, width=50, height=30, wrap="none",
                          xscrollcommand=scrollbar_x.set,
                          yscrollcommand=scrollbar_y.set,
                          font=("Courier New", 10))
        price_text.pack(side="left", fill="both", expand=True)
        
        # Настраиваем прокрутку
        scrollbar_y.config(command=price_text.yview)
        scrollbar_x.config(command=price_text.xview)
        
        # Получаем цены из всех полей
        prices = [var.get() for var in self.dynamic_price_vars]
        
        if not prices:
            price_text.insert("1.0", "Нет данных для отображения")
            return
        
        # Формируем заголовок
        header = f"{'№':^5}|{'Цена':^15}|{'Дельта':^10}\n"
        price_text.insert("1.0", header)
        price_text.insert("2.0", "-" * 32 + "\n")
        
        # Начальная цена для расчета дельты
        start_price = prices[0] if prices else 0
        
        # Добавляем строки с ценами и дельтами
        for i, price in enumerate(prices):
            if i > 0:
                delta = (price - prices[i-1]) / prices[i-1] * 100
                delta_text = f"{delta:+.2f}%"
            else:
                delta_text = "—"
            
            line = f"{i+1:^5}|{price:^15.2f}|{delta_text:^10}\n"
            price_text.insert(f"{i+3}.0", line)
        
        # Добавляем итоговую дельту
        if len(prices) > 1:
            total_delta = (prices[-1] - prices[0]) / prices[0] * 100
            price_text.insert("end", "-" * 32 + "\n")
            price_text.insert("end", f"{'Итого:':^5}|{'':^15}|{total_delta:+.2f}%\n")
        
        # Делаем текст только для чтения
        price_text.config(state="disabled")
        
        # Добавляем кнопки
        button_frame = ttk.Frame(table_window)
        button_frame.pack(fill="x", pady=10)
        
        # Кнопка экспорта в CSV
        ttk.Button(button_frame, text="Экспорт в CSV", 
                 command=self.export_prices_to_csv).pack(side="left", padx=5)
        
        # Кнопка закрытия
        ttk.Button(button_frame, text="Закрыть", 
                 command=table_window.destroy).pack(side="right", padx=5)
    
    def export_prices_to_csv(self):
        """Экспортирует только последовательность цен в CSV файл"""
        try:
            # Получаем цены
            prices = [var.get() for var in self.dynamic_price_vars]
            
            if not prices:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
                return
            
            # Открываем диалог сохранения файла
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Сохранить цены в CSV"
            )
            
            if not file_path:
                return  # Пользователь отменил сохранение
            
            # Формируем DataFrame
            df = pd.DataFrame({
                'Номер': range(1, len(prices) + 1),
                'Цена': prices
            })
            
            # Добавляем дельту, если есть хотя бы 2 цены
            if len(prices) > 1:
                deltas = [0] + [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]
                df['Дельта (%)'] = deltas
            
            # Сохраняем в CSV
            df.to_csv(file_path, index=False)
            
            messagebox.showinfo("Экспорт завершен", f"Данные успешно экспортированы в {file_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте данных: {str(e)}")
            traceback.print_exc()

    def clear_all_price_fields(self):
        """Очищает все поля цен и сбрасывает результаты"""
        try:
            # Удаляем все поля ввода цен
            for widget in self.dynamic_price_container.winfo_children():
                widget.destroy()
            
            # Очищаем список переменных цен
            self.dynamic_price_vars.clear()
            
            # Очищаем результаты
            self.dynamic_results = []
            self.dynamic_results_text.delete(1.0, tk.END)
            
            # Сбрасываем итоговые значения
            for key in self.summary_vars:
                if key == "delta":
                    self.summary_vars[key].set("0.0000")
                else:
                    self.summary_vars[key].set("0.00")
            
            # Очищаем текстовое поле для массового ввода
            self.bulk_price_text.delete(1.0, tk.END)
            
            # Добавляем новое первое поле для ввода
            price1 = tk.DoubleVar(value=0)
            self.dynamic_price_vars.append(price1)
            self.create_price_field(0, price1)
            
            # Выводим сообщение об успешной очистке
            messagebox.showinfo("Очистка", "Все значения цен были успешно очищены")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при очистке значений: {str(e)}")

if __name__ == "__main__":
    app = UniswapV3HedgeCalculator()
    app.mainloop() 