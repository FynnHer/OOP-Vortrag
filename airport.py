# ==============================================================
# 1. IMPORTS & UTILITIES
# ==============================================================

from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, List, Dict, ClassVar
import itertools

# ==============================================================
# 2. ENUMS
# ==============================================================

class FlightStatus(Enum):
    PLANNED = auto()
    BOARDING = auto()
    READY = auto()
    TAXI = auto()
    AIRBORNE = auto()
    LANDED = auto()
    CANCELLED = auto()

class RunwayStatus(Enum):
    FREE = auto()
    IN_USE = auto()
    MAINTENANCE = auto()

class EngineType(Enum):
    JET = "Jet"
    TURBOPROP = "Turboprop"
    PISTON = "Kolben"

# ==============================================================
# 3. EXCEPTIONS
# ==============================================================

class AirportError(Exception):
    pass

class CapacityExceededError(AirportError):
    pass

class GateNotAvailableError(AirportError):
    pass

class RunwayNotAvailableError(AirportError):
    pass

class FlightNotFoundError(AirportError):
    pass

class SchedulingError(AirportError):
    pass

# ==============================================================
# 4. FLUGZEUGE (ABSTRAKTE BASIS + SPEZIALISIERUNGEN)
# ==============================================================

_aircraft_id_counter = itertools.count(1)

@dataclass
class Aircraft(ABC):
    """
    Abstrakte Basisklasse für Luftfahrzeuge.
    Demonstriert:
      - Abstrakte Methoden (capacity, calculate_range_km)
      - Klassenattribut (total_aircraft_created)
      - Validierung in __post_init__
    """
    model: str
    empty_weight_kg: float
    max_takeoff_weight_kg: float
    engine_type: EngineType
    registration: str
    id: int = field(init=False)

    total_aircraft_created: ClassVar[int] = 0  # Klassenattribut

    def __post_init__(self):
        self.id = next(_aircraft_id_counter)
        type(self).total_aircraft_created += 1
        if self.empty_weight_kg >= self.max_takeoff_weight_kg:
            raise ValueError("Leermasse muss kleiner als MTOW sein.")

    @property
    @abstractmethod
    def capacity(self) -> int:
        """Muss von Unterklassen implementiert werden."""
        ...

    @abstractmethod
    def calculate_range_km(self) -> float:
        """Gibt eine (vereinfachte) Reichweite in km zurück."""
        ...

    def __str__(self):
        return f"{self.registration} ({self.model})"

@dataclass
class PassengerAircraft(Aircraft):
    seat_rows: int
    seats_per_row: int
    fuel_capacity_l: float
    avg_consumption_l_per_100km: float  # stark vereinfacht

    @property
    def capacity(self) -> int:
        return self.seat_rows * self.seats_per_row

    def calculate_range_km(self) -> float:
        if self.avg_consumption_l_per_100km <= 0:
            return 0
        return (self.fuel_capacity_l / self.avg_consumption_l_per_100km) * 100

@dataclass
class CargoAircraft(Aircraft):
    cargo_volume_m3: float
    max_payload_kg: float
    fuel_capacity_l: float
    efficiency_factor: float = 0.85  # simple factor

    @property
    def capacity(self) -> int:
        # Interpretieren Kapazität hier als mögliche Nutzlast
        return int(self.max_payload_kg)

    def calculate_range_km(self) -> float:
        # Sehr vereinfachtes Modell
        base = (self.fuel_capacity_l / 5) * self.efficiency_factor
        return base

# ==============================================================
# 5. INFRASTRUKTUR (GATE, RUNWAY)
# ==============================================================

_gate_id_counter = itertools.count(1)
_runway_id_counter = itertools.count(1)

@dataclass
class Gate:
    name: str
    max_wingspan_m: float
    occupied_by: Optional[int] = None  # Flight ID oder None
    id: int = field(init=False)

    def __post_init__(self):
        self.id = next(_gate_id_counter)

    def is_free(self) -> bool:
        return self.occupied_by is None

    def assign(self, flight_id: int):
        if not self.is_free():
            raise ValueError(f"Gate {self.name} ist belegt.")
        self.occupied_by = flight_id

    def release(self):
        self.occupied_by = None

@dataclass
class Runway:
    name: str
    length_m: int
    status: RunwayStatus = RunwayStatus.FREE
    current_flight: Optional[int] = None
    id: int = field(init=False)

    def __post_init__(self):
        self.id = next(_runway_id_counter)

    def is_available(self) -> bool:
        return self.status == RunwayStatus.FREE and self.current_flight is None

    def occupy(self, flight_id: int):
        if not self.is_available():
            raise ValueError(f"Piste {self.name} nicht verfügbar.")
        self.current_flight = flight_id
        self.status = RunwayStatus.IN_USE

    def release(self):
        self.current_flight = None
        self.status = RunwayStatus.FREE

# ==============================================================
# 6. FLIGHT
# ==============================================================

@dataclass
class Flight:
    flight_number: str
    origin: str
    destination: str
    aircraft: Aircraft
    planned_departure: str  # hier vereinfacht als String
    planned_arrival: str
    status: FlightStatus = FlightStatus.PLANNED
    gate_id: Optional[int] = None
    runway_id: Optional[int] = None
    passengers_checked_in: int = 0
    cargo_loaded_kg: float = 0.0
    id: int = field(init=False)

    _id_counter = 1  # Klassenzähler für Flüge

    def __post_init__(self):
        self.id = Flight._id_counter
        Flight._id_counter += 1

    def can_board(self) -> bool:
        return self.status == FlightStatus.BOARDING and isinstance(self.aircraft, PassengerAircraft)

    def board_passengers(self, count: int):
        if not isinstance(self.aircraft, PassengerAircraft):
            raise ValueError("Nur Passagiermaschinen können Passagiere boarden.")
        if self.status not in (FlightStatus.BOARDING, FlightStatus.PLANNED):
            raise ValueError("Boarding nicht möglich im Status " + self.status.name)
        new_total = self.passengers_checked_in + count
        if new_total > self.aircraft.capacity:
            raise CapacityExceededError("Kapazität überschritten.")
        self.passengers_checked_in = new_total
        if self.passengers_checked_in == self.aircraft.capacity:
            self.status = FlightStatus.READY

    def set_status(self, new_status: FlightStatus):
        # Hier könnte man Statusübergänge validieren (Aufgabe für Erweiterung)
        self.status = new_status

    def __str__(self):
        return f"Flight {self.flight_number} {self.origin}->{self.destination} ({self.status.name})"

# ==============================================================
# 7. SCHEDULING
# ==============================================================

@dataclass
class Schedule:
    flights: Dict[int, Flight] = field(default_factory=dict)

    def add_flight(self, flight: Flight):
        if flight.id in self.flights:
            raise SchedulingError("Flug-ID bereits vorhanden.")
        self.flights[flight.id] = flight

    def remove_flight(self, flight_id: int):
        if flight_id not in self.flights:
            raise FlightNotFoundError("Flug nicht gefunden.")
        del self.flights[flight_id]

    def find_by_number(self, flight_number: str) -> List[Flight]:
        return [f for f in self.flights.values() if f.flight_number == flight_number]

    def list_planned(self) -> List[Flight]:
        return [f for f in self.flights.values() if f.status == FlightStatus.PLANNED]

    def all(self) -> List[Flight]:
        return list(self.flights.values())

class SimpleScheduler:
    """
    Einfacher Scheduler:
    - Beispiel für spätere Erweiterung (Konflikterkennung etc.)
    """
    def __init__(self, schedule: Schedule):
        self.schedule = schedule

    def auto_ready_if_boarded(self):
        for f in self.schedule.all():
            if f.status == FlightStatus.BOARDING and hasattr(f.aircraft, "capacity"):
                if f.passengers_checked_in == f.aircraft.capacity:
                    f.set_status(FlightStatus.READY)

# ==============================================================
# 8. AIRPORT (Komposition: enthält Gates, Runways, Flights)
# ==============================================================

@dataclass
class Airport:
    name: str
    gates: List[Gate] = field(default_factory=list)
    runways: List[Runway] = field(default_factory=list)
    flights: List[Flight] = field(default_factory=list)

    def add_gate(self, gate: Gate):
        self.gates.append(gate)

    def add_runway(self, runway: Runway):
        self.runways.append(runway)

    def add_flight(self, flight: Flight):
        self.flights.append(flight)

    def find_flight(self, flight_id: int) -> Flight:
        for f in self.flights:
            if f.id == flight_id:
                return f
        raise FlightNotFoundError(f"Flug {flight_id} nicht gefunden.")

    def assign_gate(self, flight_id: int) -> Gate:
        flight = self.find_flight(flight_id)
        for g in self.gates:
            if g.is_free():
                g.assign(flight_id)
                flight.gate_id = g.id
                return g
        raise GateNotAvailableError("Kein Gate frei.")

    def release_gate(self, flight_id: int):
        flight = self.find_flight(flight_id)
        if flight.gate_id is None:
            return
        for g in self.gates:
            if g.id == flight.gate_id:
                g.release()
                flight.gate_id = None
                return

    def assign_runway_for_departure(self, flight_id: int) -> Runway:
        flight = self.find_flight(flight_id)
        for r in self.runways:
            if r.is_available():
                r.occupy(flight_id)
                flight.runway_id = r.id
                flight.set_status(FlightStatus.TAXI)
                return r
        raise RunwayNotAvailableError("Keine Piste frei.")

    def depart(self, flight_id: int):
        flight = self.find_flight(flight_id)
        if flight.status not in (FlightStatus.READY, FlightStatus.TAXI):
            raise ValueError("Flug nicht abflugbereit.")
        if flight.runway_id is None:
            raise ValueError("Keine Piste zugewiesen.")
        flight.set_status(FlightStatus.AIRBORNE)
        # Runway wieder freigeben
        for r in self.runways:
            if r.id == flight.runway_id:
                r.release()
                flight.runway_id = None
                break
        # Gate freigeben
        self.release_gate(flight_id)

    def arrive(self, flight_id: int):
        flight = self.find_flight(flight_id)
        if flight.status != FlightStatus.AIRBORNE:
            raise ValueError("Flug nicht in der Luft.")
        flight.set_status(FlightStatus.LANDED)

    def list_flights(self):
        return list(self.flights)

# ==============================================================
# 9. DEMO / NUTZUNG
# ==============================================================

def build_demo_airport() -> Airport:
    airport = Airport("Demo International")

    # Infrastruktur
    airport.add_gate(Gate("A1", max_wingspan_m=60))
    airport.add_gate(Gate("A2", max_wingspan_m=52))
    airport.add_runway(Runway("09L/27R", length_m=3800))
    airport.add_runway(Runway("09R/27L", length_m=3650))

    # Aircraft
    a1 = PassengerAircraft(
        model="A320neo",
        empty_weight_kg=43000,
        max_takeoff_weight_kg=79000,
        engine_type=EngineType.JET,
        registration="D-AIAB",
        seat_rows=30,
        seats_per_row=6,
        fuel_capacity_l=19000,
        avg_consumption_l_per_100km=2400/100,  # stark vereinfacht
    )

    a2 = CargoAircraft(
        model="B747F",
        empty_weight_kg=180000,
        max_takeoff_weight_kg=396000,
        engine_type=EngineType.JET,
        registration="D-CARG",
        cargo_volume_m3=700,
        max_payload_kg=130000,
        fuel_capacity_l=183000,
    )

    # Flüge
    f1 = Flight(
        flight_number="AB123",
        origin="DEMO",
        destination="LHR",
        aircraft=a1,
        planned_departure="2025-09-08 09:00",
        planned_arrival="2025-09-08 10:15",
    )

    f2 = Flight(
        flight_number="CG900",
        origin="DEMO",
        destination="JFK",
        aircraft=a2,
        planned_departure="2025-09-08 11:00",
        planned_arrival="2025-09-08 17:30",
    )

    airport.add_flight(f1)
    airport.add_flight(f2)

    return airport

def run_demo():
    airport = build_demo_airport()
    f1 = airport.flights[0]

    print("== DEMO START ==")
    gate = airport.assign_gate(f1.id)
    print("Gate zugewiesen:", gate.name)

    f1.set_status(FlightStatus.BOARDING)
    f1.board_passengers(100)
    f1.board_passengers(f1.aircraft.capacity - f1.passengers_checked_in)  # Auffüllen
    print("Passagiere an Bord:", f1.passengers_checked_in, "/", f1.aircraft.capacity)
    print("Status jetzt:", f1.status.name)

    runway = airport.assign_runway_for_departure(f1.id)
    print("Runway zugewiesen:", runway.name)

    airport.depart(f1.id)
    print("Abflug! Status:", f1.status.name)

    print("== DEMO ENDE ==")

if __name__ == "__main__":
    run_demo()

# ==============================================================
# 10. ERWEITERUNGSPUNKTE (Hinweise)
# ==============================================================
# - Status-Validierungslogik in Flight.set_status erweitern
# - Neue Aircraft-Subklassen (z.B. RegionalPassengerAircraft)
# - Boarding-Strategien (Strategy Pattern)
# - Crew-Verwaltung (Piloten / CabinCrew)
# - JSON-Persistenz (Serialisierung von Enum-Namen + Registrierungen als Referenzen)
# - Logging / Observer Pattern für Events (Gate zugewiesen, Start, Landung)
# - Scheduler-Konflikterkennung (gleiche Runway + Zeit)
