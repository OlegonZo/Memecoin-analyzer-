# Memecoin Signal Analyzer

A Solana memecoin scanner that identifies early smart-money accumulation and generates buy/exit alerts via Telegram.

## Overview

This bot scans newly launched and low-cap Solana memecoins, tracking on-chain activity to detect when "smart wallets" are accumulating positions. It filters out noise (dust positions, bots) and surfaces tokens showing genuine smart-money interest in the early FDV range.

## Features

- Scans Solana memecoins in the 30k–500k FDV range
- Smart wallet accumulation detection with dust filtering
- Weighted position scoring to validate signal quality
- BUY / EXIT alerts delivered via Telegram
- Liquidity and volume gating to avoid illiquid traps
- Entry-timing analysis to assess how early a signal is

## Tech Stack

- **Language:** Python
- **Database:** SQLite
- **Data Sources:** DexScreener, Helius (Solana on-chain data)
- **Alerts:** Telegram Bot API

## Architecture

1. Pull new and trending tokens from DexScreener
2. Fetch on-chain wallet activity via Helius
3. Filter out dust and low-value positions
4. Score tokens by weighted smart-wallet accumulation
5. Apply liquidity and volume gates
6. Send actionable BUY/EXIT alerts to Telegram

## Status

In active development — refining signal frequency, Sybil detection, and threshold calibration via backtesting.

---

*Code and signal logic kept private. Architecture and methodology available for discussion in interviews.*
