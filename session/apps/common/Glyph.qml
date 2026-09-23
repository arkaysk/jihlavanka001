// Glyph — ikona Tabler (rovnaké písmo ako shell Noctalia: /usr/share/noctalia/assets/fonts).
import QtQuick

Text {
    id: g
    property string name: "file"
    property real size: 18
    readonly property var map: ({
        "folder": 0xEAAD,
        "folder-open": 0xFAF7,
        "file": 0xEAA4,
        "file-text": 0xEAA2,
        "photo": 0xEB0A,
        "music": 0xEAFC,
        "movie": 0xEAFA,
        "file-zip": 0xED4E,
        "file-code": 0xEBD0,
        "home": 0xEAC1,
        "device-desktop": 0xEA89,
        "download": 0xEA96,
        "usb": 0xF00C,
        "database": 0xEA88,
        "server": 0xEB1F,
        "chevron-left": 0xEA60,
        "chevron-right": 0xEA61,
        "chevron-up": 0xEA62,
        "search": 0xEB1C,
        "world": 0xEB54,
        "world-off": 0xF1CA,
        "x": 0xEB55,
        "minus": 0xEAF2,
        "square": 0xEB2C,
        "layout-list": 0xEC14,
        "layout-grid": 0xEDBA,
        "columns-2": 0xF6D5,
        "trash": 0xEB41,
        "copy": 0xEA7A,
        "clipboard": 0xEA6F,
        "star": 0xEB2E,
        "apps": 0xEBB6,
        "files": 0xEDEF,
        "arrow-up": 0xEA25,
        "cpu": 0xEF8E,
        "package": 0xEAFF,
        "external-link": 0xEA99,
        "info-circle": 0xEAC5,
        "settings": 0xEB20,
        "palette": 0xEB01,
        "bolt": 0xEA38,
        "shield": 0xEB24,
        "layout-columns": 0xEAD4,
        "device-gamepad-2": 0xF1D2,
        "coffee": 0xEF0E,
        "user": 0xEB4D,
        "power": 0xEB0D,
        "activity": 0xED23,
        "brush": 0xEBB8,
        "adjustments": 0xEA03,
        "terminal-2": 0xEBEF,
        "eye": 0xEA9A,
        "eye-off": 0xECF0,
        "folder-plus": 0xEAAB,
        "arrows-exchange": 0xF1F4,
        "check": 0xEA5E,
        "alert-triangle": 0xEA06,
        "refresh": 0xEB13,
        "file-music": 0xEA9F,
        "device-floppy": 0xEB62,
        "keyboard": 0xEBD6,
        "wallpaper": 0xEF56,
        "window": 0xEF06,
        "sparkles": 0xF6D7,
        "lock": 0xEAE2,
        "books": 0xEFF2,
        "box": 0xEA45
    })
    FontLoader { id: tabler; source: "file:///usr/share/noctalia/assets/fonts/noctalia-tabler.ttf" }
    font.family: tabler.name
    font.pixelSize: size
    text: String.fromCodePoint(map[name] || map["file"])
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
}
