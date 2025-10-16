# Network_auto
Context 1: Restart OLT Port based on data in the olt_dig_output.txt

Crée un environement virtuel

python -m venv venv

sur windows : 
pour activer l'environement 

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1

installer les dépendances:

python -m pip install -r .\requirements-dev.txt