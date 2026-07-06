#!/usr/bin/env python3
"""GIMP 3.0 plug-in: arrange layers side by side, ordered by trailing number."""

import re
import sys

import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp
from gi.repository import GLib

PROC_NAME = "python-fu-side-by-side-arrange"

TRAILING_NUMBER_RE = re.compile(r"(\d+)(?!\D*\d)")


def trailing_number(name):
    match = TRAILING_NUMBER_RE.search(name)
    return int(match.group(1)) if match else None


def sort_by_trailing_number(layers):
    def sort_key(layer):
        number = trailing_number(layer.get_name())
        # Layers without a number sort as lowest (placed at the far right).
        return number if number is not None else -1

    return sorted(layers, key=sort_key, reverse=True)


def place_side_by_side(image, layers):
    max_height = max(layer.get_height() for layer in layers)

    x = 0
    for layer in layers:
        width = layer.get_width()
        height = layer.get_height()
        y = (max_height - height) // 2
        layer.set_offsets(x, y)
        x += width

    image.resize_to_layers()


class SideBySideArrange(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("*")
        procedure.set_menu_label("Arrange Layers Side by Side")
        procedure.add_menu_path("<Image>/Image/")
        procedure.set_documentation(
            "Arrange numbered layers side by side",
            "Sorts layers by the trailing number in their name and lines "
            "them up horizontally (highest number left, lowest number "
            "right), vertically centered, then resizes the canvas to fit.",
            name,
        )
        procedure.set_attribution("gimp-auto-arrange", "gimp-auto-arrange", "2026")
        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        layers = image.get_layers()

        if len(layers) < 2:
            Gimp.message("Side by Side Arrange: need at least 2 layers.")
            return procedure.new_return_values(
                Gimp.PDBStatusType.SUCCESS, GLib.Error()
            )

        unnumbered = [l.get_name() for l in layers if trailing_number(l.get_name()) is None]
        if unnumbered:
            Gimp.message(
                "Side by Side Arrange: no number found in: "
                + ", ".join(unnumbered)
                + " (placed at the right end)."
            )

        image.undo_group_start()
        try:
            ordered = sort_by_trailing_number(layers)
            place_side_by_side(image, ordered)
        finally:
            image.undo_group_end()

        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(SideBySideArrange.__gtype__, sys.argv)
