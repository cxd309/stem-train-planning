import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
import polars as pl
from typing import Literal, List, Dict
from dataclasses import dataclass

StationName = str
TrainType = Literal["express", "local", "freight"]
Minutes = float
Kilometers = float
KMPH = float
Network = Dict[StationName, Kilometers]  # position in km from start


@dataclass
class Stop:
    name: StationName
    dwell_time: Minutes  # in minutes


Route = List[Stop]


@dataclass
class Timetable:
    stops: Route
    departure_station: StationName
    departure_time: Minutes


@dataclass
class Position:
    time: Minutes
    location: Kilometers


TrainMovement = List[Position]
TrainMovements = Dict[str, TrainMovement]


def get_train_movement(
    timetable: Timetable, velocity: KMPH, network: Network
) -> TrainMovement:
    movement: TrainMovement = []

    # Set and log current position and time
    departure_station = timetable.departure_station
    current_time: Minutes = timetable.departure_time
    current_location: Kilometers = network[departure_station]
    movement.append(Position(current_time, current_location))

    for i in range(0, len(timetable.stops)):
        destination_stop: Stop = timetable.stops[i]
        destination_station: StationName = destination_stop.name
        destination_dwell: Minutes = destination_stop.dwell_time
        destination_location: Kilometers = network[destination_station]

        journey_distance: Kilometers = abs(destination_location - current_location)
        arrival_time: Minutes = current_time + (journey_distance / velocity) * 60.0

        current_time = arrival_time
        current_location = destination_location
        movement.append(Position(current_time, current_location))

        current_time += destination_dwell
        movement.append(Position(current_time, current_location))

    return movement


def build_network(spacing: Kilometers) -> Network:
    network: Network = {
        "A": 0 * spacing,
        "B": 1 * spacing,
        "C": 2 * spacing,
        "D": 3 * spacing,
        "E": 4 * spacing,
        "F": 5 * spacing,
        "G": 6 * spacing,
    }
    return network


def get_express_movement(departure: Minutes, network: Network) -> TrainMovement:
    express_dwell: Minutes = 7.0
    express_velocity: KMPH = 120.0
    express_route: Route = [
        Stop("D", express_dwell),
        Stop("G", 0.0),
    ]
    return get_train_movement(
        Timetable(express_route, "A", departure), express_velocity, network
    )


def get_local_movement(departure: Minutes, network: Network) -> TrainMovement:
    local_dwell: Minutes = 2.5
    local_velocity: KMPH = 80.0
    local_route: Route = [
        Stop("B", local_dwell),
        Stop("C", local_dwell),
        Stop("D", local_dwell),
        Stop("E", local_dwell),
        Stop("F", local_dwell),
        Stop("G", 0.0),
    ]
    return get_train_movement(
        Timetable(local_route, "A", departure), local_velocity, network
    )


def get_freight_movement(departure: Minutes, network: Network) -> TrainMovement:
    freight_dwell: Minutes = 15.0
    freight_velocity: KMPH = 60.0
    freight_route: Route = [
        Stop("G", 0.0),
    ]
    return get_train_movement(
        Timetable(freight_route, "A", departure), freight_velocity, network
    )


def plot_train_movements(movements: TrainMovements, filename: str, network: Network):
    plt.figure(figsize=(12, 6))

    for label, movement in movements.items():
        times = [pos.time for pos in movement]
        locations = [pos.location for pos in movement]
        plt.plot(times, locations, label=label)

    plt.xlabel("Time (minutes)")
    plt.ylabel("Distance (km)")
    plt.title("Train Graph")
    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(which="major", color="grey", linestyle="-", linewidth=0.8)
    ax.grid(which="minor", color="gray", linestyle="--", linewidth=0.4)

    plt.grid(True)
    plt.legend()

    sorted_stations = sorted(network.items(), key=lambda x: x[1])
    y_ticks = [dist for _, dist in sorted_stations]
    y_labels = [name for name, _ in sorted_stations]

    # Create twin y-axis (shares y with ax)
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())  # sync limits
    ax2.set_yticks(y_ticks)
    ax2.set_yticklabels(y_labels)
    ax2.tick_params(axis="y", which="both", length=0)

    plt.tight_layout()
    plt.savefig(filename)


def export_movements_to_csv(movements: TrainMovements, filename: str):
    rows = []
    for train_name, positions in movements.items():
        for pos in positions:
            rows.append(
                {
                    "Train": train_name,
                    "Time": round(pos.time, 2),
                    "Distance": round(pos.location),
                }
            )
    df = pl.DataFrame(rows)
    df.write_csv(filename)
    print(f"Exported train movements to {filename}")


def run_activity():
    spacing: Kilometers = 5
    network = build_network(spacing)

    # even spacing
    even_movements = {
        "Express 1": get_express_movement(0, network),
        "Local 1": get_local_movement(5, network),
        "Express 2": get_express_movement(30, network),
        "Local 2": get_local_movement(35, network),
        "Freight 2": get_freight_movement(46, network),
        "Express start": get_express_movement(60, network),
    }
    plot_train_movements(even_movements, "activity-even.png", network)

    # even extra spacing
    even_movements = {
        "Express 1": get_express_movement(0, network),
        "Local 1": get_local_movement(5, network),
        "Local (extra)": get_local_movement(12.5, network),
        "Express 2": get_express_movement(30, network),
        "Local 2": get_local_movement(35, network),
        "Freight 2": get_freight_movement(46, network),
        "Express start": get_express_movement(60, network),
    }
    plot_train_movements(even_movements, "activity-even-extra.png", network)

    # grouped spacing
    grouped_movements = {
        "Express 1": get_express_movement(0, network),
        "Express 2": get_express_movement(12, network),
        "Freight": get_freight_movement(17, network),
        "Local 1": get_local_movement(23, network),
        "Local 2": get_local_movement(23 + 7.5, network),
        "Local 3": get_local_movement(23 + 2 * 7.5, network),
        "Local 4": get_local_movement(23 + 3 * 7.5, network),
        "Express start": get_express_movement(60, network),
    }
    plot_train_movements(grouped_movements, "activity-grouped.png", network)


def run_figures():
    # http://www.railwaycodes.org.uk/line/track/distances/undergrounddistances.pdf
    victoria_network: Network = {
        "Walthamstow Central": 27.33,
        "Blackhorse Road": 28.79,
        "Tottenham Hale": 30.15,
        "Seven Sisters": 31.19,
        "Finsbury Park": 34.34,
        "Highbury and Islington": 36.29,
        "Kings Cross St Pancras": 38.72,
        "Euston": 39.47,
        "Warren Street": 40.22,
        "Oxford Circus": 41.14,
        "Green Park": 42.23,
        "Victoria": 43.35,
        "Pimlico": 44.57,
        "Vauxhall": 45.37,
        "Stockwell": 47.13,
        "Brixton": 48.61,
    }

    metro_route: Route = []

    for station in victoria_network:
        metro_route.append(Stop(station, 1))

    tph: int = 30

    n_trains = 15

    movements: TrainMovements = {}

    for i in range(0, n_trains):
        departure_time: Minutes = i * (60 / tph)
        timetable = Timetable(
            stops=metro_route,
            departure_station="Walthamstow Central",
            departure_time=departure_time,
        )

        movement = get_train_movement(timetable, 50, victoria_network)

        movements[f"Metro {str(i)}"] = movement

    plot_train_movements(movements, "victoria.png", victoria_network)


def main():
    run_activity()
    run_figures()


if __name__ == "__main__":
    main()
