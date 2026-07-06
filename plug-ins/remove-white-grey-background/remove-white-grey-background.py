#!/usr/bin/env python3
"""GIMP 3.0 plug-in: make white/grey background transparent based on how
saturated (colorful) each pixel is, so stained red/blue cells stay opaque."""

import sys

import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp
gi.require_version("Gegl", "0.4")
from gi.repository import Gegl
from gi.repository import GLib

PROC_NAME = "python-fu-remove-white-grey-background"

# HSV saturation (0-1) below this value becomes fully transparent; above this
# value stays fully opaque; values in between form a soft ramp. Raise
# TRANSPARENCY_THRESHOLD if background remnants are left behind, lower
# OPACITY_THRESHOLD if pale cell edges are getting eaten away.
TRANSPARENCY_THRESHOLD = 0.12
OPACITY_THRESHOLD = 0.35

# Smallest post-ramp value counted as "some color present" (see
# layer_has_color). A layer with nothing above this is left untouched
# instead of being made fully transparent.
NO_COLOR_EPSILON = 1.0 / 255


def apply_gegl_filter(drawable, operation, label, properties):
    filt = Gimp.DrawableFilter.new(drawable, operation, label)
    config = filt.get_config()
    for name, value in properties.items():
        config.set_property(name, value)
    filt.update()
    drawable.merge_filter(filt)


# TODO: on Indexed-mode images, merging this filter chain into an
# Indexed-format scratch layer may force palette quantization, turning the
# soft ramp into hard bands. Not yet verified against real GIMP behavior.
def saturation_map(image, layer):
    """Return a scratch layer holding the layer's HSV saturation, remapped
    into a 0..1 alpha ramp between the two threshold constants."""
    scratch = layer.copy()
    image.insert_layer(scratch, None, -1)

    apply_gegl_filter(
        scratch, "gegl:component-extract", "Saturation", {"component": "hsv-s"}
    )
    apply_gegl_filter(
        scratch,
        "gegl:levels",
        "Threshold Ramp",
        {
            "in-low": TRANSPARENCY_THRESHOLD,
            "in-high": OPACITY_THRESHOLD,
            "out-low": 0.0,
            "out-high": 1.0,
        },
    )
    return scratch


def layer_has_color(scratch):
    """True if any pixel of the (already ramped) saturation map is above
    NO_COLOR_EPSILON, i.e. the layer has at least some non-background color."""
    _, _, _, _, count, _ = scratch.histogram(
        Gimp.HistogramChannel.VALUE, NO_COLOR_EPSILON, 1.0
    )
    return count > 0


def remove_background(image, layer):
    if layer.get_mask() is not None:
        Gimp.message(
            'Remove White/Grey Background: skipped "%s" (it already has a '
            "layer mask)." % layer.get_name()
        )
        return

    scratch = saturation_map(image, layer)
    try:
        if not layer_has_color(scratch):
            return

        if not layer.has_alpha():
            layer.add_alpha()

        mask = layer.create_mask(Gimp.AddMaskType.WHITE)
        layer.add_mask(mask)
        try:
            src_buffer = scratch.get_buffer()
            dst_buffer = mask.get_shadow_buffer()
            src_buffer.copy(None, Gegl.AbyssPolicy.NONE, dst_buffer, None)
            dst_buffer.flush()
            mask.merge_shadow(True)
            mask.update(0, 0, layer.get_width(), layer.get_height())
            layer.remove_mask(Gimp.MaskApplyMode.APPLY)
        except Exception:
            layer.remove_mask(Gimp.MaskApplyMode.DISCARD)
            raise
    finally:
        image.remove_layer(scratch)


class RemoveWhiteGreyBackground(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROC_NAME]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("*")
        procedure.set_menu_label("Remove White/Grey Background")
        procedure.add_menu_path("<Image>/Image/")
        procedure.set_documentation(
            "Make white/grey background transparent",
            "Makes low-saturation (white/grey) areas of every layer "
            "transparent, with a soft edge, while keeping colored "
            "(e.g. red/blue stained) areas opaque.",
            name,
        )
        procedure.set_attribution("gimp-auto-arrange", "gimp-auto-arrange", "2026")
        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        layers = image.get_layers()

        image.undo_group_start()
        try:
            for layer in layers:
                remove_background(image, layer)
        finally:
            image.undo_group_end()

        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(RemoveWhiteGreyBackground.__gtype__, sys.argv)
