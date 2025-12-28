
# NOOB EG Prompt Builder – Full System Guide  using CyberRealistic Pony / Stability Matrix #
V 1.9.0

Added eye color

(see comments in eg_prompt_builder.py for setup info and up to date notes)

This project generates stable, SFW, show-accurate Equestria Girls prompts using CSV-driven characters and templates.

It supports:

    	Singles
    	Manual groups
    	Random groups
    	Generate everything
    	Camp Everfree
    	Crystal Prep
    	Students + adult staff
    	Automatic age and gender injection

## 	Required Files ##


**Place all files in the SAME folder:**

Scripts

    eg_prompt_builder.py

Character Data

    equestria_girls_reference.csv

Templates

    ultra_minimal_bulletproof_eg_template_classroom.csv
    ultra_minimal_bulletproof_eg_template_daytime.csv
    ultra_minimal_bulletproof_eg_template_outdoor.csv
    ultra_minimal_bulletproof_eg_template_sleep.csv
    ultra_minimal_bulletproof_eg_template_winter.csv
    ultra_minimal_bulletproof_eg_template_camp_everfree.csv (optional but recommended)

## 	Character CSV Format (IMPORTANT) ##

**The character CSV MUST use this exact header:**

Character,Age_Group,Gender,Eye_Color,Hair_Block,Casual_Outfit_Block,Pajamas_Block,Camp_Everfree_Outfit_Block,Rainbooms_Band_Outfit_Block,Formal_Outfit_Block

Age_Group values

    	child
    	teen
    	adult

Gender values

    	female
    	male

These are automatically injected into prompts as:

    	child girl / child boy
    	teen girl / teen boy
    	adult woman / adult man

This prevents model aging drift and keeps outputs safe.

## 	Template Placeholders ##

Templates may include:

    	[CHARACTER NAME]
    	[PASTE HAIR BLOCK HERE]
    	[PASTE CASUAL OUTFIT BLOCK HERE]
    	[PASTE PAJAMAS BLOCK HERE]
    	[PASTE CAMP EVERFREE OUTFIT BLOCK HERE]

You do NOT need a demographics placeholder. Age and gender are injected automatically by the script.

## 	Running the Script ##

From the same folder, run:

`python eg_prompt_builder.py`

## 	Interactive Menus Explained ##

**Character Selection (applies to ALL modes)**

    1	All characters
    2	Select ONE character
    3	Select MULTIPLE characters

Random groups and manual groups will ONLY use the selected scope.

**Outfit Mode (Global, applies to ALL outputs)**

    	Auto
    	sleep templates -> pajamas
    	camp templates -> camp attire
    	everything else -> casual
    	Force Casual
    	Force Pajamas
    	Force Camp Everfree

**Generation Modes**

1	Singles

    	One prompt per character x per template

2	Manual Group

    	You specify characters by name

3	Random Groups

    	Randomly sampled from selected scope

4	Generate Everything

    	Singles
    
    	Optional manual group
    
    	Optional random groups

## 	Outputs ##

**TXT Files** 

Written to your chosen output folder (default: out_prompts)

Examples:

    	apple_bloom__classroom.txt
    	group__camp__sunset_shimmer_twilight_sparkle.txt
    	group_rand003__winter__rarity_fluttershy_applejack.txt

Each TXT includes:

    	MAIN PROMPT
    	NEGATIVE PROMPT
    	RECOMMENDED SETTINGS

**Combined CSV** 

A single CSV containing everything generated.

Columns include:

    	Mode
    	Character_Scope
    	Forced_Outfit_Mode
    	Resolved_Outfit_Mode
    	Group_Name
    	Character
    	Template_Kind
    	Template_File
    	Main_Prompt
    	Negative_Prompt
    	Settings
    	Output_File

This is ideal for batch runs or external tools.

## 	Stability Matrix Settings (CyberRealistic Pony) ##

**Recommended Base Settings**

    	Sampler: DPM++ 2M Karras
    	Steps: 24
    	CFG: 4.1
    	Clip Skip: 1
    	Batch size: 1
    	Batch count: 6-12

Resolution

    	Single character: 576x576
    	Groups: 640x512
    	Sleep scenes: 512x512

Troubleshooting
    
    	Double heads -> lower CFG (3.8-4.0)
    	Bad hands -> generate more seeds, do not raise CFG
    	Identity bleed -> reduce group size (2-3 max)

## 	Camp Everfree and Staff Notes ##
    
    	Camp Everfree attire is supported per-character
    	Adult staff are tagged as adult man / adult woman
    	Staff outfits are modest and non-student by design

## 	Safety Notes ##

    	This system is SFW by construction
    	Age tags are explicit
    	No sexualized language should be added
    	Keep templates clean and minimal

## 	Summary ##

**This system is:**

    	CSV-driven
    	Modular
    	Safe
    	Stable
    	Expandable

You can add characters, outfits, templates, or entire settings without modifying the core logic.
