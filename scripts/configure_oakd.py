#!/usr/bin/env python3
"""Configure a Luxonis OAK-D PoE camera for the RAMMP network."""

import argparse
import ipaddress
import sys

DEFAULT_MASK = "255.255.255.0"
DEFAULT_GATEWAY = "192.168.1.1"


def valid_ipv4(value: str) -> str:
    try:
        return str(ipaddress.IPv4Address(value))
    except ipaddress.AddressValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid IPv4 address: {value}") from exc


def validate_network(ip: str, mask: str, gateway: str) -> None:
    address = ipaddress.IPv4Address(ip)
    network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
    gateway_address = ipaddress.IPv4Address(gateway)

    if address in (network.network_address, network.broadcast_address):
        raise ValueError(f"{ip} cannot be a network or broadcast address")

    if gateway_address not in network:
        raise ValueError(f"gateway {gateway} is outside {network}")

    if gateway_address in (network.network_address, network.broadcast_address):
        raise ValueError(f"gateway {gateway} cannot be a network or broadcast address")


def configure(ip: str, mask: str, gateway: str, confirm: bool) -> int:
    validate_network(ip, mask, gateway)

    print("OAK-D network configuration")
    print(f"  Static IP : {ip}")
    print(f"  Netmask   : {mask}")
    print(f"  Gateway   : {gateway}")

    if not confirm:
        answer = input("Flash this configuration to the OAK-D? [y/N] ")
        if answer.strip().lower() != "y":
            print("Aborted.")
            return 0

    try:
        import depthai as dai
    except ImportError:
        print(
            "DepthAI is not installed. Install it with:\n"
            "  python -m pip install depthai",
            file=sys.stderr,
        )
        return 1

    found, info = dai.DeviceBootloader.getFirstAvailableDevice()

    if not found:
        print(
            "No OAK-D bootloader device found.\n"
            "Connect the OAK-D to the host with USB and power it on.",
            file=sys.stderr,
        )
        return 1

    print(f"Found OAK-D: {info.name}")

    config = dai.DeviceBootloader.Config()
    config.setStaticIPv4(ip, mask, gateway)

    with dai.DeviceBootloader(info) as bootloader:
        success, error = bootloader.flashConfig(config)

    if not success:
        print(f"Failed to configure OAK-D: {error}", file=sys.stderr)
        return 1

    print(f"Successfully configured OAK-D with static IP {ip}.")
    print("Reconnect the camera to the RAMMP network.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure an OAK-D PoE camera for the RAMMP network."
    )
    parser.add_argument(
        "--ip",
        required=True,
        type=valid_ipv4,
        help="Target static IPv4 address",
    )
    parser.add_argument(
        "--mask",
        type=valid_ipv4,
        default=DEFAULT_MASK,
        help=f"IPv4 netmask (default: {DEFAULT_MASK})",
    )
    parser.add_argument(
        "--gateway",
        type=valid_ipv4,
        default=DEFAULT_GATEWAY,
        help=f"IPv4 gateway (default: {DEFAULT_GATEWAY})",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt",
    )

    args = parser.parse_args()

    try:
        return configure(args.ip, args.mask, args.gateway, args.yes)
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
