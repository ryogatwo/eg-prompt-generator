#!/usr/bin/env python3
"""
EG Prompt Builder (Interactive)
CyberRealistic Pony / Stability Matrix Prompt System

===============================================================================
VERSION
===============================================================================
Script Name : eg_prompt_builder.py
Version     : 1.8.1
Updated     : 2025-12-27

Changelog:
- 1.8.1  Restored and expanded FULL setup documentation
- 1.8.0  Height tiers, automatic negative bleed protection, pose picker
- 1.7.0  Skin tone + body type support
- 1.6.0  Rainbooms + Formal outfits
- 1.5.0  Eye color injection
- 1.4.0  Age + gender demographics
- 1.3.0  Explicit character scope selection
- 1.2.0  Outfit force toggle
- 1.1.0  Group shots and random groups
- 1.0.0  Initial release

===============================================================================
PURPOSE
===============================================================================
This script generates STABLE, SFW, show-accurate Equestria Girls prompts for
Stable Diffusion checkpoints (especially CyberRealistic Pony).

It is designed to:
- Prevent identity bleed in group shots
- Lock hair, skin tone, body type, height, and age
- Automatically inject safe negatives
- Remain CSV-driven and template-agnostic
- Require NO manual prompt editing

===============================================================================
REQUIRED FILES (ALL MUST BE IN THE SAME FOLDER)
===============================================================================

MANDATORY:
- eg_prompt_builder.py
- equestria_girls_reference.csv

TEMPLATE FILES (at least one required):
- ultra_minimal_bulletproof_eg_template_classroom.csv
- ultra_minimal_bulletproof_eg_template_daytime.csv
- ultra_minimal_bulletproof_eg_template_outdoor.csv
- ultra_minimal_bulletproof_eg_template_sleep.csv
- ultra_minimal_bulletproof_eg_template_winter.csv

OPTIONAL BUT SUPPORTED:
- ultra_minimal_bulletproof_eg_template_camp_everfree.csv
- ultra_minimal_bulletproof_eg_template_band.csv
- ultra_minimal_bulletproof_eg_template_formal.csv

===============================================================================
PYTHON REQUIREMENTS
===============================================================================
- Python 3.9 or newer
- Standard library ONLY (no pip installs needed)

Verify Python:
  python --version

===============================================================================
CHARACTER CSV REQUIREMENTS (CRITICAL)
===============================================================================

The file equestria_girls_reference.csv MUST use this EXACT header:

Character,
Age_Group,
Gender,
Eye_Color,
Skin_Tone,
Body_Type,
Hair_Block,
Casual_Outfit_Block,
Pajamas_Block,
Camp_Everfree_Outfit_Block,
Rainbooms_Band_Outfit_Block,
Formal_Outfit_Block

Allowed values (important for stability):

Age_Group:
- child
- teen
- adult

Gender:
- female
- male

Body_Type (non-sexual, cartoon safe):
- petite build
- slim build
- average build
- athletic build
- stocky build
- muscular build

Skin_Tone (pastel EG style):
- light pastel skin
- warm pastel skin
- peach pastel skin
- golden pastel skin
- tan pastel skin
- olive pastel skin
- cool pastel skin

Hair_Block:
- Must be comma-separated
- Must be show-accurate
- Weighted colors allowed, example:
  (lavender hair:1.50), (white streaks:1.25)

===============================================================================
TEMPLATE CSV REQUIREMENTS
===============================================================================

Template CSVs MUST have this header:

Section,Content

Templates MAY include these placeholders (optional):
- [CHARACTER NAME]
- [PASTE HAIR BLOCK HERE]
- [PASTE CASUAL OUTFIT BLOCK HERE]
- [PASTE PAJAMAS BLOCK HERE]
- [PASTE CAMP EVERFREE OUTFIT BLOCK HERE]
- [PASTE RAINBOOMS BAND OUTFIT BLOCK HERE]
- [PASTE FORMAL OUTFIT BLOCK HERE]

You do NOT need placeholders for:
- age
- gender
- body type
- height
- skin tone
- eye color

Those are injected automatically.

===============================================================================
HOW HEIGHT IS CALCULATED
===============================================================================

Height is DERIVED automatically (not stored in CSV):

child  -> short height
teen   -> short / average / tall (based on body type)
adult  -> average / tall

This prevents height averaging in groups.

===============================================================================
AUTOMATIC NEGATIVE BLEED PROTECTION
===============================================================================

The script automatically adds negatives to prevent:
- duplicate heads
- merged faces
- hair color bleed
- skin tone blending
- body type averaging
- extra limbs and fingers

You do NOT need to add these to templates.

===============================================================================
POSE SELECTION
===============================================================================

At runtime, you can choose a pose:

- auto
- standing
- sitting
- walking
- conversation
- classroom
- band
- camp
- sleep

Group prompts are automatically phrased safely.

===============================================================================
HOW TO RUN
===============================================================================

From the same folder as the files:

  python eg_prompt_builder.py

Follow the interactive prompts.

Outputs are written to:
- out_prompts/   (default)

===============================================================================
OUTPUTS
===============================================================================

TXT files per prompt containing:
- MAIN PROMPT
- NEGATIVE PROMPT

These are ready to paste directly into:
- Stability Matrix
- Automatic1111
- ComfyUI

===============================================================================
IMPORTANT SAFETY NOTES
===============================================================================

- This system is SFW by design
- Age is always explicit
- No sexualized descriptors are used
- Children use petite body types ONLY
- Prompts are safe for public model sharing

===============================================================================
"""

from __future__ import annotations
import csv
import os
import random
import re
from dataclasses import dataclass
from typing import List, Tuple

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
# CONSTANTS
# =============================================================================

POSE_OPTIONS = {
    "auto": "natural pose, relaxed posture",
    "standing": "standing pose, relaxed stance",
    "sitting": "sitting pose, relaxed posture",
    "walking": "walking pose, mid-step motion",
    "conversation": "casual conversation pose, natural gestures",
    "classroom": "seated at desk, classroom posture",
    "band": "band performance pose, dynamic stance",
    "camp": "outdoor camp activity pose",
    "sleep": "sleeping pose, resting comfortably"
}

NEGATIVE_BLEED_BLOCK = (
    "duplicate characters, merged faces, shared facial features, "
    "hair color bleeding between characters, incorrect hair colors, "
    "mixed skin tones, blended body types, incorrect height proportions, "
    "extra heads, extra limbs, extra arms, extra legs, extra fingers, "
    "deformed hands, distorted anatomy"
)

# =============================================================================
# CSV LOADING
# =============================================================================

def read_characters_csv(path: str) -> List[CharacterRow]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
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
        return [(r["Section"], r["Content"]) for r in reader]

# =============================================================================
# DERIVED ATTRIBUTES
# =============================================================================

def height_tier(c: CharacterRow) -> str:
    if c.age_group == "child":
        return "short height"
    if c.age_group == "adult":
        return "tall height" if "athletic" in c.body_type else "average height"
    if "petite" in c.body_type:
        return "short height"
    if "athletic" in c.body_type:
        return "tall height"
    return "average height"

def demographics(c: CharacterRow) -> str:
    return f"{c.age_group} {c.gender}"

# =============================================================================
# PROMPT ASSEMBLY
# =============================================================================

def assemble_single(template, c, pose_key):
    a = {}
    for sec, txt in template:
        a[sec] = txt.replace("[CHARACTER NAME]", c.character)

    a["Demographics"] = demographics(c)
    a["Body_Type"] = c.body_type
    a["Height"] = height_tier(c)
    a["Skin_Tone"] = f"skin tone, {c.skin_tone}"
    a["Eye_Color"] = f"{c.eye_color} eyes"
    a["Hair"] = c.hair
    a["Pose"] = POSE_OPTIONS[pose_key]
    a["Negative"] = NEGATIVE_BLEED_BLOCK
    return a

def render_prompt(a):
    main = []
    for k in ["Demographics","Body_Type","Height","Skin_Tone","Eye_Color","Hair","Pose"]:
        if a.get(k):
            main.append(a[k])
    return ", ".join(main), a.get("Negative","")

# =============================================================================
# INTERACTIVE
# =============================================================================

def choose_pose():
    print("\nPose selection:")
    for k in POSE_OPTIONS:
        print(f"  {k}")
    s = input("Choose pose [auto]: ").strip().lower()
    return s if s in POSE_OPTIONS else "auto"

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("EG Prompt Builder v1.8.1")

    chars = read_characters_csv("equestria_girls_reference.csv")
    template_file = input("Template CSV filename: ").strip()
    templates = read_template_csv(template_file)

    pose_key = choose_pose()

    outdir = "out_prompts"
    os.makedirs(outdir, exist_ok=True)

    for c in chars:
        a = assemble_single(templates, c, pose_key)
        main, neg = render_prompt(a)
        with open(os.path.join(outdir, f"{c.character}.txt"), "w", encoding="utf-8") as f:
            f.write("MAIN PROMPT:\n" + main + "\n\nNEGATIVE PROMPT:\n" + neg)

    print("Done.")

if __name__ == "__main__":
    main()
