from pypdf import PdfReader
from datetime import datetime
from models import PDFResponse, DeliveryStop
import re
import difflib

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

    # load known stores
    known_stores = load_known_stores()
    unmatched_stores = []

    # Save for debug
    with open("pdf_text_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    full_text = "\n".join(lines)
    sid = re.search(r"SID:\s*(\d+)", full_text).group(1)
    order = re.search(r"Order #:\s*(\d+)", full_text).group(1)

    # --- Parse Pickup ---
    pickup_location = ""
    pickup_address = ""
    pickup_datetime = None
    for i, line in enumerate(lines):
        if "Load At" in line:
            pickup_location = find_next_non_empty(lines, i + 3)
            addr_1 = find_next_non_empty(lines, i + 4)
            addr_2 = find_next_non_empty(lines, i + 5)
            pickup_address = f"{addr_1} {addr_2}"
            for j in range(i, i + 20):
                if "Earliest date:" in lines[j]:
                    pickup_date = find_next_non_empty(lines, j + 1)
                    pickup_time = find_next_non_empty(lines, j + 2)
                    pickup_datetime = datetime.strptime(f"{pickup_date} {pickup_time}", "%m/%d/%y %H:%M")
                    break
            break

    # --- Parse Deliveries ---
    deliveries = []
    for i in range(len(lines)):
        if lines[i].strip() == "Commodity:" and "UNKNOWN" in lines[i + 1].strip() and re.match(r"PO \d+", lines[i + 2].strip()):
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
            delivery_address = f"{addr_1} {addr_2}"

            # Find delivery date and time
            delivery_date = delivery_time = None
            for j in range(i, i + 25):
                if "Earliest date:" in lines[j]:
                    delivery_date = find_next_non_empty(lines, j + 1)
                    delivery_time = find_next_non_empty(lines, j + 2)
                    break

            if delivery_date and delivery_time:
                delivery_datetime = datetime.strptime(f"{delivery_date} {delivery_time}", "%m/%d/%y %H:%M")
                deliveries.append(
                    DeliveryStop(
                        po_number=po_number,
                        store=store_name,
                        address=delivery_address,
                        datetime=delivery_datetime
                    )
                )

    return PDFResponse(
        sid=sid,
        order_number=order,
        pickup_location=pickup_location,
        pickup_address=pickup_address,
        pickup_datetime=pickup_datetime,
        deliveries=deliveries
    )

# Test runner
if __name__ == "__main__":
    from io import BytesIO
    with open("test.pdf", "rb") as f:
        pdf_stream = BytesIO(f.read())
        data = extract_order_info(pdf_stream)
        print(data.model_dump_json(indent=2))
