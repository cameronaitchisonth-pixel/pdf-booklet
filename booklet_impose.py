#!/usr/bin/env python3
"""
Impose any PDF into a half-size saddle-stitch booklet.

Output: 2x2 grid pages, meant to be printed duplex (short edge flip).
After printing, cut each sheet horizontally in half,
nest the halves together, fold in half, and staple on the spine.

Pages are padded to the nearest multiple of 8 with blanks.

Usage: python booklet_impose.py input.pdf [output.pdf]
"""

import sys
import math
from pypdf import PdfReader, PdfWriter, PageObject, Transformation


def compute_booklet_pairs(n):
    """
    For n pages (must be multiple of 4), return saddle-stitch
    pairs: [(left, right), ...] alternating front/back of each leaf.
    """
    pairs = []
    lo, hi = 1, n
    while lo < hi:
        pairs.append((hi, lo))          # front of leaf
        pairs.append((lo + 1, hi - 1))  # back of leaf
        lo += 2
        hi -= 2
    return pairs


def impose_booklet(input_path, output_path=None):
    if output_path is None:
        output_path = input_path.replace(".pdf", "-booklet.pdf")

    reader = PdfReader(input_path)
    n = len(reader.pages)

    # Pad to multiple of 8 (4 for booklet, 8 for top/bottom halves)
    padded = math.ceil(n / 8) * 8
    if padded != n:
        print(f"Padding from {n} to {padded} pages (blanks at the end).")

    # Page dimensions from first page
    first = reader.pages[0]
    pw = float(first.mediabox.width)
    ph = float(first.mediabox.height)

    sheet_w = 2 * pw
    sheet_h = 2 * ph

    pairs = compute_booklet_pairs(padded)

    num_sheets = padded // 8

    # Group pairs into leaves (each leaf = front pair + back pair)
    leaves = []
    for i in range(0, len(pairs), 2):
        leaves.append((pairs[i], pairs[i + 1]))

    # Outer leaves on top half, inner leaves on bottom half
    top_leaves = leaves[:num_sheets]
    bottom_leaves = leaves[num_sheets:]

    def get_page(page_num):
        idx = page_num - 1
        if 0 <= idx < len(reader.pages):
            return reader.pages[idx]
        return PageObject.create_blank_page(width=pw, height=ph)

    def make_sheet(tl, tr, bl, br):
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        sheet.merge_transformed_page(get_page(tl), Transformation().translate(0, ph))
        sheet.merge_transformed_page(get_page(tr), Transformation().translate(pw, ph))
        sheet.merge_transformed_page(get_page(bl), Transformation().translate(0, 0))
        sheet.merge_transformed_page(get_page(br), Transformation().translate(pw, 0))
        return sheet

    writer = PdfWriter()

    for i in range(num_sheets):
        top_front, top_back = top_leaves[i]
        bot_front, bot_back = bottom_leaves[i]

        # Front of physical sheet
        front = make_sheet(top_front[0], top_front[1], bot_front[0], bot_front[1])
        writer.add_page(front)

        # Back of physical sheet
        back = make_sheet(top_back[0], top_back[1], bot_back[0], bot_back[1])
        writer.add_page(back)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Booklet written to: {output_path}")
    print(f"  {n} content pages -> {padded} padded -> {num_sheets} sheet(s) (print duplex)")
    print()
    print("Instructions:")
    print("1. Print duplex (flip on SHORT edge)")
    print("2. Cut each sheet horizontally in half")
    print("3. Nest the halves together (outer wraps inner)")
    print("4. Fold in half, staple on the spine")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input.pdf [output.pdf]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    impose_booklet(input_path, output_path)
