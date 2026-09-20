"""Rozmery lišty na jednom mieste (docs/lista-a-rohy.md, časť 1).

Všetky dlaždice lišty (rohy aj segmenty) sú pritlačené k spodnému okraju obrazovky a ich horná hrana
je v tej istej výške. Rezervované miesto pre okná preto končí presne nad nimi.
"""

BAR_HEIGHT = 84                         # výška lišty, každej dlaždice aj rezervovaného miesta pre okná
SEGMENT = BAR_HEIGHT                    # výška segmentu lišty (hodiny, zoznam okien, prompt)
ICON_SEGMENT_WIDTH = 64                 # šírka segmentu s jednou ikonou (napájanie, správca súborov)
CORNER_HEIGHT = BAR_HEIGHT              # rohová dlaždica je rovnako vysoká ako lišta
CORNER_WIDTH = 2 * BAR_HEIGHT           # a dvakrát taká široká: obdĺžnik, nie štvorec
ARM_HEIGHT = 110                        # výška ramena L (kmeňa) nad lištou

# Plátno textúry lišty: päta L (dlaždica) a nad ňou kmeň (rameno). Súradnice plátna idú od rohu
# obrazovky doprava a nahor. Šírku kmeňa v R3 zladí s popupom.
TEXTURE_WIDTH = 640
TEXTURE_HEIGHT = BAR_HEIGHT + ARM_HEIGHT
