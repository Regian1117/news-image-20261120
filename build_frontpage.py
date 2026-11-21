#!/usr/bin/env python3
"""Render the 1024x1024 Friday 20 November 2026 world-news front page."""

from __future__ import annotations

import argparse
import html
import os
import re
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
MAX_BYTES = 1_048_576
CANVAS_SIZE = 1024

REGION_COLORS = {
    "Europe": "#1D4ED8",
    "Asia-Pacific": "#0D9488",
    "Middle East": "#B45309",
    "Africa": "#991B1B",
    "Latin America": "#7C3AED",
    "Oceania": "#0369A1",
    "Global": "#334155",
}

STATUS_COLORS = {
    "REPORTED": "#1D4ED8",
    "CONFIRMED": "#047857",
    "OFFICIAL": "#0F766E",
    "CLAIM": "#B45309",
}

UTC_MILESTONES = [
    ("02:00", "Odisha 372k evac"),
    ("04:30", "Kyiv 9 dead"),
    ("05:30", "Taiwan -6.2%"),
    ("12:00", "China rocket"),
    ("13:30", "EU\u2013UK pact"),
    ("17:00", "COP31 stalls"),
    ("21:00", "Peru M 6.7"),
]

EXCLUDED_OTHER_DAYS = [
    ("Orbit burn: BepiColombo", "Sat 21 Nov"),
    ("Prior day: Xi\u2013Putin\u2013Trump talks", "Thu 19 Nov"),
    ("Prior day: ICJ Myanmar ruling", "Thu 19 Nov"),
    ("Prior day: Anthropic $81B IPO", "Thu 19 Nov"),
    ("Prior days: GTA VI & Voyager 1", "18\u201319 Nov"),
]

BRIEF_COL_A = [
    ("CN", "China", False, "Long March launches 30th internet-sat batch"),
    ("JP", "Japan", False, "Oct CPI rises 2.3%, lifting BoJ hike bets"),
    ("KR", "South Korea", False, "Democrats seek Chief Justice ouster"),
    ("ID", "Indonesia", False, "Passes 18-yr Asset Forfeiture Law"),
    ("PK", "India\u2013Pak.", False, "Pakistan minister joins Delhi SCO talks"),
    ("TW", "Taiwan", True, "Flags 2,700 Meta election accounts"),
    ("NZ", "NZ Cricket", False, "Glenn Phillips hits 118 vs India in Test"),
    ("GB", "UK Retail", False, "Sales rise 0.7% on 'Be Ready' stockpiling"),
    ("EU", "ECB Lagarde", False, "Warns AI cyber risks threaten finance"),
    ("EE", "Estonia", False, "Moves to shut Russia border road Dec 1"),
    ("US", "Formula 1", False, "Wet practice opens Las Vegas finale"),
    ("DE", "Germany", False, "Students march nationwide vs draft plan"),
    ("AI", "Anthropic", True, "AI-assisted Riemann proof posted"),
]

BRIEF_COL_B = [
    ("YE", "Yemen", False, "Saudi-led strikes hit Hodeidah & Sanaa"),
    ("IR", "Hormuz", True, "Oil tanker ablaze; Iran claims mine"),
    ("UN", "Vienna / IAEA", False, "US & Europe press Iran on monitors"),
    ("LB", "Lebanon", False, "Israeli strikes hit Nabatieh & Beqaa"),
    ("SD", "Sudan", True, "Rebels say they seized Blue Nile town"),
    ("ET", "Ethiopia", False, "Border clashes displace 700,000 (UN)"),
    ("NG", "Nigeria", False, "Bayelsa funeral boat capsizes; 4 dead"),
    ("SN", "Senegal", False, "16th Dakar Biennale & migration pact"),
    ("UN", "UNICEF", False, "Children's Day AI rights pledge"),
    ("US", "US Courts", False, "Judge blocks 250-ft victory arch"),
    ("US", "Los Angeles", False, "M 4.4 quake hits Commerce; no damage"),
    ("SV", "El Salvador", False, "Bukele files for 3rd presidential term"),
    ("UN", "UN / WFP", False, "Warns 266 million face acute hunger"),
]


def svg_hero_kyiv() -> str:
    return """<svg viewBox="0 0 316 146" preserveAspectRatio="xMidYMid slice" class="scene-svg" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="kyivSky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1E293B"/>
      <stop offset="58%" stop-color="#334155"/>
      <stop offset="100%" stop-color="#475569"/>
    </linearGradient>
    <linearGradient id="dnieper" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#1E3A5F"/>
      <stop offset="55%" stop-color="#27507B"/>
      <stop offset="100%" stop-color="#1E3A5F"/>
    </linearGradient>
  </defs>
  <rect width="316" height="146" fill="url(#kyivSky)"/>
  <!-- Distant smoke plumes -->
  <path d="M58 92 Q68 62 92 44 Q112 28 134 22 L152 38 Q128 54 114 72 L96 95 Z" fill="#0F172A" opacity="0.55"/>
  <path d="M128 96 Q142 66 168 48 Q186 35 204 28 L214 45 Q190 62 172 80 L156 98 Z" fill="#1E293B" opacity="0.62"/>
  <circle cx="102" cy="56" r="14" fill="#334155" opacity="0.5"/>
  <circle cx="154" cy="60" r="16" fill="#475569" opacity="0.45"/>
  <!-- Kyiv skyline silhouette -->
  <path d="M0 95 L0 74 L14 74 L14 66 L26 66 L26 78 L36 78 L36 58 L44 50 L52 58 L52 76 L66 76 L66 64 L82 64 L82 77 L98 77 L98 69 L114 69 L114 80 L132 80 L132 63 L144 63 L144 74 L162 74 L162 68 L178 68 L178 82 L218 82 L218 95 Z" fill="#0F172A"/>
  <!-- Golden spire hint -->
  <polygon points="44,44 41,52 47,52" fill="#F59E0B"/>
  <!-- Dnieper River -->
  <rect x="0" y="94" width="218" height="52" fill="url(#dnieper)"/>
  <line x1="8" y1="106" x2="72" y2="106" stroke="#60A5FA" stroke-width="1" opacity="0.35"/>
  <line x1="120" y1="116" x2="196" y2="116" stroke="#60A5FA" stroke-width="1" opacity="0.35"/>
  <line x1="36" y1="128" x2="146" y2="128" stroke="#93C5FD" stroke-width="1" opacity="0.28"/>
  <!-- 3 Arched Bridges across river -->
  <g stroke="#E2E8F0" stroke-width="2.3" fill="none">
    <path d="M4 102 L214 102"/>
    <path d="M12 102 Q36 87 60 102 M66 102 Q90 87 114 102 M122 102 Q146 87 170 102"/>
    <path d="M4 118 L214 118" stroke="#CBD5E1" stroke-width="2.1"/>
    <path d="M22 118 Q50 105 78 118 M88 118 Q116 105 144 118 M152 118 Q180 105 208 118" stroke="#CBD5E1" stroke-width="1.9"/>
    <path d="M4 134 L214 134" stroke="#94A3B8" stroke-width="2"/>
    <path d="M18 134 Q48 122 78 134 M92 134 Q122 122 152 134" stroke="#94A3B8" stroke-width="1.7"/>
  </g>
  <!-- Explosion burst on bridge -->
  <polygon points="154,84 160,96 173,92 164,102 175,110 161,109 156,120 150,108 137,111 146,101 138,91 150,95" fill="#F97316"/>
  <polygon points="154,90 158,98 166,97 160,103 165,109 156,106 152,113 149,105 142,106 148,100 144,94 152,97" fill="#FEF08A"/>
  <!-- Poland airspace right zone -->
  <rect x="218" y="0" width="98" height="146" fill="#0F172A" opacity="0.56"/>
  <line x1="218" y1="6" x2="218" y2="140" stroke="#EF4444" stroke-width="2.5" stroke-dasharray="6,4"/>
  <!-- Missile & drone trajectories entering Poland -->
  <path d="M148 44 Q202 36 262 52" fill="none" stroke="#F87171" stroke-width="2.1" stroke-dasharray="5,3"/>
  <polygon points="266,53 256,48 258,56" fill="#EF4444"/>
  <path d="M168 68 Q216 62 278 78" fill="none" stroke="#FCA5A5" stroke-width="1.9" stroke-dasharray="5,3"/>
  <polygon points="282,79 272,74 274,82" fill="#EF4444"/>
  <path d="M186 92 Q226 94 268 102" fill="none" stroke="#FDE047" stroke-width="1.7" stroke-dasharray="3,3"/>
  <polygon points="272,103 264,99 265,106" fill="#FDE047"/>
  <!-- POLAND pill -->
  <rect x="232" y="14" width="70" height="20" rx="3" fill="#B91C1C"/>
  <text x="267" y="28" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11.2" font-weight="800" fill="#FFFFFF" letter-spacing="0.6">POLAND</text>
  <!-- Airspace sublabel pill -->
  <rect x="222" y="114" width="90" height="16" rx="2.5" fill="#0F172A" opacity="0.92"/>
  <text x="267" y="125" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="7.8" font-weight="800" fill="#FECACA" letter-spacing="0.25">2 MISSILES + 1 DRONE</text>
  <!-- KYIV label -->
  <rect x="172" y="14" width="38" height="16" rx="2" fill="#0F172A" opacity="0.9"/>
  <text x="191" y="25.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#E2E8F0" letter-spacing="0.5">KYIV</text>
  <!-- Left stacked callout pills -->
  <rect x="8" y="14" width="114" height="21" rx="3" fill="#0F172A"/>
  <text x="65" y="28.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11.2" font-weight="800" fill="#FDE047" letter-spacing="0.3">3 KYIV BRIDGES</text>
  <rect x="8" y="39" width="164" height="20" rx="3" fill="#1E293B" stroke="#64748B" stroke-width="0.9"/>
  <text x="90" y="52.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.0" font-weight="800" fill="#FFFFFF" letter-spacing="0.45">111 MISSILES + 404 DRONES</text>
  <rect x="8" y="63" width="66" height="20" rx="3" fill="#B91C1C"/>
  <text x="41" y="76.8" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.8" font-weight="800" fill="#FFFFFF" letter-spacing="0.4">9 DEAD</text>
</svg>"""


def svg_hero_cyclone() -> str:
    return """<svg viewBox="0 0 316 146" preserveAspectRatio="xMidYMid slice" class="scene-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="316" height="146" fill="#CBE8F4"/>
  <!-- Ocean wave texture -->
  <path d="M128 32 Q146 28 164 32 M138 118 Q160 114 182 118 M180 48 Q198 44 216 48" stroke="#7CC4DF" stroke-width="1.4" fill="none"/>
  <!-- Odisha coastline sand -->
  <path d="M0 0 L132 0 L118 22 L96 48 L82 78 L66 108 L46 146 L0 146 Z" fill="#E6D5B8" stroke="#B69E76" stroke-width="2"/>
  <path d="M0 10 L114 10 L96 36 L74 74 L52 114 L34 146 L0 146 Z" fill="#EFE2CB" opacity="0.55"/>
  <!-- Labels on coast -->
  <text x="12" y="30" font-family="Segoe UI, Arial, sans-serif" font-size="11.5" font-weight="800" fill="#574326" letter-spacing="0.9">ODISHA</text>
  <circle cx="80" cy="80" r="5" fill="#DC2626" stroke="#FFFFFF" stroke-width="1.8"/>
  <text x="11" y="84" font-family="Segoe UI, Arial, sans-serif" font-size="9.5" font-weight="800" fill="#991B1B" letter-spacing="0.4">GOPALPUR</text>
  <!-- Cyclone concentric spiral -->
  <g transform="translate(152,78)">
    <circle r="44" fill="none" stroke="#0D9488" stroke-width="2.2" stroke-dasharray="14,6" opacity="0.45"/>
    <circle r="33" fill="none" stroke="#0F766E" stroke-width="3" stroke-dasharray="18,7" opacity="0.68"/>
    <circle r="21" fill="none" stroke="#0369A1" stroke-width="3.6" stroke-dasharray="16,5" opacity="0.88"/>
    <path d="M-4,-14 C14,-30 40,-18 42,6 M6,14 C-14,30 -38,18 -40,-6" fill="none" stroke="#0F766E" stroke-width="3.2" stroke-linecap="round"/>
    <circle r="8" fill="#FFFFFF" stroke="#0F766E" stroke-width="2.6"/>
  </g>
  <!-- Track arrow moving west to Gopalpur landfall -->
  <path d="M144 78 Q116 74 91 80" fill="none" stroke="#B91C1C" stroke-width="2.8"/>
  <polygon points="86,80 96,75 95,85" fill="#B91C1C"/>
  <!-- Right-aligned stat boxes -->
  <rect x="196" y="13" width="112" height="21" rx="3" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1"/>
  <text x="252" y="27" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="9.2" font-weight="800" fill="#0F172A" letter-spacing="0.2">02:00 UTC · 7:30 IST</text>
  <rect x="206" y="40" width="102" height="44" rx="4" fill="#0F172A"/>
  <text x="257" y="61" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="18.5" font-weight="900" fill="#5EEAD4">372,000</text>
  <text x="257" y="76" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="9.4" font-weight="800" fill="#E2E8F0" letter-spacing="0.7">EVACUATED</text>
  <rect x="206" y="90" width="102" height="42" rx="4" fill="#047857"/>
  <text x="257" y="110" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="16.0" font-weight="900" fill="#FFFFFF">0 DEATHS</text>
  <text x="257" y="124" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="9.0" font-weight="800" fill="#D1FAE5" letter-spacing="0.7">BY MIDDAY</text>
</svg>"""


def svg_hero_markets() -> str:
    return """<svg viewBox="0 0 316 132" preserveAspectRatio="xMidYMid meet" class="scene-svg markets-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="316" height="132" fill="#FDF8F5"/>
  <!-- Subtle horizontal gridlines -->
  <line x1="0" y1="30" x2="316" y2="30" stroke="#EFE4DC" stroke-width="1"/>
  <line x1="0" y1="62" x2="316" y2="62" stroke="#EFE4DC" stroke-width="1"/>
  <line x1="0" y1="94" x2="316" y2="94" stroke="#EFE4DC" stroke-width="1"/>
  <line x1="0" y1="124" x2="316" y2="124" stroke="#EFE4DC" stroke-width="1"/>
  <!-- Faint downward crimson area & polyline -->
  <polygon points="0,24 58,34 114,48 172,62 238,88 316,118 316,132 0,132" fill="#DC2626" opacity="0.06"/>
  <polyline points="0,24 58,34 114,48 172,62 238,88 316,118" fill="none" stroke="#DC2626" stroke-width="1.8" opacity="0.22"/>
  <!-- Top band: Asia Closing Bell -->
  <text x="10" y="13" font-family="Segoe UI, Arial, sans-serif" font-size="9.4" font-weight="800" fill="#991B1B" letter-spacing="0.4">ASIA CLOSING BELL (FRI)</text>
  <!-- Tile 1: TAIWAN -->
  <rect x="10" y="17" width="94" height="45" rx="3" fill="#FFFFFF" stroke="#E5D5CC" stroke-width="1"/>
  <rect x="10" y="17" width="94" height="3.5" rx="1" fill="#B91C1C"/>
  <text x="57" y="33" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="800" fill="#0F172A" letter-spacing="0.3">TAIWAN</text>
  <text x="57" y="55" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="19.5" font-weight="900" fill="#B91C1C">-6.2%</text>
  <!-- Tile 2: KOSPI -->
  <rect x="110" y="17" width="94" height="45" rx="3" fill="#FFFFFF" stroke="#E5D5CC" stroke-width="1"/>
  <rect x="110" y="17" width="94" height="3.5" rx="1" fill="#B91C1C"/>
  <text x="157" y="33" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="800" fill="#0F172A" letter-spacing="0.3">KOSPI</text>
  <text x="157" y="55" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="19.5" font-weight="900" fill="#B91C1C">-5.2%</text>
  <!-- Tile 3: NIKKEI -->
  <rect x="210" y="17" width="96" height="45" rx="3" fill="#FFFFFF" stroke="#E5D5CC" stroke-width="1"/>
  <rect x="210" y="17" width="96" height="3.5" rx="1" fill="#B91C1C"/>
  <text x="258" y="33" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="800" fill="#0F172A" letter-spacing="0.3">NIKKEI</text>
  <text x="258" y="55" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="19.5" font-weight="900" fill="#B91C1C">-5.1%</text>
  <!-- Bottom band: US Session Intraday -->
  <text x="10" y="75" font-family="Segoe UI, Arial, sans-serif" font-size="9.4" font-weight="800" fill="#0F172A" letter-spacing="0.4">US SESSION INTRADAY (FRI)</text>
  <!-- Tile 4: NVIDIA -->
  <rect x="10" y="79" width="94" height="45" rx="3" fill="#FEE2E2" stroke="#B91C1C" stroke-width="1.4"/>
  <rect x="10" y="79" width="94" height="3.5" rx="1" fill="#991B1B"/>
  <text x="57" y="95" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="900" fill="#0F172A" letter-spacing="0.3">NVIDIA</text>
  <text x="57" y="117" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="19.5" font-weight="900" fill="#991B1B">-14%</text>
  <!-- Tile 5: NASDAQ -->
  <rect x="110" y="79" width="94" height="45" rx="3" fill="#FFFFFF" stroke="#E5D5CC" stroke-width="1"/>
  <rect x="110" y="79" width="94" height="3.5" rx="1" fill="#334155"/>
  <text x="157" y="95" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="800" fill="#0F172A" letter-spacing="0.3">NASDAQ</text>
  <text x="157" y="117" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="19.5" font-weight="900" fill="#B91C1C">-5.3%</text>
  <!-- Tile 6: S&P 500 -->
  <rect x="210" y="79" width="96" height="45" rx="3" fill="#FFFFFF" stroke="#E5D5CC" stroke-width="1"/>
  <rect x="210" y="79" width="96" height="3.5" rx="1" fill="#334155"/>
  <text x="258" y="95" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="800" fill="#0F172A" letter-spacing="0.3">S&amp;P 500</text>
  <text x="258" y="117" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="19.5" font-weight="900" fill="#B91C1C">-3.7%</text>
</svg>"""


def svg_mid_cop31() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#EEF4FA"/>
  <!-- Clean globe -->
  <circle cx="44" cy="30" r="22" fill="#BFDBFE" stroke="#1D4ED8" stroke-width="2"/>
  <ellipse cx="44" cy="30" rx="10" ry="22" fill="none" stroke="#1D4ED8" stroke-width="1.4"/>
  <line x1="22" y1="30" x2="66" y2="30" stroke="#1D4ED8" stroke-width="1.4"/>
  <path d="M26 20 Q44 24 62 20 M26 40 Q44 36 62 40" fill="none" stroke="#1D4ED8" stroke-width="1.2"/>
  <!-- Red-rimmed clock -->
  <circle cx="104" cy="30" r="20" fill="#FFFFFF" stroke="#B91C1C" stroke-width="3.2"/>
  <line x1="104" y1="30" x2="104" y2="17" stroke="#0F172A" stroke-width="2.4" stroke-linecap="round"/>
  <line x1="104" y1="30" x2="115" y2="34" stroke="#B91C1C" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="104" cy="30" r="2.2" fill="#0F172A"/>
  <!-- Stacked badges -->
  <rect x="136" y="9" width="80" height="20" rx="3" fill="#1D4ED8"/>
  <text x="176" y="23" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12.2" font-weight="900" fill="#FFFFFF" letter-spacing="0.5">COP31</text>
  <rect x="136" y="33" width="80" height="19" rx="3" fill="#B91C1C"/>
  <text x="176" y="46" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.2" font-weight="800" fill="#FFFFFF" letter-spacing="0.5">OVERTIME</text>
</svg>"""


def svg_mid_eu_uk() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#F1F5F9"/>
  <!-- EU flag -->
  <rect x="28" y="6" width="52" height="28" rx="2" fill="#003399"/>
  <g fill="#FFCC00">
    <circle cx="54" cy="11" r="1.4"/><circle cx="60" cy="13" r="1.4"/><circle cx="63" cy="20" r="1.4"/>
    <circle cx="60" cy="27" r="1.4"/><circle cx="54" cy="29" r="1.4"/><circle cx="48" cy="27" r="1.4"/>
    <circle cx="45" cy="20" r="1.4"/><circle cx="48" cy="13" r="1.4"/>
  </g>
  <!-- Handshake/link icon -->
  <path d="M90 20 L136 20" stroke="#0F766E" stroke-width="2.4" stroke-dasharray="4,3"/>
  <circle cx="113" cy="20" r="7" fill="#0F766E"/>
  <path d="M109 20 L112 23 L117 17" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
  <!-- UK flag -->
  <rect x="146" y="6" width="52" height="28" rx="2" fill="#012169"/>
  <path d="M146 6 L198 34 M198 6 L146 34" stroke="#FFFFFF" stroke-width="4"/>
  <path d="M146 6 L198 34 M198 6 L146 34" stroke="#C8102E" stroke-width="1.8"/>
  <path d="M172 6 L172 34 M146 20 L198 20" stroke="#FFFFFF" stroke-width="6"/>
  <path d="M172 6 L172 34 M146 20 L198 20" stroke="#C8102E" stroke-width="3.2"/>
  <!-- Crisp 100K VISAS green pill -->
  <rect x="55" y="39" width="116" height="17" rx="8.5" fill="#047857"/>
  <text x="113" y="51" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="10.6" font-weight="900" fill="#FFFFFF" letter-spacing="0.6">100K VISAS</text>
</svg>"""


def svg_mid_health() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#F0FDF9"/>
  <!-- Lab vial -->
  <rect x="16" y="16" width="18" height="32" rx="3" fill="#FFFFFF" stroke="#0F766E" stroke-width="2"/>
  <rect x="19" y="11" width="12" height="5" rx="1" fill="#334155"/>
  <rect x="18" y="30" width="14" height="16" fill="#5EEAD4"/>
  <!-- Two-tone capsule -->
  <g transform="translate(66,30) rotate(-25)">
    <rect x="-18" y="-8" width="18" height="16" rx="8" fill="#0D9488"/>
    <rect x="0" y="-8" width="18" height="16" rx="8" fill="#FFFFFF" stroke="#0D9488" stroke-width="2"/>
  </g>
  <!-- Arrow -->
  <line x1="92" y1="30" x2="112" y2="30" stroke="#334155" stroke-width="2.2"/>
  <polygon points="116,30 109,26 109,34" fill="#334155"/>
  <!-- Shrinking target circle -->
  <circle cx="140" cy="30" r="18" fill="none" stroke="#FCA5A5" stroke-width="2" stroke-dasharray="4,2"/>
  <circle cx="140" cy="30" r="11" fill="#FECACA" stroke="#DC2626" stroke-width="1.8"/>
  <circle cx="140" cy="30" r="5" fill="#991B1B"/>
  <!-- TRIAL badge -->
  <rect x="167" y="19" width="50" height="22" rx="3" fill="#334155"/>
  <text x="192" y="34" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11.2" font-weight="900" fill="#FFFFFF" letter-spacing="0.6">TRIAL</text>
</svg>"""


def svg_mid_iraq() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="iraqSky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FDE68A"/>
      <stop offset="100%" stop-color="#FEF3C7"/>
    </linearGradient>
  </defs>
  <rect width="226" height="60" fill="url(#iraqSky)"/>
  <!-- Desert horizon & dunes -->
  <path d="M0 44 Q55 34 115 41 Q175 46 226 38 L226 60 L0 60 Z" fill="#D9B982"/>
  <rect x="0" y="48" width="226" height="12" fill="#B68B4C"/>
  <!-- Date palms -->
  <g stroke="#365314" stroke-width="2.1" fill="none">
    <line x1="26" y1="45" x2="26" y2="21" stroke="#78350F" stroke-width="2.6"/>
    <path d="M26 21 Q16 14 10 20 M26 21 Q36 14 42 20 M26 21 Q18 22 13 28 M26 21 Q34 22 39 28"/>
    <line x1="50" y1="45" x2="50" y2="25" stroke="#78350F" stroke-width="2.2"/>
    <path d="M50 25 Q42 19 37 24 M50 25 Q58 19 63 24"/>
  </g>
  <!-- Armored convoy -->
  <g fill="#1F2937">
    <rect x="74" y="34" width="34" height="12" rx="2"/>
    <polygon points="80,34 86,28 102,28 106,34"/>
    <circle cx="82" cy="48" r="4" fill="#090D16"/><circle cx="100" cy="48" r="4" fill="#090D16"/>
    <rect x="118" y="36" width="32" height="10" rx="2"/>
    <polygon points="124,36 128,30 142,30 146,36"/>
    <circle cx="126" cy="48" r="3.8" fill="#090D16"/><circle cx="142" cy="48" r="3.8" fill="#090D16"/>
  </g>
  <!-- IRAQ badge -->
  <rect x="160" y="9" width="58" height="22" rx="3" fill="#B45309"/>
  <text x="189" y="24.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12.2" font-weight="900" fill="#FFFFFF" letter-spacing="0.7">IRAQ</text>
</svg>"""


def svg_mid_italy() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#F8FAFC"/>
  <!-- Italian tricolor left edge -->
  <rect x="0" y="0" width="6" height="60" fill="#009246"/>
  <rect x="6" y="0" width="6" height="60" fill="#FFFFFF"/>
  <rect x="12" y="0" width="6" height="60" fill="#CE2B37"/>
  <!-- Marchers & placards -->
  <rect x="28" y="11" width="24" height="14" rx="1.5" fill="#1D4ED8"/>
  <line x1="40" y1="25" x2="40" y2="44" stroke="#334155" stroke-width="2"/>
  <rect x="60" y="15" width="22" height="13" rx="1.5" fill="#CE2B37"/>
  <line x1="71" y1="28" x2="71" y2="45" stroke="#334155" stroke-width="2"/>
  <g fill="#0F172A">
    <circle cx="34" cy="40" r="4.5"/><rect x="29" y="45" width="10" height="15" rx="3"/>
    <circle cx="52" cy="42" r="4.5"/><rect x="47" y="47" width="10" height="13" rx="3"/>
    <circle cx="71" cy="40" r="4.5"/><rect x="66" y="45" width="10" height="15" rx="3"/>
    <circle cx="90" cy="42" r="4.5"/><rect x="85" y="47" width="10" height="13" rx="3"/>
  </g>
  <!-- Megaphone -->
  <polygon points="103,26 122,18 122,34" fill="#B91C1C"/>
  <rect x="98" y="24" width="6" height="5" fill="#1E293B"/>
  <path d="M126 20 Q131 26 126 32" fill="none" stroke="#B91C1C" stroke-width="2"/>
  <!-- 100 CITIES badge -->
  <rect x="136" y="18" width="82" height="23" rx="3" fill="#1D4ED8"/>
  <text x="177" y="33.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11.4" font-weight="900" fill="#FFFFFF" letter-spacing="0.4">100 CITIES</text>
</svg>"""


def svg_mid_peru() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#F5F3FF"/>
  <!-- Snow-capped Andes -->
  <polygon points="4,58 38,14 72,58" fill="#6D28D9"/>
  <polygon points="38,14 29,26 36,24 41,28 47,25" fill="#FFFFFF"/>
  <polygon points="46,58 84,20 120,58" fill="#5B21B6"/>
  <polygon points="84,20 75,31 82,29 88,33 93,30" fill="#FFFFFF"/>
  <!-- Pulsing epicenter -->
  <circle cx="84" cy="42" r="14" fill="none" stroke="#DC2626" stroke-width="1.6" opacity="0.5"/>
  <circle cx="84" cy="42" r="8" fill="none" stroke="#DC2626" stroke-width="2"/>
  <circle cx="84" cy="42" r="3.5" fill="#DC2626"/>
  <!-- Seismograph trace -->
  <polyline points="116,44 128,44 133,38 138,51 144,24 150,55 156,33 162,48 168,42 178,44 218,44" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linejoin="round"/>
  <!-- M 6.7 badge -->
  <rect x="150" y="7" width="68" height="22" rx="3" fill="#7C3AED"/>
  <text x="184" y="22.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="13.5" font-weight="900" fill="#FFFFFF" letter-spacing="0.4">M 6.7</text>
</svg>"""


def svg_mid_safrica() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#FEF2F2"/>
  <!-- 3 rising bars -->
  <line x1="14" y1="52" x2="102" y2="52" stroke="#991B1B" stroke-width="1.6"/>
  <rect x="20" y="34" width="18" height="18" rx="1.5" fill="#F87171"/>
  <rect x="46" y="23" width="18" height="29" rx="1.5" fill="#DC2626"/>
  <rect x="72" y="10" width="18" height="42" rx="1.5" fill="#991B1B"/>
  <!-- Stacked red badge: 581 KILLED / Q3 REPORT OUT -->
  <rect x="106" y="7" width="112" height="46" rx="4" fill="#991B1B"/>
  <text x="162" y="29" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="13.8" font-weight="900" fill="#FFFFFF" letter-spacing="0.3">581 KILLED</text>
  <rect x="114" y="35" width="96" height="13" rx="2" fill="#7F1D1D"/>
  <text x="162" y="44.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="8.8" font-weight="800" fill="#FECACA" letter-spacing="0.5">Q3 REPORT OUT</text>
</svg>"""


def svg_mid_nz() -> str:
    return """<svg viewBox="0 0 226 60" class="mid-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="226" height="60" fill="#E0F2FE"/>
  <!-- Emerald headland hill -->
  <path d="M0 32 Q36 8 88 26 L124 34 L0 34 Z" fill="#059669"/>
  <!-- Ocean surf -->
  <rect x="0" y="32" width="226" height="10" fill="#0369A1"/>
  <path d="M0 40 Q28 36 56 40 T112 40 T168 40 T226 40" fill="none" stroke="#FFFFFF" stroke-width="2"/>
  <!-- Sandy shore -->
  <rect x="0" y="41" width="226" height="19" fill="#EEDBC0"/>
  <!-- 3 stranded whale silhouettes -->
  <g fill="#0F172A">
    <path d="M16 52 C16 44.5 34 44.5 46 49 L55 45 L53 53.5 L46 53 C34 55.5 16 55.5 16 52 Z"/>
    <path d="M66 53 C66 46.5 82 46.5 93 50 L101 46.5 L99 54.5 L92 54 C82 56.5 66 56.5 66 53 Z"/>
    <path d="M114 52 C114 45.5 129 45.5 139 49 L146 46 L144 53.5 L138 53 C129 55.5 114 55.5 114 52 Z"/>
  </g>
  <!-- 24 WHALES badge -->
  <rect x="136" y="7" width="82" height="21" rx="3" fill="#0369A1"/>
  <text x="177" y="21.5" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="11.0" font-weight="900" fill="#FFFFFF" letter-spacing="0.4">24 WHALES</text>
</svg>"""


HERO_STORIES = [
    {
        "num": 1,
        "region": "Europe",
        "kicker": "EUROPE · UKRAINE WAR",
        "headline": "Kyiv bridges hit; Russian missiles enter Poland",
        "summary": "Barrage of 111 missiles & 404 drones hits 3 Kyiv bridges, officials report 9 dead; Poland says 2 missiles & 1 drone entered its airspace.",
        "status": "REPORTED",
        "source": "KYIV INDEPENDENT",
        "lat": 50.45,
        "lon": 30.52,
        "svg": svg_hero_kyiv(),
    },
    {
        "num": 2,
        "region": "Asia-Pacific",
        "kicker": "ASIA · WEATHER",
        "headline": "Cyclone Akvan hits Odisha after 372,000 evacuate",
        "summary": "Makes landfall near Gopalpur at 02:00 UTC (7:30am IST) with gale winds, then weakens fast; zero deaths reported by midday.",
        "status": "CONFIRMED",
        "source": "IMD / THE HINDU",
        "lat": 19.27,
        "lon": 84.91,
        "svg": svg_hero_cyclone(),
    },
    {
        "num": 3,
        "region": "Global",
        "kicker": "GLOBAL · MARKETS",
        "headline": "AI sell-off sinks Asia markets; Nvidia -14%",
        "summary": "Taiwan (-6.2%), Seoul (-5.2%) & Tokyo (-5.1%) close sharply lower; in US trading, Nvidia falls 14% amid a Reuters-reported SEC accounting probe.",
        "status": "REPORTED",
        "source": "REUTERS / CNN",
        "lat": 25.03,
        "lon": 121.56,
        "svg": svg_hero_markets(),
    },
]

MID_STORIES = [
    {
        "num": 4,
        "region": "Europe",
        "kicker": "EUROPE · CLIMATE",
        "headline": "COP31 stalls on fossil-fuel exit",
        "status": "REPORTED",
        "source": "UNFCCC",
        "lat": 36.89,
        "lon": 30.71,
        "svg": svg_mid_cop31(),
    },
    {
        "num": 5,
        "region": "Europe",
        "kicker": "EUROPE · DIPLOMACY",
        "headline": "EU, UK agree post-Brexit reset pact",
        "status": "OFFICIAL",
        "source": "EU / UK",
        "lat": 50.85,
        "lon": 4.35,
        "svg": svg_mid_eu_uk(),
    },
    {
        "num": 6,
        "region": "Global",
        "kicker": "SCIENCE · HEALTH",
        "headline": "Trial pill slows pancreatic cancer",
        "status": "REPORTED",
        "source": "GUARDIAN",
        "lat": 42.36,
        "lon": -71.06,
        "svg": svg_mid_health(),
    },
    {
        "num": 7,
        "region": "Middle East",
        "kicker": "MIDEAST · SECURITY",
        "headline": "Iraqi troops deploy to Jurf al-Sakhar",
        "status": "REPORTED",
        "source": "REUTERS",
        "lat": 32.88,
        "lon": 44.19,
        "svg": svg_mid_iraq(),
    },
    {
        "num": 8,
        "region": "Europe",
        "kicker": "EUROPE · LABOUR",
        "headline": "General strike hits 100 Italian cities",
        "status": "REPORTED",
        "source": "CGIL / WAPO",
        "lat": 41.90,
        "lon": 12.49,
        "svg": svg_mid_italy(),
    },
    {
        "num": 9,
        "region": "Latin America",
        "kicker": "AMERICAS · SEISMIC",
        "headline": "M 6.7 quake shakes Peru Andes & Lima",
        "status": "CONFIRMED",
        "source": "USGS / AP",
        "lat": -11.40,
        "lon": -75.50,
        "svg": svg_mid_peru(),
    },
    {
        "num": 10,
        "region": "Africa",
        "kicker": "AFRICA · CRIME",
        "headline": "S. Africa Q3 report: 581 women killed",
        "status": "OFFICIAL",
        "source": "SAPS",
        "lat": -26.20,
        "lon": 28.04,
        "svg": svg_mid_safrica(),
    },
    {
        "num": 11,
        "region": "Oceania",
        "kicker": "OCEANIA · NATURE",
        "headline": "24 sperm whales strand in NZ north",
        "status": "REPORTED",
        "source": "NZ MEDIA",
        "lat": -34.65,
        "lon": 172.80,
        "svg": svg_mid_nz(),
    },
]


def flag_svg(code: str) -> str:
    """Return a crisp 14x10 inline SVG flag or emblem."""
    body = {
        "CN": '<rect width="14" height="10" fill="#DE2910"/><circle cx="3.4" cy="3.2" r="1.4" fill="#FFDE00"/><circle cx="5.8" cy="2" r="0.5" fill="#FFDE00"/><circle cx="6.2" cy="3.8" r="0.5" fill="#FFDE00"/>',
        "JP": '<rect width="14" height="10" fill="#FFFFFF"/><circle cx="7" cy="5" r="2.8" fill="#BC002D"/>',
        "KR": '<rect width="14" height="10" fill="#FFFFFF"/><circle cx="7" cy="5" r="2.5" fill="#CD2E3A"/><path d="M4.5 5 A2.5 2.5 0 0 0 9.5 5 A1.25 1.25 0 0 1 7 5 A1.25 1.25 0 0 0 4.5 5 Z" fill="#0047A0"/>',
        "ID": '<rect width="14" height="5" fill="#CE1126"/><rect y="5" width="14" height="5" fill="#FFFFFF"/>',
        "PK": '<rect width="14" height="10" fill="#01411C"/><rect width="3.5" height="10" fill="#FFFFFF"/><circle cx="8.8" cy="5" r="2.4" fill="#FFFFFF"/><circle cx="9.6" cy="4.7" r="2.0" fill="#01411C"/>',
        "TW": '<rect width="14" height="10" fill="#FE0000"/><rect width="7" height="5.4" fill="#000095"/><circle cx="3.5" cy="2.7" r="1.4" fill="#FFFFFF"/>',
        "NZ": '<rect width="14" height="10" fill="#012169"/><rect width="6.5" height="5" fill="#012169"/><path d="M3.25 0 V5 M0 2.5 H6.5" stroke="#FFFFFF" stroke-width="1.3"/><path d="M3.25 0 V5 M0 2.5 H6.5" stroke="#C8102E" stroke-width="0.7"/><circle cx="10.8" cy="2.8" r="0.7" fill="#EF4444"/><circle cx="11.6" cy="5.5" r="0.7" fill="#EF4444"/><circle cx="10.2" cy="7.8" r="0.7" fill="#EF4444"/>',
        "GB": '<rect width="14" height="10" fill="#012169"/><path d="M0 0 L14 10 M14 0 L0 10" stroke="#FFFFFF" stroke-width="1.8"/><path d="M0 0 L14 10 M14 0 L0 10" stroke="#C8102E" stroke-width="0.8"/><path d="M7 0 V10 M0 5 H14" stroke="#FFFFFF" stroke-width="2.6"/><path d="M7 0 V10 M0 5 H14" stroke="#C8102E" stroke-width="1.5"/>',
        "EU": '<rect width="14" height="10" fill="#003399"/><circle cx="7" cy="5" r="2.8" fill="none" stroke="#FFCC00" stroke-width="1.1" stroke-dasharray="1,1.4"/>',
        "EE": '<rect width="14" height="3.33" fill="#0072CE"/><rect y="3.33" width="14" height="3.34" fill="#111827"/><rect y="6.67" width="14" height="3.33" fill="#FFFFFF"/>',
        "US": '<rect width="14" height="10" fill="#FFFFFF"/><rect y="0" width="14" height="1.5" fill="#B22234"/><rect y="3" width="14" height="1.5" fill="#B22234"/><rect y="6" width="14" height="1.5" fill="#B22234"/><rect y="8.5" width="14" height="1.5" fill="#B22234"/><rect width="6.5" height="5.5" fill="#3C3B6E"/>',
        "DE": '<rect width="14" height="3.33" fill="#111827"/><rect y="3.33" width="14" height="3.34" fill="#DD0000"/><rect y="6.67" width="14" height="3.33" fill="#FFCE00"/>',
        "AI": '<rect width="14" height="10" rx="1.5" fill="#1E293B"/><text x="7" y="7.4" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="6.8" font-weight="900" fill="#FDE047">AI</text>',
        "YE": '<rect width="14" height="3.33" fill="#CE1126"/><rect y="3.33" width="14" height="3.34" fill="#FFFFFF"/><rect y="6.67" width="14" height="3.33" fill="#111827"/>',
        "IR": '<rect width="14" height="3.33" fill="#239F40"/><rect y="3.33" width="14" height="3.34" fill="#FFFFFF"/><rect y="6.67" width="14" height="3.33" fill="#DA0000"/><circle cx="7" cy="5" r="1.1" fill="#DA0000"/>',
        "UN": '<rect width="14" height="10" fill="#009EDB"/><circle cx="7" cy="5" r="2.7" fill="none" stroke="#FFFFFF" stroke-width="1"/><line x1="7" y1="2.3" x2="7" y2="7.7" stroke="#FFFFFF" stroke-width="0.8"/><line x1="4.3" y1="5" x2="9.7" y2="5" stroke="#FFFFFF" stroke-width="0.8"/>',
        "LB": '<rect width="14" height="2.6" fill="#ED1C24"/><rect y="2.6" width="14" height="4.8" fill="#FFFFFF"/><rect y="7.4" width="14" height="2.6" fill="#ED1C24"/><polygon points="7,3 5.2,6.8 8.8,6.8" fill="#00A651"/>',
        "SD": '<rect width="14" height="3.33" fill="#D21034"/><rect y="3.33" width="14" height="3.34" fill="#FFFFFF"/><rect y="6.67" width="14" height="3.33" fill="#111827"/><polygon points="0,0 5.4,5 0,10" fill="#007229"/>',
        "ET": '<rect width="14" height="3.33" fill="#078930"/><rect y="3.33" width="14" height="3.34" fill="#FCDD09"/><rect y="6.67" width="14" height="3.33" fill="#DA121A"/><circle cx="7" cy="5" r="2.0" fill="#0F47AF"/>',
        "NG": '<rect width="4.7" height="10" fill="#008751"/><rect x="4.7" width="4.6" height="10" fill="#FFFFFF"/><rect x="9.3" width="4.7" height="10" fill="#008751"/>',
        "SN": '<rect width="4.7" height="10" fill="#00853F"/><rect x="4.7" width="4.6" height="10" fill="#FDEF42"/><rect x="9.3" width="4.7" height="10" fill="#E31B23"/><circle cx="7" cy="5" r="1.1" fill="#00853F"/>',
        "SV": '<rect width="14" height="3.33" fill="#0F47AF"/><rect y="3.33" width="14" height="3.34" fill="#FFFFFF"/><rect y="6.67" width="14" height="3.33" fill="#0F47AF"/><circle cx="7" cy="5" r="1.0" fill="#C9A227"/>',
    }[code]
    return (
        f'<svg viewBox="0 0 14 10" width="14" height="10" class="flag-svg" '
        f'xmlns="http://www.w3.org/2000/svg">{body}'
        f'<rect x="0.25" y="0.25" width="13.5" height="9.5" fill="none" stroke="#CBD5E1" stroke-width="0.5"/></svg>'
    )


def compute_map_pins() -> list[tuple[int, float, float, str]]:
    """Project 11 scene coordinates with anti-overlap nudges and assert pin separation."""
    def project(lat: float, lon: float) -> tuple[float, float]:
        x = 6.0 + ((lon + 180.0) / 360.0) * 250.0
        y = 8.0 + ((82.0 - lat) / 142.0) * 86.0
        return x, y

    # Anti-overlap nudges for tight clusters (#1, #4, #5, #6, #7, #8, #11)
    nudges = {
        1: (4.5, -5.5),
        4: (2.5, 2.0),
        5: (-5.5, -5.5),
        6: (-2.0, 0.0),
        7: (11.5, 5.0),
        8: (-6.5, 5.5),
        11: (-3.5, -1.5),
    }

    pins: list[tuple[int, float, float, str]] = []
    for story in HERO_STORIES + MID_STORIES:
        x, y = project(story["lat"], story["lon"])
        dx, dy = nudges.get(story["num"], (0.0, 0.0))
        pins.append((story["num"], x + dx, y + dy, REGION_COLORS[story["region"]]))

    for i in range(len(pins)):
        for j in range(i + 1, len(pins)):
            n1, x1, y1, _ = pins[i]
            n2, x2, y2, _ = pins[j]
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            assert dist >= 12.0, f"Map pins #{n1} and #{n2} too close: {dist:.2f}"
    return pins


def build_world_map_svg() -> str:
    """Stylized 262x100 world map with 11 region-colored numbered pins."""
    pins_svg = []
    for num, px, py, color in compute_map_pins():
        pins_svg.append(
            f'<g>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.6" fill="{color}" stroke="#FFFFFF" stroke-width="1.3"/>'
            f'<text x="{px:.1f}" y="{py + 2.8:.1f}" text-anchor="middle" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="7.8" font-weight="900" fill="#FFFFFF">{num}</text>'
            f'</g>'
        )

    return f"""<svg viewBox="0 0 262 100" class="world-map-svg" xmlns="http://www.w3.org/2000/svg">
  <rect width="262" height="100" rx="2" fill="#DCE7EE"/>
  <!-- Subtle graticule -->
  <line x1="0" y1="57.7" x2="262" y2="57.7" stroke="#C5D5E0" stroke-width="0.7" stroke-dasharray="2,2"/>
  <line x1="131" y1="0" x2="131" y2="100" stroke="#C5D5E0" stroke-width="0.7" stroke-dasharray="2,2"/>
  <!-- Continents (#C4BBA6) -->
  <g fill="#C4BBA6" stroke="#9E937C" stroke-width="0.85" stroke-linejoin="round">
    <!-- North America -->
    <path d="M18,16 L46,12 L74,16 L84,26 L75,36 L67,46 L59,51 L50,48 L43,40 L30,34 L20,26 Z"/>
    <!-- Greenland -->
    <path d="M84,9 L102,8 L104,17 L91,20 Z"/>
    <!-- South America -->
    <path d="M64,53 L80,55 L92,66 L87,80 L76,92 L69,89 L68,74 L61,62 Z"/>
    <!-- Europe -->
    <path d="M122,19 L142,14 L158,18 L156,28 L146,33 L134,34 L125,31 L122,25 Z"/>
    <!-- Africa -->
    <path d="M123,37 L144,37 L157,46 L160,60 L152,77 L142,81 L133,68 L131,55 L121,49 Z"/>
    <!-- Asia -->
    <path d="M156,15 L198,13 L236,18 L242,29 L226,38 L215,49 L204,52 L193,48 L184,54 L173,45 L160,44 L152,36 Z"/>
    <!-- Japan / Taiwan / Indonesia hints -->
    <path d="M227,32 L233,31 L232,37 L226,38 Z"/>
    <path d="M204,58 L224,60 L226,64 L205,62 Z"/>
    <!-- Australia -->
    <path d="M210,69 L232,68 L238,79 L228,87 L213,84 L208,76 Z"/>
    <!-- New Zealand -->
    <path d="M245,83 L252,79 L253,86 L247,90 Z"/>
  </g>
  {"".join(pins_svg)}
</svg>"""


def render_brief_rows(rows: list[tuple[str, str, bool, str]]) -> str:
    items = []
    for code, subject, is_claim, text in rows:
        claim_html = '<span class="claim-tag">CLAIM</span>' if is_claim else ""
        items.append(
            f'<div class="b-row">'
            f'{flag_svg(code)}'
            f'<span class="b-txt"><strong>{html.escape(subject)}</strong>{claim_html}: {html.escape(text)}</span>'
            f'</div>'
        )
    return "\n".join(items)


def build_html() -> str:
    utc_html = "\n".join(
        f'<span class="ur-item"><strong>{html.escape(t)}</strong> {html.escape(lbl)}</span>'
        for t, lbl in UTC_MILESTONES
    )

    hero_cards = []
    for s in HERO_STORIES:
        rcol = REGION_COLORS[s["region"]]
        scol = STATUS_COLORS[s["status"]]
        hero_cards.append(
            f"""<article class="hero-card" style="border-top-color:{rcol}">
  <div class="h-kicker">
    <span class="pin" style="background:{rcol}">{s["num"]}</span>
    <span class="k-txt" style="color:{rcol}">{html.escape(s["kicker"])}</span>
  </div>
  <div class="h-art">{s["svg"]}</div>
  <h2 class="h-head">{html.escape(s["headline"])}</h2>
  <p class="h-sum">{html.escape(s["summary"])}</p>
  <div class="meta-bar">
    <span class="st-pill" style="background:{scol}">{html.escape(s["status"])}</span>
    <span class="src-txt">{html.escape(s["source"])}</span>
  </div>
</article>"""
        )

    mid_cards = []
    for s in MID_STORIES:
        rcol = REGION_COLORS[s["region"]]
        scol = STATUS_COLORS[s["status"]]
        mid_cards.append(
            f"""<article class="mid-card" style="border-top-color:{rcol}">
  <div class="m-kicker">
    <span class="pin" style="background:{rcol}">{s["num"]}</span>
    <span class="k-txt" style="color:{rcol}">{html.escape(s["kicker"])}</span>
  </div>
  <div class="m-art">{s["svg"]}</div>
  <h3 class="m-head">{html.escape(s["headline"])}</h3>
  <div class="meta-bar">
    <span class="st-pill" style="background:{scol}">{html.escape(s["status"])}</span>
    <span class="src-txt">{html.escape(s["source"])}</span>
  </div>
</article>"""
        )

    legend_items = [
        ("Eur", REGION_COLORS["Europe"]),
        ("Asia", REGION_COLORS["Asia-Pacific"]),
        ("MidE", REGION_COLORS["Middle East"]),
        ("Afr", REGION_COLORS["Africa"]),
        ("Amer", REGION_COLORS["Latin America"]),
        ("Oce", REGION_COLORS["Oceania"]),
        ("Glob", REGION_COLORS["Global"]),
    ]
    legend_html = "".join(
        f'<span class="leg-i"><i style="background:{c}"></i>{lbl}</span>'
        for lbl, c in legend_items
    )

    excluded_html = "".join(
        f'<div class="ex-row"><span class="ex-l">{html.escape(l)}</span><span class="ex-d">{html.escape(d)}</span></div>'
        for l, d in EXCLUDED_OTHER_DAYS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Friday 20 November 2026 — World News Front Page</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 1024px;
    height: 1024px;
    overflow: hidden;
    background: #FAF7F0;
    color: #090D16;
    font-family: "Segoe UI", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .page {{
    width: 1024px;
    height: 1024px;
    padding: 7px 14px 5px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: #FAF7F0;
    overflow: hidden;
  }}
  /* Masthead: 70px */
  .masthead {{
    height: 70px;
    flex: 0 0 70px;
    border-bottom: 2px solid #090D16;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding-bottom: 2px;
    overflow: hidden;
  }}
  .mast-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10.6px;
    font-weight: 800;
    letter-spacing: 0.35px;
    line-height: 1.1;
  }}
  .mast-left {{ color: #991B1B; }}
  .mast-right {{ color: #111827; }}
  .mast-title {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 51px;
    font-weight: 700;
    line-height: 1.0;
    text-align: center;
    letter-spacing: -0.5px;
    color: #090D16;
  }}
  /* UTC Ribbon: 26px */
  .utc-ribbon {{
    height: 26px;
    flex: 0 0 26px;
    border-bottom: 1.5px solid #C9C1B0;
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 2px;
    overflow: hidden;
  }}
  .utc-badge {{
    background: #991B1B;
    color: #FFFFFF;
    font-size: 9.6px;
    font-weight: 800;
    letter-spacing: 0.45px;
    padding: 3px 7px;
    border-radius: 2px;
    flex: 0 0 auto;
    line-height: 1.1;
  }}
  .ur-items {{
    flex: 1 1 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10.6px;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
  }}
  .ur-item strong {{
    color: #090D16;
    font-weight: 800;
  }}
  /* Hero Grid: 308px */
  .hero-grid {{
    height: 308px;
    flex: 0 0 308px;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    overflow: hidden;
  }}
  .hero-card {{
    height: 308px;
    background: #FFFDF9;
    border: 1px solid #D9D1C0;
    border-top: 3.5px solid #1D4ED8;
    padding: 5px 8px 5px 8px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 3px;
    overflow: hidden;
  }}
  .h-kicker, .m-kicker {{
    display: flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    overflow: hidden;
  }}
  .h-kicker {{ height: 18px; flex: 0 0 18px; }}
  .m-kicker {{ height: 17px; flex: 0 0 17px; gap: 4px; }}
  .pin {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    color: #FFFFFF;
    font-size: 9.8px;
    font-weight: 900;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 16px;
    line-height: 1;
  }}
  .k-txt {{
    font-size: 9.8px;
    font-weight: 800;
    letter-spacing: 0.45px;
    line-height: 1;
  }}
  .m-kicker .k-txt {{ font-size: 9.1px; letter-spacing: 0.35px; }}
  .h-art {{
    height: 128px;
    flex: 0 0 128px;
    width: 100%;
    border-radius: 3px;
    overflow: hidden;
    border: 1px solid #D5CCC0;
    background: #FDF8F5;
  }}
  .scene-svg {{
    width: 100%;
    height: 100%;
    display: block;
  }}
  .h-head {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 23.6px;
    font-weight: 700;
    line-height: 1.03;
    color: #090D16;
    letter-spacing: -0.25px;
  }}
  .h-sum {{
    font-size: 12.6px;
    line-height: 1.20;
    color: #111827;
    font-weight: 400;
  }}
  .meta-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    height: 16px;
    flex: 0 0 16px;
    margin-top: auto;
    white-space: nowrap;
    overflow: hidden;
  }}
  .st-pill {{
    color: #FFFFFF;
    font-size: 8.6px;
    font-weight: 800;
    letter-spacing: 0.45px;
    padding: 2px 5px;
    border-radius: 2px;
    line-height: 1;
  }}
  .src-txt {{
    font-size: 9.4px;
    font-weight: 800;
    color: #1F2937;
    letter-spacing: 0.3px;
  }}
  /* Mid Grid: 2 rows x 150px + 8px gap = 308px */
  .mid-grid {{
    height: 308px;
    flex: 0 0 308px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: 150px 150px;
    row-gap: 8px;
    column-gap: 10px;
    overflow: hidden;
  }}
  .mid-card {{
    height: 150px;
    background: #FFFDF9;
    border: 1px solid #D9D1C0;
    border-top: 3.5px solid #1D4ED8;
    padding: 4px 7px 4px 7px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 2px;
    overflow: hidden;
  }}
  .m-art {{
    height: 60px;
    flex: 0 0 60px;
    width: 100%;
    border-radius: 2px;
    overflow: hidden;
    border: 1px solid #E5DFD2;
  }}
  .mid-svg {{
    width: 100%;
    height: 100%;
    display: block;
  }}
  .m-head {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 18.0px;
    font-weight: 700;
    line-height: 1.04;
    letter-spacing: 0.1px;
    color: #090D16;
  }}
  /* Lower Grid: 264px */
  .lower-grid {{
    height: 264px;
    flex: 0 0 264px;
    display: grid;
    grid-template-columns: 274px 1fr 1fr;
    column-gap: 10px;
    overflow: hidden;
  }}
  .f-left {{
    width: 274px;
    height: 264px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 5px;
    overflow: hidden;
  }}
  .map-box {{
    height: 141px;
    flex: 0 0 141px;
    background: #FFFDF9;
    border: 1px solid #D6CEBE;
    padding: 4px 5px 3px 5px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }}
  .box-hdr {{
    font-size: 9.2px;
    font-weight: 800;
    letter-spacing: 0.4px;
    color: #090D16;
    line-height: 1.1;
  }}
  .world-map-svg {{
    width: 100%;
    height: 100px;
    display: block;
  }}
  .map-leg {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 8.6px;
    font-weight: 800;
    color: #1F2937;
    white-space: nowrap;
    overflow: hidden;
  }}
  .leg-i {{
    display: inline-flex;
    align-items: center;
    gap: 2.5px;
  }}
  .leg-i i {{
    width: 6.5px;
    height: 6.5px;
    border-radius: 50%;
    display: inline-block;
  }}
  .date-box {{
    height: 118px;
    flex: 0 0 118px;
    border: 1.5px solid #B91C1C;
    background: #FFF7F5;
    padding: 4px 6px 4px 6px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }}
  .date-hdr {{
    font-size: 9.3px;
    font-weight: 800;
    letter-spacing: 0.35px;
    color: #991B1B;
    line-height: 1.1;
  }}
  .ex-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10.1px;
    line-height: 1.15;
    border-top: 1px solid #F3D6D0;
    padding-top: 2px;
    white-space: nowrap;
    overflow: hidden;
  }}
  .ex-l {{ color: #111827; font-weight: 600; }}
  .ex-d {{ color: #991B1B; font-weight: 800; font-size: 9.6px; }}
  /* Brief columns */
  .b-col {{
    height: 264px;
    background: #FFFDF9;
    border-top: 2px solid #090D16;
    padding: 3px 4px 1px 4px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .b-hdr {{
    font-size: 9.6px;
    font-weight: 800;
    letter-spacing: 0.4px;
    color: #090D16;
    border-bottom: 1.5px solid #090D16;
    padding-bottom: 2px;
    margin-bottom: 2px;
    flex: 0 0 auto;
    line-height: 1.15;
  }}
  .b-list {{
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }}
  .b-row {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12.3px;
    line-height: 1.12;
    color: #111827;
    border-bottom: 1px solid #EFE9DC;
    padding: 1.5px 0;
    white-space: nowrap;
    overflow: hidden;
    letter-spacing: -0.22px;
  }}
  .b-row:last-child {{ border-bottom: none; }}
  .flag-svg {{ flex: 0 0 14px; display: block; }}
  .b-txt {{ overflow: hidden; white-space: nowrap; }}
  .b-txt strong {{ color: #090D16; font-weight: 800; }}
  .claim-tag {{
    display: inline-block;
    background: #B45309;
    color: #FFFFFF;
    font-size: 7.7px;
    font-weight: 900;
    padding: 0.8px 3.5px;
    border-radius: 2px;
    margin-left: 3px;
    vertical-align: 1px;
    letter-spacing: 0.25px;
  }}
  /* Footer: 16px */
  .footer-bar {{
    height: 16px;
    flex: 0 0 16px;
    border-top: 1.5px solid #090D16;
    padding-top: 2px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 9.0px;
    font-weight: 600;
    color: #374151;
    white-space: nowrap;
    overflow: hidden;
  }}
</style>
</head>
<body>
<main class="page">
  <header class="masthead">
    <div class="mast-top">
      <span class="mast-left">THE WORLD'S NEWS OF ONE DAY</span>
      <span class="mast-right">37 STORIES (11 SCENES + 26 BRIEFS) · 7 REGIONS · 20 FIELDS · FRI 20 NOV</span>
    </div>
    <h1 class="mast-title">Friday 20 November 2026</h1>
  </header>

  <nav class="utc-ribbon" aria-label="The day in UTC">
    <span class="utc-badge">THE DAY IN UTC</span>
    <div class="ur-items">
      {utc_html}
    </div>
  </nav>

  <section class="hero-grid">
    {"".join(hero_cards)}
  </section>

  <section class="mid-grid">
    {"".join(mid_cards)}
  </section>

  <section class="lower-grid">
    <div class="f-left">
      <div class="map-box">
        <div class="box-hdr">WHERE IT HAPPENED · 11 SCENES</div>
        {build_world_map_svg()}
        <div class="map-leg">{legend_html}</div>
      </div>
      <div class="date-box">
        <div class="date-hdr">DATE CHECK · EXCLUDED (OTHER DAYS)</div>
        {excluded_html}
      </div>
    </div>

    <div class="b-col">
      <div class="b-hdr">ASIA · OCEANIA · EUROPE · TECH (13)</div>
      <div class="b-list">
        {render_brief_rows(BRIEF_COL_A)}
      </div>
    </div>

    <div class="b-col">
      <div class="b-hdr">MIDEAST · AFRICA · AMERICAS · UN (13)</div>
      <div class="b-list">
        {render_brief_rows(BRIEF_COL_B)}
      </div>
    </div>
  </section>

  <footer class="footer-bar">
    <span>All 37 stories from Fri 20 Nov 2026 · Tags: Green=Confirmed/Official · Blue=Reported · Amber=Claim.</span>
    <span>Sources: Reuters, AP, AFP, Guardian, Kyiv Independent, IMD, ONS, USGS, UN, Xinhua.</span>
  </footer>
</main>
</body>
</html>"""


def run_negative_self_checks(doc_html: str) -> None:
    """Assert editorial integrity, exact story count, banned phrases, and palette coverage."""
    assert len(HERO_STORIES) == 3, f"Expected 3 hero stories, got {len(HERO_STORIES)}"
    assert len(MID_STORIES) == 8, f"Expected 8 mid stories, got {len(MID_STORIES)}"
    assert len(BRIEF_COL_A) == 13, f"Expected 13 Col-A briefs, got {len(BRIEF_COL_A)}"
    assert len(BRIEF_COL_B) == 13, f"Expected 13 Col-B briefs, got {len(BRIEF_COL_B)}"

    all_story_keys = (
        [s["headline"].strip().lower() for s in HERO_STORIES]
        + [s["headline"].strip().lower() for s in MID_STORIES]
        + [f"{subj.strip().lower()}: {txt.strip().lower()}" for _, subj, _, txt in BRIEF_COL_A]
        + [f"{subj.strip().lower()}: {txt.strip().lower()}" for _, subj, _, txt in BRIEF_COL_B]
    )
    assert len(all_story_keys) == 37, f"Expected 37 stories, got {len(all_story_keys)}"
    assert len(set(all_story_keys)) == 37, "Duplicate story detected"

    lower_html = doc_html.lower()
    date_box_match = re.search(r'<div class="date-box">(.*?)</div>\s*</div>', doc_html, re.DOTALL)
    assert date_box_match is not None, "Missing .date-box"
    assert "20 nov" not in date_box_match.group(1).lower(), '"20 nov" must not appear inside .date-box'

    for forbidden in ("verified stories", "(est)", "asia closes", "f1 las vegas", "damp friday", "nth-child"):
        assert forbidden not in lower_html, f'Forbidden string found in HTML: "{forbidden}"'

    for region_name, color_hex in REGION_COLORS.items():
        assert color_hex.lower() in lower_html, f"Missing region color for {region_name}: {color_hex}"

    hero_idx = lower_html.find('<section class="hero-grid">')
    assert hero_idx != -1, 'Missing <section class="hero-grid">'
    assert "akvan" not in lower_html[:hero_idx], '"akvan" must not appear before <section class="hero-grid">'

    body_idx = lower_html.find("<body>")
    assert body_idx != -1, "Missing <body>"
    body_lower = lower_html[body_idx:]
    zero_deaths_count = body_lower.count("zero deaths reported by midday")
    assert zero_deaths_count == 1, f'Expected 1 occurrence of "zero deaths reported by midday", found {zero_deaths_count}'


DOM_AUDIT_JS = """() => {
  const selectors = [
    '.masthead', '.utc-ribbon', '.ur-items', '.hero-card', '.mid-card',
    '.b-col', '.b-list', '.b-row', '.f-left', '.map-leg',
    '.date-box', '.ex-row', '.h-kicker', '.m-kicker', '.footer-bar'
  ];
  const errs = [];
  for (const sel of selectors) {
    const els = document.querySelectorAll(sel);
    if (els.length === 0) {
      errs.push(`Missing selector: ${sel}`);
      continue;
    }
    els.forEach((el, idx) => {
      if (el.scrollWidth > el.clientWidth + 1) {
        errs.push(`H-overflow ${sel}[${idx}]: scrollW=${el.scrollWidth} > clientW=${el.clientWidth} text=${JSON.stringify(el.innerText.slice(0, 60))}`);
      }
      if (el.scrollHeight > el.clientHeight + 1) {
        errs.push(`V-overflow ${sel}[${idx}]: scrollH=${el.scrollHeight} > clientH=${el.clientHeight} text=${JSON.stringify(el.innerText.slice(0, 60))}`);
      }
    });
  }
  const heroTops = [...document.querySelectorAll('.h-head')].map(el => Math.round(el.getBoundingClientRect().top));
  if (new Set(heroTops).size > 1) {
    errs.push(`Hero headline baseline mismatch: ${JSON.stringify(heroTops)}`);
  }
  const midTops = [...document.querySelectorAll('.m-head')].map(el => Math.round(el.getBoundingClientRect().top));
  if (midTops.length !== 8 || new Set(midTops.slice(0, 4)).size > 1 || new Set(midTops.slice(4, 8)).size > 1) {
    errs.push(`Mid headline baseline mismatch: ${JSON.stringify(midTops)}`);
  }
  return {
    scrollWidth: document.documentElement.scrollWidth,
    scrollHeight: document.documentElement.scrollHeight,
    heroTops,
    midTops,
    errs
  };
}"""


def render_frontpage(out_path: Path) -> None:
    doc_html = build_html()
    run_negative_self_checks(doc_html)

    tmp_dir = Path(tempfile.gettempdir())
    tmp_html = tmp_dir / "news_image_20261120_render.html"
    tmp_raw_png = tmp_dir / "news_image_20261120_raw.png"
    tmp_html.write_text(doc_html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            launch_kwargs: dict[str, object] = {"headless": True}
            if os.path.exists(CHROME_PATH):
                launch_kwargs["executable_path"] = CHROME_PATH
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(
                viewport={"width": CANVAS_SIZE, "height": CANVAS_SIZE},
                device_scale_factor=1,
            )
            page.goto(tmp_html.as_uri(), wait_until="load")
            page.evaluate("() => document.fonts.ready")
            audit = page.evaluate(DOM_AUDIT_JS)
            print(
                f"DOM_AUDIT: scrollWidth={audit['scrollWidth']} "
                f"scrollHeight={audit['scrollHeight']} errs={len(audit['errs'])}"
            )
            for err in audit["errs"]:
                print(f"  OVERFLOW: {err}")
            assert audit["scrollWidth"] == CANVAS_SIZE, f"scrollWidth={audit['scrollWidth']}"
            assert audit["scrollHeight"] == CANVAS_SIZE, f"scrollHeight={audit['scrollHeight']}"
            assert audit["errs"] == [], f"DOM clipping detected: {audit['errs']}"

            page.screenshot(path=str(tmp_raw_png), type="png", full_page=False)
            browser.close()
    finally:
        if tmp_html.exists():
            tmp_html.unlink()

    with Image.open(tmp_raw_png) as img:
        rgb = img.convert("RGB")
        assert rgb.size == (CANVAS_SIZE, CANVAS_SIZE), f"Unexpected size {rgb.size}"
        rgb.save(out_path, format="PNG", optimize=True)

    if tmp_raw_png.exists():
        tmp_raw_png.unlink()

    size_bytes = out_path.stat().st_size
    assert size_bytes <= MAX_BYTES, f"PNG exceeds 1 MiB cap: {size_bytes} bytes"
    print(f"RENDER_OK: path={out_path} dims={CANVAS_SIZE}x{CANVAS_SIZE} bytes={size_bytes}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Friday 20 Nov 2026 front-page PNG.")
    parser.add_argument("--out", default="entry.png", help="Output PNG path")
    args = parser.parse_args()
    render_frontpage(Path(args.out).resolve())


if __name__ == "__main__":
    main()
