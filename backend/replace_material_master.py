"""
Replace Material Master with New 73 Solar Manufacturing Materials
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

# Load environment variables
load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# New material list (Name | Category/Short Name)
MATERIALS_DATA = """
String Interconnect Ribbon 6X0.40MM	Interconnect Ribbon
SPLIT JUNCTION BOX,400MM CABLE 30AMP	JUNCTION BOX
POTTING MATERIAL-WHITE-COMPONENT (A)	POTTING -A
POTTING MATERIAL-COMPONENT (B)	POTTING -B
SILOCON SEALANT DRUM	SILOCON
RIBBON ROUND WIRE 0.26MM WITH COATING	Ribbon
Cell Alignment Tape	Cell TAPE
SOLAR GLASS TEMP/ARC2272X1128X2.0MM	GLASS FRONT
SOLAR GLASS TEMP/NON ARC2272X1128 X2.0MM	GLASS BACK
SOLAR GLASS TEMP/ARC2457X1128X2.0MM FRNT	GLASS FRONT
SLR GLASS TEMP/NON ARC2457X1128X2.0MM	GLASS BACK
RFID UHF ALIEN 9640 WET INLAY	RFID
Flux	Flux
BARCODE LABEL(66MMX15MM) POLYESTER	BARCODE-1
BARCODE LABEL(50MMX12MM) POLYESTER	BARCODE-2
THERMAL RIBBON(105MMX300MTR)	THERMAL RIBBON
THERMAL RIBBON(50MMX300MTR)	THERMAL RIBBON
POE WIDTH 1122MM THICKNESS 480GSM500	POE
Back- EPE UVT 1128MMX550μ,450GSM	Back- EPE
SC182X182 TOPCON- 16BB- E>25.3%- P>8.35W	CELL
SC182X182 TOPCON- 16BB- E>25.4%- P>8.39W	CELL
SC182X182 TOPCON-16BB- E>25.5%-P>8.25W	CELL
SC182X182 TOPCON-16BB- E>25.1%-P>8.29W	CELL
SC182X182 TOPCON- 16BB- E>25.2%- P>8.32W	CELL
STRETCH FILM 450MMX23MIC	STRETCH FILM
STRAPPING ROLL 16X0.85MM	STRAPING ROLL
Corrugated sheet set (30 module)	Corrugated Sheet
Wooden Pallet 2475X1090X153MM	PALLETS
Back label 15X166MM_620Wp	BACK LABLE
Back label 15X166MM_625Wp	BACK LABLE
Back label 15X166MM_630Wp	BACK LABLE
Back label 15X166MM_635Wp	BACK LABLE
Back label 15X166MM_640Wp	BACK LABLE
COLOURED STICKER(QC OK SITCKER18MM)Green	Round sticker
COLOUREDSTICKER(QC OK SITCKER18MM)Yellow	Round sticker
COLOURED STICKER(QC OK SITCKER18MM)Blue	Round sticker
COLOURED STICKER(QC OK SITCKER18MM)Red	Round sticker
Back- EPE UVT 1128MMX500μm,420GSM	Back- EPE
Front- EPE UVT 1122MMX550μm,440GSM	Front- EPE
EDGE SEALING TAPE	EDGE TAPE
AL.FRAME2462X35X33MM6036 T6 (L)	FRAME LONG
AL.FRAME1133X35X33MM6036 T6 (S)	FRAME SHORT
Front- EPE UVT 1122MMX550μm,440GSM	Front- EPE
POE WIDTH1122MMX500µ,480GSM(First solar)	POE
Back-EPEUVT1128MMX550μ,450GSM(Firstsolar)	Back- EPE
BARCODE LABEL(100MMX8MM)	BARCODE-1
RFID UHF ALIEN 9640 WET INLAY(100MMX8MM)	RFID
AL.FRAME2277X35X33MM (L)	FRAME LONG
AL.FRAME1133X35X33MM(S)	FRAME SHORT
SPLIT JUNCTION BOX,300MM CABLE 30AMP	JUNCTION BOX
SC182.2X183.75MM BT GA 16BB8.40Effi25.1%	CELL
SC182.2X183.75MM BT GA 16BB8.43Effi25.2%	CELL
SC182.2X183.75MM BT GA 16BB8.47Effi25.3%	CELL
SC182.2X183.75MM BT GA 16BB8.50Effi25.4%	CELL
SC182.2X183.75MM BT GA 16BB8.54Effi25.5%	CELL
SC182.2X183.75MM BT GA 16BB8.57Effi25.6%	CELL
String Interconnect Ribbon 4X0.40MM	Interconnect Ribbon
Uv Protected Label (15Mmx120Mm)Polyester	UV Protected
Back label 15X162MM_580Wp	BACK LABLE
Back label 15X162MM_585Wp	BACK LABLE
Back label 15X162MM_590Wp	BACK LABLE
Wooden Pallet 2300X1090X152MM	PALLETS
IN HOUSE WOODEN PALLET-30	PALLETS
Wooden Pallet 2300X1130X152MM_36 Module	PALLETS
Corrugated sheet set 144 HC (30 module	Corrugated Sheet
Corrugated Corner Protector_30MM	Corrugated Sheet
Back label 15X162MM_595Wp	BACK LABLE
Back label 15X162MM_600Wp	BACK LABLE
AL.FRAME 1134X30X15 MM (S)	FRAME SHORT
AL.FRAME 2278X30X30 MM (L)	FRAME LONG
Back label 15X162MM_30MM_585Wp	BACK LABLE
Back label 15X162MM_30MM_595Wp	BACK LABLE
Back label 15X162MM_30MM_600Wp	BACK LABLE
"""

def categorize_material(name, short_name):
    """Categorize material based on name and assign appropriate UOM"""
    name_lower = name.lower()
    
    # Category mapping
    if 'cell' in name_lower or 'sc182' in name_lower or 'topcon' in name_lower:
        return "Solar Cells", "PCS"
    elif 'glass' in name_lower:
        return "Glass & Encapsulation", "PCS"
    elif 'frame' in name_lower or 'al.frame' in name_lower:
        return "Frames & Mounting", "PCS"
    elif 'junction box' in name_lower:
        return "Junction Box", "PCS"
    elif 'ribbon' in name_lower or 'interconnect' in name_lower:
        return "Interconnect Materials", "MTR"
    elif 'poe' in name_lower or 'epe' in name_lower:
        return "Encapsulant", "MTR"
    elif 'potting' in name_lower or 'silocon' in name_lower:
        return "Potting & Sealant", "KG"
    elif 'tape' in name_lower:
        return "Assembly Consumables", "MTR"
    elif 'label' in name_lower or 'barcode' in name_lower or 'sticker' in name_lower:
        return "Labels & Identification", "PCS"
    elif 'rfid' in name_lower:
        return "Labels & Identification", "PCS"
    elif 'thermal ribbon' in name_lower:
        return "Printing Materials", "ROLL"
    elif 'flux' in name_lower:
        return "Assembly Consumables", "LTR"
    elif 'pallet' in name_lower:
        return "Packaging Materials", "PCS"
    elif 'corrugated' in name_lower:
        return "Packaging Materials", "PCS"
    elif 'stretch film' in name_lower or 'strapping' in name_lower:
        return "Packaging Materials", "ROLL"
    else:
        return "Raw Materials", "PCS"

def generate_material_code(name, index):
    """Generate unique material code"""
    # Extract key identifier from name
    if 'SC182' in name:
        return f"CELL-{index:03d}"
    elif 'GLASS' in name.upper():
        return f"GLASS-{index:03d}"
    elif 'FRAME' in name.upper():
        return f"FRAME-{index:03d}"
    elif 'JUNCTION' in name.upper():
        return f"JBOX-{index:03d}"
    elif 'POE' in name.upper():
        return f"POE-{index:03d}"
    elif 'EPE' in name.upper():
        return f"EPE-{index:03d}"
    elif 'RIBBON' in name.upper():
        return f"RIB-{index:03d}"
    elif 'LABEL' in name.upper() or 'BARCODE' in name.upper():
        return f"LBL-{index:03d}"
    elif 'PALLET' in name.upper():
        return f"PKG-PLT-{index:03d}"
    elif 'CORRUGATED' in name.upper():
        return f"PKG-COR-{index:03d}"
    else:
        return f"MAT-{index:03d}"

def replace_material_master():
    print("=" * 70)
    print("REPLACE MATERIAL MASTER - NEW 73 MATERIALS")
    print("=" * 70)
    print()
    
    # Parse material data
    lines = [line.strip() for line in MATERIALS_DATA.strip().split('\n') if line.strip()]
    materials_to_create = []
    
    print(f"📦 Parsing {len(lines)} materials...")
    
    for idx, line in enumerate(lines, 1):
        parts = line.split('\t')
        if len(parts) >= 2:
            name = parts[0].strip()
            short_name = parts[1].strip()
            
            category, uom = categorize_material(name, short_name)
            material_code = generate_material_code(name, idx)
            
            material_doc = {
                "material_id": f"mat_{uuid.uuid4().hex[:12]}",
                "material_code": material_code,
                "name": name,
                "description": short_name,
                "category": category,
                "uom": uom,
                "stock_method": "FIFO",
                "min_stock_level": 0,
                "max_stock_level": 10000,
                "reorder_point": 500,
                "current_stock": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "created_by": "admin"
            }
            materials_to_create.append(material_doc)
            print(f"  ✓ {idx}. {material_code} - {name} ({category})")
    
    print()
    print(f"📊 Total materials to create: {len(materials_to_create)}")
    print()
    
    # Show current state
    current_count = db.materials.count_documents({})
    print(f"🗄️  Current materials in database: {current_count}")
    print()
    
    # Confirm action
    confirmation = input("⚠️  This will DELETE all existing materials and add 73 new ones. Proceed? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("❌ Operation cancelled.")
        return
    
    print()
    print("🔄 Starting replacement...")
    print()
    
    # Delete old materials
    delete_result = db.materials.delete_many({})
    print(f"  ✓ Deleted {delete_result.deleted_count} old materials")
    
    # Insert new materials
    insert_result = db.materials.insert_many(materials_to_create)
    print(f"  ✓ Inserted {len(insert_result.inserted_ids)} new materials")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Group by category
    from collections import defaultdict
    category_counts = defaultdict(int)
    for mat in materials_to_create:
        category_counts[mat['category']] += 1
    
    print("\n📊 Materials by Category:")
    for category, count in sorted(category_counts.items()):
        print(f"  - {category}: {count} materials")
    
    print()
    print(f"✅ Material Master replacement complete!")
    print(f"   Total materials: {len(materials_to_create)}")
    print(f"   All materials initialized with 0 current stock")
    print("=" * 70)

if __name__ == "__main__":
    replace_material_master()
