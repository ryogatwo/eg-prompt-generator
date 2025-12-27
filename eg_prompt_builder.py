#!/usr/bin/env python3
"""
EG Prompt Builder (Interactive)
CyberRealistic Pony prompt assembler for singles + groups, CSV-driven.

===============================================================================
VERSIONING
===============================================================================
Script Name: eg_prompt_builder.py
Version:     1.4.0
Last Change: 2025-12-26

Changelog
- 1.4.0  Added Demographics Injection (Age_Group + Gender) into prompts
- 1.3.0  Added Explicit Character Selection (All / One / Multiple) for entire run
- 1.2.0  Added Outfit Force Toggle (Auto / Casual / Pajamas / Camp Everfree)
- 1.1.0  Added Group shots (manual + random) and "Generate everything"
- 1.0.0  Initial CSV template-driven prompt builder

If you change logic or CSV schema, bump Version and add a changelog line.
===============================================================================


===============================================================================
STEP-BY-STEP SETUP (READ THIS ONCE, SAVE FUTURE YOU)
===============================================================================

STEP 1) Put these files in ONE folder
- eg_prompt_builder.py   (this script)
- equestria_girls_reference.csv   (character data)
- ultra_minimal_bulletproof_eg_template_sleep.csv
- ultra_minimal_bulletproof_eg_template_daytime.csv
- ultra_minimal_bulletproof_eg_template_classroom.csv
- ultra_minimal_bulletproof_eg_template_outdoor.csv
- ultra_minimal_bulletproof_eg_template_winter.csv
- optional: ultra_minimal_bulletproof_eg_template_camp_everfree.csv
  (or any template filename containing "camp" or "everfree" will be treated as camp)

STEP 2) Make sure Python works
- Install Python 3.9+ (3.10+ recommended)
- No extra packages required (uses only standard library)

STEP 3) Confirm your Character CSV header is EXACT
Your equestria_girls_reference.csv MUST have this header line exactly:

Character,Age_Group,Gender,Hair_Block,Casual_Outfit_Block,Pajamas_Block,Camp_Everfree_Outfit_Block

Allowed values:
- Age_Group: child | teen | adult
- Gender:    female | male

Notes:
- Age/Gender are injected into prompts automatically (you do NOT need template placeholders).
- Keep character names consistent, you must type them exactly for manual groups.

STEP 4) Confirm your Template CSV header is EXACT
Each template CSV must have:

Section,Content

Each row is a section name and its content. Content can include placeholders:
- [CHARACTER NAME]
- [PASTE HAIR BLOCK HERE]
- [PASTE CASUAL OUTFIT BLOCK HERE]
- [PASTE PAJAMAS BLOCK HERE]
- [PASTE CAMP EVERFREE OUTFIT BLOCK HERE]

You do NOT need a demographics placeholder.
The script injects a "Demographics" section automatically.

STEP 5) Run the script
From that folder:

python eg_prompt_builder.py

STEP 6) Answer the prompts (the script is interactive)
You will be asked for:
- Character CSV path (Enter = default)
- Template CSV list (Enter = default list)
- Output folder name (Enter = out_prompts)
- Combined CSV filename (Enter = assembled_prompts.csv)

Then two important run-wide toggles:
A) Character selection scope (applies to all outputs this run)
   1) All characters
   2) One character
   3) Multiple characters

B) Outfit mode (applies to all outputs this run)
   a) Auto (sleep -> pajamas, camp -> camp attire, else -> casual)
   c) Force Casual
   p) Force Pajamas
   e) Force Camp Everfree

Finally, choose a generation mode:
1) Singles (every in-scope character x every template)
2) Manual group (you type the names, must be in-scope)
3) Random groups (random samples from in-scope)
4) Generate everything (singles + optional manual + optional random)

STEP 7) Check outputs
You will get:
- TXT files in your output folder (default out_prompts/)
- A combined CSV inside that output folder

TXT format:
MAIN PROMPT:
...
NEGATIVE PROMPT:
...
SETTINGS:
...

Combined CSV columns:
Mode, Character_Scope, Forced_Outfit_Mode, Resolved_Outfit_Mode, Group_Name, Character,
Template_Kind, Template_File, Main_Prompt, Negative_Prompt, Settings, Output_File

STEP 8) Troubleshooting
- "Character CSV missing columns": Header does not match EXACTLY.
- "Template CSV missing columns": Template header must be Section,Content.
- "Not found in selected character scope": You typed a name not present in the CSV OR not included by scope.
- Double heads: lower CFG slightly, keep prompts minimal, avoid conflicting descriptors.
- Bad hands: keep the "Hands" section simple, do more seeds, don't crank CFG.

===============================================================================
SAFETY + CONSISTENCY NOTES
===============================================================================
- This system is designed for SFW prompt generation.
- Age tags prevent unwanted "aging drift" by making age explicit.
- For child characters, keep outfits modest and non-suggestive.
- For group shots, keep group sizes small for best identity stability (2-3 ideal).

===============================================================================
"""

from __future__ import annotations
import csv
import os
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


# Placeholders used inside template CSV files.
# Templates can use any/all of these, but the script will also run if some are absent.
PLACEHOLDERS = {
    "name": "[CHARACTER NAME]",
    "hair": "[PASTE HAIR BLOCK HERE]",
    "casual": "[PASTE CASUAL OUTFIT BLOCK HERE]",
    "pajamas": "[PASTE PAJAMAS BLOCK HERE]",
    "camp": "[PASTE CAMP EVERFREE OUTFIT BLOCK HERE]",
}


@dataclass
class CharacterRow:
    """One character entry from equestria_girls_reference.csv"""
    character: str
    age_group: str  # child / teen / adult
    gender: str     # female / male
    hair: str
    casual: str
    pajamas: str
    camp: str


# -----------------------------
# CSV IO
# -----------------------------
def read_characters_csv(path: str) -> List[CharacterRow]:
    """
    Reads the character reference CSV.
    REQUIRED HEADERS:
      Character, Age_Group, Gender, Hair_Block, Casual_Outfit_Block, Pajamas_Block, Camp_Everfree_Outfit_Block
    """
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {
            "Character",
            "Age_Group",
            "Gender",
            "Hair_Block",
            "Casual_Outfit_Block",
            "Pajamas_Block",
            "Camp_Everfree_Outfit_Block",
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
                hair=(r.get("Hair_Block") or "").strip(),
                casual=(r.get("Casual_Outfit_Block") or "").strip(),
                pajamas=(r.get("Pajamas_Block") or "").strip(),
                camp=(r.get("Camp_Everfree_Outfit_Block") or "").strip(),
            ))
        return rows


def read_template_csv(path: str) -> List[Tuple[str, str]]:
    """
    Reads a template CSV.
    REQUIRED HEADERS:
      Section, Content
    """
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"Section", "Content"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Template CSV missing columns: {sorted(missing)}")

        items: List[Tuple[str, str]] = []
        for r in reader:
            sec = (r.get("Section") or "").strip()
            content = (r.get("Content") or "").strip()
            if sec:
                items.append((sec, content))
        return items


# -----------------------------
# Helpers
# -----------------------------
def slugify(s: str) -> str:
    """Converts a string into a safe filename slug."""
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]+", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_") or "item"


def template_kind_from_filename(path: str) -> str:
    """
    Infers template kind from filename.
    Used for AUTO outfit mode.
    Convention:
      * contains classroom -> classroom
      * contains daytime   -> daytime
      * contains outdoor   -> outdoor
      * contains winter    -> winter
      * contains camp/everfree -> camp
      * otherwise -> sleep
    """
    base = os.path.basename(path).lower()
    if "classroom" in base:
        return "classroom"
    if "daytime" in base:
        return "daytime"
    if "outdoor" in base:
        return "outdoor"
    if "winter" in base:
        return "winter"
    if "camp" in base or "everfree" in base:
        return "camp"
    return "sleep"


def parse_list(s: str) -> List[str]:
    """Parses comma- or semicolon-separated lists."""
    parts = re.split(r"[;,]", s)
    return [p.strip() for p in parts if p.strip()]


def build_lookup(rows: List[CharacterRow]) -> Dict[str, CharacterRow]:
    """Case-insensitive lookup for Character names."""
    return {r.character.lower(): r for r in rows}


# -----------------------------
# Character scope selection
# -----------------------------
def prompt_character_scope(rows_all: List[CharacterRow]) -> List[CharacterRow]:
    """
    Lets the user choose which characters are "in scope" for this run.
    This affects:
      - singles
      - manual groups (must choose from scope)
      - random groups (only draw from scope)
      - generate everything
    """
    print("\nCharacter selection (applies to ALL modes this run):")
    print("  1) All characters")
    print("  2) Select ONE character")
    print("  3) Select MULTIPLE characters")

    lookup_all = {r.character.lower(): r for r in rows_all}

    while True:
        s = input("Choose 1 / 2 / 3 [1]: ").strip()
        if s == "" or s == "1":
            return rows_all

        if s == "2":
            name = input("Enter character name (exact match): ").strip()
            r = lookup_all.get(name.lower())
            if not r:
                raise ValueError(f"Not found in character CSV: {name}")
            return [r]

        if s == "3":
            names = input("Enter character names (comma-separated): ").strip()
            selected: List[CharacterRow] = []
            missing: List[str] = []
            for n in parse_list(names):
                r = lookup_all.get(n.lower())
                if r:
                    selected.append(r)
                else:
                    missing.append(n)
            if missing:
                raise ValueError(f"Not found in character CSV: {missing}")
            if not selected:
                raise ValueError("No valid characters selected.")
            return selected


# -----------------------------
# Outfit mode toggle
# -----------------------------
def prompt_outfit_force() -> str:
    """
    Global outfit mode toggle for this run.
    Returns: 'auto' | 'casual' | 'pajamas' | 'camp'
    """
    print("\nOutfit mode (applies to ALL outputs this run):")
    print("  a) Auto (by template type: sleep=pajamas, camp=camp, else casual)")
    print("  c) Force Casual outfits")
    print("  p) Force Pajamas")
    print("  e) Force Camp Everfree attire")
    while True:
        s = input("Choose a/c/p/e [a]: ").strip().lower()
        if s == "" or s == "a":
            return "auto"
        if s == "c":
            return "casual"
        if s == "p":
            return "pajamas"
        if s == "e":
            return "camp"


def resolve_outfit_mode(kind: str, forced_mode: str) -> str:
    """If user forces a mode, use it. Otherwise use auto per template kind."""
    if forced_mode in ("casual", "pajamas", "camp"):
        return forced_mode
    if kind == "sleep":
        return "pajamas"
    if kind == "camp":
        return "camp"
    return "casual"


def outfit_block_for(c: CharacterRow, outfit_mode: str) -> str:
    """Returns the correct outfit block string for a character row."""
    if outfit_mode == "pajamas":
        return c.pajamas
    if outfit_mode == "camp":
        return c.camp
    return c.casual


# -----------------------------
# Demographics injection
# -----------------------------
def demographics_tags(age_group: str, gender: str) -> str:
    """
    Converts Age_Group + Gender into stable, Pony-friendly prompt tags.
    This is intentionally simple to prevent unwanted drift.
    """
    age_group = (age_group or "").strip().lower()
    gender = (gender or "").strip().lower()

    age_map = {"child": "child", "teen": "teen", "adult": "adult"}
    gender_map = {"female": "female", "male": "male"}

    age = age_map.get(age_group, age_group or "teen")
    gen = gender_map.get(gender, gender or "female")

    if age == "teen" and gen == "female":
        return "teen girl, female"
    if age == "teen" and gen == "male":
        return "teen boy, male"
    if age == "child" and gen == "female":
        return "child girl, female"
    if age == "child" and gen == "male":
        return "child boy, male"
    if age == "adult" and gen == "female":
        return "adult woman, female"
    if age == "adult" and gen == "male":
        return "adult man, male"
    return f"{age}, {gen}"


# -----------------------------
# Group pose helper
# -----------------------------
def group_pose_hint(kind: str, n: int) -> str:
    """Minimal group-shot framing hint."""
    if kind == "classroom":
        return f"group shot, {n} students, sitting at desks, simple composition"
    if kind == "sleep":
        return f"group shot, {n} students, sleepover scene, simple composition"
    if kind == "winter":
        return f"group shot, {n} students, standing together, simple composition"
    if kind == "camp":
        return f"group shot, {n} students, camp everfree scene, simple composition"
    return f"group shot, {n} students, standing together, simple composition"


# -----------------------------
# Assembly
# -----------------------------
def assemble_single(
    template_items: List[Tuple[str, str]],
    c: CharacterRow,
    kind: str,
    forced_mode: str,
) -> Dict[str, str]:
    """
    Assemble a single-character prompt dict.
    - Replaces placeholders where present
    - Injects demographics regardless of template placeholders
    - Applies outfit mode (auto/forced)
    """
    outfit_mode = resolve_outfit_mode(kind, forced_mode)
    assembled: Dict[str, str] = {}

    for sec, content in template_items:
        out = content
        out = out.replace(PLACEHOLDERS["name"], c.character)
        out = out.replace(PLACEHOLDERS["hair"], c.hair)
        out = out.replace(PLACEHOLDERS["casual"], c.casual)
        out = out.replace(PLACEHOLDERS["pajamas"], c.pajamas)
        out = out.replace(PLACEHOLDERS["camp"], c.camp)

        # Clothing fallback injection if the template's Clothing content is blank
        if sec.lower() == "clothing" and not out.strip():
            out = outfit_block_for(c, outfit_mode)

        assembled[sec] = out

    # Demographics is injected even if your template CSV has no "Demographics" section
    assembled["Demographics"] = demographics_tags(c.age_group, c.gender)
    return assembled


def assemble_group(
    template_items: List[Tuple[str, str]],
    group_chars: List[CharacterRow],
    kind: str,
    forced_mode: str,
) -> Dict[str, str]:
    """
    Assemble a group prompt dict.
    - Uses a combined identity string
    - Builds per-character hair+outfit identity block to reduce identity bleed
    - Injects demographics list for the group
    """
    outfit_mode = resolve_outfit_mode(kind, forced_mode)
    n = len(group_chars)
    names = [x.character for x in group_chars]

    assembled: Dict[str, str] = {sec: content for sec, content in template_items}
    assembled["Character_Identity"] = ", ".join(names) + ", equestria girls, group of students"

    parts: List[str] = []
    for c in group_chars:
        outfit = outfit_block_for(c, outfit_mode)
        parts.append(", ".join([c.character, c.hair.rstrip(","), outfit.rstrip(",")]))
    assembled["Hair_Block_Placeholder"] = ", ".join(parts)

    pose_template = (assembled.get("Pose") or "").strip()
    assembled["Pose"] = ", ".join([p for p in [group_pose_hint(kind, n), pose_template] if p])

    # Group stability defaults
    assembled["Body"] = "simple composition, clear spacing between characters"
    assembled["Hands"] = "simple cartoon hands, hands at sides or resting, five fingers per hand"
    assembled["Clothing"] = "modest clothing"

    # Demographics list (one per character)
    assembled["Demographics"] = ", ".join([demographics_tags(x.age_group, x.gender) for x in group_chars])

    # Clear remaining placeholders to prevent bracket text from leaking into output
    for sec, val in list(assembled.items()):
        if not isinstance(val, str):
            continue
        assembled[sec] = (
            val.replace(PLACEHOLDERS["name"], " and ".join(names))
               .replace(PLACEHOLDERS["hair"], "")
               .replace(PLACEHOLDERS["casual"], "")
               .replace(PLACEHOLDERS["pajamas"], "")
               .replace(PLACEHOLDERS["camp"], "")
        ).strip().strip(",")

    return assembled


def render_prompt(assembled: Dict[str, str]) -> Tuple[str, str, str]:
    """
    Converts assembled section dictionary into:
      main prompt string, negative prompt string, settings string
    using a stable section order.
    """
    def get(sec: str) -> str:
        return (assembled.get(sec) or "").strip()

    main_order = [
        "Header",
        "Character_Identity",
        "Demographics",
        "Hair_Block_Placeholder",
        "Head_Structure",
        "Pose",
        "Body",
        "Hands",
        "Clothing",
        "Camp_Everfree_Clothing_Block",
        "Art_Style",
        "Environment",
        "Lighting",
        "Background_Element",
        "Mood",
    ]
    main_parts = [get(s).rstrip(",") for s in main_order if get(s)]
    main_prompt = ", ".join([p for p in main_parts if p])

    neg_parts: List[str] = []
    if get("Negative_Prompt_Header"):
        neg_parts.append(get("Negative_Prompt_Header").rstrip(","))
    for sec in ["Negative_Content_1", "Negative_Content_2", "Negative_Content_3", "Negative_Content_4", "Negative_Content_5"]:
        if get(sec):
            neg_parts.append(get(sec).rstrip(","))
    neg_prompt = ", ".join([p for p in neg_parts if p])

    settings_lines: List[str] = []
    for sec in ["Recommended_CFG", "Recommended_Steps", "Recommended_Sampler", "Recommended_Resolution"]:
        if get(sec):
            settings_lines.append(f"{sec.replace('Recommended_', '')}: {get(sec)}")
    settings = "\n".join(settings_lines)

    return main_prompt, neg_prompt, settings


# -----------------------------
# Interactive prompts
# -----------------------------
def prompt_path(label: str, default: str) -> str:
    s = input(f"{label} [{default}]: ").strip()
    return s or default


def prompt_int(label: str, default: int, minv: int = 0, maxv: int = 10_000) -> int:
    s = input(f"{label} [{default}]: ").strip()
    if not s:
        return default
    try:
        v = int(s)
    except ValueError:
        return default
    return max(minv, min(maxv, v))


def prompt_yes_no(label: str, default_yes: bool = True) -> bool:
    default = "Y/n" if default_yes else "y/N"
    s = input(f"{label} ({default}): ").strip().lower()
    if not s:
        return default_yes
    return s in {"y", "yes"}


def prompt_choice() -> str:
    print("\nChoose mode:")
    print("  1) Single-character prompts (ALL characters in-scope x ALL templates)")
    print("  2) Manual group prompts (YOUR chosen group x ALL templates)")
    print("  3) Random group prompts (N groups x ALL templates, drawn from in-scope)")
    print("  4) Generate everything (singles + optional manual group + random groups)")
    while True:
        s = input("Enter 1, 2, 3, or 4: ").strip()
        if s in {"1", "2", "3", "4"}:
            return s


def write_txt(outdir: str, filename: str, main_p: str, neg_p: str, settings: str) -> None:
    with open(os.path.join(outdir, filename), "w", encoding="utf-8") as f:
        f.write("MAIN PROMPT:\n" + main_p + "\n\nNEGATIVE PROMPT:\n" + neg_p)
        if settings:
            f.write("\n\nSETTINGS:\n" + settings + "\n")
        else:
            f.write("\n")


# -----------------------------
# Main
# -----------------------------
def main():
    print("EG Prompt Builder (Interactive)")

    char_csv = prompt_path("Character CSV", "equestria_girls_reference.csv")

    default_templates = [
        "ultra_minimal_bulletproof_eg_template_classroom.csv",
        "ultra_minimal_bulletproof_eg_template_daytime.csv",
        "ultra_minimal_bulletproof_eg_template_outdoor.csv",
        "ultra_minimal_bulletproof_eg_template_sleep.csv",
        "ultra_minimal_bulletproof_eg_template_winter.csv",
        # Optional camp template:
        # "ultra_minimal_bulletproof_eg_template_camp_everfree.csv",
    ]

    print("\nTemplate CSVs (comma or semicolon separated). Press Enter to use defaults:")
    for t in default_templates:
        print(f"  - {t}")
    t_in = input("Templates: ").strip()
    templates = parse_list(t_in) if t_in else default_templates

    outdir = prompt_path("Output folder", "out_prompts")
    combined_csv_name = prompt_path("Combined CSV filename", "assembled_prompts.csv")
    os.makedirs(outdir, exist_ok=True)

    rows_all = read_characters_csv(char_csv)
    rows = prompt_character_scope(rows_all)
    lookup = build_lookup(rows)

    forced_mode = prompt_outfit_force()

    template_pack: List[Tuple[str, List[Tuple[str, str]], str]] = []
    for tpath in templates:
        kind = template_kind_from_filename(tpath)
        items = read_template_csv(tpath)
        template_pack.append((kind, items, tpath))

    scope_names = ", ".join([r.character for r in rows])

    combined_rows: List[Dict[str, str]] = []
    mode = prompt_choice()

    def generate_singles() -> None:
        for c in rows:
            for kind, items, tpath in template_pack:
                assembled = assemble_single(items, c, kind, forced_mode)
                main_p, neg_p, settings = render_prompt(assembled)

                filename = f"{slugify(c.character)}__{kind}.txt"
                write_txt(outdir, filename, main_p, neg_p, settings)

                combined_rows.append({
                    "Mode": "single",
                    "Character_Scope": scope_names,
                    "Forced_Outfit_Mode": forced_mode,
                    "Resolved_Outfit_Mode": resolve_outfit_mode(kind, forced_mode),
                    "Group_Name": "",
                    "Character": c.character,
                    "Template_Kind": kind,
                    "Template_File": os.path.basename(tpath),
                    "Main_Prompt": main_p,
                    "Negative_Prompt": neg_p,
                    "Settings": settings,
                    "Output_File": filename,
                })

    def generate_manual_group() -> None:
        print("\nEnter group character names separated by commas (must match Character column).")
        print("Note: manual group names must be IN-SCOPE for this run.")
        group_str = input("Group: ").strip()
        names = parse_list(group_str)
        if len(names) < 2:
            raise ValueError("Manual group requires at least 2 characters.")

        group_chars: List[CharacterRow] = []
        missing: List[str] = []
        for n in names:
            r = lookup.get(n.lower())
            if r:
                group_chars.append(r)
            else:
                missing.append(n)
        if missing:
            raise ValueError(f"Not found in selected character scope: {missing}")

        for kind, items, tpath in template_pack:
            assembled = assemble_group(items, group_chars, kind, forced_mode)
            main_p, neg_p, settings = render_prompt(assembled)

            group_slug = slugify("_".join([c.character for c in group_chars])[:120])
            filename = f"group__{kind}__{group_slug}.txt"
            write_txt(outdir, filename, main_p, neg_p, settings)

            combined_rows.append({
                "Mode": "group_manual",
                "Character_Scope": scope_names,
                "Forced_Outfit_Mode": forced_mode,
                "Resolved_Outfit_Mode": resolve_outfit_mode(kind, forced_mode),
                "Group_Name": ", ".join([c.character for c in group_chars]),
                "Character": "",
                "Template_Kind": kind,
                "Template_File": os.path.basename(tpath),
                "Main_Prompt": main_p,
                "Negative_Prompt": neg_p,
                "Settings": settings,
                "Output_File": filename,
                })

    def generate_random_groups() -> None:
        group_size = prompt_int("Random group size", 3, minv=2, maxv=10)
        num_groups = prompt_int("How many random groups", 10, minv=1, maxv=10_000)
        seed = prompt_int("Random seed (0 = random each run)", 123, minv=0, maxv=2_147_483_647)
        if seed != 0:
            random.seed(seed)

        pool = rows
        if len(pool) < group_size:
            raise ValueError("Not enough characters in the selected scope for the requested group size.")

        for gi in range(1, num_groups + 1):
            group_chars = random.sample(pool, group_size)
            for kind, items, tpath in template_pack:
                assembled = assemble_group(items, group_chars, kind, forced_mode)
                main_p, neg_p, settings = render_prompt(assembled)

                group_slug = slugify("_".join([c.character for c in group_chars])[:120])
                filename = f"group_rand{gi:03d}__{kind}__{group_slug}.txt"
                write_txt(outdir, filename, main_p, neg_p, settings)

                combined_rows.append({
                    "Mode": "group_random",
                    "Character_Scope": scope_names,
                    "Forced_Outfit_Mode": forced_mode,
                    "Resolved_Outfit_Mode": resolve_outfit_mode(kind, forced_mode),
                    "Group_Name": ", ".join([c.character for c in group_chars]),
                    "Character": "",
                    "Template_Kind": kind,
                    "Template_File": os.path.basename(tpath),
                    "Main_Prompt": main_p,
                    "Negative_Prompt": neg_p,
                    "Settings": settings,
                    "Output_File": filename,
                })

    if mode == "1":
        generate_singles()
    elif mode == "2":
        generate_manual_group()
    elif mode == "3":
        generate_random_groups()
    else:
        print("\nGenerating ALL single-character prompts for selected scope...")
        generate_singles()
        print("Singles done.")

        if prompt_yes_no("Also generate a manual group?", default_yes=False):
            generate_manual_group()

        if prompt_yes_no("Also generate random groups?", default_yes=True):
            generate_random_groups()

    combined_path = os.path.join(outdir, combined_csv_name)
    fieldnames = [
        "Mode",
        "Character_Scope",
        "Forced_Outfit_Mode",
        "Resolved_Outfit_Mode",
        "Group_Name",
        "Character",
        "Template_Kind",
        "Template_File",
        "Main_Prompt",
        "Negative_Prompt",
        "Settings",
        "Output_File",
    ]
    with open(combined_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(combined_rows)

    print("\nDone.")
    print(f"Character scope: {scope_names}")
    print(f"Forced outfit mode: {forced_mode}")
    print(f"Output folder: {outdir}")
    print(f"Combined CSV:  {combined_path}")


if __name__ == "__main__":
    main()
