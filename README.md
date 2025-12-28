
# NOOB EG Prompt Builder – Full System Guide  using CyberRealistic Pony / Stability Matrix #

EG PROMPT BUILDER

CyberRealistic Pony / Stability Matrix

Version 1.10.0


OVERVIEW
================================================================================

EG Prompt Builder is a CSV-driven prompt generation system designed to produce
stable, SFW, show-accurate Equestria Girls prompts for Stable Diffusion models,
with a focus on CyberRealistic Pony.

The system is built to eliminate:
- Identity bleed
- Hair color drift
- Skin tone blending
- Body type averaging
- Height inconsistencies
- Duplicate heads and limbs

It supports:
- Single character prompts
- Manual group prompts
- Random group prompts
- Generate-everything mode
- Outfit control
- Pose control
- Automatic negative prompt protection

No manual prompt editing is required.


REQUIRED FILES (ALL IN THE SAME FOLDER)
================================================================================

MANDATORY FILES:
- eg_prompt_builder.py
- equestria_girls_reference.csv

TEMPLATE FILES (at least one required):
- ultra_minimal_bulletproof_eg_template_classroom.csv
- ultra_minimal_bulletproof_eg_template_daytime.csv
- ultra_minimal_bulletproof_eg_template_outdoor.csv
- ultra_minimal_bulletproof_eg_template_sleep.csv
- ultra_minimal_bulletproof_eg_template_winter.csv

OPTIONAL TEMPLATES:
- ultra_minimal_bulletproof_eg_template_camp_everfree.csv
- ultra_minimal_bulletproof_eg_template_band.csv
- ultra_minimal_bulletproof_eg_template_formal.csv


PYTHON REQUIREMENTS
================================================================================

- Python 3.9 or newer
- Standard library only
- No pip installs required

Check Python version:
python --version


CHARACTER CSV FORMAT (CRITICAL)
================================================================================

Filename:
equestria_girls_reference.csv

REQUIRED HEADER (EXACT, CASE-SENSITIVE):

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

ALLOWED VALUES
--------------------------------------------------------------------------------

Age_Group:
- child
- teen
- adult

Gender:
- female
- male

Body_Type (non-sexual, cartoon-safe):
- petite build
- slim build
- average build
- athletic build
- stocky build
- muscular build

Skin_Tone (Equestria Girls pastel style):
- light pastel skin
- warm pastel skin
- peach pastel skin
- golden pastel skin
- tan pastel skin
- olive pastel skin
- cool pastel skin

Hair_Block:
- Comma-separated
- Show-accurate
- Weighted colors allowed
Example:
show accurate hair, (lavender hair:1.50), (white streaks:1.25), side part, curled ends


TEMPLATE CSV FORMAT
================================================================================

Template CSVs MUST have this header:

Section,Content

OPTIONAL PLACEHOLDERS:
- [CHARACTER NAME]
- [PASTE HAIR BLOCK HERE]
- [PASTE CASUAL OUTFIT BLOCK HERE]
- [PASTE PAJAMAS BLOCK HERE]
- [PASTE CAMP EVERFREE OUTFIT BLOCK HERE]
- [PASTE RAINBOOMS BAND OUTFIT BLOCK HERE]
- [PASTE FORMAL OUTFIT BLOCK HERE]

DO NOT ADD placeholders for:
- Age
- Gender
- Height
- Body type
- Skin tone
- Eye color

These are injected automatically.

HEIGHT SYSTEM (AUTOMATIC)
================================================================================

Height is derived automatically to prevent group averaging:

child  -> short height
teen   -> short / average / tall (based on body type)
adult  -> average / tall

Height is never stored in the CSV.


POSE SYSTEM
================================================================================

At runtime, you may choose a pose:

- auto (template-aware)
- standing
- sitting
- walking
- conversation
- classroom
- band
- camp
- sleep

If AUTO is selected, pose is inferred from the template filename:
- sleep templates -> sleeping pose
- classroom templates -> seated classroom pose
- band templates -> performance pose
- camp templates -> outdoor camp pose

NEGATIVE BLEED PROTECTION (AUTOMATIC)
================================================================================

The script automatically injects negatives to prevent:

- duplicate characters
- merged faces
- hair color bleed
- skin tone blending
- body type averaging
- height distortion
- extra heads
- extra limbs
- extra fingers
- malformed hands

DO NOT add negative bleed protection manually to templates.

HOW TO RUN
================================================================================

From the same folder as all files:

python eg_prompt_builder.py

Follow the interactive menus to select:
- generation mode
- pose mode
- group configuration

GENERATION MODES
================================================================================

1) Singles
   - One prompt per character

2) Manual Group
   - You select character names explicitly

3) Random Groups
   - Randomly sampled characters
   - Configurable group size and count

4) Generate Everything
   - Singles
   - Optional manual group
   - Optional random groups


OUTPUTS
================================================================================

Default output folder:
out_prompts/

Each output file contains:
- MAIN PROMPT
- NEGATIVE PROMPT

These files are ready for:
- Stability Matrix
- Automatic1111
- ComfyUI

SAFETY GUARANTEES
================================================================================

- SFW by design
- Explicit age tagging
- No sexualized descriptors
- Child characters restricted to petite builds
- Group prompts remain identity-safe
- Suitable for public model sharing

SUMMARY
================================================================================

EG Prompt Builder is a fully stabilized, CSV-driven prompt generation system
designed for reliability, safety, and show accuracy.

Once configured, it requires no prompt tweaking and scales cleanly from single
characters to complex group scenes.


A complete, production-grade prompt generator:

- Singles ✔
- Manual groups ✔
- Random groups ✔
- Generate everything ✔
- Pose auto-selection ✔
- Pose override ✔
- Height tiers ✔
- Bleed protection ✔
- Fully documented ✔

END OF FILE
================================================================================
