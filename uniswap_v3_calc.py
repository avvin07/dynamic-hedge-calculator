import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import math

class UniswapV3Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Калькулятор Uniswap V3")
        self.geometry("900x700")
        self.configure(bg="#f0f0f0")
        
        # Initialize variables
        self.current_price = tk.DoubleVar(value=1616)
        self.lower_bound = tk.DoubleVar(value=1550)
        self.upper_bound = tk.DoubleVar(value=2200)
        self.total_pool_value = tk.DoubleVar(value=10000)
        
        # Create the GUI
        self.create_widgets()
        
        # Initial calculation
        self.calculate()
    
    def create_widgets(self):
        # Create input frame
        input_frame = ttk.LabelFrame(self, text="Входные параметры", padding=10)
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
        
        # Calculate button
        ttk.Button(input_frame, text="Рассчитать", command=self.calculate).grid(row=3, column=1, pady=10)
        
        # Create results frame
        self.results_frame = ttk.LabelFrame(self, text="Результаты расчетов", padding=10)
        self.results_frame.pack(fill="x", padx=20, pady=10)
        
        # Results
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
        
        # Create plot frame
        self.plot_frame = ttk.LabelFrame(self, text="Визуализация диапазона ликвидности", padding=10)
        self.plot_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create matplotlib figure with subplots
        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.ax1 = self.figure.add_subplot(211)  # Верхний график для ETH и USDC
        self.ax2 = self.figure.add_subplot(212)  # Нижний график для общей ценности
        self.figure.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def calculate(self):
        try:
            current_price = self.current_price.get()
            lower_bound = self.lower_bound.get()
            upper_bound = self.upper_bound.get()
            total_pool_value = self.total_pool_value.get()
            
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
            
            # Update plot
            self.plot_liquidity_range(current_price, lower_bound, upper_bound, liquidity)
            
        except Exception as e:
            print(f"Error in calculation: {e}")
    
    def plot_liquidity_range(self, current_price, lower_bound, upper_bound, liquidity):
        self.ax1.clear()
        self.ax2.clear()
        
        # Create price range for x-axis
        price_range = np.linspace(lower_bound * 0.9, upper_bound * 1.1, 1000)
        
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
        
        # Отмечаем границы и текущую цену на обоих графиках
        v1 = self.ax1.axvline(x=lower_bound, color='gray', linestyle='--')
        v2 = self.ax1.axvline(x=upper_bound, color='gray', linestyle='--')
        v3 = self.ax1.axvline(x=current_price, color='black', linestyle='-')
        
        # То же для правой оси
        ax1_right.axvline(x=lower_bound, color='gray', linestyle='--')
        ax1_right.axvline(x=upper_bound, color='gray', linestyle='--')
        ax1_right.axvline(x=current_price, color='black', linestyle='-')
        
        # Отмечаем на втором графике
        self.ax2.axvline(x=lower_bound, color='gray', linestyle='--')
        self.ax2.axvline(x=upper_bound, color='gray', linestyle='--')
        self.ax2.axvline(x=current_price, color='black', linestyle='-')
        
        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)
        
        # Объединяем линии для общей легенды на верхнем графике
        lines = l1 + l2 + [v1, v3]
        labels = ['ETH', 'USDC', 'Границы диапазона', 'Текущая цена']
        self.ax1.legend(lines, labels, loc='best', fontsize=9)
        
        # Устанавливаем подписи для верхнего графика
        self.ax1.set_title('Количество ETH и USDC', fontsize=12, fontweight='bold')
        
        # График 2: Общая ценность
        l3 = self.ax2.plot(price_range, total_values, linewidth=2, label='Общая стоимость (USDC)', color='#d62728')
        
        # Устанавливаем подписи для нижнего графика
        self.ax2.set_title('Общая стоимость позиции', fontsize=12, fontweight='bold')
        self.ax2.set_xlabel('Цена (USDC за ETH)', fontsize=10)
        self.ax2.set_ylabel('Стоимость (USDC)', fontsize=10)
        
        # Легенда для нижнего графика
        self.ax2.legend(['Общая стоимость (USDC)', 'Границы диапазона', 'Текущая цена'], loc='best', fontsize=9)
        
        # Выравниваем макет
        self.figure.tight_layout()
        
        # Draw the plot
        self.canvas.draw()

if __name__ == "__main__":
    app = UniswapV3Calculator()
    app.mainloop() 