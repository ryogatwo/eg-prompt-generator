#!/usr/bin/env python3
"""
EG Prompt Builder (Interactive)
CyberRealistic Pony Prompt System

===============================================================================
VERSION
===============================================================================
Version: 1.7.0
Last Updated: 2025-12-27

Changelog:
- Added Skin_Tone + Body_Type support
- Fully stabilized hair blocks
- Expanded outfit modes: Casual, Pajamas, Camp Everfree, Rainbooms, Formal
- Explicit character scope selection
- Group-safe prompt assembly
- No template placeholders required for new fields

===============================================================================
SETUP (STEP BY STEP)
===============================================================================
1) Place these files in ONE folder:
   - eg_prompt_builder.py
   - equestria_girls_reference.csv
   - One or more template CSV files

2) Python 3.9+ required (standard library only)

3) Character CSV MUST include columns:
   Character,Age_Group,Gender,Eye_Color,Skin_Tone,Body_Type,
   Hair_Block,Casual_Outfit_Block,Pajamas_Block,
   Camp_Everfree_Outfit_Block,Rainbooms_Band_Outfit_Block,Formal_Outfit_Block

4) Run:
   python eg_prompt_builder.py
===============================================================================
"""

from __future__ import annotations
import csv
import os
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


# =============================================================================
# CONSTANTS
# =============================================================================

PLACEHOLDERS = {
    "name": "[CHARACTER NAME]",
    "hair": "[PASTE HAIR BLOCK HERE]",
    "casual": "[PASTE CASUAL OUTFIT BLOCK HERE]",
    "pajamas": "[PASTE PAJAMAS BLOCK HERE]",
    "camp": "[PASTE CAMP EVERFREE OUTFIT BLOCK HERE]",
    "band": "[PASTE RAINBOOMS BAND OUTFIT BLOCK HERE]",
    "formal": "[PASTE FORMAL OUTFIT BLOCK HERE]",
}


# =============================================================================
# DATA MODEL
# =============================================================================

@dataclass
class CharacterRow:
    character: str
    age_group: str
    gender: str
    eye_color: str
    skin_tone: str
    body_type: str
    hair: str
    casual: str
    pajamas: str
    camp: str
    band: str
    formal: str


# =============================================================================
# CSV LOADING
# =============================================================================

def read_characters_csv(path: str) -> List[CharacterRow]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "Character","Age_Group","Gender","Eye_Color",
            "Skin_Tone","Body_Type",
            "Hair_Block","Casual_Outfit_Block","Pajamas_Block",
            "Camp_Everfree_Outfit_Block",
            "Rainbooms_Band_Outfit_Block",
            "Formal_Outfit_Block",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Character CSV missing columns: {sorted(missing)}")

        rows = []
        for r in reader:
            rows.append(CharacterRow(
                character=r["Character"].strip(),
                age_group=r["Age_Group"].strip().lower(),
                gender=r["Gender"].strip().lower(),
                eye_color=r["Eye_Color"].strip().lower(),
                skin_tone=r["Skin_Tone"].strip().lower(),
                body_type=r["Body_Type"].strip().lower(),
                hair=r["Hair_Block"].strip(),
                casual=r["Casual_Outfit_Block"].strip(),
                pajamas=r["Pajamas_Block"].strip(),
                camp=r["Camp_Everfree_Outfit_Block"].strip(),
                band=r["Rainbooms_Band_Outfit_Block"].strip(),
                formal=r["Formal_Outfit_Block"].strip(),
            ))
        return rows


def read_template_csv(path: str) -> List[Tuple[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not {"Section","Content"} <= set(reader.fieldnames or []):
            raise ValueError("Template CSV must contain Section,Content headers")
        return [(r["Section"].strip(), r["Content"].strip()) for r in reader]


# =============================================================================
# HELPERS
# =============================================================================

def slugify(s: str) -> str:
    return re.sub(r"[^\w]+", "_", s.lower()).strip("_")


def template_kind_from_filename(path: str) -> str:
    name = os.path.basename(path).lower()
    for k in ["sleep","camp","band","formal","winter","classroom","outdoor","daytime"]:
        if k in name:
            return k
    return "default"


def demographics(c: CharacterRow) -> str:
    if c.age_group == "child":
        return f"child {c.gender}"
    if c.age_group == "teen":
        return f"teen {c.gender}"
    return f"adult {c.gender}"


def outfit_block(c: CharacterRow, mode: str) -> str:
    return {
        "casual": c.casual,
        "pajamas": c.pajamas,
        "camp": c.camp,
        "band": c.band,
        "formal": c.formal,
    }.get(mode, c.casual)


def resolve_outfit(kind: str, forced: str) -> str:
    if forced != "auto":
        return forced
    if kind == "sleep":
        return "pajamas"
    if kind == "camp":
        return "camp"
    if kind == "band":
        return "band"
    if kind == "formal":
        return "formal"
    return "casual"


# =============================================================================
# ASSEMBLY
# =============================================================================

def assemble_single(template, c, kind, forced):
    mode = resolve_outfit(kind, forced)
    assembled = {}

    for sec, txt in template:
        txt = txt.replace(PLACEHOLDERS["name"], c.character)
        txt = txt.replace(PLACEHOLDERS["hair"], c.hair)
        txt = txt.replace(PLACEHOLDERS["casual"], c.casual)
        txt = txt.replace(PLACEHOLDERS["pajamas"], c.pajamas)
        txt = txt.replace(PLACEHOLDERS["camp"], c.camp)
        txt = txt.replace(PLACEHOLDERS["band"], c.band)
        txt = txt.replace(PLACEHOLDERS["formal"], c.formal)
        assembled[sec] = txt

    assembled["Demographics"] = demographics(c)
    assembled["Body_Type"] = c.body_type
    assembled["Skin_Tone"] = f"skin tone, {c.skin_tone}"
    assembled["Eye_Color"] = f"{c.eye_color} eyes"

    return assembled


def assemble_group(template, chars, kind, forced):
    mode = resolve_outfit(kind, forced)
    assembled = {}

    for sec, txt in template:
        assembled[sec] = txt.replace(PLACEHOLDERS["name"], " and ".join(c.character for c in chars))

    assembled["Character_Identity"] = ", ".join(c.character for c in chars)
    assembled["Hair_Block"] = ", ".join(f"{c.character}, {c.hair}" for c in chars)
    assembled["Demographics"] = ", ".join(demographics(c) for c in chars)
    assembled["Body_Type"] = ", ".join(f"{c.character}, {c.body_type}" for c in chars)
    assembled["Skin_Tone"] = ", ".join(f"{c.character}, skin tone, {c.skin_tone}" for c in chars)
    assembled["Eye_Color"] = ", ".join(f"{c.character}, {c.eye_color} eyes" for c in chars)
    assembled["Clothing"] = ", ".join(outfit_block(c, mode) for c in chars)

    return assembled


def render_prompt(a):
    main = []
    neg = []
    settings = []

    for k in [
        "Character_Identity","Demographics","Body_Type","Skin_Tone","Eye_Color",
        "Hair_Block","Clothing","Pose","Environment","Lighting","Mood"
    ]:
        if a.get(k):
            main.append(a[k].strip(", "))

    for k in a:
        if k.startswith("Negative"):
            neg.append(a[k])

    for k in a:
        if k.startswith("Recommended"):
            settings.append(f"{k}: {a[k]}")

    return ", ".join(main), ", ".join(neg), "\n".join(settings)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("EG Prompt Builder v1.7.0")

    char_csv = input("Character CSV [equestria_girls_reference.csv]: ").strip() or "equestria_girls_reference.csv"
    templates = input("Template CSVs (comma separated): ").split(",")
    outdir = input("Output folder [out_prompts]: ").strip() or "out_prompts"

    os.makedirs(outdir, exist_ok=True)

    chars = read_characters_csv(char_csv)

    print("\nOutfit mode: auto, casual, pajamas, camp, band, formal")
    forced = input("Choose [auto]: ").strip() or "auto"

    template_sets = [(template_kind_from_filename(t), read_template_csv(t.strip()), t.strip()) for t in templates if t.strip()]

    for c in chars:
        for kind, tmpl, name in template_sets:
            assembled = assemble_single(tmpl, c, kind, forced)
            main, neg, settings = render_prompt(assembled)
            fname = f"{slugify(c.character)}__{kind}.txt"
            with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
                f.write(main)

    print("Done.")


if __name__ == "__main__":
    main()
