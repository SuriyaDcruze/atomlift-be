# Stock Register Feature

## Overview
The Stock Register is a comprehensive inventory tracking system that monitors all stock movements (inward and outward) and calculates available stock for each item in real-time.

## Features

### 1. Stock Register Model
- **Automatic Register Number**: Auto-generates unique register numbers (STK0001, STK0002, etc.)
- **Transaction Types**: 
  - INWARD: Items received/added to stock
  - OUTWARD: Items issued/removed from stock
- **Value Tracking**: Tracks unit value and automatically calculates total value
- **Reference Tracking**: Link transactions to reference documents

### 2. Stock Register View Page
Displays a comprehensive table with the following columns:

| Column | Description |
|--------|-------------|
| NO | Sequential number |
| ITEM | Item number and name |
| UNIT | Unit of measurement |
| DESCRIPTION | Item description |
| TYPE | Item type |
| VALUE | Unit value (₹) |
| INWARD STOCK | Total quantity received |
| OUTWARD STOCK | Total quantity issued |
| AVAILABLE STOCK | Current available stock (Inward - Outward) |

### 3. Features
- **Real-time Calculation**: Available stock is calculated dynamically
- **Color Coding**: 
  - Green: Positive stock
  - Red: Negative stock (deficit)
  - Gray: Zero stock
- **Print Support**: Built-in print functionality
- **Responsive Design**: Works on all screen sizes

## How to Use

### Adding Stock Entries

1. **Via Wagtail Admin**:
   - Go to Wagtail Admin → Inventory → Stock Register
   - Click "Add Stock Register"
   - Fill in the required fields:
     - Date
     - Item
     - Transaction Type (Inward/Outward)
     - Quantity (inward_qty or outward_qty)
     - Unit Value
     - Reference (optional)
   - Save

2. **Automatic Calculations**:
   - The system automatically sets the opposite quantity to 0
   - Total value is calculated automatically
   - Register number is auto-generated

### Viewing Stock Register

1. **Access the Stock Register**:
   - Go to Wagtail Admin
   - Click on "Stock Register" in the main menu (order 13)
   - Or navigate to: `/requisition/stock-register/`

2. **View Features**:
   - See all items with their current stock levels
   - View total inward and outward movements
   - See calculated available stock
   - Print the register using the Print button

## Technical Details

### Database Model
```python
class StockRegister(models.Model):
    register_no = CharField(max_length=10, unique=True, auto-generated)
    date = DateField()
    item = ForeignKey(Item)
    description = TextField()
    transaction_type = CharField(choices=['INWARD', 'OUTWARD'])
    inward_qty = PositiveIntegerField(default=0)
    outward_qty = PositiveIntegerField(default=0)
    unit_value = DecimalField(max_digits=10, decimal_places=2)
    total_value = DecimalField(auto-calculated)
    reference = CharField(max_length=100)
```

### URL Configuration
- Stock Register View: `/requisition/stock-register/`
- URL Name: `stock_register`

### Template Location
`Requisition/templates/requisition/stock_register.html`

## Integration with Existing System

The Stock Register is integrated into the Inventory Group in Wagtail:
- **Menu Location**: Inventory → Stock Register
- **Standalone Menu**: Stock Register (main menu)
- **Permissions**: Requires login (@login_required)

## Example Usage

### Scenario 1: Receiving New Stock
```
Date: 2025-10-25
Item: PART1001 - Motor
Transaction Type: INWARD
Inward Qty: 50
Unit Value: 1500.00
Reference: PO-12345

Result: Total Value = ₹75,000.00
```

### Scenario 2: Issuing Stock
```
Date: 2025-10-25
Item: PART1001 - Motor
Transaction Type: OUTWARD
Outward Qty: 10
Unit Value: 1500.00
Reference: REQ001

Result: Total Value = ₹15,000.00
```

### Available Stock Calculation
```
Total Inward: 50
Total Outward: 10
Available Stock: 50 - 10 = 40
```

## Tips

1. **Regular Updates**: Update stock entries regularly for accurate tracking
2. **Reference Numbers**: Always include reference numbers for traceability
3. **Unit Values**: Keep unit values up-to-date for accurate inventory valuation
4. **Review Reports**: Regularly review the stock register to identify:
   - Low stock items
   - Fast-moving items
   - Stock deficits (negative available stock)

## Future Enhancements

Potential features for future versions:
- [ ] Stock alerts for low inventory
- [ ] Export to Excel/PDF
- [ ] Date range filtering
- [ ] Stock movement history per item
- [ ] Batch/serial number tracking
- [ ] Integration with requisitions for automatic stock updates




