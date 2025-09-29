import re
from typing import Dict

from loguru import logger

_LANG = "fr"

# quels appareils utilisez-vous pour regarder des vidéos (4 options) ?
# quel % d’utilisation sur chaque réseau (2 options) ?
# quelle résolution pour chaque réseau (3 résolutions x 2 réseaux) ?


_TEXTS: Dict[str, Dict[str, str]] = {
    "fr": {
        # main page:
        "page_title": "Calculateur d’impact CO2 du visionnage de vidéos sur internet",
        "producer": "Je produis des vidéos",
        "consumer": "Je regarde des vidéos",
        "producer_help": "Combien d’heures votre chaîne a-t-elle été visionnée ces sept derniers jours (YouTube Studio -> Données analytiques -> Aperçu, et sélectionner « 7 derniers jours » en haut à droite) ",
        "consumer_help": "Combien d’heures de vidéos regardez-vous par semaine ? (oui, y compris le porno)",
        "consumer_weekly_hours": "Heures / semaine ",
        "producer_watch_hours": "(en heures)",
        "compute_button": "Calculer",
        "result_total_kg": "Émissions",
        "result_total_kg_year": "Émissions",
        "unit_per_year": "kg de CO2e par an",
        "result_with_production_prefix": "En prenant en compte le CO2e émis pour produire les appareils servant à regarder les vidéos (smartphone, ordinateur, tablette, TV...), cela correspond à :",
        "result_without_production_prefix": "\nSans prendre en compte le CO2e émis pour produire les appareils, cela correspond à :",
        "result_explanation": "\nExplication : la majorité du CO2 est émis lors de la fabrication des appareils servant à regarder les vidéos. Si vous ne souhaitez pas le prendre en compte (ie, que vous cherchez à connaître l’impact carbone **marginal** du visionnage de vidéos), ne considérez que le deuxième chiffre.\n\nCes estimations ont été faites sur la base de données types pour un utilisateur situé en France, mais de nombreux paramètres peuvent les faire varier. Les plus importants :\n\n  - Si vous conservez vos appareils très longtemps avant d’en changer, vous ferez baisser votre impact. À titre d’exemple, en suivant les données de l’ARCOM, nous considérons qu’un smartphone est en moyenne changé après 2,5 années à raison de 3,9h d’utilisation par jour.\n\n  - Le réseau internet fixe (à domicile, qu’il s’agisse de filaire éthernet ou de Wifi) consomme jusqu’à 20 fois moins d’énergie par Go transféré que le réseau mobile (4G/5G). Si vous regardez surtout des vidéos sur le réseau fixe, votre bilan carbone sera donc plus faible (et inversement !).\n\n  - La résolution des vidéos regardée a également un impact important. En général, la résolution automatique des lecteurs de vidéos est moins élevée sur smartphone que PC. Si vous regardez surtout des vidéos sur mobile (sans forcer la résolution à HD), cela joue en votre faveur.\n\n  - Enfin, les calculs supposent une électricité relativement peu carbonée, comme c’est le cas en France grâce notamment au nucléaire. Si vous regardez des vidéos depuis un autre pays, le bilan carbone pourrait être bien différent.\n\n  Tous ces paramètres sont modifiables dans la barre de gauche, vous pouvez mieux comprendre comment ils influent dans les calculs ci-dessous.",
        "details_subheader": "Comment ces chiffres ont-t-il été obtenus ?",
        "details_expander": "Voyons voir...",
        "details_text": (
            """
            Le CO2 total émis se décompose en trois parties:\n\n
            1. CO2 émis par les appareils utilisés pour regarder les vidéos (smartphone, ordinateur, TV, tablette), non seulement pendant leur fabrication mais aussi pendant leur utilisation (électricité consommée).
            2. CO2 émis par les réseaux transférant les vidéos (deux types de réseaux : mobile 4G/5G, ou fixe à la maison éthernet/wifi). Ce CO2 contient une part variable, dépendante du volume de données transmises, et une part fixe par utilisateur et par heure d’utilisation. À savoir : le réseau mobile est bien plus émetteur de CO2 que le réseau fixe (jusqu’à 20 fois plus de CO2 émis par Go transféré).
            3. CO2 émis par les centres de données stockant les vidéos, qui contient également une part proportionnelle aux Go transférés et une part dépendante du nombre d’heures visionnées.\n\n
            Concrètement, et pour les valeurs renseignées dans la barre de gauche, cela donne:\n\n
            1. CO2 émis par les appareils = CO2 émis à la production ramené à une heure d’utilisation + électricité consommée pour une heure d’utilisation = {device_production_co2_per_video_hour_total:.4f} + {device_energy_co2_per_video_hour_total:.4f} = **{device_production_co2_per_video_hour_total_plus_energy:.4f} kg CO2e/h**.\n\n
            2. Pour le CO2 émis par les réseaux, en supposant :\n\n
            - Que vous utilisez le réseau fixe {network_share_fixed:.1f}% du temps, le réseau mobile {network_share_mobile:.1f}% du temps, tous appareils confondus.
            - Que sur le réseau fixe, vous regardez en 480p {fixed_network_resolution_percent_480p:.0f}% du temps, en 1080p {fixed_network_resolution_percent_1080p:.0f}% du temps, en 4K {fixed_network_resolution_percent_2160p:.0f}% du temps.
            - Que sur le réseau mobile, vous regardez en 480p {mobile_network_resolution_percent_480p:.0f}% du temps, en 1080p {mobile_network_resolution_percent_1080p:.0f}% du temps, en 4K {mobile_network_resolution_percent_2160p:.0f}% du temps.\n
            Cela donne un débit de données moyen pour le réseau fixe de {gb_per_hour_fixed:.2f} Go/h, et pour le réseau mobile de {gb_per_hour_mobile:.2f} Go/h, soit une consommation d’énergie pour le réseau fixe de {network_kwh_per_video_hour_fixed:.4f} kWh/h, pour le réseau mobile de {network_kwh_per_video_hour_mobile:.4f} kWh/h 
            
            → **Total {network_kwh_per_video_hour_total:.4f} kWh/h**, soit **{network_co2_per_video_hour_total:.4f} kg CO2e/h**.\n\n

            3. CO2 émis par les centres de données. Pour un visionnage de {gb_per_hour_total_weighted:.2f} Go/h en moyenne, cela représente {datacenter_co2_per_video_hour_transfer:.4f} kg CO2e/h pour le stockage + {datacenter_co2_per_video_hour_runtime:.4f} kg/h pour le visionnage = **{datacenter_co2_per_video_hour_total:.4f} kg/h**.\n\n
          Une heure de vidéo visionnée émet donc {kg_per_video_hour_total:.4f} kg CO2e / h. Multiplié par la valeur de {hours_input:,.2f} h/semaine que vous avez entrée et 52 semaines, cela donne **{total_kg_co2e:,.2f} kg CO2e/an**.
            """
        ),
        "even_more_details_subheader": "Encore plus de détails ?",
        "even_more_details_expander": "J’aime ça !",
        "even_more_details_text": """
            Gourmand·e ! Voilà toutes les étapes du calcul. Toutes les valeurs sont personnalisables dans la barre de gauche.
        
            1. CO2e lié aux appareils (production + électricité à l’usage)
        
               a. CO2 lié à la production de chaque appareil, ramené à une heure d’utilisation = (CO2 émis à la production / durée de vie de l’appareil en heures) × part d’utilisation de cet appareil pour regarder des vidéos. Soit :
        
                  - Ordinateur: ({device_production_kg_co2e_computer:.2f} / {device_lifetime_hours_computer:.0f}) × {device_percent_computer:.1f}% = {device_production_co2_per_video_hour_by_device_computer:.6f} kg/h
                  - Smartphone: ({device_production_kg_co2e_smartphone:.2f} / {device_lifetime_hours_smartphone:.0f}) × {device_percent_smartphone:.1f}% = {device_production_co2_per_video_hour_by_device_smartphone:.6f} kg/h
                  - Tablette: ({device_production_kg_co2e_tablet:.2f} / {device_lifetime_hours_tablet:.0f}) × {device_percent_tablet:.1f}% = {device_production_co2_per_video_hour_by_device_tablet:.6f} kg/h
                  - TV: ({device_production_kg_co2e_tv:.2f} / {device_lifetime_hours_tv:.0f}) × {device_percent_tv:.1f}% = {device_production_co2_per_video_hour_by_device_tv:.6f} kg/h
        
                  **Total pour la production des appareils = {device_production_co2_per_video_hour_total:.6f} kg CO2e / h.**
        
               b. Électricité à l’usage : pour chaque appareil, CO2 émis = (Wh/h appareil / 1000) * CO2 émis par kWh. Puis pour obtenir l’émission moyenne pondérée, multiplier par la part d’utilisation de chaque appareil : 
        
                  - Ordinateur: {device_percent_computer:.1f}% × ({device_watts_computer:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_computer:.6f} kWh / h
                  ⇒ {device_energy_co2_per_video_hour_by_device_computer:.6f} kg/h
                  - Smartphone: {device_percent_smartphone:.1f}% × ({device_watts_smartphone:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_smartphone:.6f} kWh / h 
                  ⇒ {device_energy_co2_per_video_hour_by_device_smartphone:.6f} kg/h
                  - Tablette: {device_percent_tablet:.1f}% × ({device_watts_tablet:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_tablet:.6f} kWh / h 
                  ⇒ {device_energy_co2_per_video_hour_by_device_tablet:.6f} kg/h
                  - TV: {device_percent_tv:.1f}% × ({device_watts_tv:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_tv:.6f} kWh / h 
                  ⇒ {device_energy_co2_per_video_hour_by_device_tv:.6f} kg/h
        
                  **Total des émissions pour l’électricité utilisée par les appareils = {device_energy_kwh_per_video_hour_total:.6f} kWh/h 
                  ⇒ {device_energy_co2_per_video_hour_total:.6f} kg CO2e / h.**
        
               **Total des émissions liées aux appareils = {device_production_co2_per_video_hour_total:.6f} + {device_energy_co2_per_video_hour_total:.6f} = {device_production_co2_per_video_hour_total_plus_energy:.6f} kg/h.**
        
        2. CO2 lié aux réseaux (fixe et mobile)
        
          a. Part d'usage réseau fixe/ réseau mobile moyenne calculée à partir des réseaux utilisés pour chaque appareil : {network_share_fixed:.1f}% de visionnage en fixe, {network_share_mobile:.1f}% en mobile.
        
          b. Volume moyen de données par réseau par heure (Go/h) = Σ (Go/h de la résolution × part de cette résolution sur le réseau).

            - Fixe: {video_bitrate_GB_per_hour_480p:.2f}×{fixed_network_resolution_percent_480p:.0f}% (480p) + {video_bitrate_GB_per_hour_1080p:.2f}×{fixed_network_resolution_percent_1080p:.0f}% (HD) + {video_bitrate_GB_per_hour_2160p:.2f}×{fixed_network_resolution_percent_2160p:.0f}% (4K) = {gb_per_hour_fixed:.4f} GB/h.
            - Mobile: {video_bitrate_GB_per_hour_480p:.2f}×{mobile_network_resolution_percent_480p:.0f}% (480p) + {video_bitrate_GB_per_hour_1080p:.2f}×{mobile_network_resolution_percent_1080p:.0f}% (HD) + {video_bitrate_GB_per_hour_2160p:.2f}×{mobile_network_resolution_percent_2160p:.0f}% (4K)= {gb_per_hour_mobile:.4f} GB/h.
        
          c. Pour chaque réseau, suivant l’étude de l’ARCOM (voir sources barre de gauche), la consommation électrique est de la forme kWh/h = a×GB/h + b/h, où b est une consommation par utilisateur par heure.
        
            - Réseau fixe: a={network_a_kwh_per_gb_fixed:.5f}, b={network_b_kwh_per_user_hour_fixed:.5f} ⇒ {network_kwh_per_video_hour_fixed:.6f} kWh/h.
            - Réseau mobile: a={network_a_kwh_per_gb_mobile:.5f}, b={network_b_kwh_per_user_hour_mobile:.5f} ⇒ {network_kwh_per_video_hour_mobile:.6f} kWh/h.
        
          d. Pondération par part d'usage (fixe {network_share_fixed:.1f}%, mobile {network_share_mobile:.1f}%) :
        
            Réseau fixe = {network_kwh_per_video_hour_fixed:.6f} kWh/h.
            Réseau mobile = {network_kwh_per_video_hour_mobile:.6f} kWh/h.
        
          Consommation totale des réseaux : {network_kwh_per_video_hour_total:.6f} kWh/h, soit **{network_co2_per_video_hour_total:.6f} kg CO2e/h** (émissions de CO2e / kWh : {co2e_per_kWh:.4f}).
        
            3. CO2e lié aux centres de données : également de la forme c×Go/h + d/h.
        
              a. Part proportionnelle aux Gos transférés (ces Gos étant déterminés par la part réseau fixe/ réseau mobile) : c×GB/h = {datacenter_kg_co2e_per_GB:.6f}×{gb_per_hour_total_weighted:.4f} = {datacenter_co2_per_video_hour_transfer:.6f} kg/h.
        
               b. Part proportionnelle à la durée visionnée : d = {datacenter_kg_co2e_per_hour:.6f} kg/h.
        
               c. Total = {datacenter_co2_per_video_hour_transfer:.6f} + {datacenter_co2_per_video_hour_runtime:.6f} = **{datacenter_co2_per_video_hour_total:.6f} kg/h.**
        
      Tout ceci nous donne des émissions de {device_production_co2_per_video_hour_total_plus_energy:.6f} kg CO2e / h pour les appareils + {network_co2_per_video_hour_total:.6f} kg CO2e / h pour les réseaux, et {datacenter_co2_per_video_hour_total:.6f} kg CO2e / h pour les centres de données, soit  {kg_per_video_hour_total:.6f} kg CO2e / h au total.
        
      **Multiplié par {hours_input:.2f} heures de visionnage par semaine × 52 semaines = {total_kg_co2e:,.2f} kg par an.**
        
            Répartis comme suit : 

              - Production des appareils : {production_co2_total:,.2f} kg
              - Consommation en électricité des appareils : {device_energy_co2_total:,.2f} kg
              - Réseaux : {network_co2_total:,.2f} kg 
              - Centres de données : {datacenter_co2_total:,.2f} kg
        """,
        # sidebar:
        "language_label": "Langue",
        "main_assumptions_header": "Hypothèses principales",
        "main_assumptions_edit": "Modifier",
        "secondary_assumptions_header": "Hypothèses secondaires",
        "secondary_assumptions_edit": "Modifier",
        "device_percent": "Quels appareils utilisez-vous pour regarder des vidéos (part, en %) ?",
        "device_percent_computer": "Ordinateur (portable ou fixe)",
        "device_percent_smartphone": "Smartphone",
        "device_percent_tablet": "Tablette",
        "device_percent_tv": "TV",
        "device_percent_check": "(NB: si le total est inférieur à 100%, le pourcentage d’ordinateur sera augmenté pour les atteindre.)",
        "device_percent_error": "Le pourcentage total est de {percent:.1f}%. Veuillez le réduire à moins de 100%.",
        "resolution_percent": "À quelles résolutions sont regardées les vidéos (en % du temps total) ?",
        "resolution_percent_480p": "480p",
        "resolution_percent_1080p": "HD 1080p",
        "resolution_percent_2160p": "4K 2160p",
        "resolution_percent_check": "(NB: Si le total est inférieur à 100%, le pourcentage de 1080p sera augmenté pour les atteindre.)",
        "resolution_percent_error": "Le pourcentage total est de {percent:.1f}%. Veuillez le réduire à moins de 100%.",
        "device_production_kg_co2e": "Émissions CO2 dues à la fabrication des appareils (en kg de CO2)",
        "device_production_kg_co2e_source": "https://datavizta.boavizta.org/terminalimpact (représentatif d'un appareil moyen, mais d’importantes disparités peuvent exister entre appareils, notamment pour les télévisions)",
        "device_production_kg_co2e_computer": "Ordinateur (portable)",
        "device_production_kg_co2e_smartphone": "Smartphone",
        "device_production_kg_co2e_tablet": "Tablette",
        "device_production_kg_co2e_tv": "TV",
        "device_lifetime_hours": "Durée de vie moyenne de chaque appareil (en heures d’utilisation)",
        "device_lifetime_hours_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. P73 à P78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_lifetime_hours_computer": "Ordinateur (portable)",
        "device_lifetime_hours_smartphone": "Smartphone",
        "device_lifetime_hours_tablet": "Tablette",
        "device_lifetime_hours_tv": "TV",
        "device_watts": "Consommation électrique moyenne des appareils lorsqu’ils sont utilisés pour regarder des vidéos (en Wh/h)",
        "device_watts_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. P73 à P78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_watts_computer": "Ordinateur (portable)",
        "device_watts_smartphone": "Smartphone",
        "device_watts_tablet": "Tablette",
        "device_watts_tv": "TV",
        "video_bitrate_GB_per_hour": "Bitrates moyens par résolution (Go / heure)",
        "video_bitrate_GB_per_hour_source": "https://esimatic.com/blog/how-much-data-youtube-use (cohérent avec ARCOM débit HD de 2,25GBph https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=223)",
        "video_bitrate_GB_per_hour_480p": "480p",
        "video_bitrate_GB_per_hour_1080p": "HD 1080p",
        "video_bitrate_GB_per_hour_2160p": "4K 2160p",
        "network_kwh_per_gb": "Consommation énergétique des réseaux (kWh / GB)",
        "network_kwh_per_gb_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 23 P85 et tableau 25 P87. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=85",
        "network_kwh_per_gb_fixed": "Réseau fixe (Wi-Fi ou éthernet)",
        "network_kwh_per_gb_mobile": "Réseau mobile (4G/5G)",
        "hours_spent_on_network_per_year": "Nombre d’heures passées sur chaque réseau chaque année.",
        "hours_spent_on_network_per_year_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 95 P223 et tableau 96 P224. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=223",
        "hours_spent_on_network_per_year_fixed": "Réseau fixe (Wi-Fi ou éthernet)",
        "hours_spent_on_network_per_year_mobile": "Réseau mobile (4G/5G)",
        "network_kwh_per_user_per_hour": "Consommation énergétique des réseaux, par utilisateur par heure (kWh / utilisateur / heure).",
        "network_kwh_per_user_per_hour_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 23 P85 et tableau 25 P86. Valeurs obtenues en divisant kWh/utilisateur/an par le nombre d'heures par an considéré par Arcom. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=85",
        "network_kwh_per_user_per_hour_fixed": "Réseau fixe (Wi-Fi ou éthernet)",
        "network_kwh_per_user_per_hour_mobile": "Réseau mobile (4G/5G)",
        # New per-device fixed network percent (0..100)
        "fixed_network_percent": "Part d’utilisation sur réseau fixe (ethernet ou wifi à la maison, par opposition à 4G/5G) selon l’appareil (en %)",
        "fixed_network_percent_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. P110 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=110",
        "fixed_network_percent_computer": "Ordinateur (portable)",
        "fixed_network_percent_smartphone": "Smartphone",
        "fixed_network_percent_tablet": "Tablette",
        "fixed_network_percent_tv": "TV",
        # P73 à P78 New per-network resolution mixes as percents (each group sums to 100)
        "fixed_network_resolution_percent": "Répartition des résolutions sur réseau fixe",
        "fixed_network_resolution_percent_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 45 P112 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=112",
        "fixed_network_resolution_percent_480p": "480p",
        "fixed_network_resolution_percent_1080p": "HD 1080p",
        "fixed_network_resolution_percent_2160p": "4K 2160p",
        "mobile_network_resolution_percent": "Répartition des résolutions sur réseau mobile (somme = 100%)",
        "mobile_network_resolution_percent_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 45 P112 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=112",
        "mobile_network_resolution_percent_480p": "480p",
        "mobile_network_resolution_percent_1080p": "HD 1080p",
        "mobile_network_resolution_percent_2160p": "4K 2160p",
        # Validation messages for resolution percents per network
        "fixed_network_resolution_percent_check": "(NB: Si la somme est inférieure à 100%, la part en 1080p sera augmentée pour atteindre 100%.)",
        "fixed_network_resolution_percent_error": "La somme actuelle des parts est de {percent:.1f}%. Veuillez la réduire à 100%.",
        "mobile_network_resolution_percent_check": "(NB: Si la somme est inférieure à 100%, la part en 1080p sera augmentée pour atteindre 100%.)",
        "mobile_network_resolution_percent_error": "La somme actuelle des parts est de {percent:.1f}%. Veuillez la réduire à 100%.",
        "co2e_per_kWh": "Émissions de C02e par kWh d’électricité consommé (kg CO2e / kWh).",
        "co2e_per_kWh_source": "https://ourworldindata.org/grapher/carbon-intensity-electricity?tab=chart&country=FRA",
        "datacenter_kg_co2e": "Émissions de CO2e des centres de données.",
        "datacenter_kg_co2e_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 38 P102, Tableau 56 et 57 P130. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=102",
        "datacenter_kg_co2e_per_GB": "par GB de données transférées (kg CO2e / GB).",
        "datacenter_kg_co2e_per_hour": "par heure de vidéo visionnée (kg CO2e / heure).",
        "co2e_offsetting": "Compensations",
        "co2e_offsetting_source": "https://impactco2.fr/outils/comparateur?value=14.308389148006217#simulateur",
        "co2e_offsetting_electric_vs_thermic_vehicle": "CO2e évité par km roulé en véhicule électrique, par rapport à thermique (kg CO2e / km)",
        "co2e_offsetting_no_meat_meal_vs_chicken_meal": "CO2 évité en mangeant un repas végétarien plutôt qu’avec du poulet (kg CO2e / repas)",
        "co2e_offsetting_title": "Exemples de choses que vous pourriez faire pour compenser les émissions...",
        "offsetting_table_usage_only": "qui ne prennent pas en compte le CO2 à la production",
        "offsetting_table_with_production": "qui prennent en compte le CO2 à la production",
        "electric_vs_thermic_vehicle_display": "Conduire {x} kms en voiture électrique plutôt que thermique.",
        "no_meat_meal_vs_chicken_meal_display": "Remplacer {x} repas avec poulet par un repas végétarien.",
    },
}


def set_language(lang: str) -> None:
    """Set current UI language."""
    global _LANG
    _LANG = lang if lang in _TEXTS else "fr"


def T(key: str) -> str:
    """Translate a key in the current language."""
    return _TEXTS.get(_LANG, {}).get(key, _TEXTS["fr"].get(key, key))


def get_decimal_separator() -> str:
    """Return the decimal separator for the current language.

    Returns:
      "." for English-like languages, "," for French.
    """
    return "," if _LANG == "fr" else "."


def format_float(value: float, decimals: int = 2) -> str:
    """Format a float using the current language's decimal separator.

    Args:
      value: Numeric value to format.
      decimals: Number of digits after the decimal separator.

    Returns:
      The formatted string, with a comma as decimal in French and dot otherwise.
    """
    try:
        # Always format using Python standard then localize the decimal separator.
        s = f"{value:.{decimals}f}"
    except Exception:
        # Fallback: attempt string conversion
        s = str(value)
    if _LANG == "fr":
        return s.replace(".", ",")
    return s


def localize_decimals_in_text(text: str) -> str:
    """Replace only decimal points between digits by commas for French.

    This avoids touching dots in URLs or regular punctuation by only targeting
    patterns like 123.45 where a dot is between two digits.

    Args:
      text: Arbitrary text possibly containing numbers.

    Returns:
      Text with localized decimal separators if language is French, unchanged otherwise.
    """
    if _LANG != "fr" or not text:
        return text
    # Replace digit . digit with digit , digit
    return re.sub(r"(?<=\d)\.(?=\d)", ",", text)
