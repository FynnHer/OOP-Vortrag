# OOP-Vortrag von Linus und Fynn-Lasse

---

## Aufgaben

1. Beispielaufgabe 1
   >Hier steht etwas über die Aufgabe
3. Beispielaufgabe 2
   >Hier steht etwas über die Aufgabe

---

## Klassendiagramm (PlantUML)

Das folgende PlantUML-Diagramm zeigt die Beziehungen. Kopiere den Code z.B. nach https://www.plantuml.com/plantuml/ oder verwende ein lokales PlantUML-Tool.

```plantuml
@startuml
skinparam classAttributeIconSize 0

title Flughafen OOP System (vereinfachtes Modell)

class Airport {
  - name: str
  - gates: List[Gate]
  - runways: List[Runway]
  - flights: List[Flight]
  + add_gate(g: Gate)
  + add_runway(r: Runway)
  + add_flight(f: Flight)
  + assign_gate(flight_id)
  + assign_runway_for_departure(flight_id)
  + depart(flight_id)
  + arrive(flight_id)
  + find_flight(flight_id): Flight
}

class Gate {
  - id: int
  - name: str
  - max_wingspan_m: float
  - occupied_by: int?
  + is_free(): bool
  + assign(flight_id)
  + release()
}

class Runway {
  - id: int
  - name: str
  - length_m: int
  - status: RunwayStatus
  - current_flight: int?
  + is_available(): bool
  + occupy(flight_id)
  + release()
}

enum RunwayStatus {
  FREE
  IN_USE
  MAINTENANCE
}

enum FlightStatus {
  PLANNED
  BOARDING
  READY
  TAXI
  AIRBORNE
  LANDED
  CANCELLED
}

enum EngineType {
  JET
  TURBOPROP
  PISTON
}

abstract class Aircraft {
  + id: int
  + model: str
  + registration: str
  + empty_weight_kg: float
  + max_takeoff_weight_kg: float
  + engine_type: EngineType
  + capacity: int {abstract}
  + calculate_range_km(): float {abstract}
}

class PassengerAircraft {
  + seat_rows: int
  + seats_per_row: int
  + fuel_capacity_l: float
  + avg_consumption_l_per_100km: float
  + capacity: int
  + calculate_range_km(): float
}

class CargoAircraft {
  + cargo_volume_m3: float
  + max_payload_kg: float
  + fuel_capacity_l: float
  + efficiency_factor: float
  + capacity: int
  + calculate_range_km(): float
}

class Flight {
  + id: int
  + flight_number: str
  + origin: str
  + destination: str
  + planned_departure: str
  + planned_arrival: str
  + status: FlightStatus
  + gate_id: int?
  + runway_id: int?
  + passengers_checked_in: int
  + cargo_loaded_kg: float
  + board_passengers(count)
  + set_status(new_status)
}

class Schedule {
  - flights: Dict[int, Flight]
  + add_flight(f: Flight)
  + remove_flight(id: int)
  + find_by_number(num: str): List[Flight]
  + list_planned(): List[Flight]
  + all(): List[Flight]
}

class SimpleScheduler {
  - schedule: Schedule
  + auto_ready_if_boarded()
}

Airport "1" o-- "*" Gate
Airport "1" o-- "*" Runway
Airport "1" o-- "*" Flight
Flight "1" *-- "1" Aircraft
Schedule "1" o-- "*" Flight
SimpleScheduler "1" o-- "1" Schedule

Aircraft <|-- PassengerAircraft
Aircraft <|-- CargoAircraft

FlightStatus <-- Flight
RunwayStatus <-- Runway
EngineType <-- Aircraft
@enduml
```

### Legende / Beziehungen
- A o-- B: Komposition (A besitzt B, aber Lebenszyklus kann relativ unabhängig sein)
- A *-- B: Stärkere Besitz-Beziehung (hier symbolisch für "hat genau eins")
- Vererbung: Pfeil mit leerer Spitze (z.B. PassengerAircraft erbt von Aircraft)
- Enums werden von Klassen referenziert (Abhängigkeit)

### Wichtige OOP-Konzepte im Diagramm
- Abstraktion: Aircraft ist abstrakt (abstrakte Methoden)
- Vererbung: PassengerAircraft, CargoAircraft
- Polymorphie: Nutzung über den gemeinsamen Typ Aircraft
- Komposition: Airport verwaltet Gates, Runways, Flights
- Kapselung: Methoden sorgen für Zustandsänderungen (assign_gate, board_passengers)

