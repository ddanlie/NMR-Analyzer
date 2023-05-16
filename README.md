# NMR-Analyzer
This application analyzes NMR data to decompose them into individual exponential functions

# How to run:
1. Execute python nmrAnalyzer.py

# How to use:
- Select file to analyze
- Select linear areas on the graph figure, when selected press "save curve" button, you will be shown next area to choose
- When you see "save curve" button is blocked, that means no exponential functions are found anymore 
and you can find parameters (by pressing "approximate" button) approximating this funciton w1*exp(-t/T1) + w2*exp(-t/T2) + ...
*you can approximate with any count of exponents you found (see status label above the buttons)
- After parameters found you will see edit panel, where you can change parameters:
  1. W parameters are changed with sliders and their sum must be 1 before changes can be made (check sum in status)
  2. T parameters can be changed by pressing spinbox arrows OR putting any number from 1000 to defaulT*10 and PRESSING ENTER inside input field
- You can copy parameters from right-bottom text field

# IMPORTANT
- If you seee weights are not 1 in sum in botton-right result panel - you found wrong count of exponents OR selected too noisy area
