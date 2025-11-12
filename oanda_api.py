#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OANDA API Connector
اتصال به OANDA برای دریافت داده‌های فارکس
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class OandaAPI:
    """کلاس اتصال به OANDA API"""

    def __init__(self, api_token: str, environment: str = 'practice'):
        """
        مقداردهی اولیه

        Args:
            api_token: توکن API از OANDA
            environment: 'practice' یا 'live'
        """
        self.api_token = api_token
        self.environment = environment

        # تعیین URL بر اساس environment
        if environment == 'practice':
            self.api_url = 'https://api-fxpractice.oanda.com'
        else:
            self.api_url = 'https://api-fxtrade.oanda.com'

        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }

    def test_connection(self) -> bool:
        """
        تست اتصال به OANDA

        Returns:
            True اگر اتصال موفق بود
        """
        try:
            url = f'{self.api_url}/v3/accounts'
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'accounts' in data and len(data['accounts']) > 0:
                    print(f"✅ اتصال به OANDA برقرار شد")
                    print(f"   Account: {data['accounts'][0]['id']}")
                    return True
            else:
                print(f"❌ خطا: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ خطا در اتصال: {e}")
            return False

    def fetch_candles(self, instrument: str = 'AUD_USD', granularity: str = 'H1',
                     count: int = 500) -> Optional[pd.DataFrame]:
        """
        دریافت کندل‌های تاریخی

        Args:
            instrument: نماد (مثل AUD_USD)
            granularity: بازه زمانی (H1 = 1 hour)
            count: تعداد کندل‌ها

        Returns:
            DataFrame حاوی داده‌های OHLCV
        """
        try:
            url = f'{self.api_url}/v3/instruments/{instrument}/candles'
            params = {
                'granularity': granularity,
                'count': count
            }

            print(f"📥 دریافت {count} کندل {granularity} برای {instrument}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            if response.status_code != 200:
                print(f"❌ خطا: {response.status_code} - {response.text}")
                return None

            data = response.json()

            if 'candles' not in data:
                print("❌ داده‌ای دریافت نشد")
                return None

            # تبدیل به DataFrame
            candles = []
            for candle in data['candles']:
                if not candle['complete']:
                    continue  # فقط کندل‌های کامل

                candles.append({
                    'timestamp': pd.to_datetime(candle['time']),
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': int(candle['volume'])
                })

            df = pd.DataFrame(candles)
            df.set_index('timestamp', inplace=True)

            print(f"✅ دریافت {len(df)} کندل")
            print(f"   از {df.index[0]} تا {df.index[-1]}")
            print(f"   قیمت شروع: {df.iloc[0]['close']:.5f} | قیمت پایان: {df.iloc[-1]['close']:.5f}")

            return df

        except Exception as e:
            print(f"❌ خطا در دریافت داده: {e}")
            return None


if __name__ == '__main__':
    # تست اتصال
    api_token = 'dd81e6f027e604f8f213ee371aff985acb-91d76fd9d01e79cd02632684a06d7b89'

    oanda = OandaAPI(api_token, environment='practice')

    # تست اتصال
    if oanda.test_connection():
        # دریافت داده
        df = oanda.fetch_candles('AUD_USD', 'H1', 100)
        if df is not None:
            print(f"\n📊 نمونه داده:")
            print(df.head())
