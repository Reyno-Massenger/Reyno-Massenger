# LiteSpeed LSAPI worker saturation

The supplied server output showed `LSAPI_CHILDREN` configured at **6**, two
extra children in use, **8 current workers**, and **7–8 workers busy**. This is
a host-level process-pool limit, not a setting exposed by the Flask/Passenger
application. `passenger_wsgi.py` imports the Flask app and does not configure
LiteSpeed worker counts.

## Application-side work in this repository

- Chat message polling remains on its existing fast cadence; secondary chat
  metadata, pinned-message and delivery-status refreshes are consolidated to a
  **15-second** cadence rather than running on every message poll.
- Admin-controlled authentication policy is cached per worker for **15 seconds**
  to avoid a settings-table lookup on every login or registration request.

These changes reduce avoidable application/database work; they do **not** raise
the LSAPI child limit or guarantee that a saturated host will recover.

## Host-side action

If workers remain near capacity, the hosting owner or provider must inspect and
adjust the LiteSpeed/LSAPI application settings (including `LSAPI_CHILDREN` and
the extra-child policy) in the hosting control panel or server configuration,
then restart/reload the application as required by that host. Increase worker
counts only after checking available memory and database connection limits.
The repository cannot safely make this server-level change.
