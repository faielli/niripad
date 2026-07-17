# Niripad

Un editor di testo leggero scritto in Python con PyQt6, ottimizzato per Wayland/X11.

## Requisiti

- Arch Linux (o derivate: Manjaro, EndeavourOS, ecc.)
- `python`
- `python-pyqt6`
- `python-qtawesome`

## Installazione

```bash
git clone https://github.com/tuousername/text-editor
cd text-editor
chmod +x install.sh
./install.sh
```

Lo script crea automaticamente il pacchetto e lo installa tramite `pacman`.

## Avvio

Dal launcher delle applicazioni cerca **Niripad**, oppure da terminale:

```bash
niripad
```

## Disinstallazione

```bash
sudo pacman -R niripad
```

## Aggiornamento

```bash
cd text-editor
git pull
./install.sh
```
