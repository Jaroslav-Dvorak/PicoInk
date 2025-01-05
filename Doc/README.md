[Manuál - Popis a obsluha zařízení](./PicoInk_control_manual_cs.pdf)\
[Manuál - MQTT nastavení](./PicoInk_MQTT_cs.pdf)\
[Manuál - Stavba zařízení](./PicoInk_assembly_cs.pdf)\
[Manuál - Instalační manuál](./PicoInk_installation_manual_cs.pdf) \
[Video - nastavení zařízení](https://fb.watch/vx8vt5eCgY/)\
[Video - stavba zařízení](https://www.youtube.com/watch?v=83LGPPGywaA)


## Rychlé uvedení do provozu

1. Ujistěte se, že je zařízení funkční. 
   * Krátkým stiskem prostředního tlačítka spustíme běžný cyklus.
   * Stavová LED se rozsvítí oranžově, poté problikne zelená a LED zhasne.
2. Proveďte mechanickou instalaci dle typu modulu.
    * **Modul měření teploty bojleru:**
      * Ujistěte se, že díra připravená pro teploměr je do dostatečné hloubky zbavená přebytečné izolační pěny.
      * Celé zařízení vtlačte do bojleru.
3. Dvojklikem a následným držením prostředního tlačítka vyberte vyhovující grafické zobrazení naměřené hodnoty.
4. Zvažte typ datového připojení. 
   * **Bluetooth Low Energy** s protokolem [BTHome](https://bthome.io):
     * Několikanásobně nižší spotřeba a tím vyšší výdrž baterie.
     * Velmi snadná konfigurace i integrace do Home Assistanta.
     * Žádná zpětná vazba (PicoInk nehlásí žádný problém, pokud datová zpráva nedorazí).
     * Datové zprávy nejsou šifrované a je možné je jednoduše odchytit v okolí senzoru.
   * **WiFi** s protokolem [MQTT](https://mqtt.org):
     * Baterie s kapacitou 3500mAh vydrží zaslání cca 10000 zpráv. Při 15 minutovém intervalu je to cca půl roku.
     * Při nezdařeném odeslání zařízení červeně blikne a na displeji informuje o problému.
     * V zařízení jsou zapsána hesla WiFi a Home Assistanta. Hesla lze vyčíst pomocí kabelového připojení k procesoru.
5. Spusťte nastavovací režim dlouhým podržením levého tlačítka a současným krátkým stiskem prostředního tlačítka.
   * Připojte se k nově vytvořené WiFi (PICOINK) telefonem nebo počítačem.
   * V případě telefonu, naskenujte zobrazený QR kód a potvrďte přesměrování.
   * V případě PC, zadejte do prohlížeče zobrazenou IP adresu (192.168.4.1).
6. Nastavte hodnoty. **Každou změnu je nutno potvrdit tlačítkem Write**.
   * Minimum a Maximum - ovlivňují pouze zobrazení na samotném zařízení (rozsah grafu nebo stupnice).
   * **Bluetooth Low Energy** varianta:
     * Vyplňte pole označené jako BLE-name (název zařízení - např. "bojler").
     * Kliněte na tlačítko Save and restart a zavřete nastavovací stránku.
     * V notifikacích Home Assistantu se zobrazí hlášení o nalezeném novém zařízení. Potvrdíme nakonfigurování do HA.
     * V zařízeních --> BTHome --> můžeme zapnout skrytou entitu signal.
   * **Wifi** varianta:
     * V Home Assistant musí být funkční MQTT integrace. Pokud není postujte podle [tohoto návodu](./PicoInk_MQTT_cs.pdf).
     * **Wifi-SSID** - Název WiFi sítě na kterou se má teploměr připojovat.
     * **WiFi-passw** - WiFi heslo.
     * **WiFi-IP** - nechat prázdné. *Pouze pro zkušené: Statická IP - formát CIDR. Pokud je prázdné, DHCP přidělení.*
     * **MQTT-broker** - IP adresa serveru Home Assistanta (MQTT brokera) nebo jeho DNS název.
     * **MQTT-user** - uživatelské jmeno některého z uživatelů Home Assistanta.
     * **MQTT-passw** - heslo výše zadaného uživatele.
     * **MQTT-name** - název zařízení (součást názvu entit v Home Assistant).
     * Kliněte na tlačítko Save and restart a zavřete nastavovací stránku.
     * Počkejte až zhasne stavová LED.
     * Dlouhým požením pravého tlačítka a současným krátkým stiskem prostředního tlačítka spusťte testovací režim.
     * Pokud hlášení končí "Everything is ok..:-)" V Home Assistantu přibylo nové zařízení s potřebnými entitami.
