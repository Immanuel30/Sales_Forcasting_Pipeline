from datetime import datetime, timedelta
import random
from typing import List
import numpy as np
import pandas as pd
import holidays
import os
import logging
import sys



logger = logging.getLogger(__name__)


def last_day_of_month(month, year=None):
    """Returns the last day of the given month for the specified year (defaults to current year)."""
    if year is None:
        year = pd.Timestamp.now().year
    if month == 12:
        return pd.Timestamp(year, month, 31)
    else:
        return pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)

def first_day_of_month(month, year=None):
    """Returns the first day of the given month for the specified year (defaults to current year)."""
    if year is None:
        year = pd.Timestamp.now().year
    return pd.Timestamp(year, month, 1)

class USData:
    def __init__(self):
        self.holidays = holidays.US()


class RealisticSalesDataGenerator:
    def __init__(self, start_date="2024-01-01", end_date="2025-10-08"):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.us = USData() 

        self.us.holidays = holidays.US()

        self.stores = {
            "stote_001": {"location": "New York", "size": 'large', 'base_traffic': 1000},
            "store_002": {"location": "Los Angeles", "size": 'large', 'base_traffic': 950},
            "store_003": {"location": "Chicago", "size": 'medium', 'base_traffic': 800},
            "store_004": {"location": "Houston", "size": 'medium', 'base_traffic': 650},
            "store_005": {"location": "Phoenix", "size": 'small', 'base_traffic': 400},
            "store_006": {"location": "Philadelphia", "size": 'medium', 'base_traffic': 600},
            "store_007": {"location": "San Antonio", "size": 'small', 'base_traffic': 350},
            "store_008": {"location": "San Diego", "size": 'medium', 'base_traffic': 550},
            "store_009": {"location": "Dallas", "size": 'large', 'base_traffic': 850},
            "store_010": {"location": "Miami", "size": 'medium', 'base_traffic': 600},
        }
        
        self.products_categories = {
            "Electronics": {
                'Elec_001': {'name': 'Smartphone', 'price': 699, 'margin':0.15, 'seasonality': 'holidays'},
                'Elec_002': {'name': 'Laptop', 'price': 999, 'margin':0.10, 'seasonality': 'back_to_school'},
                'Elec_003': {'name': 'Headphones', 'price': 199, 'margin':0.20, 'seasonality': 'holidays'},
                'Elec_004': {'name': 'Smartwatch', 'price': 299, 'margin':0.18, 'seasonality': 'holidays'},
                'Elec_005': {'name': 'Tablet', 'price': 499, 'margin':0.12, 'seasonality': 'back_to_school'},
            },

            "Clothing": {
                'Cloth_001': {'name': 'Jeans', 'price': 59, 'margin':0.40, 'seasonality': 'summer'},
                'Cloth_002': {'name': 'T-Shirt', 'price': 25, 'margin':0.50, 'seasonality': 'summer'},
                'Cloth_003': {'name': 'Jacket', 'price': 120, 'margin':0.35, 'seasonality': 'winter'},
                'Cloth_004': {'name': 'Sneakers', 'price': 80, 'margin':0.30, 'seasonality': 'back_to_school'},
                'Cloth_005': {'name': 'Dress', 'price': 70, 'margin':0.45, 'seasonality': 'summer'},
            },

            "Home Goods": {
                'Home_001': {'name': 'Blender', 'price': 150, 'margin':0.25, 'seasonality': 'holidays'},
                'Home_002': {'name': 'Vacuum Cleaner', 'price': 200, 'margin':0.22, 'seasonality': 'holidays'},
                'Home_003': {'name': 'Coffee Maker', 'price': 100, 'margin':0.30, 'seasonality': 'holidays'},
                'Home_004': {'name': 'Air Fryer', 'price': 120, 'margin':0.28, 'seasonality': 'holidays'},
                'Home_005': {'name': 'Toaster', 'price': 40, 'margin':0.35, 'seasonality': None},
            },

            "Sports": {
                'Sport_001': {'name': 'Running Shoes', 'price': 90, 'margin':0.30, 'seasonality': 'summer'},
                'Sport_002': {'name': 'Yoga Mat', 'price': 40, 'margin':0.50, 'seasonality': None},
                'Sport_003': {'name': 'Dumbbell Set', 'price': 150, 'margin':0.25, 'seasonality': None},
                'Sport_004': {'name': 'Bicycle', 'price': 300, 'margin':0.20, 'seasonality': 'summer'},
                'Sport_005': {'name': 'Tennis Racket', 'price': 120, 'margin':0.30, 'seasonality': 'summer'},
            },
        }   

        self.all_products = {}
        for category, products in self.products_categories.items():
            for product_id, product_info in products.items():
                self.all_products[product_id] = {
                    **product_info,
                    'category': category,  
                }
        
    def get_day_of_week_factor(self, date: pd.Timestamp) -> float: 
        dow = date.dayofweek
        dow_factors = [0.9] * 5 + [1.2, 1.3]  # Mon-Fri:0.9, Sat:1.2, Sun:1.3
        return dow_factors[dow]



    def generate_promotions(self) -> pd.DataFrame:
        promotions = []
        promo_id = 1
        
        major_events = [
            ('Black Friday', 11, 4, 5, 25),  # Fourth Friday in November, 5 days, 25% off
            ('Labor Day Sale', 9, 1, 3, 20), # First Monday in September, 3 days, 20% off
            ('Christmas Sale', 12, 25, 7, 15), # Dec 25th, 7 days, 15% off
            ('New Year Sale', 1, 1, 7, 10), # Jan 1st, 7 days, 10% off
            ('Presidents Day Sale', 2, 3, 3, 20), # Third Monday in February, 3 days, 20% off
            ('Memorial Day Sale', 5,  last_day_of_month(5).day - 6, 3, 15), # Last Monday in May, 3 days, 15% off
            ('Independence Day Sale', 7, 4, 3, 15), # July 4th, 3 days, 15% off
            ('Labor Day Sale', 9,  first_day_of_month(9).day + 1, 3, 20), # First Monday in September, 3 days, 20% off
        ]

        current_date = self.start_date
        while current_date <= self.end_date:
            year = current_date.year

            for event_name, month, day, duration, discount in major_events:
                if event_name == 'Black Friday':
                    november = pd.Timestamp (year, 11, 1)
                    thursday = pd.date_range(november, november+timedelta(30), freq='W-THU')
                    event_date = thursday[3] + timedelta(days=1)  # Fourth Friday
                else:
                    try:
                        event_date = pd.Timestamp(year, month, day)
                    except ValueError:
                        continue
                    if self.start_date <= event_date <= self.end_date:
                        for d in range(duration):
                            promo_date = event_date + timedelta(days=d)
                            if promo_date <= self.end_date:
                                promo_products = random.sample(list(self.all_products.keys()), k=random.randint(5, 15))

                                for product_id in promo_products:
                                    promotions.append({
                                        'product_id': product_id,
                                        'date': promo_date,
                                        'discount_percent': discount,
                                        'promotion_type': f'{event_name}'
                                    })
            current_date += pd.DateOffset(years=1)

        n_flash_sales = int(((self.end_date - self.start_date).days * 0.05))  # 5% of days have flash sales
        flash_dates = pd.date_range(self.start_date, self.end_date, periods=n_flash_sales)

        for date in flash_dates:
            promo_products = random.sample(list(self.all_products.keys()), k=random.randint(3, 8))
            for product_id in promo_products:
                promotions.append({
                    'product_id': product_id,
                    'date': date,
                    'discount_percent': random.uniform(0.1, 0.3),  # 10% to 30% off
                    'promotion_type': 'Flash Sale'
                })
            return pd.DataFrame(promotions)


    def generate_store_events(self) -> pd.DataFrame:
        events = []
        for store_id, store_info in self.stores.items():
            n_closures = random.randint(2, 5)
            closure_dates = pd.date_range(self.start_date, self.end_date, periods=n_closures)

            for date in closure_dates:
                events.append({
                    'store_id': store_id,
                    'date': date,
                    'event_type': 'Store Closure',
                    'impact': -1.0,  # 100% reduction in sales
                })

            #Store renovations(longer impact)
            if random.random() < 0.3:  # 30% chance of renovation   
                renovation_start = date + timedelta(days=random.randint(100, 600))  # Renovation starts 1-6 months after a closure
                renovation_duration = random.randint(7, 30)  # Renovation lasts between 1 week to 1 month
                for d in range((self.end_date - renovation_start).days):
                    reno_date = renovation_start + timedelta(days=d)
                    if reno_date <= self.end_date:
                        events.append({
                            'store_id': store_id,
                            'date': reno_date,
                            'event_type': 'renovation',
                            'impact': -0.3,  # 30% drop in sales during renovation
                        })
        
        return pd.DataFrame(events) 


    def generate_sales_data(self, output_dir: str = 'tmp/sales_data') -> dict[str, List[str]]: 
        os.makedirs(output_dir, exist_ok=True)
        
        #Generate supplementary data
        promotions_df = self.generate_promotions()
        store_events_df = self.generate_store_events()


        file_paths = {
            'sales': [],
            'inventory': [],
            'customer_traffic': [],
            'promotions': [],
            'store_events': [],
        }

        #supplementary data
        promotions_path = os.path.join(output_dir, 'promotions/promotions.parquet')
        os.makedirs(os.path.dirname(promotions_path), exist_ok=True)
        promotions_df.to_parquet(promotions_path, index=False)
        file_paths['promotions'].append(promotions_path)

        events_path = os.path.join(output_dir, 'store_events/store_events.parquet')
        os.makedirs(os.path.dirname(events_path), exist_ok=True)    
        store_events_df.to_parquet(events_path, index=False)
        file_paths['store_events'].append(events_path)

        #Generate daily sales data
        current_date = self.start_date
        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Generating sales data for {date_str}...")

            #daily sales data for stores
            daily_sales_data = []
            daily_traffic_data = []
            daily_inventory_data = []

            for store_id, store_info in self.stores.items():
                base_traffic = store_info['base_traffic']

                #date factors
                dow_factor = self.get_day_of_week_factor(current_date)
                is_holiday = current_date in self.us.holidays
                holiday_factor = 1.3 if is_holiday else 1.0

                #weather impact(random)
                weather_factor = np.random.normal(1.0, 0.1)  # Normal distribution around 1.0
                wether_factor = max(0.7, min(weather_factor, 1.3))  # Clamp between 0.7 and 1.3

                #check for store events
                store_event_impact = 1.0
                if store_events_df.empty:
                    event = store_events_df[
                        (store_events_df['store_id'] == store_id) & 
                        (store_events_df['date'] == current_date)
                    ]

                    if not event.empty:
                        store_event_impact = 1.0 + event['impact'].values[0]  # e.g., -1.0 for closure, -0.3 for renovation 

                #calculate store traffic
                store_traffic = int(base_traffic * dow_factor * holiday_factor * weather_factor * store_event_impact * random.uniform(0.9, 1.1))


                daily_traffic_data.append({
                    'store_id': store_id,   
                    'date': current_date,
                    'customer_traffic': store_traffic,
                    'weather_impact': weather_factor,
                    'is_holiday': is_holiday,   
                })

                #generate product level sales
                for product_id, product_info in self.all_products.items():
                   #seasonality factor
                   seasonality = 1.0
                   if product_info['seasonality'] == 'holidays':
                       seasonality_factor = holiday_factor
                   elif product_info['seasonality'] == 'back_to_school':
                       seasonality_factor = dow_factor
                   elif product_info['seasonality'] == 'summer':
                       seasonality_factor = 1.2 if current_date.month in [6, 7, 8] else 0.8
                   elif product_info['seasonality'] == 'winter':
                       seasonality_factor = 1.2 if current_date.month in [12, 1, 2] else 0.8


                   #check for promotions
                   promotion_factor = 1.0
                   discount_percent = 0.0
                   if not promotions_df.empty:
                        promo = promotions_df[
                            (promotions_df['product_id'] == product_id) & 
                            (promotions_df['date'] == current_date)
                        ]
                        if not promo.empty:
                            discount_percent = promo['discount_percent'].values[0]
                            promotion_factor += discount_percent / 100.0  # e.g., 20% discount -> 1.2x sales

                    # sales quantity
                size_factor = {'small': 0.5, 'medium': 0.7, 'large': 1.0}[store_info['size']]
                price_factor = 1.0 / (1 + (product_info['price'] / 1000))  # Higher price -> lower sales

                base_quantity = store_traffic * 0.05 * size_factor * price_factor  # 5% of traffic might buy something

                quantity = int(
                    base_quantity * seasonality_factor * promotion_factor * random.uniform(1.0, 0.2)
                )
                quantity = max(0, quantity)  # Ensure no negative sales

                #calculate revenue
                actual_price = product_info['price'] * (1 - discount_percent)
                revenue = round(quantity * actual_price, 2)
                cost = round(quantity * (1 - product_info['margin']), 2)

                

                 #record sales if quantity > 0
                if quantity > 0:
                    daily_sales_data.append({
                        'date': current_date,
                        'store_id': store_id,
                        'product_id': product_id,
                        'category': product_info['category'],
                        'quantity_sold': quantity,
                        'unit_price': product_info['price'],
                        'revenue': revenue,
                        'cost': cost,
                        'discount_percent': discount_percent,
                        'profit': revenue - cost,
                    })

                    #inventory tracking
                inventory_level = random.randint(50, 200)
                reorder_point = random.randint(20, 50)

                daily_inventory_data.append({
                    'date': current_date,
                    'store_id': store_id,
                    'product_id': product_id,
                    'inventory_level': inventory_level,
                    'reorder_point': reorder_point,
                    'days_of_supply': inventory_level / (max(1, quantity))
                })

            #Save daily data with proper partitioning
            if daily_sales_data:
                sales_df = pd.DataFrame(daily_sales_data)
                sales_path = os.path.join(output_dir, f'sales/year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/sales_{date_str}.parquet')
                os.makedirs(os.path.dirname(sales_path), exist_ok=True)
                sales_df.to_parquet(sales_path, index=False)
                file_paths['sales'].append(sales_path)

            #customer traffic data
            if daily_traffic_data:
                traffic_df = pd.DataFrame(daily_traffic_data)
                traffic_path = os.path.join(output_dir, f'customer_traffic/year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/traffic_{date_str}.parquet')
                os.makedirs(os.path.dirname(traffic_path), exist_ok=True)
                traffic_df.to_parquet(traffic_path, index=False)
                file_paths['customer_traffic'].append(traffic_path)

            #inventory data
            if daily_inventory_data and current_date.dayofweek == 6:  # Save inventory data weekly (on Sundays)
                inventory_df = pd.DataFrame(daily_inventory_data)
                inventory_path = os.path.join(output_dir, f'inventory/year={current_date.year}/month={current_date.month:02d}/day={current_date.day:02d}/inventory_{date_str}.parquet')
                os.makedirs(os.path.dirname(inventory_path), exist_ok=True)
                inventory_df.to_parquet(inventory_path, index=False)
                file_paths['inventory'].append(inventory_path)

            #move to next day
            current_date = current_date + timedelta(days=1)

        metadata_in = {
            'generation_date': datetime.now().isoformat(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'total_stores': len(self.stores),
            'total_products': len(self.all_products),
            'file_count': {k: len(v) for k, v in file_paths.items()},
            'total_files': sum(len(v) for v in file_paths.values()),

        }

        metadata_df = pd.DataFrame([metadata_in])
        metadata_path = os.path.join(output_dir, 'metadata/generation_metadata.parquet')
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        metadata_df.to_parquet(metadata_path, index=False)

        logger.info(f"Generated sales date for {len(file_paths['sales'])} days")
        logger.info(f"Sales files: {len(file_paths['sales'])}, " )
        logger.info(f"Output directory: {output_dir}")

        return file_paths