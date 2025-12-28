#!/usr/bin/env python3
"""
EG Prompt Builder (Interactive)
CyberRealistic Pony / Stability Matrix Prompt System

===============================================================================
VERSION
===============================================================================
Script Name : eg_prompt_builder.py
Version     : 1.10.0
Updated     : 2025-12-27

Changelog:
- 1.10.0 Added fuzzy name matching (manual groups) + fancy ASCII interactive menus
- 1.9.0  Re-added group modes + optional auto-pose per template
- 1.8.1  Full setup notes restored
- 1.8.0  Height tiers, automatic negative bleed protection, pose picker
- 1.7.0  Skin tone + body type support
- 1.6.0  Rainbooms + Formal outfits (CSV support)
- 1.5.0  Eye color injection

===============================================================================
FULL SETUP NOTES
===============================================================================

REQUIRED FILES (ALL IN ONE FOLDER):
- eg_prompt_builder.py
- equestria_girls_reference.csv
- One or more template CSV files (Section,Content)

Character CSV REQUIRED HEADER (EXACT):
Character,Age_Group,Gender,Eye_Color,Skin_Tone,Body_Type,Hair_Block,Casual_Outfit_Block,Pajamas_Block,Camp_Everfree_Outfit_Block,Rainbooms_Band_Outfit_Block,Formal_Outfit_Block

Template CSV REQUIRED HEADER (EXACT):
Section,Content

Optional template placeholders:
- [CHARACTER NAME]

You do NOT need placeholders for:
- demographics, body type, height, skin tone, eye color, hair, negatives, pose
Those are injected automatically.

RUN:
python eg_prompt_builder.py

OUTPUTS:
- Writes TXT prompt files to an output folder (default: out_prompts/)
- Each TXT contains MAIN PROMPT and NEGATIVE PROMPT

POSES:
- You can pick a pose, or choose AUTO which infers from template filename:
  sleep -> sleep, classroom -> classroom, band -> band, camp/everfree -> camp, otherwise -> standing

HEIGHT TIERS (derived automatically):
- child -> short height
- teen -> short/average/tall (based on body type)
- adult -> average/tall

NEGATIVE BLEED PROTECTION:
- Automatically appended to negative prompt (prevents merged faces, hair bleed, extra heads/limbs, etc.)

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
import difflib
import os
import random
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


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

POSE_OPTIONS: Dict[str, str] = {
    "auto": "natural pose, relaxed posture",
    "standing": "standing pose, relaxed stance",
    "sitting": "sitting pose, relaxed posture",
    "walking": "walking pose, mid-step motion",
    "conversation": "casual conversation pose, natural gestures",
    "classroom": "seated at desk, classroom posture",
    "band": "band performance pose, dynamic stance",
    "camp": "outdoor camp activity pose",
    "sleep": "sleeping pose, resting comfortably",
}

AUTO_POSE_BY_TEMPLATE: Dict[str, str] = {
    "sleep": "sleep",
    "classroom": "classroom",
    "band": "band",
    "camp": "camp",
    "everfree": "camp",
    "outdoor": "standing",
    "daytime": "standing",
    "winter": "standing",
    "formal": "standing",
    "gala": "standing",
}

NEGATIVE_BLEED_BLOCK = (
    "duplicate characters, merged faces, shared facial features, "
    "hair color bleeding between characters, incorrect hair colors, "
    "mixed skin tones, blended body types, incorrect height proportions, "
    "extra heads, extra limbs, extra arms, extra legs, extra fingers, "
    "deformed hands, distorted anatomy"
)

DEFAULT_TEMPLATES = [
    "ultra_minimal_bulletproof_eg_template_classroom.csv",
    "ultra_minimal_bulletproof_eg_template_daytime.csv",
    "ultra_minimal_bulletproof_eg_template_outdoor.csv",
    "ultra_minimal_bulletproof_eg_template_sleep.csv",
    "ultra_minimal_bulletproof_eg_template_winter.csv",
]


# =============================================================================
# PRETTY ASCII UI
# =============================================================================

def _term_width(default: int = 80) -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default


def hr(char: str = "═") -> str:
    return char * min(_term_width(), 100)


def box(title: str, lines: List[str]) -> None:
    width = min(max(len(title), *(len(x) for x in lines), 50) + 6, 100)
    top = "╔" + "═" * (width - 2) + "╗"
    mid = "╟" + "─" * (width - 2) + "╢"
    bot = "╚" + "═" * (width - 2) + "╝"

    def pad(s: str) -> str:
        s = s[: width - 6]
        return "║ " + s + " " * (width - 4 - len(s)) + "║"

    print(top)
    print(pad(title))
    print(mid)
    for ln in lines:
        print(pad(ln))
    print(bot)


def menu(title: str, options: List[Tuple[str, str]], default_index: int = 0) -> str:
    """
    options: list of (key, label)
    returns selected key
    """
    lines = []
    for i, (_, label) in enumerate(options, start=1):
        lines.append(f"{i:>2}) {label}")
    lines.append("")
    lines.append(f"Enter 1-{len(options)} (default {default_index+1})")
    box(title, lines)

    while True:
        raw = input("> ").strip()
        if raw == "":
            return options[default_index][0]
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1][0]
        print("Invalid choice, try again.")


def prompt_path(label: str, default: str) -> str:
    box("INPUT", [f"{label}", f"Default: {default}", "Press Enter to accept default"])
    s = input("> ").strip()
    return s or default


def prompt_list(label: str, default_list: List[str]) -> List[str]:
    lines = [label, "Press Enter to use defaults:", *[f"- {x}" for x in default_list], "", "Or type comma-separated list:"]
    box("TEMPLATES", lines)
    s = input("> ").strip()
    if not s:
        return default_list
    parts = [p.strip() for p in re.split(r"[;,]", s) if p.strip()]
    return parts


def prompt_int(label: str, default: int, minv: int, maxv: int) -> int:
    box("NUMBER", [label, f"Default: {default}", f"Range: {minv} to {maxv}"])
    s = input("> ").strip()
    if not s:
        return default
    try:
        v = int(s)
        return max(minv, min(maxv, v))
    except ValueError:
        return default


# =============================================================================
# CSV LOADING
# =============================================================================

def read_characters_csv(path: str) -> List[CharacterRow]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        required = {
            "Character", "Age_Group", "Gender", "Eye_Color", "Skin_Tone", "Body_Type",
            "Hair_Block", "Casual_Outfit_Block", "Pajamas_Block",
            "Camp_Everfree_Outfit_Block", "Rainbooms_Band_Outfit_Block", "Formal_Outfit_Block",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Character CSV missing columns: {sorted(missing)}")

        rows: List[CharacterRow] = []
        for r in reader:
            name = (r.get("Character") or "").strip()
            if not name:
                continue
            rows.append(CharacterRow(
                character=name,
                age_group=(r.get("Age_Group") or "").strip().lower(),
                gender=(r.get("Gender") or "").strip().lower(),
                eye_color=(r.get("Eye_Color") or "").strip().lower(),
                skin_tone=(r.get("Skin_Tone") or "").strip().lower(),
                body_type=(r.get("Body_Type") or "").strip().lower(),
                hair=(r.get("Hair_Block") or "").strip(),
                casual=(r.get("Casual_Outfit_Block") or "").strip(),
                pajamas=(r.get("Pajamas_Block") or "").strip(),
                camp=(r.get("Camp_Everfree_Outfit_Block") or "").strip(),
                band=(r.get("Rainbooms_Band_Outfit_Block") or "").strip(),
                formal=(r.get("Formal_Outfit_Block") or "").strip(),
            ))
        return rows


def read_template_csv(path: str) -> List[Tuple[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not {"Section", "Content"} <= set(reader.fieldnames or []):
            raise ValueError(f"Template CSV must contain Section,Content headers: {path}")
        items: List[Tuple[str, str]] = []
        for r in reader:
            sec = (r.get("Section") or "").strip()
            content = (r.get("Content") or "").strip()
            if sec:
                items.append((sec, content))
        return items


# =============================================================================
# HELPERS
# =============================================================================

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]+", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_") or "item"


def template_kind_from_filename(path: str) -> str:
    p = os.path.basename(path).lower()
    for key in AUTO_POSE_BY_TEMPLATE.keys():
        if key in p:
            return key
    return "default"


def demographics(c: CharacterRow) -> str:
    return f"{c.age_group} {c.gender}"


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


def fuzzy_pick_character(
    typed: str,
    lookup_exact: Dict[str, CharacterRow],
    all_names: List[str],
    cutoff: float = 0.55,
) -> Optional[CharacterRow]:
    """
    Returns the best match for typed.
    - Exact match (case-insensitive) succeeds immediately
    - Otherwise, suggests close matches and lets the user pick
    """
    key = typed.strip().lower()
    if not key:
        return None
    if key in lookup_exact:
        return lookup_exact[key]

    # Closest matches by difflib
    candidates = difflib.get_close_matches(typed, all_names, n=6, cutoff=cutoff)
    if not candidates:
        box("FUZZY MATCH", [f'No close matches found for "{typed}"', "Tip: copy/paste from the Character column."])
        return None

    opts = [("cancel", "Cancel / skip")] + [(c, f'Use "{c}"') for c in candidates]
    picked = menu(f'Name not found: "{typed}"', opts, default_index=1 if len(opts) > 1 else 0)
    if picked == "cancel":
        return None
    return lookup_exact[picked.lower()]


# =============================================================================
# PROMPT ASSEMBLY
# =============================================================================

def assemble_single(template_items: List[Tuple[str, str]], c: CharacterRow, pose_key: str) -> Dict[str, str]:
    a: Dict[str, str] = {}
    for sec, txt in template_items:
        a[sec] = txt.replace("[CHARACTER NAME]", c.character)

    # Inject identity locks
    a["Demographics"] = demographics(c)
    a["Body_Type"] = c.body_type
    a["Height"] = height_tier(c)
    a["Skin_Tone"] = f"skin tone, {c.skin_tone}"
    a["Eye_Color"] = f"{c.eye_color} eyes"
    a["Hair"] = c.hair

    # Pose + negatives
    a["Pose"] = POSE_OPTIONS.get(pose_key, POSE_OPTIONS["auto"])
    a["Negative"] = NEGATIVE_BLEED_BLOCK
    return a


def assemble_group(template_items: List[Tuple[str, str]], chars: List[CharacterRow], pose_key: str) -> Dict[str, str]:
    a: Dict[str, str] = {}
    names = ", ".join(c.character for c in chars)

    for sec, txt in template_items:
        a[sec] = txt.replace("[CHARACTER NAME]", names)

    # Group-safe per-character locks
    a["Demographics"] = ", ".join(demographics(c) for c in chars)
    a["Body_Type"] = ", ".join(f"{c.character}, {c.body_type}" for c in chars)
    a["Height"] = ", ".join(f"{c.character}, {height_tier(c)}" for c in chars)
    a["Skin_Tone"] = ", ".join(f"{c.character}, skin tone, {c.skin_tone}" for c in chars)
    a["Eye_Color"] = ", ".join(f"{c.character}, {c.eye_color} eyes" for c in chars)
    a["Hair"] = ", ".join(f"{c.character}, {c.hair}" for c in chars)

    a["Pose"] = POSE_OPTIONS.get(pose_key, POSE_OPTIONS["auto"])
    a["Negative"] = NEGATIVE_BLEED_BLOCK
    return a


def render_prompt(a: Dict[str, str]) -> Tuple[str, str]:
    order = ["Demographics", "Body_Type", "Height", "Skin_Tone", "Eye_Color", "Hair", "Pose"]
    main = ", ".join(a[k].strip().strip(",") for k in order if a.get(k))
    neg = a.get("Negative", "").strip()
    return main, neg


# =============================================================================
# INTERACTIVE: CHOICES
# =============================================================================

def choose_mode() -> str:
    return menu(
        "GENERATION MODE",
        [
            ("singles", "Singles (one per character)"),
            ("manual_group", "Manual group (you type names, fuzzy matching enabled)"),
            ("random_groups", "Random groups (sample characters randomly)"),
            ("everything", "Generate everything (singles + manual + random)"),
        ],
        default_index=0,
    )


def choose_pose_mode() -> str:
    return menu(
        "POSE MODE",
        [
            ("auto", "AUTO (infer pose from template filename)"),
            ("pick", "Pick one pose manually (apply to all templates)"),
        ],
        default_index=0,
    )


def choose_pose_key() -> str:
    pose_keys = [k for k in POSE_OPTIONS.keys() if k != "auto"]
    opts = [("auto", "auto")] + [(k, k) for k in pose_keys]
    return menu("CHOOSE POSE", opts, default_index=0)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    box("EG PROMPT BUILDER", [
        "CyberRealistic Pony prompt generator",
        "Fuzzy character matching, group modes, auto pose",
        f"Version 1.10.0",
    ])

    char_csv = prompt_path("Character CSV path", "equestria_girls_reference.csv")
    templates = prompt_list("Template CSV list", DEFAULT_TEMPLATES)
    outdir = prompt_path("Output folder", "out_prompts")
    os.makedirs(outdir, exist_ok=True)

    rows = read_characters_csv(char_csv)
    if not rows:
        raise RuntimeError("No characters loaded from CSV.")

    # Lookups for fuzzy matching
    lookup_exact: Dict[str, CharacterRow] = {c.character.lower(): c for c in rows}
    all_names: List[str] = [c.character for c in rows]

    mode = choose_mode()
    pose_mode = choose_pose_mode()

    # Preload templates
    template_pack: List[Tuple[str, List[Tuple[str, str]], str]] = []
    for tpath in templates:
        kind = template_kind_from_filename(tpath)
        items = read_template_csv(tpath)
        template_pack.append((kind, items, tpath))

    # Pose selection behavior
    if pose_mode == "pick":
        forced_pose = choose_pose_key()
    else:
        forced_pose = "auto"

    def resolve_pose_for_template(kind: str) -> str:
        if forced_pose != "auto":
            return forced_pose
        return AUTO_POSE_BY_TEMPLATE.get(kind, "standing")

    def write_txt(filename: str, main_p: str, neg_p: str) -> None:
        path = os.path.join(outdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write("MAIN PROMPT:\n" + main_p + "\n\nNEGATIVE PROMPT:\n" + neg_p + "\n")

    # -------------------------------------------------------------------------
    # Singles
    # -------------------------------------------------------------------------
    def run_singles() -> None:
        box("RUN", [f"Mode: Singles", f"Templates: {len(template_pack)}", f"Characters: {len(rows)}"])
        for c in rows:
            for kind, items, tpath in template_pack:
                pose_key = resolve_pose_for_template(kind)
                a = assemble_single(items, c, pose_key)
                main_p, neg_p = render_prompt(a)
                fname = f"{slugify(c.character)}__{kind}.txt"
                write_txt(fname, main_p, neg_p)

    # -------------------------------------------------------------------------
    # Manual group
    # -------------------------------------------------------------------------
    def run_manual_group() -> None:
        box("MANUAL GROUP", [
            "Type names separated by commas.",
            "Fuzzy matching will suggest close matches if you typo.",
            "Example: twilight sparkl, rarit, pinky pie",
        ])
        raw = input("> ").strip()
        names = [n.strip() for n in re.split(r"[;,]", raw) if n.strip()]
        if len(names) < 2:
            box("ERROR", ["Manual group requires at least 2 names."])
            return

        chosen: List[CharacterRow] = []
        for n in names:
            c = fuzzy_pick_character(n, lookup_exact, all_names)
            if c:
                # Avoid duplicates if user types same person twice
                if c.character.lower() not in {x.character.lower() for x in chosen}:
                    chosen.append(c)

        if len(chosen) < 2:
            box("ERROR", ["Not enough valid characters selected after fuzzy matching."])
            return

        box("GROUP LOCKED", [", ".join(c.character for c in chosen)])

        for kind, items, tpath in template_pack:
            pose_key = resolve_pose_for_template(kind)
            a = assemble_group(items, chosen, pose_key)
            main_p, neg_p = render_prompt(a)
            group_slug = slugify("_".join([c.character for c in chosen])[:120])
            fname = f"group_manual__{kind}__{group_slug}.txt"
            write_txt(fname, main_p, neg_p)

    # -------------------------------------------------------------------------
    # Random groups
    # -------------------------------------------------------------------------
    def run_random_groups() -> None:
        box("RANDOM GROUPS", [
            "Creates random groups from the character roster.",
            "Tip: group size 2-3 is the most stable.",
        ])
        group_size = prompt_int("Random group size", default=3, minv=2, maxv=min(10, len(rows)))
        count = prompt_int("How many random groups", default=5, minv=1, maxv=5000)
        seed = prompt_int("Random seed (0 = different each run)", default=123, minv=0, maxv=2_147_483_647)
        if seed != 0:
            random.seed(seed)

        for i in range(1, count + 1):
            grp = random.sample(rows, group_size)
            for kind, items, tpath in template_pack:
                pose_key = resolve_pose_for_template(kind)
                a = assemble_group(items, grp, pose_key)
                main_p, neg_p = render_prompt(a)
                group_slug = slugify("_".join([c.character for c in grp])[:120])
                fname = f"group_rand{i:03d}__{kind}__{group_slug}.txt"
                write_txt(fname, main_p, neg_p)

    # -------------------------------------------------------------------------
    # Execute selected mode(s)
    # -------------------------------------------------------------------------
    if mode == "singles":
        run_singles()
    elif mode == "manual_group":
        run_manual_group()
    elif mode == "random_groups":
        run_random_groups()
    else:
        run_singles()
        # Manual group optional
        again = menu("ADD MANUAL GROUP?", [("yes", "Yes"), ("no", "No")], default_index=1)
        if again == "yes":
            run_manual_group()
        # Random groups optional
        again2 = menu("ADD RANDOM GROUPS?", [("yes", "Yes"), ("no", "No")], default_index=0)
        if again2 == "yes":
            run_random_groups()

    box("DONE", [
        f"Output folder: {outdir}",
        "TXT files contain MAIN PROMPT and NEGATIVE PROMPT",
        "Paste directly into Stability Matrix / A1111 / ComfyUI",
    ])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
