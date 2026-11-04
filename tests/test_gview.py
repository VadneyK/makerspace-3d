"""tools/gview.py: draw a plate from its own G-code."""
import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

import gview  # noqa: E402
import synthetic as syn  # noqa: E402

RED, BLUE = (255, 0, 0), (0, 0, 255)
BG = (235, 235, 235)


def _render(tmp_path, g, **kw):
    path = syn.write_3mf(tmp_path / "p.3mf", gcodes={1: g})
    out = tmp_path / "plate.png"
    gview.render(str(path), str(out), {0: RED, 1: BLUE}, (0, 0, 256, 256), scale=2, **kw)
    return Image.open(out).convert("RGB")


def test_later_layers_paint_over_earlier_ones(tmp_path):
    im = _render(tmp_path, syn.gcode(layers=2, tools=(0, 1)))
    assert im.size == (512, 512)
    # the square outline from (60,60) to (180,180), drawn last by tool 1 (blue); y is flipped
    assert im.getpixel((int(120 * 2), int((256 - 60) * 2))) == BLUE
    assert im.getpixel((int(120 * 2), int((256 - 120) * 2))) == BG     # inside the outline: nothing


def test_layer_filter_shows_the_first_layer_color(tmp_path):
    im = _render(tmp_path, syn.gcode(layers=2, tools=(0, 1)), layers={1})
    assert im.getpixel((240, 392)) == RED


def test_tool_changes_above_t7_are_ignored(tmp_path):
    g = syn.gcode(layers=1).replace("T0\n", "T0\nT255\n", 1)   # Bambu writes T255 / T1000 as markers
    im = _render(tmp_path, g)
    assert im.getpixel((240, 392)) == RED


def test_moves_outside_the_box_are_skipped(tmp_path):
    g = syn.gcode(layers=1, extra_lines=["G1 X400 Y400 E1"])
    im = _render(tmp_path, g)          # must not raise or draw outside the canvas
    assert im.size == (512, 512)
