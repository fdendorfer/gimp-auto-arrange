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

# HSV saturation (0-1) at or below this value becomes fully transparent; at
# or above OPACITY_THRESHOLD stays fully opaque; values in between form a
# ramp (a gap between the two gives a soft/feathered edge; equal values, the
# shipped default, give a hard edge). Raise TRANSPARENCY_THRESHOLD if
# background remnants are left behind, lower OPACITY_THRESHOLD if pale cell
# edges are getting eaten away. Real saturation values tend to be much lower
# than you'd guess - check a layer's actual range before tuning, e.g. in the
# Python-Fu console: `layer.histogram(Gimp.HistogramChannel.VALUE, 0, 1)`
# after running just the component-extract step (see README).
TRANSPARENCY_THRESHOLD = 0.02
OPACITY_THRESHOLD = 0.02

# How similar a pixel must be to a corner pixel to flood-fill together as
# "background" when protecting enclosed islands (see protect_enclosed_islands
# below) - same units as GIMP's own sample threshold.
SAMPLE_THRESHOLD = 0.05

# Pixels to grow the flood-filled background selection by before inverting
# it, so the soft transition ring right at the true outer edge isn't
# clobbered along with genuinely enclosed interior islands.
GROW_PIXELS = 1


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


def protect_enclosed_islands(image, layer, scratch, mask):
    """Restore full opacity to any area the ramp marked transparent but that
    isn't actually reachable from the image border (e.g. a light-colored
    area enclosed inside a cell), by flood-filling the background from all
    four corners of scratch and refilling everything else on the mask back
    to opaque. Assumes the corners of the image are genuine background."""
    width = layer.get_width()
    height = layer.get_height()

    Gimp.context_set_sample_threshold(SAMPLE_THRESHOLD)
    image.select_contiguous_color(Gimp.ChannelOps.REPLACE, scratch, 0, 0)
    image.select_contiguous_color(Gimp.ChannelOps.ADD, scratch, width - 1, 0)
    image.select_contiguous_color(Gimp.ChannelOps.ADD, scratch, 0, height - 1)
    image.select_contiguous_color(
        Gimp.ChannelOps.ADD, scratch, width - 1, height - 1
    )
    Gimp.Selection.grow(image, GROW_PIXELS)
    Gimp.Selection.invert(image)
    mask.edit_fill(Gimp.FillType.WHITE)
    Gimp.Selection.none(image)


def remove_background(image, layer):
    if layer.get_mask() is not None:
        Gimp.message(
            'Remove White/Grey Background: skipped "%s" (it already has a '
            "layer mask)." % layer.get_name()
        )
        return

    if image.get_base_type() == Gimp.ImageBaseType.GRAY:
        return

    scratch = saturation_map(image, layer)
    try:
        if not layer.has_alpha():
            layer.add_alpha()

        mask = layer.create_mask(Gimp.AddMaskType.WHITE)
        layer.add_mask(mask)
        try:
            src_buffer = scratch.get_buffer()
            dst_buffer = mask.get_shadow_buffer()
            rect = src_buffer.get_extent()
            src_buffer.copy(rect, Gegl.AbyssPolicy.NONE, dst_buffer, rect)
            dst_buffer.flush()
            mask.merge_shadow(True)
            mask.update(0, 0, layer.get_width(), layer.get_height())

            protect_enclosed_islands(image, layer, scratch, mask)

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
            "transparent, while keeping colored (e.g. red/blue stained) "
            "areas opaque - including any low-saturation areas enclosed "
            "inside them.",
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
