@echo off
title BioHarvest-Sim - Run Automated Unit Tests
echo ===================================================
echo Running BioHarvest-Sim Automated Unit Test Suite...
echo ===================================================
python -m unittest discover -s tests -p "test_*.py" -v
pause
