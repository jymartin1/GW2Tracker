# GW2 Legendary Tracker

A Python Flask web application that helps Guild Wars 2 players track their progress towards crafting legendary weapons.

## Features

- **Account Integration**: Connect your GW2 account using your API key
- **Progress Tracking**: View detailed progress for legendary weapon crafting
- **Time-Gated Materials**: Track daily crafting materials and estimate completion time
- **Inventory Scanning**: Automatically scans bank, character inventories, and material storage
- **Progress Visualization**: Beautiful dashboard with progress bars and completion estimates
- **Multiple Legendaries**: Support for tracking multiple legendary weapons

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Your GW2 API Key**:
   - Go to [account.arena.net/applications](https://account.arena.net/applications)
   - Click "New Key"
   - Give it a name (e.g., "Legendary Tracker")
   - Select these permissions: **account**, **inventories**, **characters**, **unlocks**, **progression**
   - Copy the generated key

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Access the App**:
   - Open your browser to `http://localhost:5000`
   - Enter your API key to connect your account
   - Select a legendary weapon to track progress

## Supported Legendary Weapons

Currently supports tracking for:
- **Twilight** (Greatsword)
- **Sunrise** (Greatsword) 
- **The Predator** (Rifle)

More legendary weapons can be easily added by updating the `legendary_data.py` file.

## How It Works

The application uses the Guild Wars 2 API v2 to:

1. **Fetch Account Data**: Retrieves your character information, inventories, bank contents, and material storage
2. **Calculate Progress**: Compares your current materials against legendary requirements
3. **Estimate Completion**: Calculates minimum days needed based on time-gated materials
4. **Display Results**: Shows detailed progress breakdown with visual indicators

## Time-Gated Materials

The tracker specifically accounts for daily time-gated crafting materials:
- **Spiritwood Plank** (1/day)
- **Deldrimor Steel Ingot** (1/day)
- **Elonian Leather Square** (1/day)  
- **Damask Patch** (1/day)

These materials typically require 100+ of each and can only be crafted once per day, making them the primary bottleneck for legendary crafting.

## API Permissions Required

The application requires these GW2 API permissions:
- **account**: Basic account information
- **inventories**: Access to bank and character inventories
- **characters**: Character names and equipment
- **unlocks**: Recipe and skin unlocks
- **progression**: Achievement and world completion status

## Security

- API keys are stored in session cookies (not permanently stored)
- All API requests use HTTPS to Guild Wars 2 servers
- No sensitive account information is logged or stored

## Development

The application consists of several key components:

- `app.py`: Main Flask application and routes
- `gw2_api.py`: GW2 API client with rate limiting
- `legendary_data.py`: Legendary weapon requirements database
- `progress_calculator.py`: Progress calculation logic
- `templates/`: HTML templates for the web interface

## Contributing

To add support for additional legendary weapons:

1. Research the legendary's requirements on the GW2 Wiki
2. Add the weapon data to `LEGENDARY_REQUIREMENTS` in `legendary_data.py`
3. Update `MATERIAL_IDS` if new materials are needed
4. Test the progress calculation

## Limitations

- Currently supports first-generation legendary weapons only
- Precursor progress detection is basic (checks if you own it)
- Achievement progress tracking is limited
- No support for legendary armor or accessories yet

## Rate Limiting

The application respects GW2 API rate limits:
- Maximum 300 requests per minute
- 200ms delay between requests
- Proper error handling for rate limit exceptions