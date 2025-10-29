# 🖱️ Automatikus Egér Mozgató

Egyszerű automatikus egérmozgató program, amely megakadályozza a képernyővédő vagy az automatikus zárolás aktiválódását.

## Funkciók

- Automatikus egérmozgatás beállítható időközönként
- Állítható mozgási távolság
- Egyszerű, intuitív PySide6 alapú grafikus felület
- Valós idejű állapot megjelenítés
- Magyar nyelvű felület

## Használat

A programot a főmenüből lehet elindítani a "🖱️ Automatikus Egér Mozgató" gombra kattintva.

### Beállítások

1. **Időköz**: Az egérmozgatás gyakorisága másodpercben (5-300 másodperc)
   - Alapértelmezett: 30 másodperc
   
2. **Mozgási távolság**: Maximális mozgási távolság pixelekben (1-50 pixel)
   - Alapértelmezett: 5 pixel

### Működés

1. Állítsd be a kívánt időközt és mozgási távolságot
2. Kattints az "▶️ Indítás" gombra
3. A program automatikusan mozgatni fogja az egeret a megadott időközönként
4. Az állapot ablakban láthatod a mozgatások részleteit
5. A leállításhoz kattints a "⏹️ Leállítás" gombra

## Technikai részletek

A program a PySide6 könyvtár QCursor osztályát használja az egér vezérlésére, így nem igényel külső függőségeket a már telepített PySide6-on kívül.

### Fájlok

- `run.py`: Belépési pont
- `app/mouse_mover_ui.py`: Grafikus felület
- `app/mouse_controller.py`: Egérvezérlő logika
