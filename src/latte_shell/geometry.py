"""Rozmery lišty na jednom mieste (docs/lista-a-rohy.md, časť 1).

Všetky dlaždice lišty (rohy aj segmenty) sú pritlačené k spodnému okraju obrazovky a ich horná hrana
je v tej istej výške. Rezervované miesto pre okná preto končí presne nad nimi.

Výška lišty je nastavenie (appearance.toml, `bar.height`; Nastavenia › Prostredie › Lišta). Lišta ju
načíta pri štarte a pri každej zmene súboru a volá set_bar_height; ostatné moduly si ju pýtajú
funkciou bar_height() vždy, keď ju potrebujú (nikdy si ju nekopírujú do konštanty).
"""

DEFAULT_BAR_HEIGHT = 84
MIN_BAR_HEIGHT = 48                     # obsah lišty (hodiny, prompt) si pýta aspoň 43 px; pod 48 by lišta klamala
MAX_BAR_HEIGHT = 96                     # vyššia zdrobní zoznam okien (rohy sú dvakrát také široké ako vysoké)
ICON_SEGMENT_WIDTH = 64                 # šírka segmentu s jednou ikonou (napájanie, správca súborov)
ARM_HEIGHT = 110                        # výška ramena L (kmeňa) nad lištou
POPUP_WIDTH = 820                       # šírka popupu mapy aj kmeňa L (dva stĺpce skupín zariadení sa doň vojdú)
TEXTURE_WIDTH = POPUP_WIDTH             # šírka plátna textúry lišty

_bar_height = DEFAULT_BAR_HEIGHT


def clamp_bar_height(px):
    """Výška lišty v dovolenom rozsahu; nezmyselná hodnota dá predvolenú."""
    try:
        return max(MIN_BAR_HEIGHT, min(MAX_BAR_HEIGHT, int(round(px))))
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_BAR_HEIGHT


def set_bar_height(px):
    """Nastaví výšku lišty. Vráti True, ak sa zmenila."""
    global _bar_height
    value = clamp_bar_height(px)
    changed = value != _bar_height
    _bar_height = value
    return changed


def bar_height():
    """Výška lišty, každej dlaždice aj rezervovaného miesta pre okná."""
    return _bar_height


def corner_width():
    """Rohová dlaždica je dvakrát taká široká ako vysoká: obdĺžnik, nie štvorec."""
    return 2 * _bar_height


def texture_height():
    """Plátno textúry lišty: päta L (dlaždica) a nad ňou kmeň (rameno).

    Súradnice plátna idú od rohu obrazovky doprava a nahor.
    """
    return _bar_height + ARM_HEIGHT


def corner_icon_size():
    """Ikona rohovej dlaždice (bez popisu, ten je až v otvorenom popupe) rastie s výškou lišty."""
    return max(20, min(40, round(_bar_height * 0.42)))
