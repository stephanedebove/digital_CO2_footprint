from __future__ import annotations

from typing import Any, Dict, Tuple

from loader import Assumptions


def compute_total_kg_co2e(
    assumptions: Assumptions, role: str = "producer"
) -> Tuple[float, float, Dict[str, Any]]:
    """Compute annual CO2e emissions from online video, with detailed breakdown.

    Model overview (per-hour basis before annualization):
    1) Devices: production amortization (kg CO2e/h) + electricity usage (kWh/h × kg/kWh).
    2) Networks: energy model in kWh using a·GB + b/hour, then converted to kg via co2e_per_kWh.
       - a is per-GB energy, b is per-user-per-hour overhead.
    3) Data centers: emissions model already in kg using c·GB + d/hour.

    Annualization: both "producer" and "consumer" roles input weekly hours; totals are always
    expressed per year by multiplying weekly hours by 52.

    Args:
        assumptions: Loaded configuration and user inputs (see assumptions.yaml).
        role: Kept for UI/display symmetry ("producer" vs "consumer"); both are annualized the same.

    Returns:
        A tuple of (total_kg_usage_only, total_kg_with_production, intermediate_values)
        where the first value excludes device production, the second includes it,
        and intermediate_values exposes detailed values used in the calculation
        for display purposes (including per-network/per-device breakdowns).

    """

    intermediate_values: Dict[str, Any] = {}

    role = (role or "producer").lower()
    intermediate_values["role"] = role

    # Per-network resolution shares are already expressed in [0,1] and should sum to 1 per network.
    # Resolution mixes provided as percents (0..100); convert to fractions
    fixed_resolution_share = {
        k: v / 100.0 for k, v in assumptions["fixed_network_resolution_percent"].items()
    }
    fixed_resolution_total = sum(fixed_resolution_share.values())
    if fixed_resolution_total > 0.0:
        fixed_resolution_share = {
            key: value / fixed_resolution_total
            for key, value in fixed_resolution_share.items()
        }

    mobile_resolution_share = {
        k: v / 100.0
        for k, v in assumptions["mobile_network_resolution_percent"].items()
    }
    mobile_resolution_total = sum(mobile_resolution_share.values())
    if mobile_resolution_total > 0.0:
        mobile_resolution_share = {
            key: value / mobile_resolution_total
            for key, value in mobile_resolution_share.items()
        }
    # Compute GB/h per network using per-network resolution mix
    gb_per_hour_fixed = sum(
        fixed_resolution_share[key] * assumptions["video_bitrate_GB_per_hour"][key]
        for key in assumptions["video_bitrate_GB_per_hour"]
    )
    gb_per_hour_mobile = sum(
        mobile_resolution_share[key] * assumptions["video_bitrate_GB_per_hour"][key]
        for key in assumptions["video_bitrate_GB_per_hour"]
    )
    # Store for details
    intermediate_values["gb_per_hour_fixed"] = gb_per_hour_fixed
    intermediate_values["gb_per_hour_mobile"] = gb_per_hour_mobile

    # Device usage shares
    device_usage_share_fraction = {
        key: percent / 100.0 for key, percent in assumptions["device_percent"].items()
    }
    device_share_total = sum(device_usage_share_fraction.values())
    if device_share_total > 0.0:
        device_usage_share_fraction = {
            key: value / device_share_total
            for key, value in device_usage_share_fraction.items()
        }
    else:
        device_usage_share_fraction = {key: 0.0 for key in device_usage_share_fraction}
    device_keys = list(device_usage_share_fraction.keys())

    # Derive network shares from devices: each device splits its usage between fixed and mobile
    # Per-device fixed percent (0..100); convert to fraction [0,1]
    fixed_share_by_device_percent = assumptions["fixed_network_percent"]
    fixed_share_by_device = {
        # Convert percent [0..100] to a fraction [0..1] and clamp once
        k: min(1.0, max(0.0, float(v) / 100.0))
        for k, v in fixed_share_by_device_percent.items()
    }
    total_share_fixed = sum(
        device_usage_share_fraction[d] * fixed_share_by_device.get(d, 0.0)
        for d in device_keys
    )
    total_share_fixed = min(1.0, max(0.0, total_share_fixed))
    total_share_mobile = max(0.0, 1.0 - total_share_fixed)
    share_total = total_share_fixed + total_share_mobile
    if share_total > 0.0:
        total_share_fixed /= share_total
        total_share_mobile /= share_total
    intermediate_values["network_share_fixed"] = total_share_fixed * 100.0
    intermediate_values["network_share_mobile"] = total_share_mobile * 100.0

    # Device production amortization per video hour
    device_production_co2_per_video_hour_by_device: Dict[str, float] = {}
    for device in device_keys:
        production_kg = assumptions["device_production_kg_co2e"].get(device, 0.0)
        lifetime_hours = max(1.0, assumptions["device_lifetime_hours"].get(device, 1.0))
        production_per_device_hour = production_kg / lifetime_hours
        # New logic: consider production amortized per hour of device usage for video (video_share removed)
        device_production_co2_per_video_hour_by_device[device] = (
            device_usage_share_fraction[device] * production_per_device_hour
        )
        intermediate_values[
            f"device_production_co2_per_video_hour_by_device_{device}"
        ] = device_production_co2_per_video_hour_by_device[device]
    device_production_co2_per_video_hour_total = sum(
        device_production_co2_per_video_hour_by_device.values()
    )
    intermediate_values["device_production_co2_per_video_hour_total"] = (
        device_production_co2_per_video_hour_total
    )

    # Device electricity consumption per video hour
    device_energy_kwh_per_video_hour_by_device: Dict[str, float] = {}
    device_energy_co2_per_video_hour_by_device: Dict[str, float] = {}
    for device in device_keys:
        watts = assumptions["device_watts"].get(device, 0.0)
        kwh = device_usage_share_fraction[device] * (watts / 1000.0)
        device_energy_kwh_per_video_hour_by_device[device] = kwh
        device_energy_co2_per_video_hour_by_device[device] = (
            kwh * assumptions["co2e_per_kWh"]
        )
        intermediate_values[f"device_energy_kwh_per_video_hour_by_device_{device}"] = (
            kwh
        )
        intermediate_values[f"device_energy_co2_per_video_hour_by_device_{device}"] = (
            device_energy_co2_per_video_hour_by_device[device]
        )

    device_energy_co2_per_video_hour_total = sum(
        device_energy_co2_per_video_hour_by_device.values()
    )
    intermediate_values["device_energy_kwh_per_video_hour_total"] = sum(
        device_energy_kwh_per_video_hour_by_device.values()
    )
    intermediate_values["device_energy_co2_per_video_hour_total"] = (
        device_energy_co2_per_video_hour_total
    )
    intermediate_values["device_production_co2_per_video_hour_total_plus_energy"] = (
        device_production_co2_per_video_hour_total
        + device_energy_co2_per_video_hour_total
    )

    # Network calculations
    # CO2e = a*GB + b/hour, applied per network with its own GB/h and weighted by share of viewing hours
    # Derive network keys from assumptions to avoid hard-coding
    network_keys = list(assumptions["network_kwh_per_gb"].keys())
    gb_per_hour_by_network = {"fixed": gb_per_hour_fixed, "mobile": gb_per_hour_mobile}
    network_share = {"fixed": total_share_fixed, "mobile": total_share_mobile}
    network_kwh_per_video_hour_weighted: Dict[str, float] = {}
    network_co2_per_video_hour_weighted: Dict[str, float] = {}
    for network in network_keys:
        coefficient_a = assumptions["network_kwh_per_gb"][network]
        coefficient_b_hour = assumptions["network_kwh_per_user_per_hour"][network]
        # Network energy: a*GB/h + b/h, weighted by network share
        # Units note: networks are computed in kWh then converted to kg via co2e_per_kWh; datacenters are in kg.
        raw_kwh_with_b = (
            coefficient_a * gb_per_hour_by_network[network] + coefficient_b_hour
        )
        network_kwh_per_video_hour_weighted[network] = (
            raw_kwh_with_b * network_share[network]
        )
        network_co2_per_video_hour_weighted[network] = (
            network_kwh_per_video_hour_weighted[network] * assumptions["co2e_per_kWh"]
        )
        intermediate_values[f"network_a_kwh_per_gb_{network}"] = coefficient_a
        intermediate_values[f"network_b_kwh_per_user_hour_{network}"] = (
            coefficient_b_hour
        )
        intermediate_values[f"network_gb_per_hour_{network}"] = gb_per_hour_by_network[
            network
        ]
        intermediate_values[f"network_kwh_per_video_hour_{network}"] = (
            network_kwh_per_video_hour_weighted[network]
        )
        intermediate_values[f"network_co2_per_video_hour_{network}"] = (
            network_co2_per_video_hour_weighted[network]
        )

    # Datacenter calculations
    # CO2e = c*GB + d/hour. Use weighted GB/h across networks according to viewing share.
    datacenter_c_per_gb = assumptions["datacenter_kg_co2e"]["per_GB"]
    datacenter_d_per_hour = assumptions["datacenter_kg_co2e"]["per_hour"]
    gb_per_hour_total_weighted = (
        total_share_fixed * gb_per_hour_fixed + total_share_mobile * gb_per_hour_mobile
    )
    intermediate_values["gb_per_hour_total_weighted"] = gb_per_hour_total_weighted
    datacenter_co2_transfer = datacenter_c_per_gb * gb_per_hour_total_weighted
    datacenter_co2_runtime = datacenter_d_per_hour
    datacenter_co2_per_video_hour_total = (
        datacenter_co2_transfer + datacenter_co2_runtime
    )
    intermediate_values["datacenter_co2_per_video_hour_transfer"] = (
        datacenter_co2_transfer
    )
    intermediate_values["datacenter_co2_per_video_hour_runtime"] = (
        datacenter_co2_runtime
    )
    intermediate_values["datacenter_co2_per_video_hour_total"] = (
        datacenter_co2_per_video_hour_total
    )

    # Convert user-provided hours to annual hours
    # Both roles use weekly hours; results are per year
    hours_per_year = assumptions["hours_input"] * 52.0
    intermediate_values["hours_input"] = assumptions["hours_input"]
    intermediate_values["hours_input_year"] = hours_per_year

    intermediate_values["network_kwh_per_video_hour_total"] = sum(
        network_kwh_per_video_hour_weighted.values()
    )
    network_co2_per_video_hour_total = sum(network_co2_per_video_hour_weighted.values())
    intermediate_values["network_co2_per_video_hour_total"] = (
        network_co2_per_video_hour_total
    )

    # Now that network totals are available, compute per-hour usage-only and with-production totals
    kilograms_co2e_per_video_hour_usage_only = (
        device_energy_co2_per_video_hour_total
        + network_co2_per_video_hour_total
        + datacenter_co2_per_video_hour_total
    )
    kilograms_co2e_per_video_hour_with_production = (
        device_production_co2_per_video_hour_total
        + kilograms_co2e_per_video_hour_usage_only
    )
    intermediate_values["kg_per_video_hour_total"] = (
        kilograms_co2e_per_video_hour_with_production
    )
    intermediate_values["kg_per_video_hour_usage_only"] = (
        kilograms_co2e_per_video_hour_usage_only
    )

    total_kilograms_co2e_usage_only = (
        kilograms_co2e_per_video_hour_usage_only * hours_per_year
    )
    total_kilograms_co2e_with_production = (
        kilograms_co2e_per_video_hour_with_production * hours_per_year
    )
    intermediate_values["total_kg_co2e"] = total_kilograms_co2e_with_production
    intermediate_values["total_kg_co2e_usage_only"] = total_kilograms_co2e_usage_only

    intermediate_values["production_co2_total"] = (
        device_production_co2_per_video_hour_total * hours_per_year
    )
    intermediate_values["device_energy_co2_total"] = (
        device_energy_co2_per_video_hour_total * hours_per_year
    )
    intermediate_values["network_co2_total"] = (
        network_co2_per_video_hour_total * hours_per_year
    )
    intermediate_values["datacenter_co2_total"] = (
        datacenter_co2_per_video_hour_total * hours_per_year
    )

    return (
        total_kilograms_co2e_usage_only,
        total_kilograms_co2e_with_production,
        intermediate_values,
    )


def calculate_co2e_offsetting(
    total_kg_co2e: float, co2e_offsetting: Dict[str, float]
) -> Dict[str, float]:
    """Calculate the actions needed to compensate for the emitted CO2.

    Args:
        total_kg_co2e: Total CO2 emissions in kilograms.
        co2e_offsetting: Dictionary of CO2 savings per action (e.g., per km, per meal).

    Returns:
        A dictionary with actions as keys and the number of times each action needs to be performed.
    """
    offsetting = {}
    for action, saving in co2e_offsetting.items():
        if saving > 0:  # Avoid division by zero
            offsetting[action] = total_kg_co2e / saving
    return offsetting
