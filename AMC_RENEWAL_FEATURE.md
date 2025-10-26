# AMC Renewal Feature Implementation

## Overview
Added a comprehensive AMC renewal feature that allows users to renew expired or expiring AMCs with pre-filled data from the existing AMC record.

## Features Implemented

### 1. Renew AMC Button ("Renew AMC")
- Added a custom button in the Wagtail admin AMC listing page
- Button appears similar to the "Download PDF" button in the complaints page
- Icon: `repeat` (refresh/renew icon)
- Priority: 90
- **IMPORTANT**: Only shows for expired AMCs or AMCs expiring within 30 days
- Not displayed for active AMCs with more than 30 days remaining

### 2. Renewal Form with Pre-filled Data
The renewal form includes the following fields that are pre-filled from the existing AMC:
- **START DATE**: Automatically set to the day after the current AMC's end date
- **END DATE**: Automatically set to 1 year from the new start date
- **AMC TYPE**: Pre-filled with the existing AMC type
- **PAYMENT MODE**: Pre-filled with the existing payment terms
- **NO OF SERVICES (ROUTINE SERVICES)**: Pre-filled with existing value
- **AMOUNT**: Pre-filled with existing price
- **NOTES**: Pre-filled with existing notes
- **AMC DETAILS**: Pre-filled with equipment number and site address

### 3. Backend Implementation

#### Files Modified:
1. **amc/wagtail_hooks.py**
   - Added `@hooks.register('register_snippet_listing_buttons')` decorator
   - Created `add_renew_amc_button()` function to add the button
   - Added three new URL routes:
     - `/admin/snippets/amc/amc/renew/<int:pk>/` - Page to render renewal form
     - `/admin/api/amc/renew-data/<int:pk>/` - API to fetch AMC data
     - `/admin/api/amc/renew/` - API to create renewed AMC

2. **amc/views.py**
   - Added `renew_amc_page()` - Renders the renewal page with modal
   - Added `get_amc_renewal_data()` - Fetches and formats AMC data for renewal
   - Added `create_renewed_amc()` - Creates a new AMC record based on renewal data
   - Imported `Item` model

3. **amc/templates/amc/renew_amc.html** (NEW FILE)
   - Full-page form interface matching the add_amc_custom.html style
   - Blue gradient header matching the design from the image
   - Form fields arranged in a 2-column grid
   - Loading spinner while fetching data
   - JavaScript to handle:
     - Loading AMC data on page load
     - Pre-filling form fields
     - Form submission
     - Success/error handling
     - Redirect to AMC list after success

### 4. Data Flow

1. **User clicks "Renew AMC" button** → Opens renewal page
2. **Page loads** → JavaScript fetches AMC data via `/admin/api/amc/renew-data/<pk>/`
3. **Data is pre-filled** → Form fields populated with existing AMC data
4. **User modifies fields** → Can change dates, amounts, notes, etc.
5. **User clicks SAVE** → Data sent to `/admin/api/amc/renew/`
6. **New AMC created** → Success message shown, redirects to AMC list

### 5. Key Features

- **Automatic Date Calculation**: 
  - Start date = end date of current AMC + 1 day
  - End date = start date + 365 days

- **Pre-filled Data**: All relevant fields from the existing AMC are automatically populated

- **Editable Fields**: User can modify any field before saving

- **New AMC Record**: Creates a completely new AMC with a new reference ID

- **Same Customer**: Maintains the customer relationship

- **Validation**: Validates required fields before creating renewal

## Usage

1. Navigate to **AMC > All AMCs** in Wagtail admin
2. Find an expired AMC or an AMC expiring within 30 days
3. Click the **"Renew AMC"** button in the actions column (only visible for expired/expiring AMCs)
4. Review and modify the pre-filled data in the renewal form
5. Click **"SAVE"** to create the renewal
6. You'll be redirected to the AMC list with a success message

**Note**: The "Renew AMC" button only appears for:
- AMCs that have already expired (end_date < today)
- AMCs expiring within the next 30 days (0 <= days_until_expiry <= 30)

## Technical Details

- **Modal Styling**: Matches the design shown in the image
- **CSRF Protection**: Properly handles CSRF tokens
- **Error Handling**: Comprehensive error messages for failed operations
- **Loading States**: Shows loading indicator while fetching data
- **Button States**: Disables submit button during save operation

## Notes

- The "AMC DETAILS" field currently combines equipment number and site address
- The renewal creates a brand new AMC record with a new reference ID
- All financial data (amounts, payments) starts fresh for the renewal
- The original AMC record remains unchanged

