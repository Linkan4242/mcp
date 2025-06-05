import math
import time
import asyncio
from pathlib import Path

import aiohttp
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from qiskit.circuit.library import RealAmplitudes
from qiskit_aer import AerSimulator
from qiskit.primitives import Sampler
from qiskit_machine_learning.algorithms import VQC
from qiskit_algorithms.optimizers import COBYLA

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "SOLUSDT",
    "DOGEUSDT",
    "LTCUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "TRXUSDT",
]

INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]
LIMIT = 1000  # max rows per API call
ROWS = 3000  # rows we want per file (~2 days on 1m)
ROOT = Path("klines")
ROOT.mkdir(exist_ok=True)

np.random.seed(42)
simulator = AerSimulator()
sampler = Sampler()

# ----------------------------------------------------------------------------
# Helpers for downloading kline data
# ----------------------------------------------------------------------------
async def _page(session: aiohttp.ClientSession, symbol: str, interval: str, rows: int = ROWS) -> pd.DataFrame:
    """Fetch a single set of klines with pagination."""
    url = "https://api.mexc.com/api/v3/klines"
    end = int(time.time() * 1000)
    out = []

    while len(out) < rows:
        query = f"?symbol={symbol}&interval={interval}&limit={LIMIT}&endTime={end}"
        resp = await session.get(url + query, timeout=8)
        batch = await resp.json()
        if not batch:
            break
        out = batch + out
        end = batch[0][0] - 1
        if len(batch) < LIMIT:
            break

    cols = [
        "ts",
        "open",
        "high",
        "low",
        "close",
        "vol",
        "close_ts",
        "qvol",
        "trades",
        "tbbav",
        "tbqav",
        "ignore",
    ]
    df = pd.DataFrame(out, columns=cols).astype({"close": float})
    return df.sort_values("ts")


async def download_all() -> None:
    """Download kline data for all symbols and intervals."""
    async with aiohttp.ClientSession() as session:
        coros = [_page(session, s, i) for s in SYMBOLS for i in INTERVALS]
        results = await asyncio.gather(*coros)

    for (symbol, interval), df in zip([(s, i) for s in SYMBOLS for i in INTERVALS], results):
        csv_path = ROOT / f"{symbol}_{interval}.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ {symbol}-{interval} rows={len(df)}")


# ----------------------------------------------------------------------------
# Quantum model helpers
# ----------------------------------------------------------------------------

def norm8(v: np.ndarray) -> np.ndarray:
    """Normalize a length-8 vector to the range [0,1] with L2 norm 1."""
    vv = (v - v.min()) / (v.max() - v.min())
    return vv / np.linalg.norm(vv)


def vqc() -> VQC:
    """Construct a small variational quantum classifier."""
    return VQC(
        num_qubits=3,
        feature_map=RealAmplitudes(3, reps=1),
        ansatz=RealAmplitudes(3, reps=2),
        optimizer=COBYLA(maxiter=60),
        sampler=sampler,
    )


# ----------------------------------------------------------------------------
# Backtesting logic
# ----------------------------------------------------------------------------

def backtest() -> None:
    """Run a simple backtest using previously downloaded data."""
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            csv_path = ROOT / f"{symbol}_{interval}.csv"
            if not csv_path.exists():
                continue

            close = pd.read_csv(csv_path)["close"].astype(float).values
            if len(close) < 40:
                continue

            scaled = (close - close.min()) / (close.max() - close.min())
            diff = np.diff(close)

            X, Y, R = [], [], []
            for i in range(len(diff) - 7):
                X.append(norm8(scaled[i : i + 8]))
                Y.append(int(diff[i + 7] > 0))
                R.append(diff[i + 7] / close[i + 7])

            X = np.array(X)
            Y = np.array(Y)
            R = np.array(R)

            if len(X) < 40:
                continue

            split = int(0.8 * len(X))
            model = vqc()
            model.fit(X[:split], Y[:split])
            pred = model.predict(X[split:])

            acc = (pred == Y[split:]).mean()
            pnl = np.cumsum(R[split:] * (pred * 2 - 1))
            sharpe = pnl.mean() / (pnl.std() + 1e-9) * math.sqrt(len(pnl))

            print(f"{symbol}-{interval}  acc={acc:.2f}  sharpe={sharpe:.2f}")

            if interval in ["1h", "4h", "1d"]:
                plt.figure(figsize=(4, 2))
                plt.plot(pnl)
                plt.title(f"{symbol}-{interval} PnL")
                plt.show()


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quantum backtesting utilities")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download fresh kline data before running the backtest",
    )
    args = parser.parse_args()

    if args.download:
        asyncio.run(download_all())

    backtest()
