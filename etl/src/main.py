from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configuration de Selenium avec ChromeDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Ouvrir la page de recherche Google
driver.get("https://www.google.com")
time.sleep(2)  # Pause pour laisser le temps à la page de charger

# Trouver la barre de recherche et envoyer la requête
search_box = driver.find_element(By.NAME, 'q')
search_box.send_keys('hôpitaux Montréal')
search_box.send_keys(Keys.RETURN)
time.sleep(2)  # Pause pour laisser le temps aux résultats de charger

# Collecter les résultats sur plusieurs pages
results = []
try:
    while True:  # Boucle pour naviguer dans les pages
        # Extraire les titres des résultats de recherche
        titles = driver.find_elements(By.TAG_NAME, 'h3')
        results.extend([title.text for title in titles])

        # Trouver et cliquer sur le bouton "Suivant"
        next_button = driver.find_element(By.ID, 'pnnext')
        next_button.click()
        time.sleep(2)  # Pause pour laisser le temps à la page suivante de charger
except Exception as e:
    print("Fin des résultats ou erreur:", e)

# Afficher tous les résultats collectés
for result in results:
    print(result)

# Fermer le navigateur
driver.quit()
