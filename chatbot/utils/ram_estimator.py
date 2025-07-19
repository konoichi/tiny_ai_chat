"""
/chatbot/utils/ram_estimator.py
Version: 1.0.0
------------------------------
Schätzt RAM/VRAM-Bedarf basierend auf Quantisierung + Kontext.

Autor: Stephan Wilkens / Abby-System
Stand: Juli 2025
"""

# Heuristische Werte pro Token bei 4096 Kontext
# Quelle: Erfahrungswerte aus llama.cpp-Profiling
QUANT_RAM_MB = {
    "Q2_K": 2500,
    "Q3_K_S": 3100,
    "Q4_0": 3500,
    "Q4_K_M": 3900,
    "Q5_0": 4500,
    "Q5_K_M": 4900,
    "Q6_K": 5500,
    "Q8_0": 8000
}


def estimate_ram(quant: str, context: int = 4096) -> int:
    if not quant:
        return 0
    base = QUANT_RAM_MB.get(quant.upper(), 0)
    scale = context / 4096
    return int(base * scale)


def format_ram_info(quant: str, context: int = 4096) -> str:
    mb = estimate_ram(quant, context)
    if mb == 0:
        return "unbekannt"
    return f"~{mb // 1024}.{mb % 1024 // 100} GB RAM"
