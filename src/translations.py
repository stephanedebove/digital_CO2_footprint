import re
from typing import Dict

_LANG = "fr"

# quels appareils utilisez-vous pour regarder des vidéos (4 options) ?
# quel % d’utilisation sur chaque réseau (2 options) ?
# quelle résolution pour chaque réseau (3 résolutions x 2 réseaux) ?


_TEXTS: Dict[str, Dict[str, str]] = {
    "fr": {
        # main page:
        "page_title": "🎥 Calculateur d'impact climatique du visionnage de vidéos en ligne",
        "flag": "🇫🇷",
        "producer": "Je produis des vidéos",
        "consumer": "Je regarde des vidéos",
        "producer_help": "Combien d’heures de vidéos votre chaîne a-t-elle été visionnée au cours de l’année dernière  (YouTube Studio → Données analytiques → Aperçu, et sélectionner « 365 derniers jours » en haut à droite) ?",
        "consumer_help": "Combien d’heures de vidéos regardez-vous par semaine ? (oui, même les plus inavouables...)",
        "consumer_weekly_hours": "Heures / semaine ",
        "producer_watch_hours": "(en heures par an)",
        "compute_button": "Calculer",
        "sidebar_draw_attention": "(NB : toutes les valeurs par défaut utilisées par le calculateur sont modifiables dans la barre latérale)",
        "result_total_kg": "Émissions",
        "result_total_kg_year": "Émissions",
        "unit_per_year": "kg de CO2e par an",
        "result_with_production_prefix": "En prenant en compte le CO2e émis pour produire les appareils servant à regarder les vidéos (smartphone, ordinateur, tablette, TV...), cela correspond à :",
        "result_without_production_prefix": "\nSans prendre en compte le CO2e émis pour produire les appareils, cela correspond à :",
        "emissions_breakdown_title": "Pourquoi on vous embrouille avec deux chiffres ?",
        "emissions_breakdown_text": "Parce que la majorité du CO2e émis l’est à la fabrication des appareils servant à regarder les vidéos (smartphone, ordinateur, tablette, TV...). Regardez ce graphe, dans votre cas précis :",
        "emissions_production": "🏭 Production des appareils",
        "emissions_networks": "🌐 Réseaux",
        "emissions_datacenters": "🖥️ Centres de données",
        "result_explanation": "\nCe CO2e émis à la production est réparti sur la durée de vie des appareils, mais vous ne voulez peut-être pas le prendre en compte. Par exemple, si vous cherchez à connaître l’impact carbone **marginal** du visionnage de vidéos (une fois un appareil acheté), vous ne devez considérer que le plus petit chiffre.\n\n\n\nÉvidemment, ces estimations ont été faites sur la base de données types pour un utilisateur situé en France, mais de nombreux paramètres peuvent les faire varier. Les plus importants :\n\n  - Si vous conservez vos appareils très longtemps avant d’en changer, vous ferez baisser votre impact. À titre d’exemple, dans le scénario par défaut (si vous n’avez pas changé ces données dans la barre latérale), nous considérons qu’un smartphone est en moyenne renouvelé tous les 2,5 ans et utilisé 3,9h par jour.\n\n  - Le réseau internet fixe (à domicile, qu’il s’agisse de filaire éthernet ou de Wifi) consomme 20 fois moins d’énergie par Go transféré que le réseau mobile (4G/5G). Si vous regardez surtout des vidéos sur le réseau fixe, votre bilan carbone sera donc plus faible. Sauf si... vous profitez du Wifi/ethernet pour augmenter la résolution des vidéos (voir point suivant) !\n\n  - La résolution des vidéos regardée a également un impact important. En général, la résolution automatique des lecteurs de vidéos est moins élevée sur smartphone que PC. Si vous regardez surtout des vidéos sur mobile (sans forcer la résolution à HD), cela joue en votre faveur. Sauf si... vous n’utilisez jamais le réseau fixe pour ça (voir point précédent).\n\n  - Enfin, les calculs supposent une électricité française et donc peu carbonée grâce au nucléaire et aux renouvelables. Si vous regardez des vidéos depuis un autre pays, l'impact sera plus élevé.\n\n  Tous ces paramètres sont modifiables dans la barre de gauche, vous pouvez mieux comprendre comment ils influent dans les calculs ci-dessous.",
        "details_subheader": "Comment ces chiffres ont-t-il été obtenus ?",
        "details_expander": "Voyons voir...",
        "details_text": (
            """
            Le CO2e total émis se décompose en trois parties:\n\n
            1. CO2e émis par les appareils utilisés pour regarder les vidéos (smartphone, ordinateur, TV, tablette), non seulement pendant leur fabrication mais aussi pendant leur utilisation (électricité consommée).
            2. CO2e émis par les réseaux transférant les vidéos (deux types de réseaux : mobile 4G/5G, ou fixe à la maison éthernet/wifi). Ce CO2 contient une part variable, dépendante du volume de données transmises, et une part fixe par utilisateur et par heure d’utilisation. À savoir : le réseau mobile est bien plus émetteur de CO2e que le réseau fixe (jusqu’à 20 fois plus de CO2 émis par Go transféré).
            3. CO2e émis par les centres de données stockant les vidéos, qui contient également une part proportionnelle aux Go transférés et une part dépendante du nombre d’heures visionnées.\n\n
            Concrètement, et pour les valeurs renseignées dans la barre de gauche, cela donne:\n\n
            1. CO2e émis par les appareils = CO2e émis à la production ramené à une heure d’utilisation + électricité consommée pour une heure d’utilisation = {device_production_co2_per_video_hour_total:.4f} + {device_energy_co2_per_video_hour_total:.4f} = **{device_production_co2_per_video_hour_total_plus_energy:.4f} kg CO2e/h**.\n\n
            2. Pour le CO2e émis par les réseaux, en supposant :\n\n
            - Que vous utilisez le réseau fixe {network_share_fixed:.1f}% du temps, le réseau mobile {network_share_mobile:.1f}% du temps, tous appareils confondus.
            - Que sur le réseau fixe, vous regardez en 480p {fixed_network_resolution_percent_480p:.0f}% du temps, en 1080p {fixed_network_resolution_percent_1080p:.0f}% du temps, en 4K {fixed_network_resolution_percent_2160p:.0f}% du temps.
            - Que sur le réseau mobile, vous regardez en 480p {mobile_network_resolution_percent_480p:.0f}% du temps, en 1080p {mobile_network_resolution_percent_1080p:.0f}% du temps, en 4K {mobile_network_resolution_percent_2160p:.0f}% du temps.\n
            Cela donne un débit de données moyen pour le réseau fixe de {gb_per_hour_fixed:.2f} Go/h, et pour le réseau mobile de {gb_per_hour_mobile:.2f} Go/h, soit une consommation d’énergie pour le réseau fixe de {network_kwh_per_video_hour_fixed:.4f} kWh/h, pour le réseau mobile de {network_kwh_per_video_hour_mobile:.4f} kWh/h 
            
            → **Total {network_kwh_per_video_hour_total:.4f} kWh/h**, soit **{network_co2_per_video_hour_total:.4f} kg CO2e/h**.\n\n

            3. CO2e émis par les centres de données. Pour un visionnage de {gb_per_hour_total_weighted:.2f} Go/h en moyenne, cela représente {datacenter_co2_per_video_hour_transfer:.4f} kg CO2e/h pour le stockage + {datacenter_co2_per_video_hour_runtime:.4f} kg/h pour le visionnage = **{datacenter_co2_per_video_hour_total:.4f} kg/h**.\n\n
          Une heure de vidéo visionnée émet donc {kg_per_video_hour_total:.4f} kg CO2e / h. Multiplié par la valeur de {hours_input:,.2f} {hours_unit} que vous avez entrée{annual_multiplier_text}, cela donne **{total_kg_co2e:,.2f} kg CO2e/an**.
            """
        ),
        "even_more_details_subheader": "Encore plus de détails ?",
        "even_more_details_expander": "J’aime ça !",
        "even_more_details_text": """
            Gourmand·e ! Voilà toutes les étapes du calcul. Toutes les valeurs sont personnalisables dans la barre de gauche.
        
            1. CO2e lié aux appareils (production + électricité à l’usage)
        
               a. CO2e lié à la production de chaque appareil, ramené à une heure d’utilisation = (CO2e émis à la production / durée de vie de l’appareil en heures). Soit :
        
                  - Ordinateur: ({device_production_kg_co2e_computer:.2f} / ({device_lifetime_years_computer:.1f} * 365 * {device_usage_hours_per_day_computer:.2f})) × {device_percent_computer:.1f}% = {device_production_co2_per_video_hour_by_device_computer:.6f} kg/h
                  - Smartphone: ({device_production_kg_co2e_smartphone:.2f} / ({device_lifetime_years_smartphone:.1f} * 365 * {device_usage_hours_per_day_smartphone:.2f})) × {device_percent_smartphone:.1f}% = {device_production_co2_per_video_hour_by_device_smartphone:.6f} kg/h
                  - Tablette: ({device_production_kg_co2e_tablet:.2f} / ({device_lifetime_years_tablet:.1f} * 365 * {device_usage_hours_per_day_tablet:.2f})) × {device_percent_tablet:.1f}% = {device_production_co2_per_video_hour_by_device_tablet:.6f} kg/h
                  - TV: ({device_production_kg_co2e_tv:.2f} / ({device_lifetime_years_tv:.1f} * 365 * {device_usage_hours_per_day_tv:.2f})) × {device_percent_tv:.1f}% = {device_production_co2_per_video_hour_by_device_tv:.6f} kg/h
        
                  **Total pour la production des appareils = {device_production_co2_per_video_hour_total:.6f} kg CO2e / h.**
        
               b. Électricité à l’usage : pour chaque appareil, CO2e émis = (Wh/h appareil / 1000) * CO2e émis par kWh. Puis pour obtenir l’émission moyenne pondérée, multiplier par la part d’utilisation de chaque appareil : 
        
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
        
        2. CO2e lié aux réseaux (fixe et mobile)
        
          a. Part d'usage réseau fixe/ réseau mobile moyenne calculée à partir des réseaux utilisés pour chaque appareil : {network_share_fixed:.1f}% de visionnage en fixe, {network_share_mobile:.1f}% en mobile.
        
          b. Volume moyen de données par réseau par heure (Go/h) = Σ (Go/h de la résolution × part de cette résolution sur le réseau).

            - Fixe: {video_bitrate_GB_per_hour_480p:.2f}×{fixed_network_resolution_percent_480p:.0f}% (480p) + {video_bitrate_GB_per_hour_1080p:.2f}×{fixed_network_resolution_percent_1080p:.0f}% (HD) + {video_bitrate_GB_per_hour_2160p:.2f}×{fixed_network_resolution_percent_2160p:.0f}% (4K) = {gb_per_hour_fixed:.4f} Go/h.
            - Mobile: {video_bitrate_GB_per_hour_480p:.2f}×{mobile_network_resolution_percent_480p:.0f}% (480p) + {video_bitrate_GB_per_hour_1080p:.2f}×{mobile_network_resolution_percent_1080p:.0f}% (HD) + {video_bitrate_GB_per_hour_2160p:.2f}×{mobile_network_resolution_percent_2160p:.0f}% (4K)= {gb_per_hour_mobile:.4f} Go/h.
        
          c. Pour chaque réseau, suivant l’étude de l’ARCOM (voir sources barre de gauche), la consommation électrique est de la forme kWh/h = a×Go/h + b/h, où b est une consommation par utilisateur par heure.
        
            - Réseau fixe: a={network_a_kwh_per_gb_fixed:.5f}, b={network_b_kwh_per_user_hour_fixed:.5f} ⇒ {network_kwh_per_video_hour_fixed:.6f} kWh/h.
            - Réseau mobile: a={network_a_kwh_per_gb_mobile:.5f}, b={network_b_kwh_per_user_hour_mobile:.5f} ⇒ {network_kwh_per_video_hour_mobile:.6f} kWh/h.
        
          d. Pondération par part d'usage (fixe {network_share_fixed:.1f}%, mobile {network_share_mobile:.1f}%) :
        
            Réseau fixe = {network_kwh_per_video_hour_fixed:.6f} kWh/h.
            Réseau mobile = {network_kwh_per_video_hour_mobile:.6f} kWh/h.
        
          Consommation totale des réseaux : {network_kwh_per_video_hour_total:.6f} kWh/h, soit **{network_co2_per_video_hour_total:.6f} kg CO2e/h** (émissions de CO2e / kWh : {co2e_per_kWh:.4f}).
        
            3. CO2e lié aux centres de données : également de la forme c×Go/h + d/h.
        
              a. Part proportionnelle aux Gos transférés (ces Gos étant déterminés par la part réseau fixe/ réseau mobile) : c×Go/h = {datacenter_kg_co2e_per_GB:.6f}×{gb_per_hour_total_weighted:.4f} = {datacenter_co2_per_video_hour_transfer:.6f} kg/h.
        
               b. Part proportionnelle à la durée visionnée : d = {datacenter_kg_co2e_per_hour:.6f} kg/h.
        
               c. Total = {datacenter_co2_per_video_hour_transfer:.6f} + {datacenter_co2_per_video_hour_runtime:.6f} = **{datacenter_co2_per_video_hour_total:.6f} kg/h.**
        
      Tout ceci nous donne des émissions de {device_production_co2_per_video_hour_total_plus_energy:.6f} kg CO2e / h pour les appareils + {network_co2_per_video_hour_total:.6f} kg CO2e / h pour les réseaux, et {datacenter_co2_per_video_hour_total:.6f} kg CO2e / h pour les centres de données, soit  {kg_per_video_hour_total:.6f} kg CO2e / h au total.
        
      **Multiplié par {hours_input:.2f} {hours_unit}{annual_multiplier_text} = {total_kg_co2e:,.2f} kg par an.**
        
            Répartis comme suit : 

              - Production des appareils : {production_co2_total:,.2f} kg
              - Consommation en électricité des appareils : {device_energy_co2_total:,.2f} kg
              - Réseaux : {network_co2_total:,.2f} kg 
              - Centres de données : {datacenter_co2_total:,.2f} kg
        """,
        # sidebar:
        "language_label": "Langue/Language",
        "main_assumptions_header": "📊 Hypothèses principales",
        "main_assumptions_edit": "Modifier",
        "secondary_assumptions_header": "⚙️ Hypothèses secondaires",
        "secondary_assumptions_edit": "Modifier",
        "device_percent": "Quels appareils utilisez-vous pour regarder des vidéos (part, en %) ?",
        "device_percent_computer": "Ordinateur*",
        "device_percent_smartphone": "Smartphone",
        "device_percent_tablet": "Tablette",
        "device_percent_tv": "TV",
        "device_percent_check": "(La dernière variable est automatiquement ajustée pour que la somme fasse 100%)",
        "device_percent_error": "Le pourcentage total est de {percent:.1f}%. Veuillez le réduire à moins de 100%.",
        "device_computer_note": "*Par manque de données, on considère que tous les ordinateurs sont des ordinateurs portables. La production d'un ordinateur de bureau génère souvent plus de CO2e mais celui-ci est amorti sur une durée plus longue. La consommation électrique d'un ordinateur de bureau est aussi souvent plus élevée que celle d'un ordinateur portable mais l'impact de la consommation électrique est minoritaire dans l'impact total.",
        "resolution_percent": "À quelles résolutions sont regardées les vidéos (en % du temps total) ?",
        "resolution_percent_480p": "480p",
        "resolution_percent_1080p": "HD 1080p",
        "resolution_percent_2160p": "4K 2160p",
        "resolution_percent_check": "(NB: Si le total est inférieur à 100%, le pourcentage de 1080p sera augmenté pour les atteindre.)",
        "resolution_percent_error": "Le pourcentage total est de {percent:.1f}%. Veuillez le réduire à moins de 100%.",
        "device_production_kg_co2e": "Émissions CO2 dues à la fabrication des appareils (en kg de CO2)",
        "device_production_kg_co2e_source": "https://datavizta.boavizta.org/terminalimpact (représentatif d'un appareil moyen, mais d’importantes disparités peuvent exister entre appareils, notamment pour les télévisions).",
        "device_production_kg_co2e_computer": "Ordinateur*",
        "device_production_kg_co2e_smartphone": "Smartphone",
        "device_production_kg_co2e_tablet": "Tablette",
        "device_production_kg_co2e_tv": "TV",
        "device_lifetime_years": "Combien d’années gardez-vous généralement vos appareils ?",
        "device_lifetime_years_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. P73 à P78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_lifetime_years_computer": "Ordinateur*",
        "device_lifetime_years_smartphone": "Smartphone",
        "device_lifetime_years_tablet": "Tablette",
        "device_lifetime_years_tv": "TV",
        "device_usage_hours_per_day": "Combien d’heures par jour utilisez-vous chaque type d’appareil (tous usages compris, pas que vidéo) ?",
        "device_usage_hours_per_day_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. P73 à P78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_usage_hours_per_day_computer": "Ordinateur*",
        "device_usage_hours_per_day_smartphone": "Smartphone",
        "device_usage_hours_per_day_tablet": "Tablette",
        "device_usage_hours_per_day_tv": "TV",
        "device_watts": "Consommation électrique moyenne des appareils lorsqu’ils sont utilisés pour regarder des vidéos (en Wh/h)",
        "device_watts_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. P73 à P78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_watts_computer": "Ordinateur*",
        "device_watts_smartphone": "Smartphone",
        "device_watts_tablet": "Tablette",
        "device_watts_tv": "TV",
        "video_bitrate_GB_per_hour": "Bitrates moyens par résolution (Go / heure)",
        "video_bitrate_GB_per_hour_source": "https://esimatic.com/blog/how-much-data-youtube-use (cohérent avec ARCOM débit HD de 2,25Goph https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=223)",
        "video_bitrate_GB_per_hour_480p": "480p",
        "video_bitrate_GB_per_hour_1080p": "HD 1080p",
        "video_bitrate_GB_per_hour_2160p": "4K 2160p",
        "network_kwh_per_gb": "Consommation énergétique des réseaux (kWh / Go)",
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
        "fixed_network_percent_computer": "Ordinateur*",
        "fixed_network_percent_smartphone": "Smartphone",
        "fixed_network_percent_tablet": "Tablette",
        "fixed_network_percent_tv": "TV",
        # P73 à P78 New per-network resolution mixes as percents (each group sums to 100)
        "fixed_network_resolution_percent": "Répartition des résolutions sur réseau fixe",
        "fixed_network_resolution_percent_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Calculé pour être cohérent avec le Tableau 45 P112 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=112",
        "fixed_network_resolution_percent_480p": "480p",
        "fixed_network_resolution_percent_1080p": "HD 1080p",
        "fixed_network_resolution_percent_2160p": "4K 2160p",
        "mobile_network_resolution_percent": "Répartition des résolutions sur réseau mobile",
        "mobile_network_resolution_percent_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Calculé pour être cohérent avec le Tableau 45 P112 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=112",
        "mobile_network_resolution_percent_480p": "480p",
        "mobile_network_resolution_percent_1080p": "HD 1080p",
        "mobile_network_resolution_percent_2160p": "4K 2160p",
        # Validation messages for resolution percents per network
        "fixed_network_resolution_percent_check": "(La dernière variable est automatiquement ajustée pour que la somme fasse 100%)",
        "fixed_network_resolution_percent_error": "La somme actuelle des parts est de {percent:.1f}%. Veuillez la réduire à 100%.",
        "mobile_network_resolution_percent_check": "(La dernière variable est automatiquement ajustée pour que la somme fasse 100%)",
        "mobile_network_resolution_percent_error": "La somme actuelle des parts est de {percent:.1f}%. Veuillez la réduire à 100%.",
        "co2e_per_kWh": "Émissions de CO2e par kWh d’électricité consommé (kg CO2e / kWh).",
        "co2e_per_kWh_source": "https://ourworldindata.org/grapher/carbon-intensity-electricity?tab=chart&country=FRA",
        "datacenter_kg_co2e": "Émissions de CO2e des centres de données.",
        "datacenter_kg_co2e_source": "Arcom, 2024. Étude de l'impact environnemental des usages audiovisuels en france. Tableau 38 P102, Tableau 56 et 57 P130. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=102",
        "datacenter_kg_co2e_per_GB": "par Go de données transférées (kg CO2e / Go).",
        "datacenter_kg_co2e_per_hour": "par heure de vidéo visionnée (kg CO2e / heure).",
        "co2e_offsetting": "Compensations",
        "co2e_offsetting_source": "https://impactco2.fr/outils/comparateur#simulateur",
        "co2e_offsetting_electric_vs_thermic_vehicle": "CO2e évité par km roulé en véhicule électrique, par rapport à thermique (kg CO2e / km)",
        "co2e_offsetting_no_meat_meal_vs_chicken_meal": "CO2 évité en mangeant un repas végétarien plutôt qu'avec du poulet (kg CO2e / repas)",
        "co2e_offsetting_train_vs_plane_per_km": "CO2e évité par km en prenant le train au lieu de l'avion (kg CO2e / km)",
        "co2e_offsetting_no_meat_meal_vs_beef_meal": "CO2 évité en mangeant un repas végétarien plutôt qu'avec du bœuf (kg CO2e / repas)",
        "co2e_offsetting_tap_water_vs_beer_wine": "CO2 évité en buvant un verre (250mL) d'eau du robinet plutôt qu’une bière/verre de vin (kg CO2e / verre)",
        "co2e_offsetting_title": "🌱 Ça ne vous parle pas ? Moi non plus. Alors concrètement, voilà ce que vous devriez faire si vous vouliez compenser ces émissions :",
        "electric_vs_thermic_vehicle_display": "🚗 Conduire {x} kms en voiture électrique plutôt que thermique.",
        "no_meat_meal_vs_chicken_meal_display": "🍗 Remplacer {x} repas avec du poulet par des repas végétariens.",
        "train_vs_plane_per_km_display": "✈️ Prendre le train plutôt que l’avion pour faire {x} kms.",
        "no_meat_meal_vs_beef_meal_display": "🥩 Remplacer {x} repas avec du bœuf par des repas végétariens.",
        "tap_water_vs_beer_wine_display": "🍺 Boire {x} verres d'eau du robinet au lieu de verres de bière/vin.",
        "source_text": "Source(s) pour les valeurs par défaut : ",
        "alternative_behaviors": "À titre d’exemple, voilà comment vos émissions seraient modifiées si vous regardiez des vidéos uniquement sur le wifi, uniquement en 480p, ou si vous renouveliez vos appareils deux fois moins souvent :",
        "current_behavior": "Comportement actuel",
        "longer_device_lifetime": "Garder vos appareils 2x plus longtemps",
        "only_wifi": "Wi-Fi uniquement",
        "only_480p": "480p uniquement",
    },
    "en": {
        "page_title": "🎥 Climate impact calculator for online video streaming",
        "flag": "🇬🇧",
        "producer": "I produce videos",
        "consumer": "I watch videos",
        "producer_help": "How many hours of videos has your channel been watched over the past year (YouTube Studio → Analytics → Overview, and select 'Last 365 days' in the top right)?",
        "consumer_help": "How many hours of videos do you watch per week? (yes, even the most embarrassing ones...)",
        "consumer_weekly_hours": "Hours / week",
        "producer_watch_hours": "(in hours per year)",
        "compute_button": "Calculate",
        "sidebar_draw_attention": "(Note: the calculator uses a number of default values but you can change them all in the sidebar)",
        "result_total_kg": "Emissions",
        "result_total_kg_year": "Emissions",
        "unit_per_year": "kg of CO2e per year",
        "result_with_production_prefix": "Including the CO2e emitted to produce the devices used to watch videos (smartphone, computer, tablet, TV...), this corresponds to:",
        "result_without_production_prefix": "\nExcluding the CO2e emitted to produce the devices, this corresponds to:",
        "emissions_breakdown_title": "Why are we confusing you with two different figures?",
        "emissions_breakdown_text": "Because the majority of CO2e emitted is during the manufacturing of devices used to watch videos (smartphone, computer, tablet, TV...). Look at this graph, in your specific case:",
        "emissions_production": "🏭 Device production",
        "emissions_networks": "🌐 Networks",
        "emissions_datacenters": "🖥️ Data centers",
        "result_explanation": "\nThis CO2e emitted during production is spread over the lifespan of the devices, but this is not necessarily something you want to take into account. For example, if you are looking to know the marginal carbon impact of watching videos (once a device is purchased), you should only consider the smaller figure..\n\n\n\nThese estimates are based on typical data for a user located in France, but many factors can cause variations. The most important ones:\n\n  - If you keep your devices for a very long time before replacing them, your impact will decrease. For example, in the base scenario (if you haven’t changed these values in the sidebar), we assume that a smartphone is replaced on average every 2.5 years with 3.9 hours of daily use.\n\n  - Fixed internet networks (at home, whether via Ethernet cable or Wi-Fi) consume 20 times less energy per GB transferred than mobile networks (4G/5G). If you mostly watch videos on a fixed network, your carbon footprint will be lower (and vice versa!). Unless... you take advantage of Wi-Fi/Ethernet to increase video resolution (see next point)!\n\n  - The resolution of the videos watched also has a significant impact. Generally, the default resolution of video players is lower on smartphones than on PCs. If you mostly watch videos on mobile (without forcing HD resolution), this works in your favor. Unless... you never use the fixed network for that (see previous point).\n\n  - Finally, the calculations assume French electricity, which is low-carbon thanks to nuclear and renewable energy. If you watch videos from another country, the impact will be higher.\n\n  All these parameters can be adjusted in the left sidebar, and you can better understand how they influence the calculations below.",
        "details_subheader": "How were these figures calculated?",
        "details_expander": "Let's see...",
        "details_text": (
            """
    The total CO2e emissions are divided into three parts:\n\n
    1. CO2e emitted by the devices used to watch videos (smartphone, computer, TV, tablet), not only during their manufacturing but also during their usage (electricity consumption).
    2. CO2e emitted by the networks transferring the videos (two types of networks: mobile 4G/5G, or fixed at home via Ethernet/Wi-Fi). This CO2 includes a variable part, dependent on the volume of data transmitted, and a fixed part per user and per hour of usage. Note: mobile networks emit significantly more CO2e than fixed networks (up to 20 times more CO2 per GB transferred).
    3. CO2e emitted by the data centers storing the videos, which also includes a part proportional to the GB transferred and a part dependent on the number of hours watched.\n\n
    Specifically, for the values entered in the left sidebar, this gives:\n\n
    1. CO2e emitted by devices = CO2e emitted during production allocated per hour of usage + electricity consumed per hour of usage = {device_production_co2_per_video_hour_total:.4f} + {device_energy_co2_per_video_hour_total:.4f} = **{device_production_co2_per_video_hour_total_plus_energy:.4f} kg CO2e/h**.\n\n
    2. For CO2e emitted by networks, assuming:\n\n
    - That you use fixed networks {network_share_fixed:.1f}% of the time, and mobile networks {network_share_mobile:.1f}% of the time, across all devices.
    - That on fixed networks, you watch in 480p {fixed_network_resolution_percent_480p:.0f}% of the time, in 1080p {fixed_network_resolution_percent_1080p:.0f}% of the time, and in 4K {fixed_network_resolution_percent_2160p:.0f}% of the time.
    - That on mobile networks, you watch in 480p {mobile_network_resolution_percent_480p:.0f}% of the time, in 1080p {mobile_network_resolution_percent_1080p:.0f}% of the time, and in 4K {mobile_network_resolution_percent_2160p:.0f}% of the time.\n
    This results in an average data rate for fixed networks of {gb_per_hour_fixed:.2f} GB/h, and for mobile networks of {gb_per_hour_mobile:.2f} GB/h, leading to an energy consumption for fixed networks of {network_kwh_per_video_hour_fixed:.4f} kWh/h, and for mobile networks of {network_kwh_per_video_hour_mobile:.4f} kWh/h 
    
    → **Total {network_kwh_per_video_hour_total:.4f} kWh/h**, or **{network_co2_per_video_hour_total:.4f} kg CO2e/h**.\n\n

    3. CO2e emitted by data centers. For an average viewing rate of {gb_per_hour_total_weighted:.2f} GB/h, this represents {datacenter_co2_per_video_hour_transfer:.4f} kg CO2e/h for storage + {datacenter_co2_per_video_hour_runtime:.4f} kg/h for viewing = **{datacenter_co2_per_video_hour_total:.4f} kg/h**.\n\n
    Watching one hour of video emits {kg_per_video_hour_total:.4f} kg CO2e/h. Multiplied by the value of {hours_input:,.2f} {hours_unit} you entered{annual_multiplier_text}, this gives **{total_kg_co2e:,.2f} kg CO2e/year**.
    """
        ),
        "even_more_details_subheader": "Want even more details?",
        "even_more_details_expander": "I love that!",
        "even_more_details_text": """
    Hungry for more? Here are all the calculation steps. All values can be customized in the left sidebar.

    1. CO2e related to devices (production + electricity usage)

        a. CO2e from the production of each device, allocated per hour of usage = (CO2e emitted during production / device lifespan in hours). For example:

            - Computer: ({device_production_kg_co2e_computer:.2f} / ({device_lifetime_years_computer:.1f} * 365 * {device_usage_hours_per_day_computer:.2f})) × {device_percent_computer:.1f}% = {device_production_co2_per_video_hour_by_device_computer:.6f} kg/h
            - Smartphone: ({device_production_kg_co2e_smartphone:.2f} / ({device_lifetime_years_smartphone:.1f} * 365 * {device_usage_hours_per_day_smartphone:.2f})) × {device_percent_smartphone:.1f}% = {device_production_co2_per_video_hour_by_device_smartphone:.6f} kg/h
            - Tablet: ({device_production_kg_co2e_tablet:.2f} / ({device_lifetime_years_tablet:.1f} * 365 * {device_usage_hours_per_day_tablet:.2f})) × {device_percent_tablet:.1f}% = {device_production_co2_per_video_hour_by_device_tablet:.6f} kg/h
            - TV: ({device_production_kg_co2e_tv:.2f} / ({device_lifetime_years_tv:.1f} * 365 * {device_usage_hours_per_day_tv:.2f})) × {device_percent_tv:.1f}% = {device_production_co2_per_video_hour_by_device_tv:.6f} kg/h

            **Total for device production = {device_production_co2_per_video_hour_total:.6f} kg CO2e/h.**

        b. Electricity usage: for each device, CO2e emitted = (device power consumption in Wh/h / 1000) × CO2e emitted per kWh. To get the weighted average, multiply by the usage share of each device:

            - Computer: {device_percent_computer:.1f}% × ({device_watts_computer:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_computer:.6f} kWh/h
            ⇒ {device_energy_co2_per_video_hour_by_device_computer:.6f} kg/h
            - Smartphone: {device_percent_smartphone:.1f}% × ({device_watts_smartphone:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_smartphone:.6f} kWh/h 
            ⇒ {device_energy_co2_per_video_hour_by_device_smartphone:.6f} kg/h
            - Tablet: {device_percent_tablet:.1f}% × ({device_watts_tablet:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_tablet:.6f} kWh/h 
            ⇒ {device_energy_co2_per_video_hour_by_device_tablet:.6f} kg/h
            - TV: {device_percent_tv:.1f}% × ({device_watts_tv:.2f}/1000) = {device_energy_kwh_per_video_hour_by_device_tv:.6f} kWh/h 
            ⇒ {device_energy_co2_per_video_hour_by_device_tv:.6f} kg/h

            **Total emissions for device electricity usage = {device_energy_kwh_per_video_hour_total:.6f} kWh/h 
            ⇒ {device_energy_co2_per_video_hour_total:.6f} kg CO2e/h.**

        **Total emissions related to devices = {device_production_co2_per_video_hour_total:.6f} + {device_energy_co2_per_video_hour_total:.6f} = {device_production_co2_per_video_hour_total_plus_energy:.6f} kg/h.**

2. CO2e related to networks (fixed and mobile)

    a. Average usage share of fixed/mobile networks calculated based on the networks used by each device: {network_share_fixed:.1f}% viewing on fixed, {network_share_mobile:.1f}% on mobile.

    b. Average data volume per network per hour (GB/h) = Σ (GB/h for resolution × share of that resolution on the network).

    - Fixed: {video_bitrate_GB_per_hour_480p:.2f}×{fixed_network_resolution_percent_480p:.0f}% (480p) + {video_bitrate_GB_per_hour_1080p:.2f}×{fixed_network_resolution_percent_1080p:.0f}% (HD) + {video_bitrate_GB_per_hour_2160p:.2f}×{fixed_network_resolution_percent_2160p:.0f}% (4K) = {gb_per_hour_fixed:.4f} GB/h.
    - Mobile: {video_bitrate_GB_per_hour_480p:.2f}×{mobile_network_resolution_percent_480p:.0f}% (480p) + {video_bitrate_GB_per_hour_1080p:.2f}×{mobile_network_resolution_percent_1080p:.0f}% (HD) + {video_bitrate_GB_per_hour_2160p:.2f}×{mobile_network_resolution_percent_2160p:.0f}% (4K) = {gb_per_hour_mobile:.4f} GB/h.

    c. For each network, based on the ARCOM study (see sources in the left sidebar), energy consumption is of the form kWh/h = a×GB/h + b/h, where b is a per-user hourly consumption.

    - Fixed network: a={network_a_kwh_per_gb_fixed:.5f}, b={network_b_kwh_per_user_hour_fixed:.5f} ⇒ {network_kwh_per_video_hour_fixed:.6f} kWh/h.
    - Mobile network: a={network_a_kwh_per_gb_mobile:.5f}, b={network_b_kwh_per_user_hour_mobile:.5f} ⇒ {network_kwh_per_video_hour_mobile:.6f} kWh/h.

    d. Weighted by usage share (fixed {network_share_fixed:.1f}%, mobile {network_share_mobile:.1f}%):

    Fixed network = {network_kwh_per_video_hour_fixed:.6f} kWh/h.
    Mobile network = {network_kwh_per_video_hour_mobile:.6f} kWh/h.

    Total network consumption: {network_kwh_per_video_hour_total:.6f} kWh/h, or **{network_co2_per_video_hour_total:.6f} kg CO2e/h** (CO2e emissions per kWh: {co2e_per_kWh:.4f}).

3. CO2e related to data centers: also of the form c×GB/h + d/h.

        a. Proportional to GB transferred (these GB are determined by the fixed/mobile network share): c×GB/h = {datacenter_kg_co2e_per_GB:.6f}×{gb_per_hour_total_weighted:.4f} = {datacenter_co2_per_video_hour_transfer:.6f} kg/h.

        b. Proportional to viewing time: d = {datacenter_kg_co2e_per_hour:.6f} kg/h.

        c. Total = {datacenter_co2_per_video_hour_transfer:.6f} + {datacenter_co2_per_video_hour_runtime:.6f} = **{datacenter_co2_per_video_hour_total:.6f} kg/h.**

This gives us emissions of {device_production_co2_per_video_hour_total_plus_energy:.6f} kg CO2e/h for devices + {network_co2_per_video_hour_total:.6f} kg CO2e/h for networks, and {datacenter_co2_per_video_hour_total:.6f} kg CO2e/h for data centers, for a total of {kg_per_video_hour_total:.6f} kg CO2e/h.

**Multiplied by {hours_input:.2f} {hours_unit}{annual_multiplier_text} = {total_kg_co2e:,.2f} kg per year.**

    Distributed as follows: 

        - Device production: {production_co2_total:,.2f} kg
        - Device electricity consumption: {device_energy_co2_total:,.2f} kg
        - Networks: {network_co2_total:,.2f} kg 
        - Data centers: {datacenter_co2_total:,.2f} kg
""",
        # sidebar:
        "language_label": "Langue/Language",
        "main_assumptions_header": "📊 Main assumptions",
        "main_assumptions_edit": "Edit",
        "secondary_assumptions_header": "⚙️ Secondary assumptions",
        "secondary_assumptions_edit": "Edit",
        "device_percent": "Which devices do you use to watch videos (share, in %)?",
        "device_percent_computer": "Computer*",
        "device_percent_smartphone": "Smartphone",
        "device_percent_tablet": "Tablet",
        "device_percent_tv": "TV",
        "device_percent_check": "(The last variable is automatically adjusted so that the sum equals 100%)",
        "device_percent_error": "The total percentage is {percent:.1f}%. Please reduce it to less than 100%.",
        "device_computer_note": "*Due to lack of data, all computers are assumed to be laptops. Desktop computers often generate more CO2e during production, but this is offset by their longer lifespan. Desktop computers also tend to consume more electricity than laptops, but electricity consumption is a minor factor in the total impact.",
        "resolution_percent": "At what resolutions do you watch videos (as a percentage of total time)?",
        "resolution_percent_480p": "480p",
        "resolution_percent_1080p": "HD 1080p",
        "resolution_percent_2160p": "4K 2160p",
        "resolution_percent_check": "(Note: If the total is less than 100%, the 1080p percentage will be increased to make up the difference.)",
        "resolution_percent_error": "The total percentage is {percent:.1f}%. Please reduce it to 100%.",
        "device_production_kg_co2e": "CO2 emissions from device manufacturing (in kg of CO2)",
        "device_production_kg_co2e_source": "https://datavizta.boavizta.org/terminalimpact (representative of an average device, but significant variations may exist between devices, especially TVs).",
        "device_production_kg_co2e_computer": "Computer*",
        "device_production_kg_co2e_smartphone": "Smartphone",
        "device_production_kg_co2e_tablet": "Tablet",
        "device_production_kg_co2e_tv": "TV",
        "device_lifetime_hours": "Average lifespan of each device (in hours of use)",
        "device_lifetime_hours_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Pages 73 to 78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_lifetime_hours_computer": "Computer*",
        "device_lifetime_hours_smartphone": "Smartphone",
        "device_lifetime_hours_tablet": "Tablet",
        "device_lifetime_hours_tv": "TV",
        "device_lifetime_years": "How many years do you generally keep a device?",
        "device_lifetime_years_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Pages 73 to 78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_lifetime_years_computer": "Computer*",
        "device_lifetime_years_smartphone": "Smartphone",
        "device_lifetime_years_tablet": "Tablet",
        "device_lifetime_years_tv": "TV",
        "device_usage_hours_per_day": "How many hours do you use each type of device each day (all uses included, not only video)?",
        "device_usage_hours_per_day_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Pages 73 to 78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_usage_hours_per_day_computer": "Computer*",
        "device_usage_hours_per_day_smartphone": "Smartphone",
        "device_usage_hours_per_day_tablet": "Tablet",
        "device_usage_hours_per_day_tv": "TV",
        "device_watts": "Average power consumption of devices when used to watch videos (in Wh/h)",
        "device_watts_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Pages 73 to 78 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=73",
        "device_watts_computer": "Computer*",
        "device_watts_smartphone": "Smartphone",
        "device_watts_tablet": "Tablet",
        "device_watts_tv": "TV",
        "video_bitrate_GB_per_hour": "Average bitrates by resolution (GB / hour)",
        "video_bitrate_GB_per_hour_source": "https://esimatic.com/blog/how-much-data-youtube-use (consistent with ARCOM HD bitrate of 2.25GB/h https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=223)",
        "video_bitrate_GB_per_hour_480p": "480p",
        "video_bitrate_GB_per_hour_1080p": "HD 1080p",
        "video_bitrate_GB_per_hour_2160p": "4K 2160p",
        "network_kwh_per_gb": "Network energy consumption (kWh / GB)",
        "network_kwh_per_gb_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Table 23 P85 and Table 25 P87. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=85",
        "network_kwh_per_gb_fixed": "Fixed network (Wi-Fi or Ethernet)",
        "network_kwh_per_gb_mobile": "Mobile network (4G/5G)",
        "hours_spent_on_network_per_year": "Number of hours spent on each network per year.",
        "hours_spent_on_network_per_year_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Table 95 P223 and Table 96 P224. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=223",
        "hours_spent_on_network_per_year_fixed": "Fixed network (Wi-Fi or Ethernet)",
        "hours_spent_on_network_per_year_mobile": "Mobile network (4G/5G)",
        "network_kwh_per_user_per_hour": "Network energy consumption per user per hour (kWh / user / hour).",
        "network_kwh_per_user_per_hour_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Table 23 P85 and Table 25 P86. Values obtained by dividing kWh/user/year by the number of hours per year considered by Arcom. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=85",
        "network_kwh_per_user_per_hour_fixed": "Fixed network (Wi-Fi or Ethernet)",
        "network_kwh_per_user_per_hour_mobile": "Mobile network (4G/5G)",
        "fixed_network_percent": "Share of usage on fixed networks (Ethernet or Wi-Fi at home, as opposed to 4G/5G) by device (in %)",
        "fixed_network_percent_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. P110 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=110",
        "fixed_network_percent_computer": "Computer*",
        "fixed_network_percent_smartphone": "Smartphone",
        "fixed_network_percent_tablet": "Tablet",
        "fixed_network_percent_tv": "TV",
        "fixed_network_resolution_percent": "Resolution distribution on fixed networks",
        "fixed_network_resolution_percent_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Calculated to be consistent with Table 45 P112 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=112",
        "fixed_network_resolution_percent_480p": "480p",
        "fixed_network_resolution_percent_1080p": "HD 1080p",
        "fixed_network_resolution_percent_2160p": "4K 2160p",
        "mobile_network_resolution_percent": "Resolution distribution on mobile networks",
        "mobile_network_resolution_percent_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Calculated to be consistent with Table 45 P112 https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=112",
        "mobile_network_resolution_percent_480p": "480p",
        "mobile_network_resolution_percent_1080p": "HD 1080p",
        "mobile_network_resolution_percent_2160p": "4K 2160p",
        # Validation messages for resolution percents per network
        "fixed_network_resolution_percent_check": "(The last variable is automatically adjusted so that the sum equals 100%)",
        "fixed_network_resolution_percent_error": "The current total share is {percent:.1f}%. Please reduce it to 100%.",
        "mobile_network_resolution_percent_check": "(The last variable is automatically adjusted so that the sum equals 100%)",
        "mobile_network_resolution_percent_error": "The current total share is {percent:.1f}%. Please reduce it to 100%.",
        "co2e_per_kWh": "CO2e emissions per kWh of electricity consumed (kg CO2e / kWh).",
        "co2e_per_kWh_source": "https://ourworldindata.org/grapher/carbon-intensity-electricity?tab=chart&country=FRA",
        "datacenter_kg_co2e": "CO2e emissions from data centers.",
        "datacenter_kg_co2e_source": "Arcom, 2024. Study on the environmental impact of audiovisual usage in France. Table 38 P102, Table 56 and 57 P130. https://www.arcom.fr/sites/default/files/2024-10/Arcom-arcep-ademe-etude-impact-environnemental-des-usages-audiovisuels.pdf#page=102",
        "datacenter_kg_co2e_per_GB": "per GB of data transferred (kg CO2e / GB).",
        "datacenter_kg_co2e_per_hour": "per hour of video watched (kg CO2e / hour).",
        "co2e_offsetting": "Offsets",
        "co2e_offsetting_source": "https://impactco2.fr/outils/comparateur#simulateur",
        "co2e_offsetting_electric_vs_thermic_vehicle": "CO2e avoided per km driven in an electric vehicle compared to a thermal vehicle (kg CO2e / km)",
        "co2e_offsetting_no_meat_meal_vs_chicken_meal": "CO2 avoided by eating a vegetarian meal instead of chicken (kg CO2e / meal)",
        "co2e_offsetting_train_vs_plane_per_km": "CO2e avoided per km by taking the train instead of flying (kg CO2e / km)",
        "co2e_offsetting_no_meat_meal_vs_beef_meal": "CO2 avoided by eating a vegetarian meal instead of a meal with beef (kg CO2e / meal)",
        "co2e_offsetting_tap_water_vs_beer_wine": "CO2 avoided by drinking a glass (250mL) of tap water instead of a glass of beer/wine (kg CO2e / glass)",
        "co2e_offsetting_title": "🌱 Doesn’t ring a bell? Me neither. So in practise, things you should do if you wanted to offset these emissions:",
        "electric_vs_thermic_vehicle_display": "🚗 Drive {x} km in an electric car instead of a thermal car.",
        "no_meat_meal_vs_chicken_meal_display": "🍗 Replace {x} chicken meals with vegetarian meals.",
        "train_vs_plane_per_km_display": "✈️ Take the train instead of flying {x} km.",
        "no_meat_meal_vs_beef_meal_display": "🥩 Replace {x} beef meals with vegetarian meals.",
        "tap_water_vs_beer_wine_display": "🍺 Drink {x} glasses of tap water instead of glasses of beer/wine.",
        "source_text": "Source(s) for default values: ",
        "alternative_behaviors": "For example, here is how your emissions would change if you renewed your devices twice less often, if you only watched videos on wifi, and if you only watched them in 480p resolution:",
        "current_behavior": "Current behavior",
        "longer_device_lifetime": "Double your devices' lifetime",
        "only_wifi": "Wi-Fi only",
        "only_480p": "480p only",
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
    """Format a float using the current language's decimal and thousands separators.

    Args:
      value: Numeric value to format.
      decimals: Number of digits after the decimal separator.

    Returns:
      The formatted string, with space as thousands separator and comma as decimal in French,
      comma as thousands separator and dot as decimal in English.
    """
    try:
        # Format with comma as thousands separator and dot as decimal
        s = f"{value:,.{decimals}f}"
    except Exception:
        # Fallback: attempt string conversion
        s = str(value)
    if _LANG == "fr":
        # Replace comma (thousands) with space, dot (decimal) with comma
        return s.replace(",", " ").replace(".", ",")
    return s


def localize_decimals_in_text(text: str) -> str:
    """Replace decimal points and thousands commas for French localization.

    For French, converts numbers like 1,234.56 to 1 234,56.

    Args:
      text: Arbitrary text possibly containing numbers.

    Returns:
      Text with localized number formats if language is French, unchanged otherwise.
    """
    if _LANG != "fr" or not text:
        return text
    # Handle numbers with thousands commas and decimal dot: 1,234.56 -> 1 234,56
    text = re.sub(
        r"(\d{1,3}(?:,\d{3})*\.\d+)",
        lambda m: m.group().replace(",", " ").replace(".", ","),
        text,
    )
    # Handle simple decimal dots without thousands: 123.45 -> 123,45
    text = re.sub(r"(?<=\d)\.(?=\d)", ",", text)
    return text
