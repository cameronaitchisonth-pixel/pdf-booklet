import io
import math
import streamlit as st
from pypdf import PdfReader, PdfWriter, PageObject, Transformation


def compute_booklet_pairs(n):
    """
    For n pages (must be multiple of 4), return saddle-stitch
    pairs: [(left, right), ...] alternating front/back of each leaf.
    """
    pairs = []
    lo, hi = 1, n
    while lo < hi:
        pairs.append((hi, lo))
        pairs.append((lo + 1, hi - 1))
        lo += 2
        hi -= 2
    return pairs


def impose_booklet(reader):
    n = len(reader.pages)
    padded = math.ceil(n / 8) * 8

    first = reader.pages[0]
    pw = float(first.mediabox.width)
    ph = float(first.mediabox.height)

    sheet_w = 2 * pw
    sheet_h = 2 * ph

    pairs = compute_booklet_pairs(padded)
    num_sheets = padded // 8

    leaves = []
    for i in range(0, len(pairs), 2):
        leaves.append((pairs[i], pairs[i + 1]))

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

        front = make_sheet(top_front[0], top_front[1], bot_front[0], bot_front[1])
        writer.add_page(front)

        back = make_sheet(top_back[0], top_back[1], bot_back[0], bot_back[1])
        writer.add_page(back)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output, n, padded, num_sheets


st.set_page_config(page_title="Booklet Imposer", page_icon="📖")
st.title("📖 Booklet Imposer")
st.write(
    "Upload a PDF and get it imposed for saddle-stitch booklet printing. "
    "Print duplex, cut in half, nest, fold, and staple."
)

uploaded = st.file_uploader("Upload a PDF", type="pdf")

if uploaded:
    reader = PdfReader(io.BytesIO(uploaded.read()))
    result, n, padded, num_sheets = impose_booklet(reader)

    st.success(f"{n} pages → {padded} padded → {num_sheets} sheet(s) to print duplex")

    if padded != n:
        st.info(f"{padded - n} blank page(s) added to fill the last sheet.")

    st.download_button(
        label="Download booklet PDF",
        data=result,
        file_name=uploaded.name.replace(".pdf", "-booklet.pdf"),
        mime="application/pdf",
    )

    st.subheader("Instructions")
    st.markdown(
        "1. Print duplex (flip on **short edge**)\n"
        "2. Cut each sheet horizontally in half\n"
        "3. Nest the halves together (outer wraps inner)\n"
        "4. Fold in half, staple on the spine"
    )
