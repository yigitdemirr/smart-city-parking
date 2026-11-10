# Mobile client (Flutter, Android target)

Planned for Milestone 2 (client-server prototype). Design is fixed in M1:

- Screens: Login/Register, Find parking, Facility spaces, Reservation (hold timer + simulated payment), History, Admin spaces
- Local SQLite cache for read-only data (search results, history) with `generatedAt` labels
- Pending-operations store: `operationId` + request, resolved via `GET /operations/{id}` after reconnection
- Location module: mixed INFORM rule (new fix when moved > 100 m OR older than 60 s while the search screen is open)
