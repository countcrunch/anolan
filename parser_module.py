from pypdf import PdfReader
from datetime import datetime
from models import PDFResponse, DeliveryStop
import re
import difflib
from typing import Optional

# Mapping of specific Richmond addresses to nicknamed store identifiers
RICHMOND_ALIASES = {
    "5515 W BROAD ST": "RICHMOND (LIBBIE)",
    "11740 W BROAD ST STE A": "RICHMOND (SHORT PUMP)",
}


def _safe_search(pattern: str, text: str, group: int = 1) -> str:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group(group).strip() if m else ""

def load_known_stores(filepath="known_stores.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip().upper() for line in f if line.strip()]

def find_next_non_empty(lines, start_index):
    for i in range(start_index, len(lines)):
        line = lines[i].strip()
        if line:
            return line
    return ""

def extract_order_info(pdf_stream) -> PDFResponse:
    reader = PdfReader(pdf_stream)
    lines = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            lines.extend(text.splitlines())

    known_stores = load_known_stores()
    unmatched_stores = []

    with open("pdf_text_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    full_text = "\n".join(lines)

    # SAFE regex extraction (no .group() on None)
    sid = _safe_search(r"SID:\s*(\d+)", full_text)
    order = _safe_search(r"Order\s*#:\s*(\d+)", full_text)

    # --- Parse Pickup (defensive indices & dates) ---
    pickup_location = ""
    pickup_address = ""
    pickup_datetime: Optional[datetime] = None

    for i, line in enumerate(lines):
        if "Load At" in line:
            pickup_location = find_next_non_empty(lines, i + 3)
            addr_1 = find_next_non_empty(lines, i + 4)
            addr_2 = find_next_non_empty(lines, i + 5)
            pickup_address = f"{addr_1} {addr_2}".strip()
            # defensive window search
            for j in range(i, min(i + 40, len(lines))):
                if j < len(lines) and "Earliest date:" in lines[j]:
                    pickup_date = find_next_non_empty(lines, j + 1)
                    pickup_time = find_next_non_empty(lines, j + 2)
                    try:
                        pickup_datetime = datetime.strptime(f"{pickup_date} {pickup_time}", "%m/%d/%y %H:%M")
                    except Exception:
                        pickup_datetime = None
                    break
            break

    # --- Parse Deliveries (bounds checks + fuzzy matching) ---
    deliveries = []
    for i in range(len(lines) - 3):
        # guard indexes and look for the PO header we expect
        if (
            lines[i].strip() == "Commodity:" and
            i + 2 < len(lines) and re.match(r"PO \d+", lines[i + 2].strip(), flags=re.IGNORECASE)
        ):
            po_number = lines[i + 2].strip()

            raw_store_name = find_next_non_empty(lines, i + 6)
            store_name = raw_store_name

            matched = difflib.get_close_matches(raw_store_name.upper(), known_stores, n=1, cutoff=0.8)
            if matched:
                store_name = matched[0]
            else:
                unmatched_stores.append(raw_store_name)

            addr_1 = find_next_non_empty(lines, i + 7)
            addr_2 = find_next_non_empty(lines, i + 8)
            delivery_address = f"{addr_1} {addr_2}".strip()

            # Richmond alias exception remains
            if store_name.upper() == "RICHMOND":
                for addr, alias in RICHMOND_ALIASES.items():
                    if addr in delivery_address.upper():
                        store_name = alias
                        break

            # Find delivery date/time (defensive)
            delivery_date = delivery_time = None
            for j in range(i, min(i + 40, len(lines))):
                if "Earliest date:" in lines[j]:
                    delivery_date = find_next_non_empty(lines, j + 1)
                    delivery_time = find_next_non_empty(lines, j + 2)
                    break

            if delivery_date and delivery_time:
                try:
                    delivery_datetime = datetime.strptime(f"{delivery_date} {delivery_time}", "%m/%d/%y %H:%M")
                    deliveries.append(
                        DeliveryStop(
                            po_number=po_number,
                            store=store_name,
                            address=delivery_address,
                            datetime=delivery_datetime,
                        )
                    )
                except Exception:
                    # skip malformed delivery timestamps but keep parsing
                    pass

    # --- PU# in Remarks (unchanged, but defensive) ---
    pickup_number = "-"
    for i, line in enumerate(lines):
        if line.strip().upper() == "REMARKS":
            next_line = find_next_non_empty(lines, i + 1)
            if next_line and next_line not in {"•", "-", "—"}:
                pickup_number = next_line.strip()
            break

    return PDFResponse(
        sid=sid,
        order_number=order,
        pickup_location=pickup_location,
        pickup_address=pickup_address,
        pickup_datetime=pickup_datetime,
        deliveries=deliveries,
        pickup_number=pickup_number,
        unmatched_stores=list(dict.fromkeys(unmatched_stores)),  # dedupe & return
    )

# Test runner
if __name__ == "__main__":
    from io import BytesIO
    with open("test.pdf", "rb") as f:
        pdf_stream = BytesIO(f.read())
        data = extract_order_info(pdf_stream)
        print(data.model_dump_json(indent=2))

