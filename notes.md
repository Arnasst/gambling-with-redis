# Nereliacinės

To launch:
`docker-compose -f "docker-compose.yml" up -d`

To shut down:
`docker-compose -f "docker-compose.yml" down`

## Lab1

### 2. Loterijos bilietų pardavimo programa

Programa generuoja ir parduoda loterijos bilietus.

Kiekvienas loterijos bilietas turi unikalų, nuoseklų numerį. T.y. bilietai numeruojami: 1, 2, 3, 4 iš eilės. Sistema nepraleidžia skaičių, t.y. Bilietų numerių seka 1, 2, 4, 5 yra negalima.

Kiekvienam bilietui yra sugeneruojami 5 atsitiktiniai skaičiai (bilieto laimingi skaičiai) rėžyje nuo 1 iki 40. Skaičiai nesikartoja Skaičius galima generuoti ir ne duomenų bazės pagalba.

Sistema turi (1) užtikrinti bilietų numerių nuoseklumą net esant dideliam kiekiui pardavimų, taip pat (2) leisti efektyviai rasti laimėjusius bilietus įvedant tą naktį iškritusių skaičių (ridenimų skaičių kiekis gali būti įvairus).

Programa leidžia pirkti bilietus, suvesti išridentus skaičius surandant laimėjusius bilietus.

- Store current ticket number. Use WATCH with INCR. DONE
- Design a use case for buying multiple tickets at the same time to show redis lock functionality. DONE
- Store [lucky_numbers]: [ticket_numbers] (k: v) pair for faster search (?). TODO
