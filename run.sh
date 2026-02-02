#!/usr/bin/with-contenv bashio

bashio::log.info "Starting OctoDNS GUI Add-on..."

# Read configuration
ZONE_FILE_PATH=$(bashio::config 'zone_file_path')

# Log enabled providers
bashio::log.info "Enabled providers:"
if bashio::config.true 'providers.cloudflare'; then
    bashio::log.info "  - cloudflare"
fi
if bashio::config.true 'providers.ovh'; then
    bashio::log.info "  - ovh"
fi
if bashio::config.true 'providers.pihole'; then
    bashio::log.info "  - pihole"
fi
if bashio::config.true 'providers.netbox_dns'; then
    bashio::log.info "  - netbox_dns"
fi
if bashio::config.true 'providers.netbox'; then
    bashio::log.info "  - netbox"
fi
if bashio::config.true 'providers.bind'; then
    bashio::log.info "  - bind"
fi

bashio::log.info "Zone File Path: ${ZONE_FILE_PATH}"

# Create zone directory if it doesn't exist
if [ ! -d "$ZONE_FILE_PATH" ]; then
    bashio::log.info "Creating zone directory: ${ZONE_FILE_PATH}"
    mkdir -p "$ZONE_FILE_PATH"
fi

# Export config as environment variables for the app
export ZONE_FILE_PATH

# Check if SUPERVISOR_TOKEN is present
if [ -z "$SUPERVISOR_TOKEN" ]; then
    bashio::log.warning "SUPERVISOR_TOKEN not found. API calls will fail."
else
    bashio::log.info "SUPERVISOR_TOKEN found."
fi

bashio::log.info "Starting Flask server on port 8100..."

# Start the Python application
exec python3 /app/app.py
